import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

from .database import initialize
from .exportacao import exportar_estoque
from .movimentacoes import MovimentacaoRepository
from .produtos import ProdutoRepository


BG = "#f3f6fb"
NAVY = "#17324d"
BLUE = "#2878c8"
GREEN = "#138a68"
RED = "#c0394b"
TEXT = "#243447"


def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class SistemaEstoque(tk.Tk):
    def __init__(self):
        super().__init__()
        initialize()
        self.produtos = ProdutoRepository()
        self.movimentacoes = MovimentacaoRepository()
        self.title("Estoque Fácil | Controle de estoque")
        self.geometry("1120x720")
        self.minsize(900, 600)
        self.configure(bg=BG)
        self._configurar_estilos()

        cabecalho = tk.Frame(self, bg=NAVY, padx=24, pady=17)
        cabecalho.pack(fill="x")
        tk.Label(
            cabecalho, text="ESTOQUE FÁCIL", fg="white", bg=NAVY,
            font=("Segoe UI", 17, "bold")
        ).pack(side="left")
        tk.Label(
            cabecalho, text="Controle simples para seu negócio", fg="#cbd8e5",
            bg=NAVY, font=("Segoe UI", 10)
        ).pack(side="left", padx=16, pady=(5, 0))

        self.abas = ttk.Notebook(self)
        self.abas.pack(fill="both", expand=True, padx=22, pady=18)
        self._criar_abas()

    def _configurar_estilos(self):
        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        estilo.configure("TFrame", background=BG)
        estilo.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        estilo.configure("Title.TLabel", font=("Segoe UI", 17, "bold"), foreground=NAVY)
        estilo.configure("Hint.TLabel", foreground="#64748b")
        estilo.configure("TButton", font=("Segoe UI", 10), padding=(10, 7))
        estilo.configure("Accent.TButton", background=BLUE, foreground="white")
        estilo.map("Accent.TButton", background=[("active", "#1d65a8")])
        estilo.configure("Treeview", rowheight=29, font=("Segoe UI", 10))
        estilo.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        estilo.configure("TNotebook", background=BG, borderwidth=0)
        estilo.configure("TNotebook.Tab", padding=(15, 9), font=("Segoe UI", 10))

    def _criar_abas(self):
        self.cadastro = CadastroFrame(self.abas, self)
        self.movimentacao = MovimentacaoFrame(self.abas, self)
        self.estoque = EstoqueFrame(self.abas, self)
        self.historico = HistoricoFrame(self.abas, self)
        self.relatorios = RelatoriosFrame(self.abas, self)
        for frame, titulo in (
            (self.cadastro, "Produtos"),
            (self.movimentacao, "Movimentações"),
            (self.estoque, "Estoque atual"),
            (self.historico, "Histórico"),
            (self.relatorios, "Relatórios"),
        ):
            self.abas.add(frame, text=titulo)

    def atualizar_telas(self):
        for tela in (
            self.cadastro, self.movimentacao, self.estoque,
            self.historico, self.relatorios,
        ):
            tela.atualizar()


class Pagina(ttk.Frame):
    def __init__(self, parent, app, titulo, descricao):
        super().__init__(parent, padding=20)
        self.app = app
        ttk.Label(self, text=titulo, style="Title.TLabel").pack(anchor="w")
        ttk.Label(self, text=descricao, style="Hint.TLabel").pack(anchor="w", pady=(3, 16))

    def _tabela(self, parent, colunas, titulos, larguras):
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True)
        tabela = ttk.Treeview(container, columns=colunas, show="headings")
        barra = ttk.Scrollbar(container, orient="vertical", command=tabela.yview)
        tabela.configure(yscrollcommand=barra.set)
        for coluna, titulo, largura in zip(colunas, titulos, larguras):
            tabela.heading(coluna, text=titulo)
            tabela.column(coluna, width=largura, minwidth=60, anchor="w")
        tabela.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        return tabela


