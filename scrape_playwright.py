"""
Scraper do Bonfire Tales RPG (WorldAnvil) via Playwright.

Usa o Chromium com seu perfil/cookies reais -> passa pelo Cloudflare.
Lê as páginas de classe, persiste HTML em ./dumps/ e chama o parser/persistência
já implementado em scrape_classes.py.

Instalação (Windows):
    pip install playwright
    playwright install chromium

Uso:
    # Usa um perfil dedicado (persistente em ./pw_profile)
    # Na primeira vez, abre o Chromium não-headless para você fazer login
    python scrape_playwright.py --urls urls_classes.txt

    # Reaproveitando seu perfil do Chrome real (Windows):
    python scrape_playwright.py --urls urls_classes.txt --chrome-profile

    # Só abre o navegador e espera você logar (quando usar perfil novo)
    python scrape_playwright.py --login

    # Salva os HTMLs em ./dumps/ mas NÃO grava no DB (inspecionar antes)
    python scrape_playwright.py --urls urls_classes.txt --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import os
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    sys.exit("Playwright não instalado.  Rode: pip install playwright && "
             "playwright install chromium")

# reusa o parser/persistência
sys.path.insert(0, str(Path(__file__).parent))
from scrape_classes import parse_class_page, save, DB_PATH  # noqa: E402

DUMP_DIR = Path(__file__).parent / "dumps"
DUMP_DIR.mkdir(exist_ok=True)

WINDOWS_CHROME_USERDATA = Path(os.environ.get("LOCALAPPDATA", "")) / r"Google\Chrome\User Data"


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "item"


async def launch(pw, args) -> tuple:
    """Retorna (context, browser_or_None).  Usa persistent_context."""
    if args.chrome_profile:
        if not WINDOWS_CHROME_USERDATA.exists():
            sys.exit(f"Perfil Chrome não encontrado em {WINDOWS_CHROME_USERDATA}")
        # IMPORTANTE: o Chrome precisa estar FECHADO para abrir o user-data-dir
        print(f"Usando perfil Chrome real: {WINDOWS_CHROME_USERDATA}")
        ctx = await pw.chromium.launch_persistent_context(
            str(WINDOWS_CHROME_USERDATA),
            channel="chrome",
            headless=False,
            args=["--profile-directory=Default"],
        )
        return ctx, None

    profile_dir = Path(__file__).parent / "pw_profile"
    ctx = await pw.chromium.launch_persistent_context(
        str(profile_dir),
        headless=args.headless,
        user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"),
        viewport={"width": 1280, "height": 900},
    )
    return ctx, None


async def wait_for_content(page) -> None:
    # aguarda o Cloudflare challenge sumir e a página real aparecer
    try:
        await page.wait_for_selector("h1, main, article", timeout=45000)
    except Exception:
        pass
    # guarda alguns ms para JS final
    await page.wait_for_timeout(800)


async def fetch_one(page, url: str) -> str:
    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    await wait_for_content(page)
    return await page.content()


async def run(args) -> None:
    urls: list[str] = []
    if args.url:
        urls.append(args.url)
    if args.urls:
        for line in Path(args.urls).read_text(encoding="utf-8").splitlines():
            u = line.strip()
            if u and not u.startswith("#"):
                urls.append(u)

    async with async_playwright() as pw:
        ctx, _ = await launch(pw, args)
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()

        if args.login:
            print("=> Abrindo WorldAnvil para login. Faça login, depois feche o navegador.")
            await page.goto("https://www.worldanvil.com/login")
            await page.wait_for_timeout(1000 * 60 * 10)   # 10 min
            await ctx.close()
            return

        conn = sqlite3.connect(DB_PATH) if not args.dry_run else None
        try:
            for url in urls:
                try:
                    print(f"-> {url}")
                    html = await fetch_one(page, url)
                    (DUMP_DIR / f"{slug(url)}.html").write_text(html, encoding="utf-8")
                    parsed = parse_class_page(html, url)
                    name = parsed.get("nome")
                    if not name:
                        print(f"   (sem nome — checar {DUMP_DIR/slug(url)}.html)")
                        continue
                    print(f"   {name!r} — subs={len(parsed['subclasses'])}, "
                          f"prog={len(parsed['progressao'])}, "
                          f"habs={len(parsed['habilidades'])}")
                    if conn is not None:
                        r = save(parsed, conn)
                        print(f"   DB: {r}")
                except Exception as e:
                    print(f"   ERRO: {e}", file=sys.stderr)
        finally:
            if conn:
                conn.close()
            await ctx.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--urls", help="Arquivo com URLs (uma por linha)")
    ap.add_argument("--login", action="store_true",
                    help="Abre o site para login e encerra (cria sessão no perfil)")
    ap.add_argument("--chrome-profile", action="store_true",
                    help="Usa o perfil real do Chrome do Windows (CHROME PRECISA ESTAR FECHADO)")
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--dry-run", action="store_true",
                    help="Salva HTML e parseia, mas não grava no DB")
    args = ap.parse_args()
    if not (args.url or args.urls or args.login):
        ap.error("informe --url / --urls / --login")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
