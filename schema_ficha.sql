-- Expansão do schema para suportar ficha D&D 5.5 completa
-- Adiciona colunas em TB_Personagem e cria tabelas auxiliares

-- campos extras em TB_Personagem (IGNORA erro se já existir)
-- (usar ALTER TABLE fora deste script, via Python, por compatibilidade SQLite)

CREATE TABLE IF NOT EXISTS TB_PersonagemPericia (
    Id_Pericia     INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Personagem  INTEGER NOT NULL,
    Nome           VARCHAR(50)  NOT NULL,   -- Acrobacia, Arcanismo, ...
    Atributo       VARCHAR(3)   NOT NULL,   -- DES, INT, SAB, ...
    Proficiente    INTEGER NOT NULL DEFAULT 0,   -- 0/1
    Expertise      INTEGER NOT NULL DEFAULT 0,   -- 0/1 (dobra a prof)
    FOREIGN KEY (Id_Personagem) REFERENCES TB_Personagem(Id_Personagem) ON DELETE CASCADE,
    UNIQUE (Id_Personagem, Nome)
);

CREATE TABLE IF NOT EXISTS TB_PersonagemTalento (
    Id_Talento     INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Personagem  INTEGER NOT NULL,
    Categoria      VARCHAR(20) NOT NULL,         -- "geral" | "raca" | "extra"
    Nivel          INTEGER,                      -- nível em que foi adquirido
    Nome           VARCHAR(150) NOT NULL,
    Detalhes       VARCHAR(200),                 -- ex.: "War Caster (int) 16"
    FOREIGN KEY (Id_Personagem) REFERENCES TB_Personagem(Id_Personagem) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS TB_PersonagemIdioma (
    Id             INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Personagem  INTEGER NOT NULL,
    Tipo           VARCHAR(20) NOT NULL,     -- "idioma" | "ferramenta" | "arma" | "armadura"
    Nome           VARCHAR(100) NOT NULL,
    FOREIGN KEY (Id_Personagem) REFERENCES TB_Personagem(Id_Personagem) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS TB_PersonagemResistencia (
    Id             INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Personagem  INTEGER NOT NULL,
    Tipo           VARCHAR(20) NOT NULL,     -- "resistencia" | "imunidade" | "vulnerabilidade"
    DanoTipo       VARCHAR(50) NOT NULL,     -- "Fogo", "Necrótico", ...
    FOREIGN KEY (Id_Personagem) REFERENCES TB_Personagem(Id_Personagem) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS TB_PersonagemPersonalidade (
    Id             INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Personagem  INTEGER NOT NULL,
    Tipo           VARCHAR(20) NOT NULL,     -- "traco" | "ideal" | "vinculo" | "defeito"
    Texto          TEXT NOT NULL,
    FOREIGN KEY (Id_Personagem) REFERENCES TB_Personagem(Id_Personagem) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS TB_PersonagemInventarioItem (
    Id             INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Personagem  INTEGER NOT NULL,
    Qtd            INTEGER NOT NULL DEFAULT 1,
    Item           VARCHAR(200) NOT NULL,
    Custo          VARCHAR(30),                  -- "15 gp"
    Peso           VARCHAR(20),                  -- "3 lb."
    Sintonizado    INTEGER NOT NULL DEFAULT 0,
    Id_Item        INTEGER,                      -- FK opcional p/ TB_Item
    FOREIGN KEY (Id_Personagem) REFERENCES TB_Personagem(Id_Personagem) ON DELETE CASCADE,
    FOREIGN KEY (Id_Item)       REFERENCES TB_Item(Id_Item)             ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS TB_PersonagemMagia (
    Id             INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Personagem  INTEGER NOT NULL,
    Nivel          INTEGER NOT NULL,            -- 0 = truque
    Nome           VARCHAR(150) NOT NULL,
    Preparada      INTEGER NOT NULL DEFAULT 0,
    Concentracao   INTEGER NOT NULL DEFAULT 0,
    Ritual         INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (Id_Personagem) REFERENCES TB_Personagem(Id_Personagem) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS TB_PersonagemTecnica (
    Id             INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Personagem  INTEGER NOT NULL,
    Nome           VARCHAR(150) NOT NULL,
    Descricao      TEXT,
    FOREIGN KEY (Id_Personagem) REFERENCES TB_Personagem(Id_Personagem) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_pericia_personagem  ON TB_PersonagemPericia(Id_Personagem);
CREATE INDEX IF NOT EXISTS idx_talento_personagem  ON TB_PersonagemTalento(Id_Personagem);
CREATE INDEX IF NOT EXISTS idx_idioma_personagem   ON TB_PersonagemIdioma(Id_Personagem);
CREATE INDEX IF NOT EXISTS idx_resist_personagem   ON TB_PersonagemResistencia(Id_Personagem);
CREATE INDEX IF NOT EXISTS idx_pers_personagem     ON TB_PersonagemPersonalidade(Id_Personagem);
CREATE INDEX IF NOT EXISTS idx_inv_personagem      ON TB_PersonagemInventarioItem(Id_Personagem);
CREATE INDEX IF NOT EXISTS idx_magia_personagem    ON TB_PersonagemMagia(Id_Personagem);
CREATE INDEX IF NOT EXISTS idx_tecnica_personagem  ON TB_PersonagemTecnica(Id_Personagem);