class CadastroFrame(Pagina):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Cadastro de produtos", "Cadastre, edite ou remova produtos.")
        conteudo = ttk.Frame(self)
        conteudo.pack(fill="both", expand=True)
        formulario = ttk.LabelFrame(conteudo, text="Dados do produto", padding=14)
        formulario.pack(side="left", fill="y", padx=(0, 16))
        self.campos = {}
        definicoes = [
            ("Código *", "codigo"), ("Nome *", "nome"),
            ("Categoria", "categoria"), ("Preço (R$) *", "preco"),
            ("Estoque mínimo", "estoque_minimo"),
        ]
        for linha, (rotulo, chave) in enumerate(definicoes):
            ttk.Label(formulario, text=rotulo).grid(row=linha * 2, column=0, sticky="w", pady=(5, 2))
            campo = ttk.Entry(formulario, width=28)
            campo.grid(row=linha * 2 + 1, column=0, sticky="ew", pady=(0, 7))
            self.campos[chave] = campo
        self.campos["categoria"].insert(0, "Geral")
        self.campos["estoque_minimo"].insert(0, "5")
        botoes = ttk.Frame(formulario)
        botoes.grid(row=10, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(botoes, text="Salvar novo", style="Accent.TButton", command=self.salvar).pack(fill="x", pady=3)
        ttk.Button(botoes, text="Atualizar selecionado", command=self.editar).pack(fill="x", pady=3)
        ttk.Button(botoes, text="Excluir selecionado", command=self.excluir).pack(fill="x", pady=3)
        ttk.Button(botoes, text="Limpar formulário", command=self.limpar).pack(fill="x", pady=3)

        painel = ttk.Frame(conteudo)
        painel.pack(side="left", fill="both", expand=True)
        ttk.Label(painel, text="Selecione um produto para editar", style="Hint.TLabel").pack(anchor="w", pady=(0, 8))
        self.tabela = self._tabela(
            painel, ("codigo", "nome", "categoria", "preco", "quantidade"),
            ("Código", "Nome", "Categoria", "Preço", "Quantidade"),
            (90, 180, 130, 95, 90),
        )
        self.tabela.bind("<<TreeviewSelect>>", self.selecionar)
        self.atualizar()

    def atualizar(self):
        self.tabela.delete(*self.tabela.get_children())
        for produto in self.app.produtos.listar():
            self.tabela.insert(
                "", "end", values=(
                    produto["codigo"], produto["nome"], produto["categoria"],
                    formatar_moeda(produto["preco"]), produto["quantidade"],
                )
            )

    def selecionar(self, _evento=None):
        selecionados = self.tabela.selection()
        if not selecionados:
            return
        produto = self.app.produtos.obter(self.tabela.item(selecionados[0], "values")[0])
        for chave in self.campos:
            self.campos[chave].delete(0, "end")
        for chave in self.campos:
            self.campos[chave].insert(0, str(produto[chave]))
        self.campos["codigo"].configure(state="disabled")

    def dados(self):
        return {chave: campo.get() for chave, campo in self.campos.items()}

    def salvar(self):
        dados = self.dados()
        try:
            self.app.produtos.criar(
                dados["codigo"], dados["nome"], dados["categoria"],
                dados["preco"], dados["estoque_minimo"],
            )
        except (ValueError, sqlite3.Error) as error:
            self._mostrar_erro(error)
            return
        self.limpar()
        self.app.atualizar_telas()
        messagebox.showinfo("Produto cadastrado", "Produto cadastrado com sucesso.", parent=self)

    def editar(self):
        selecionados = self.tabela.selection()
        if not selecionados:
            messagebox.showwarning("Seleção necessária", "Selecione um produto na lista.", parent=self)
            return
        dados = self.dados()
        try:
            self.app.produtos.atualizar(
                self.tabela.item(selecionados[0], "values")[0],
                dados["nome"], dados["categoria"], dados["preco"], dados["estoque_minimo"],
            )
        except (ValueError, sqlite3.Error) as error:
            self._mostrar_erro(error)
            return
        self.limpar()
        self.app.atualizar_telas()

    def excluir(self):
        selecionados = self.tabela.selection()
        if not selecionados:
            messagebox.showwarning("Seleção necessária", "Selecione um produto na lista.", parent=self)
            return
        codigo = self.tabela.item(selecionados[0], "values")[0]
        if not messagebox.askyesno("Confirmar exclusão", f"Excluir o produto {codigo}?", parent=self):
            return
        try:
            self.app.produtos.excluir(codigo)
        except (ValueError, sqlite3.Error) as error:
            self._mostrar_erro(error)
            return
        self.limpar()
        self.app.atualizar_telas()

    def limpar(self):
        self.campos["codigo"].configure(state="normal")
        for campo in self.campos.values():
            campo.delete(0, "end")
        self.campos["categoria"].insert(0, "Geral")
        self.campos["estoque_minimo"].insert(0, "5")
        for item in self.tabela.selection():
            self.tabela.selection_remove(item)

    def _mostrar_erro(self, error):
        messagebox.showerror("Não foi possível salvar", str(error), parent=self)


class MovimentacaoFrame(Pagina):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Registrar movimentação", "Entradas aumentam o estoque; saídas não podem exceder o saldo.")
        formulario = ttk.LabelFrame(self, text="Nova movimentação", padding=16)
        formulario.pack(anchor="nw", fill="x")
        ttk.Label(formulario, text="Produto").grid(row=0, column=0, sticky="w", padx=5)
        self.produto = ttk.Combobox(formulario, state="readonly", width=42)
        self.produto.grid(row=1, column=0, padx=5, pady=6)
        ttk.Label(formulario, text="Tipo").grid(row=0, column=1, sticky="w", padx=5)
        self.tipo = ttk.Combobox(formulario, state="readonly", values=("entrada", "saida"), width=16)
        self.tipo.current(0)
        self.tipo.grid(row=1, column=1, padx=5, pady=6)
        ttk.Label(formulario, text="Quantidade").grid(row=0, column=2, sticky="w", padx=5)
        self.quantidade = ttk.Entry(formulario, width=16)
        self.quantidade.grid(row=1, column=2, padx=5, pady=6)
        ttk.Button(formulario, text="Registrar", style="Accent.TButton", command=self.registrar).grid(
            row=1, column=3, padx=12
        )
        self.disponivel = ttk.Label(formulario, text="")
        self.disponivel.grid(row=2, column=0, columnspan=4, sticky="w", padx=5, pady=(6, 0))
        self.produto.bind("<<ComboboxSelected>>", self.mostrar_disponivel)
        self.atualizar()

    def atualizar(self):
        produtos = self.app.produtos.listar()
        self.produtos_por_codigo = {p["codigo"]: p for p in produtos}
        self.produto["values"] = [
            f'{p["codigo"]} — {p["nome"]} (saldo: {p["quantidade"]})' for p in produtos
        ]
        if produtos:
            self.produto.current(0)
            self.mostrar_disponivel()
        else:
            self.disponivel.configure(text="Cadastre um produto antes de registrar movimentações.")

    def mostrar_disponivel(self, _evento=None):
        selecionado = self.produto.get()
        codigo = selecionado.split(" — ", 1)[0]
        produto = self.produtos_por_codigo.get(codigo)
        if produto:
            self.disponivel.configure(
                text=f'Estoque atual de {produto["nome"]}: {produto["quantidade"]} unidade(s).'
            )

    def registrar(self):
        selecionado = self.produto.get()
        if not selecionado:
            messagebox.showwarning("Produto necessário", "Cadastre e selecione um produto.", parent=self)
            return
        try:
            self.app.movimentacoes.registrar(
                selecionado.split(" — ", 1)[0], self.tipo.get(), self.quantidade.get()
            )
        except (ValueError, sqlite3.Error) as error:
            messagebox.showerror("Movimentação não registrada", str(error), parent=self)
            return
        self.quantidade.delete(0, "end")
        self.app.atualizar_telas()
        messagebox.showinfo("Movimentação registrada", "Estoque atualizado com sucesso.", parent=self)


class EstoqueFrame(Pagina):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Consulta de estoque", "Consulte saldos, valores e produtos que precisam de reposição.")
        filtros = ttk.Frame(self)
        filtros.pack(fill="x", pady=(0, 10))
        ttk.Label(filtros, text="Categoria:").pack(side="left")
        self.categoria = ttk.Combobox(filtros, state="readonly", width=24)
        self.categoria.pack(side="left", padx=8)
        self.categoria.bind("<<ComboboxSelected>>", lambda _e: self.atualizar())
        ttk.Button(filtros, text="Exportar CSV", command=self.exportar).pack(side="right")
        self.aviso = tk.Label(
            self, text="", bg="#fff1d6", fg="#8a5a00", anchor="w",
            padx=12, pady=8, font=("Segoe UI", 10, "bold"),
        )
        self.aviso.pack(fill="x", pady=(0, 10))
        self.tabela = self._tabela(
            self, ("codigo", "nome", "categoria", "preco", "quantidade", "minimo", "total"),
            ("Código", "Produto", "Categoria", "Preço", "Quantidade", "Mínimo", "Valor em estoque"),
            (85, 180, 125, 100, 95, 80, 140),
        )
        self.tabela.tag_configure("baixo", background="#fff1f0", foreground="#a52a2a")
        self.atualizar()

    def atualizar(self):
        categorias = ["Todas"] + self.app.produtos.categorias()
        selecionada = self.categoria.get() or "Todas"
        self.categoria["values"] = categorias
        self.categoria.set(selecionada if selecionada in categorias else "Todas")
        self.tabela.delete(*self.tabela.get_children())
        produtos = self.app.produtos.listar(
            categoria=self.categoria.get() if self.categoria.get() != "Todas" else None
        )
        baixos = []
        for produto in produtos:
            baixo = produto["quantidade"] <= produto["estoque_minimo"]
            if baixo:
                baixos.append(produto["nome"])
            self.tabela.insert(
                "", "end",
                values=(
                    produto["codigo"], produto["nome"], produto["categoria"],
                    formatar_moeda(produto["preco"]), produto["quantidade"],
                    produto["estoque_minimo"],
                    formatar_moeda(produto["preco"] * produto["quantidade"]),
                ),
                tags=("baixo",) if baixo else (),
            )
        if baixos:
            self.aviso.configure(text="⚠ Estoque baixo: " + ", ".join(baixos))
        else:
            self.aviso.configure(text="✓ Nenhum produto abaixo do estoque mínimo.")

    def exportar(self):
        from tkinter import filedialog

        caminho = filedialog.asksaveasfilename(
            parent=self, title="Exportar estoque",
            defaultextension=".csv", filetypes=(("Arquivo CSV", "*.csv"),),
            initialfile="relatorio_estoque.csv",
        )
        if not caminho:
            return
        try:
            categoria = self.categoria.get()
            produtos = self.app.produtos.listar(categoria=categoria if categoria != "Todas" else None)
            exportar_estoque(caminho, produtos)
        except OSError as error:
            messagebox.showerror("Falha na exportação", str(error), parent=self)
            return
        messagebox.showinfo("Exportação concluída", f"Relatório salvo em:\n{caminho}", parent=self)


class HistoricoFrame(Pagina):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Histórico de movimentações", "Acompanhe as entradas e saídas registradas.")
        filtros = ttk.Frame(self)
        filtros.pack(fill="x", pady=(0, 10))
        ttk.Label(filtros, text="Categoria:").pack(side="left")
        self.categoria = ttk.Combobox(filtros, state="readonly", width=24)
        self.categoria.pack(side="left", padx=8)
        self.categoria.bind("<<ComboboxSelected>>", lambda _e: self.atualizar())
        self.tabela = self._tabela(
            self, ("data", "tipo", "codigo", "nome", "categoria", "quantidade"),
            ("Data e hora", "Tipo", "Código", "Produto", "Categoria", "Quantidade"),
            (160, 100, 90, 210, 140, 105),
        )
        self.tabela.tag_configure("entrada", foreground=GREEN)
        self.tabela.tag_configure("saida", foreground=RED)
        self.atualizar()

    def atualizar(self):
        categorias = ["Todas"] + self.app.produtos.categorias()
        selecionada = self.categoria.get() or "Todas"
        self.categoria["values"] = categorias
        self.categoria.set(selecionada if selecionada in categorias else "Todas")
        self.tabela.delete(*self.tabela.get_children())
        categoria = self.categoria.get() if self.categoria.get() != "Todas" else None
        for mov in self.app.movimentacoes.listar(categoria=categoria):
            self.tabela.insert(
                "", "end",
                values=(
                    mov["data"], "Entrada" if mov["tipo"] == "entrada" else "Saída",
                    mov["produto_codigo"], mov["nome"], mov["categoria"], mov["quantidade"],
                ),
                tags=(mov["tipo"],),
            )


class RelatoriosFrame(Pagina):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Relatórios visuais", "Visão geral do valor e da distribuição do estoque.")
        self.cartoes = ttk.Frame(self)
        self.cartoes.pack(fill="x", pady=(0, 18))
        self.valores = {}
        for titulo in ("Produtos cadastrados", "Unidades em estoque", "Valor total", "Estoque baixo"):
            cartao = tk.Frame(self.cartoes, bg="white", padx=15, pady=12, highlightbackground="#dce4ee", highlightthickness=1)
            cartao.pack(side="left", fill="x", expand=True, padx=(0, 9))
            tk.Label(cartao, text=titulo, bg="white", fg="#65758b", font=("Segoe UI", 9)).pack(anchor="w")
            valor = tk.Label(cartao, text="0", bg="white", fg=NAVY, font=("Segoe UI", 19, "bold"))
            valor.pack(anchor="w", pady=(5, 0))
            self.valores[titulo] = valor
        area = ttk.LabelFrame(self, text="Valor do estoque por categoria", padding=12)
        area.pack(fill="both", expand=True)
        self.grafico = tk.Canvas(area, bg="white", height=330, highlightthickness=0)
        self.grafico.pack(fill="both", expand=True)
        self.grafico.bind("<Configure>", lambda _e: self.desenhar())
        self.atualizar()

    def atualizar(self):
        resumo = self.app.produtos.resumo()
        self.valores["Produtos cadastrados"].configure(text=str(resumo["produtos"]))
        self.valores["Unidades em estoque"].configure(text=str(resumo["unidades"]))
        self.valores["Valor total"].configure(text=formatar_moeda(resumo["valor_total"]))
        self.valores["Estoque baixo"].configure(text=str(resumo["estoque_baixo"]))
        self.dados_grafico = self.app.produtos.valores_por_categoria()
        self.desenhar()

    def desenhar(self):
        if not hasattr(self, "dados_grafico"):
            return
        canvas = self.grafico
        canvas.delete("all")
        largura = max(canvas.winfo_width(), 420)
        altura = max(canvas.winfo_height(), 250)
        dados = self.dados_grafico
        if not dados:
            canvas.create_text(largura / 2, altura / 2, text="Cadastre produtos para visualizar o relatório.",
                               fill="#64748b", font=("Segoe UI", 11))
            return
        margem_esq, margem_dir, margem_sup, margem_inf = 165, 30, 20, 32
        area_largura = max(largura - margem_esq - margem_dir, 80)
        linha = max(34, min(52, (altura - margem_sup - margem_inf) / len(dados)))
        maior = max(float(item["valor"]) for item in dados) or 1
        paleta = ("#2878c8", "#138a68", "#e59a25", "#805ad5", "#db6272")
        for indice, item in enumerate(dados):
            centro_y = margem_sup + indice * linha + linha / 2
            nome = item["categoria"]
            if len(nome) > 22:
                nome = nome[:19] + "..."
            canvas.create_text(margem_esq - 12, centro_y, text=nome, anchor="e",
                               fill=TEXT, font=("Segoe UI", 10))
            barra = area_largura * float(item["valor"]) / maior
            canvas.create_rectangle(
                margem_esq, centro_y - 10, margem_esq + barra, centro_y + 10,
                fill=paleta[indice % len(paleta)], outline="",
            )
            canvas.create_text(margem_esq + barra + 8, centro_y,
                               text=formatar_moeda(item["valor"]), anchor="w",
                               fill=TEXT, font=("Segoe UI", 9))
