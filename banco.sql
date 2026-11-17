PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS produtos (
    codigo TEXT PRIMARY KEY NOT NULL CHECK (length(trim(codigo)) > 0),
    nome TEXT NOT NULL CHECK (length(trim(nome)) > 0),
    categoria TEXT NOT NULL DEFAULT 'Geral',
    preco REAL NOT NULL CHECK (preco >= 0),
    quantidade INTEGER NOT NULL DEFAULT 0 CHECK (quantidade >= 0),
    estoque_minimo INTEGER NOT NULL DEFAULT 5 CHECK (estoque_minimo >= 0)
);

CREATE TABLE IF NOT EXISTS movimentacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_codigo TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('entrada', 'saida')),
    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
    data TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (produto_codigo) REFERENCES produtos(codigo) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_movimentacoes_produto_data
    ON movimentacoes (produto_codigo, data DESC);

CREATE TRIGGER IF NOT EXISTS movimentacao_saida_com_estoque
BEFORE INSERT ON movimentacoes
WHEN NEW.tipo = 'saida'
BEGIN
    SELECT CASE
        WHEN (SELECT quantidade FROM produtos WHERE codigo = NEW.produto_codigo) < NEW.quantidade
        THEN RAISE(ABORT, 'Estoque insuficiente para registrar a saida')
    END;
END;

CREATE TRIGGER IF NOT EXISTS movimentacao_atualiza_estoque
AFTER INSERT ON movimentacoes
BEGIN
    UPDATE produtos
    SET quantidade = quantidade +
        CASE NEW.tipo
            WHEN 'entrada' THEN NEW.quantidade
            WHEN 'saida' THEN -NEW.quantidade
        END
    WHERE codigo = NEW.produto_codigo;
END;
