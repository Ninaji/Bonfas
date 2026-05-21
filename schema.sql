-- Schema do banco de dados (SQLite) para raças, linhagens, essências e traços
-- Correspondente ao ER fornecido

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS TB_Item;
DROP TABLE IF EXISTS TB_ItemSlot;
DROP TABLE IF EXISTS TB_TracoRacial;
DROP TABLE IF EXISTS TB_Linhagem;
DROP TABLE IF EXISTS TB_Essencia;
DROP TABLE IF EXISTS TB_Raca;

CREATE TABLE TB_Raca (
    Id_Raca         INTEGER PRIMARY KEY AUTOINCREMENT,
    Nome            VARCHAR(100) NOT NULL,
    Slug            VARCHAR(100) NOT NULL UNIQUE,
    Tagline         VARCHAR(255),
    LorePresentation TEXT,
    LoreRoleplay    TEXT,
    LoreSociety     TEXT,
    PermiteEssencia INTEGER NOT NULL DEFAULT 0   -- bit (0/1)
);

CREATE TABLE TB_Linhagem (
    Id_Linhagem     INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Raca         INTEGER NOT NULL,
    Nome            VARCHAR(100) NOT NULL,
    Slug            VARCHAR(100) NOT NULL,
    LorePresentation TEXT,
    LoreRoleplay    TEXT,
    LoreSociety     TEXT,
    Descricao       TEXT,
    FOREIGN KEY (Id_Raca) REFERENCES TB_Raca(Id_Raca) ON DELETE CASCADE
);

CREATE TABLE TB_Essencia (
    Id_Essencia     INTEGER PRIMARY KEY AUTOINCREMENT,
    Nome            VARCHAR(100) NOT NULL,
    Slug            VARCHAR(100) NOT NULL UNIQUE,
    LorePresentation TEXT,
    LoreRoleplay    TEXT,
    LoreSociety     TEXT
);

CREATE TABLE TB_TracoRacial (
    Id_Traco        INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Raca         INTEGER NOT NULL,
    Id_Linhagem     INTEGER,
    Id_Essencia     INTEGER,
    Nome            VARCHAR(150) NOT NULL,
    Descricao       TEXT NOT NULL,
    NivelRequisito  INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (Id_Raca)     REFERENCES TB_Raca(Id_Raca)         ON DELETE CASCADE,
    FOREIGN KEY (Id_Linhagem) REFERENCES TB_Linhagem(Id_Linhagem) ON DELETE SET NULL,
    FOREIGN KEY (Id_Essencia) REFERENCES TB_Essencia(Id_Essencia) ON DELETE SET NULL
);

CREATE INDEX idx_linhagem_raca   ON TB_Linhagem(Id_Raca);
CREATE INDEX idx_traco_raca      ON TB_TracoRacial(Id_Raca);
CREATE INDEX idx_traco_linhagem  ON TB_TracoRacial(Id_Linhagem);
CREATE INDEX idx_traco_essencia  ON TB_TracoRacial(Id_Essencia);

-- =========================================================================
-- Itens (mesmo padrão hierárquico do ER): TB_ItemSlot -> TB_Item
-- =========================================================================
CREATE TABLE TB_ItemSlot (
    Id_Slot     INTEGER PRIMARY KEY AUTOINCREMENT,
    Codigo      VARCHAR(50)  NOT NULL UNIQUE,   -- "weapon", "ring", "armor"...
    Nome        VARCHAR(100) NOT NULL,          -- nome amigável
    SlotFicha   VARCHAR(50),                    -- mapeia para slot da ficha (maos, aneis, ...)
    BagSecao    VARCHAR(50)                     -- mapeia para seção da mochila (armas, aneis_bag, ...)
);

CREATE TABLE TB_Item (
    Id_Item         INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Slot         INTEGER,
    Nome            VARCHAR(200) NOT NULL,
    NomeTraduzido   VARCHAR(200),
    Slug            VARCHAR(220) NOT NULL UNIQUE,
    Source          VARCHAR(50),
    Page            VARCHAR(20),
    Tipo            VARCHAR(200),
    Attunement      VARCHAR(100),
    Damage          VARCHAR(100),
    Properties      TEXT,
    Mastery         VARCHAR(100),
    Weight          VARCHAR(50),
    Value           VARCHAR(50),
    Texto           TEXT,
    EfeitoTraduzido TEXT,
    FOREIGN KEY (Id_Slot) REFERENCES TB_ItemSlot(Id_Slot) ON DELETE SET NULL
);

CREATE INDEX idx_item_nome           ON TB_Item(Nome);
CREATE INDEX idx_item_nome_traduzido ON TB_Item(NomeTraduzido);
CREATE INDEX idx_item_slot           ON TB_Item(Id_Slot);
CREATE INDEX idx_item_source         ON TB_Item(Source);

-- =========================================================================
-- Classes / Subclasses / Recursos / Habilidades / Opções de Jogo
-- (modelagem do ER "Jogadores")
-- =========================================================================
DROP TABLE IF EXISTS TB_AcessoOpcao;
DROP TABLE IF EXISTS TB_ClasseHabilidade;
DROP TABLE IF EXISTS TB_RecursoClasse;
DROP TABLE IF EXISTS TB_OpcaoJogo;
DROP TABLE IF EXISTS TB_Subclasse;
DROP TABLE IF EXISTS TB_Classe;

