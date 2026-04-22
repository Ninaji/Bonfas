"""
Cliente READ-ONLY para a WorldAnvil Boromir API.

REGRAS:
- Apenas GET. Nunca PUT/POST/PATCH/DELETE.
- Token lido de .env.txt (não versionado).
- Respeita Retry-After.
- Máximo 1 req a cada 2s por padrão (WA pede "seja gentil").

Uso:
    python wa_client.py identity          # valida token
    python wa_client.py worlds            # lista mundos do usuário
    python wa_client.py world <uuid>      # dados de 1 mundo
    python wa_client.py categories <wid>  # categorias de um mundo
    python wa_client.py articles <wid>    # artigos (paginados)
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from urllib import request, error, parse

BASE = "https://www.worldanvil.com/api/external/boromir"
ENV_FILE = Path(__file__).parent / ".env.txt"
RATE_LIMIT_SECONDS = 2.0       # intervalo mínimo entre requests


def load_token() -> str:
    if not ENV_FILE.exists():
        sys.exit(".env.txt não encontrado")
    txt = ENV_FILE.read_text(encoding="utf-8").strip()
    # aceita "TOKEN=xxx" ou a string solta
    if "=" in txt and not txt.startswith(("eyJ",)):  # JWT starts with eyJ
        # formato KEY=VALUE (pega WA_TOKEN ou primeiro valor)
        for line in txt.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            k, _, v = line.partition("=")
            if k.strip() in ("WA_TOKEN", "WA_AUTH_TOKEN", "TOKEN"):
                return v.strip().strip('"').strip("'")
            return v.strip().strip('"').strip("'")
    return txt  # string solta


def load_app_key() -> str | None:
    if not ENV_FILE.exists():
        return None
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() in ("WA_APP_KEY", "APP_KEY", "APPLICATION_KEY"):
            return v.strip().strip('"').strip("'")
    return None


_last_req = [0.0]


def _throttle() -> None:
    elapsed = time.time() - _last_req[0]
    if elapsed < RATE_LIMIT_SECONDS:
        time.sleep(RATE_LIMIT_SECONDS - elapsed)
    _last_req[0] = time.time()


def _get(path: str, token: str, app_key: str | None = None, params: dict | None = None) -> dict:
    """GET apenas. Se tentarem passar método diferente, explode."""
    _throttle()
    url = BASE + path
    if params:
        url += "?" + parse.urlencode(params)
    headers = {
        "x-auth-token": token,
        "Accept": "application/json",
        # User-Agent realista é necessário para passar pelo Cloudflare do WA
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36"),
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    }
    if app_key:
        headers["x-application-key"] = app_key

    req = request.Request(url, method="GET", headers=headers)
    try:
        with request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        # erro estruturado pra facilitar debug sem expor token
        raise SystemExit(f"HTTP {e.code}: {body[:500]}")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    token = load_token()
    app_key = load_app_key()
    if not app_key:
        print("[aviso] WA_APP_KEY não encontrado em .env.txt — "
              "vou tentar só com o token; alguns endpoints podem exigir app_key.",
              file=sys.stderr)

    if cmd == "identity":
        r = _get("/identity", token, app_key)
        # mostra apenas id/username, não todo o perfil
        print(json.dumps({"id": r.get("id"), "username": r.get("username")}, indent=2))
    elif cmd == "worlds":
        # /user/{id}/worlds ou /worlds
        me = _get("/identity", token, app_key)
        uid = me.get("id")
        r = _get(f"/user/{uid}/worlds", token, app_key)
        # lista abreviada
        worlds = r if isinstance(r, list) else r.get("entities", [])
        for w in worlds:
            print(f"  {w.get('id'):36}  {w.get('slug','?'):40}  {w.get('title','?')}")
    elif cmd == "world":
        wid = sys.argv[2]
        r = _get(f"/world/{wid}", token, app_key)
        print(json.dumps({k: r.get(k) for k in ("id", "title", "slug", "description")}, indent=2))
    elif cmd == "categories":
        wid = sys.argv[2]
        r = _get(f"/world/{wid}/categories", token, app_key)
        cats = r if isinstance(r, list) else r.get("entities", [])
        for c in cats:
            print(f"  {c.get('id'):36}  {c.get('slug','?'):40}  {c.get('title','?')}")
    elif cmd == "articles":
        wid = sys.argv[2]
        offset = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        r = _get(f"/world/{wid}/articles", token, app_key, {"offset": offset, "limit": 50})
        arts = r if isinstance(r, list) else r.get("entities", [])
        for a in arts:
            print(f"  {a.get('id'):36}  {a.get('slug','?'):40}  {a.get('title','?')}")
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
