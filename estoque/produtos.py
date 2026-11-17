import sqlite3

from .database import connect
from .validacoes import validar_preco, validar_texto, validar_quantidade


class ProdutoRepository:
    def __init__(self, database_path=None):
        self.database_path = database_path

    def criar(self, codigo, nome, categoria, preco, estoque_minimo=5):
        codigo = validar_texto(codigo, "o código")
        nome = validar_texto(nome, "o nome")
        categoria = str(categoria).strip() or "Geral"
        preco = validar_preco(preco)
        estoque_minimo = validar_quantidade(estoque_minimo, permitir_zero=True)
        try:
            with connect(self.database_path) as connection:
                connection.execute(
                    """INSERT INTO produtos
                       (codigo, nome, categoria, preco, estoque_minimo)
                       VALUES (?, ?, ?, ?, ?)""",
                    (codigo, nome, categoria, preco, estoque_minimo),
                )
        except sqlite3.IntegrityError as error:
            if "UNIQUE" in str(error).upper() or "PRIMARY KEY" in str(error).upper():
                raise ValueError(f"Já existe um produto com o código {codigo}.") from error
            raise

    def atualizar(self, codigo, nome, categoria, preco, estoque_minimo=5):
        codigo = validar_texto(codigo, "o código")
        nome = validar_texto(nome, "o nome")
        categoria = str(categoria).strip() or "Geral"
        preco = validar_preco(preco)
        estoque_minimo = validar_quantidade(estoque_minimo, permitir_zero=True)
        with connect(self.database_path) as connection:
            cursor = connection.execute(
                """UPDATE produtos
                   SET nome = ?, categoria = ?, preco = ?, estoque_minimo = ?
                   WHERE codigo = ?""",
                (nome, categoria, preco, estoque_minimo, codigo),
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Produto {codigo} não encontrado.")

    def excluir(self, codigo):
        with connect(self.database_path) as connection:
            cursor = connection.execute("DELETE FROM produtos WHERE codigo = ?", (codigo,))
            if cursor.rowcount == 0:
                raise ValueError(f"Produto {codigo} não encontrado.")

    def obter(self, codigo):
        with connect(self.database_path) as connection:
            return connection.execute(
                "SELECT * FROM produtos WHERE codigo = ?", (codigo,)
            ).fetchone()

    def listar(self, categoria=None, busca=None):
        consulta = "SELECT * FROM produtos WHERE 1 = 1"
        parametros = []
        if categoria and categoria != "Todas":
            consulta += " AND categoria = ?"
            parametros.append(categoria)
        if busca:
            consulta += " AND (codigo LIKE ? OR nome LIKE ?)"
            termo = f"%{busca.strip()}%"
            parametros.extend((termo, termo))
        consulta += " ORDER BY nome COLLATE NOCASE"
        with connect(self.database_path) as connection:
            return connection.execute(consulta, parametros).fetchall()

    def categorias(self):
        with connect(self.database_path) as connection:
            rows = connection.execute(
                "SELECT DISTINCT categoria FROM produtos ORDER BY categoria COLLATE NOCASE"
            ).fetchall()
            return [row["categoria"] for row in rows]

    def resumo(self):
        with connect(self.database_path) as connection:
            return connection.execute(
                """SELECT COUNT(*) AS produtos,
                          COALESCE(SUM(quantidade), 0) AS unidades,
                          COALESCE(SUM(preco * quantidade), 0) AS valor_total,
                          COALESCE(SUM(CASE WHEN quantidade <= estoque_minimo THEN 1 ELSE 0 END), 0)
                              AS estoque_baixo
                   FROM produtos"""
            ).fetchone()

    def valores_por_categoria(self):
        with connect(self.database_path) as connection:
            return connection.execute(
                """SELECT categoria, SUM(preco * quantidade) AS valor
                   FROM produtos
                   GROUP BY categoria
                   ORDER BY valor DESC, categoria COLLATE NOCASE"""
            ).fetchall()
