"""
Migration v2: pickers para opcoes A/B/C de habilidades.

Adiciona ao schema:
  TB_ClasseHabilidade.OpcaoTipoJSON (TEXT NULL)
  TB_PersonagemHabilidadeOpcao.Id_Opcao (INTEGER NULL)
  TB_PersonagemHabilidadeOpcao.SlotIndex (INTEGER NULL)
  Indexes em (Id_Opcao) e (Id_Personagem,Id_Habilidade,SlotIndex)

Classifica:
  515 Disciplina Marcial -> [{tipo:'estilo-de-luta',quantidade:1},{tipo:'maestria-arma',quantidade:3}]
  533 Cortesao Desonrado -> [{tipo:'pericia-cortesao',quantidade:1}]
  536 Incremento Atrib/Talento -> [{tipo:'asi-ou-talento',quantidade:1}]

Popula catalogo:
  pericia-cortesao: Historia, Intuicao, Performance, Persuasao (4 entradas)
  Acesso: subclasse 39 (Cortesao Desonrado pertence a essa subclasse)

Idempotente: roda multiplas vezes sem efeito acumulado.
Fonte exaustiva 1:1: paginas/guerreiro.extracted.html linha ~1651-1660 lista
as 4 pericias explicitamente sem 'como'/'tais como'.
"""
import json
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).parent / "bonfas.db"


def col_exists(cur, table: str, col: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    return any(r[1] == col for r in cur.fetchall())


def add_col(cur, table: str, col: str, decl: str) -> None:
    if col_exists(cur, table, col):
        print(f"  skip: {table}.{col} ja existe")
        return
    cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")
    print(f"  ALTER: {table}.{col} {decl}")


def main() -> int:
    if not DB.exists():
        print(f"ERRO: {DB} nao existe", file=sys.stderr)
        return 1

    conn = sqlite3.connect(str(DB))
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    print("[1] Schema migration")
    add_col(cur, "TB_ClasseHabilidade", "OpcaoTipoJSON", "TEXT NULL")
    add_col(cur, "TB_PersonagemHabilidadeOpcao", "Id_Opcao", "INTEGER NULL")
    add_col(cur, "TB_PersonagemHabilidadeOpcao", "SlotIndex", "INTEGER NULL")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_pho_id_opcao ON TB_PersonagemHabilidadeOpcao(Id_Opcao)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_pho_pid_hid_slot ON TB_PersonagemHabilidadeOpcao(Id_Personagem, Id_Habilidade, SlotIndex)")
    print("  indexes ok")

    print("[2] Classificar habilidades")
    classifications = {
        515: [
            {"tipo": "estilo-de-luta", "quantidade": 1},
            {"tipo": "maestria-arma", "quantidade": 3},
        ],
        533: [
            {"tipo": "pericia-cortesao", "quantidade": 1},
        ],
        536: [
            {"tipo": "asi-ou-talento", "quantidade": 1},
        ],
    }
    for hid, spec in classifications.items():
        cur.execute("SELECT Nome FROM TB_ClasseHabilidade WHERE Id_Habilidade=?", (hid,))
        row = cur.fetchone()
        if not row:
            print(f"  skip: hab {hid} nao existe")
            continue
        cur.execute(
            "UPDATE TB_ClasseHabilidade SET OpcaoTipoJSON=? WHERE Id_Habilidade=?",
            (json.dumps(spec, ensure_ascii=False), hid),
        )
        print(f"  UPDATE hab {hid} ({row[0]}): {spec}")

    print("[3] Popular catalogo pericia-cortesao")
    pericias = [
        ("Historia", "historia-cortesao", "Pericia de Historia (escolha de Cortesao Desonrado)."),
        ("Intuicao", "intuicao-cortesao", "Pericia de Intuicao (escolha de Cortesao Desonrado)."),
        ("Performance", "performance-cortesao", "Pericia de Performance (escolha de Cortesao Desonrado)."),
        ("Persuasao", "persuasao-cortesao", "Pericia de Persuasao (escolha de Cortesao Desonrado)."),
    ]
    source_url = "https://www.worldanvil.com/w/bonfire-tales-rpg-bonfire-tales/a/guerreiro-article"
    for nome, slug, desc in pericias:
        cur.execute(
            "SELECT Id_Opcao FROM TB_OpcaoJogo WHERE Slug=?", (slug,)
        )
        existing = cur.fetchone()
        if existing:
            id_opcao = existing[0]
            print(f"  skip insert: {nome} (Id_Opcao={id_opcao})")
        else:
            cur.execute(
                "INSERT INTO TB_OpcaoJogo (Nome, Slug, Tipo, Descricao, SourceURL) VALUES (?,?,?,?,?)",
                (nome, slug, "pericia-cortesao", desc, source_url),
            )
            id_opcao = cur.lastrowid
            print(f"  INSERT: {nome} -> Id_Opcao={id_opcao}")

        cur.execute(
            "SELECT 1 FROM TB_AcessoOpcao WHERE Id_Opcao=? AND Id_Subclasse=39",
            (id_opcao,),
        )
        if cur.fetchone():
            continue
        cur.execute(
            "INSERT INTO TB_AcessoOpcao (Id_Opcao, Id_Classe, Id_Subclasse) VALUES (?, NULL, ?)",
            (id_opcao, 39),
        )
        print(f"  ACESSO: Id_Opcao={id_opcao} -> Subclasse 39")

    conn.commit()

    print("[4] Verificacao")
    cur.execute("SELECT COUNT(*) FROM TB_OpcaoJogo WHERE Tipo='pericia-cortesao'")
    print(f"  TB_OpcaoJogo pericia-cortesao: {cur.fetchone()[0]} rows (esperado 4)")
    cur.execute("SELECT COUNT(*) FROM TB_AcessoOpcao WHERE Id_Subclasse=39")
    print(f"  TB_AcessoOpcao Subclasse=39: {cur.fetchone()[0]} rows (esperado >= 4)")
    cur.execute("SELECT Id_Habilidade, Nome, OpcaoTipoJSON FROM TB_ClasseHabilidade WHERE OpcaoTipoJSON IS NOT NULL")
    print("  Habilidades classificadas:")
    for r in cur.fetchall():
        print(f"    hab {r[0]} ({r[1]}): {r[2]}")

    conn.close()
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