CREATE TABLE TB_Classe (
    Id_Classe   INTEGER PRIMARY KEY AUTOINCREMENT,
    Nome        VARCHAR(100) NOT NULL,
    Slug        VARCHAR(100) NOT NULL UNIQUE,
    Tagline     VARCHAR(255),
    SourceURL   VARCHAR(255)                -- URL da wiki (auditoria)
);

CREATE TABLE TB_Subclasse (
    Id_Subclasse INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Classe    INTEGER NOT NULL,
    Nome         VARCHAR(100) NOT NULL,
    Slug         VARCHAR(100) NOT NULL,
    Tagline      VARCHAR(255),
    SourceURL    VARCHAR(255),
    FOREIGN KEY (Id_Classe) REFERENCES TB_Classe(Id_Classe) ON DELETE CASCADE,
    UNIQUE (Id_Classe, Slug)
);

CREATE TABLE TB_OpcaoJogo (
    Id_Opcao    INTEGER PRIMARY KEY AUTOINCREMENT,
    Nome        VARCHAR(150) NOT NULL,
    Slug        VARCHAR(150) NOT NULL UNIQUE,
    Tipo        VARCHAR(50)  NOT NULL,    -- ex.: "talento", "manobra", "invocacao", "metamagia"
    Descricao   TEXT,
    SourceURL   VARCHAR(255)
);

CREATE TABLE TB_RecursoClasse (
    Id_Recurso   INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Classe    INTEGER NOT NULL,
    Id_Subclasse INTEGER,
    Nome         VARCHAR(100) NOT NULL,
    Slug         VARCHAR(100) NOT NULL,
    Nivel        INTEGER NOT NULL,
    Valor        VARCHAR(50),              -- flexível: dado, nº, texto curto
    FOREIGN KEY (Id_Classe)    REFERENCES TB_Classe(Id_Classe)       ON DELETE CASCADE,
    FOREIGN KEY (Id_Subclasse) REFERENCES TB_Subclasse(Id_Subclasse) ON DELETE CASCADE
);

CREATE TABLE TB_ClasseHabilidade (
    Id_Habilidade  INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Classe      INTEGER NOT NULL,
    Id_Subclasse   INTEGER,
    Nome           VARCHAR(150) NOT NULL,
    Descricao      TEXT NOT NULL,
    NivelAdquirido INTEGER NOT NULL,
    FOREIGN KEY (Id_Classe)    REFERENCES TB_Classe(Id_Classe)       ON DELETE CASCADE,
    FOREIGN KEY (Id_Subclasse) REFERENCES TB_Subclasse(Id_Subclasse) ON DELETE CASCADE
);

CREATE TABLE TB_AcessoOpcao (
    Id_AcessoOpcao INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Opcao       INTEGER NOT NULL,
    Id_Classe      INTEGER,
    Id_Subclasse   INTEGER,
    FOREIGN KEY (Id_Opcao)     REFERENCES TB_OpcaoJogo(Id_Opcao)     ON DELETE CASCADE,
    FOREIGN KEY (Id_Classe)    REFERENCES TB_Classe(Id_Classe)       ON DELETE CASCADE,
    FOREIGN KEY (Id_Subclasse) REFERENCES TB_Subclasse(Id_Subclasse) ON DELETE CASCADE,
    UNIQUE (Id_Opcao, Id_Classe, Id_Subclasse)
);

CREATE INDEX idx_subclasse_classe  ON TB_Subclasse(Id_Classe);
CREATE INDEX idx_recurso_classe    ON TB_RecursoClasse(Id_Classe, Nivel);
CREATE INDEX idx_habil_classe      ON TB_ClasseHabilidade(Id_Classe, NivelAdquirido);
CREATE INDEX idx_acesso_classe     ON TB_AcessoOpcao(Id_Classe);
CREATE INDEX idx_acesso_subclasse  ON TB_AcessoOpcao(Id_Subclasse);
CREATE INDEX idx_opcao_tipo        ON TB_OpcaoJogo(Tipo);

-- =========================================================================
-- ALTER aplicados via migrate_opcoes_v2.py (2026-05-03)
-- ver docs/habilidades-com-escolha.md
-- =========================================================================
-- ALTER TABLE TB_ClasseHabilidade ADD COLUMN OpcaoTipoJSON TEXT NULL;
-- ALTER TABLE TB_PersonagemHabilidadeOpcao ADD COLUMN Id_Opcao INTEGER NULL;
-- ALTER TABLE TB_PersonagemHabilidadeOpcao ADD COLUMN SlotIndex INTEGER NULL;
-- CREATE INDEX idx_pho_id_opcao        ON TB_PersonagemHabilidadeOpcao(Id_Opcao);
-- CREATE INDEX idx_pho_pid_hid_slot    ON TB_PersonagemHabilidadeOpcao(Id_Personagem, Id_Habilidade, SlotIndex);
