from .database import connect
from .validacoes import validar_quantidade, validar_texto


class MovimentacaoRepository:
    def __init__(self, database_path=None):
        self.database_path = database_path

    def registrar(self, produto_codigo, tipo, quantidade):
        produto_codigo = validar_texto(produto_codigo, "o código do produto")
        tipo = str(tipo).strip().lower()
        if tipo not in ("entrada", "saida"):
            raise ValueError("O tipo deve ser entrada ou saída.")
        quantidade = validar_quantidade(quantidade)
        with connect(self.database_path) as connection:
            produto = connection.execute(
                "SELECT codigo FROM produtos WHERE codigo = ?", (produto_codigo,)
            ).fetchone()
            if produto is None:
                raise ValueError(f"Produto {produto_codigo} não encontrado.")
            if tipo == "saida":
                estoque = connection.execute(
                    "SELECT quantidade FROM produtos WHERE codigo = ?", (produto_codigo,)
                ).fetchone()["quantidade"]
                if quantidade > estoque:
                    raise ValueError(
                        f"Estoque insuficiente. Disponível: {estoque} unidade(s)."
                    )
            connection.execute(
                """INSERT INTO movimentacoes (produto_codigo, tipo, quantidade)
                   VALUES (?, ?, ?)""",
                (produto_codigo, tipo, quantidade),
            )

    def listar(self, categoria=None, limite=500):
        consulta = """SELECT m.id, m.tipo, m.quantidade, m.data,
                             p.codigo AS produto_codigo, p.nome, p.categoria
                      FROM movimentacoes AS m
                      JOIN produtos AS p ON p.codigo = m.produto_codigo"""
        parametros = []
        if categoria and categoria != "Todas":
            consulta += " WHERE p.categoria = ?"
            parametros.append(categoria)
        consulta += " ORDER BY m.data DESC, m.id DESC LIMIT ?"
        parametros.append(limite)
        with connect(self.database_path) as connection:
            return connection.execute(consulta, parametros).fetchall()

    def totais_por_tipo(self):
        with connect(self.database_path) as connection:
            return connection.execute(
                """SELECT tipo, COALESCE(SUM(quantidade), 0) AS quantidade
                   FROM movimentacoes GROUP BY tipo"""
            ).fetchall()
