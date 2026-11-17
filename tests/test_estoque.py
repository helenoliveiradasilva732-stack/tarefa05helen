import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path

from estoque.database import connect, initialize
from estoque.exportacao import exportar_estoque
from estoque.movimentacoes import MovimentacaoRepository
from estoque.produtos import ProdutoRepository


class EstoqueTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "teste.db"
        initialize(self.database_path)
        self.produtos = ProdutoRepository(self.database_path)
        self.movimentacoes = MovimentacaoRepository(self.database_path)
        self.produtos.criar("P001", "Caderno", "Papelaria", "12.50", 2)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_codigo_unico_e_validado(self):
        with self.assertRaisesRegex(ValueError, "Já existe"):
            self.produtos.criar("P001", "Outro", "Papelaria", 5)

    def test_entrada_e_saida_atualizam_estoque_e_historico(self):
        self.movimentacoes.registrar("P001", "entrada", 8)
        self.movimentacoes.registrar("P001", "saida", 3)
        produto = self.produtos.obter("P001")
        self.assertEqual(produto["quantidade"], 5)
        historico = self.movimentacoes.listar()
        self.assertEqual(len(historico), 2)
        self.assertEqual(historico[0]["tipo"], "saida")

    def test_saida_nao_permite_estoque_negativo(self):
        with self.assertRaisesRegex(ValueError, "Estoque insuficiente"):
            self.movimentacoes.registrar("P001", "saida", 1)
        self.assertEqual(self.produtos.obter("P001")["quantidade"], 0)
        self.assertEqual(self.movimentacoes.listar(), [])

    def test_quantidade_de_movimentacao_precisa_ser_positiva(self):
        with self.assertRaisesRegex(ValueError, "maior que zero"):
            self.movimentacoes.registrar("P001", "entrada", 0)
        with self.assertRaisesRegex(ValueError, "inteiro"):
            self.movimentacoes.registrar("P001", "entrada", 1.5)

    def test_resumo_e_filtro_por_categoria(self):
        self.produtos.criar("P002", "Caneta", "Escrita", 2.5)
        self.movimentacoes.registrar("P001", "entrada", 4)
        resumo = self.produtos.resumo()
        self.assertEqual(resumo["produtos"], 2)
        self.assertEqual(resumo["unidades"], 4)
        self.assertEqual(resumo["valor_total"], 50)
        self.assertEqual(resumo["estoque_baixo"], 1)
        self.assertEqual(len(self.produtos.listar(categoria="Papelaria")), 1)

    def test_exporta_relatorio_csv_com_cabecalho_e_valor(self):
        self.movimentacoes.registrar("P001", "entrada", 2)
        caminho = Path(self.temp_dir.name) / "estoque.csv"
        exportar_estoque(caminho, database_path=self.database_path)
        with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
            linhas = list(csv.reader(arquivo, delimiter=";"))
        self.assertEqual(linhas[0][0], "Código")
        self.assertEqual(linhas[1][0], "P001")
        self.assertEqual(linhas[1][-1], "25.00")

    def test_produto_com_historico_nao_pode_ser_excluido(self):
        self.movimentacoes.registrar("P001", "entrada", 1)
        with self.assertRaises(sqlite3.IntegrityError):
            self.produtos.excluir("P001")

    def test_trigger_impede_saida_insuficiente_direto_no_banco(self):
        with self.assertRaisesRegex(sqlite3.IntegrityError, "Estoque insuficiente"):
            with connect(self.database_path) as connection:
                connection.execute(
                    """INSERT INTO movimentacoes (produto_codigo, tipo, quantidade)
                       VALUES ('P001', 'saida', 1)"""
                )
        self.assertEqual(self.produtos.obter("P001")["quantidade"], 0)


if __name__ == "__main__":
    unittest.main()
