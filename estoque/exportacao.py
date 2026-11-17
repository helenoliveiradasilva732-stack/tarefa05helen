import csv

from .produtos import ProdutoRepository


def exportar_estoque(caminho, produtos=None, database_path=None):
    if produtos is None:
        produtos = ProdutoRepository(database_path).listar()
    with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")
        escritor.writerow(
            ["Código", "Nome", "Categoria", "Preço unitário", "Quantidade",
             "Estoque mínimo", "Valor em estoque"]
        )
        for produto in produtos:
            escritor.writerow(
                [
                    produto["codigo"],
                    produto["nome"],
                    produto["categoria"],
                    f'{produto["preco"]:.2f}',
                    produto["quantidade"],
                    produto["estoque_minimo"],
                    f'{produto["preco"] * produto["quantidade"]:.2f}',
                ]
            )
