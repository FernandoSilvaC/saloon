from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtGui import QIcon, QColor, QPalette, QLinearGradient, QBrush, QGradient
import sys
import sqlite3
from fpdf import FPDF
from math import ceil

# --- Configuração do Banco de Dados ---
conn = sqlite3.connect('saloon_recipes.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    dollar_value REAL DEFAULT 0,
    stock INTEGER DEFAULT 0,
    category TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER,
    name TEXT NOT NULL,
    quantity INTEGER,
    FOREIGN KEY (recipe_id) REFERENCES recipes (id)
)
''')

conn.commit()

# --- Classe Principal ---
class RecipeApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Estrela do Oeste - Premium Edition')
        self.resize(1100, 750)

        # Widget Central e Layout
        central_widget = QtWidgets.QWidget(self)
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)
        
        self.main_layout = QtWidgets.QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        self.initUI()
        # Aplicamos o estilo na aplicação inteira para garantir que os popups peguem
        self.apply_glass_orange_style()

    def initUI(self):
        # --- 1. SIDEBAR ---
        self.sidebar_frame = QtWidgets.QFrame()
        self.sidebar_frame.setObjectName("GlassPanel") 
        self.sidebar_layout = QtWidgets.QVBoxLayout(self.sidebar_frame)
        self.sidebar_layout.setContentsMargins(20, 30, 20, 30)
        self.sidebar_layout.setSpacing(15)
        self.sidebar_frame.setFixedWidth(300)

        # Título
        logo = QtWidgets.QLabel("ESTRELA\nDO OESTE")
        logo.setAlignment(QtCore.Qt.AlignCenter)
        logo.setObjectName("LogoText")
        self.sidebar_layout.addWidget(logo)

        # Divisor
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setObjectName("OrangeLine")
        self.sidebar_layout.addWidget(line)

        # Navegação
        lbl_busca = QtWidgets.QLabel("NAVEGAÇÃO")
        lbl_busca.setObjectName("SectionTitle")
        self.sidebar_layout.addWidget(lbl_busca)

        self.search_bar = QtWidgets.QLineEdit(self)
        self.search_bar.setPlaceholderText('Buscar Receita...')
        self.sidebar_layout.addWidget(self.search_bar)

        self.search_button = QtWidgets.QPushButton('PESQUISAR', self)
        self.search_button.setCursor(QtCore.Qt.PointingHandCursor)
        self.search_button.clicked.connect(self.search_recipe)
        self.sidebar_layout.addWidget(self.search_button)

        # Filtro
        lbl_cat = QtWidgets.QLabel("CATEGORIAS")
        lbl_cat.setObjectName("SectionTitle")
        self.sidebar_layout.addWidget(lbl_cat)

        self.category_filter = QtWidgets.QComboBox(self)
        self.category_filter.addItem("Todas")
        self.category_filter.addItems(["Entrada", "Prato Principal", "Doces", "Bebidas Alcolicas", "Sucos", "Salgados", "Sopas", "Produtos da Fazenda"])
        self.category_filter.currentTextChanged.connect(self.load_recipes)
        self.sidebar_layout.addWidget(self.category_filter)

        self.sidebar_layout.addStretch() 
        
        footer = QtWidgets.QLabel("v2.1 Premium")
        footer.setAlignment(QtCore.Qt.AlignCenter)
        footer.setStyleSheet("color: rgba(255,255,255,0.3); font-size: 10px;")
        self.sidebar_layout.addWidget(footer)

        self.main_layout.addWidget(self.sidebar_frame)

        # --- 2. CONTEÚDO ---
        self.content_frame = QtWidgets.QFrame()
        self.content_frame.setObjectName("GlassPanel")
        self.content_layout = QtWidgets.QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(20)

        # Header
        header_layout = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Gerenciamento de Menu")
        title.setObjectName("PageTitle")
        
        btn_layout = QtWidgets.QHBoxLayout()
        self.report_button = QtWidgets.QPushButton('Relatório PDF', self)
        self.report_button.setObjectName("GhostButton")
        self.report_button.setCursor(QtCore.Qt.PointingHandCursor)
        self.report_button.clicked.connect(self.generate_pdf_report)
        
        self.budget_button = QtWidgets.QPushButton('Orçamento', self)
        self.budget_button.setObjectName("GhostButton")
        self.budget_button.setCursor(QtCore.Qt.PointingHandCursor)
        self.budget_button.clicked.connect(self.open_budget_dialog)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.report_button)
        header_layout.addWidget(self.budget_button)
        self.content_layout.addLayout(header_layout)

        # Lista
        self.recipe_list = QtWidgets.QListWidget(self)
        self.recipe_list.itemClicked.connect(self.show_recipe_options)
        self.content_layout.addWidget(self.recipe_list)

        # Botão Principal
        self.add_button = QtWidgets.QPushButton('ADICIONAR NOVA RECEITA', self)
        self.add_button.setObjectName("GradientButton")
        self.add_button.setMinimumHeight(60)
        self.add_button.setCursor(QtCore.Qt.PointingHandCursor)
        self.add_button.clicked.connect(self.add_recipe_and_ingredients)
        self.content_layout.addWidget(self.add_button)

        self.main_layout.addWidget(self.content_frame)

        self.load_recipes()

    def apply_glass_orange_style(self):
        style = """
            /* --- FUNDO GERAL (Apliquei a QDialog também) --- */
            QMainWindow, QDialog {
                background-color: #1a1a1a;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #232526, stop:1 #414345);
            }

            /* --- TIPOGRAFIA --- */
            QLabel { 
                color: #e0e0e0; 
                font-family: 'Segoe UI', sans-serif;
                background-color: transparent; /* Importante para Dialogs */
            }
            
            /* --- PAINÉIS DE VIDRO --- */
            QFrame#GlassPanel {
                background-color: rgba(30, 30, 30, 180);
                border: 1px solid rgba(255, 165, 0, 0.3);
                border-radius: 20px;
            }

            /* --- TEXTOS ESPECÍFICOS --- */
            QLabel#LogoText {
                font-size: 26pt; font-weight: 900; color: #ff9966; letter-spacing: 2px; margin-bottom: 10px;
            }
            QLabel#SectionTitle {
                color: #ffa500; font-weight: bold; font-size: 10pt; margin-top: 10px; letter-spacing: 1px;
            }
            QFrame#OrangeLine {
                color: #ff4500; background-color: #ff4500; height: 2px; border: none;
            }
            QLabel#PageTitle {
                font-size: 22pt; color: white; font-weight: 300;
            }

            /* --- INPUTS (Campos de texto e números) --- */
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: rgba(0, 0, 0, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 8px;
                color: white;
                font-size: 11pt;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 1px solid #ff9966;
                background-color: rgba(0, 0, 0, 0.6);
            }
            /* Cor do texto dentro do combobox dropdown */
            QComboBox QAbstractItemView {
                background-color: #2b2b2b;
                color: white;
                selection-background-color: #ff9966;
                border: 1px solid #444;
            }

            /* --- BOTÕES --- */
            QPushButton {
                background-color: #333;
                color: white;
                border-radius: 10px;
                padding: 10px;
                font-weight: bold;
                border: 1px solid rgba(255,255,255,0.1);
            }
            
            QPushButton#GradientButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF512F, stop:1 #F09819);
                color: white;
                border: none;
                font-size: 12pt;
                letter-spacing: 1px;
            }
            QPushButton#GradientButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #dd2476, stop:1 #ff512f);
            }
            
            QPushButton#GhostButton {
                background-color: transparent;
                border: 1px solid rgba(255, 255, 255, 0.3);
                color: rgba(255, 255, 255, 0.8);
            }
            QPushButton#GhostButton:hover {
                background-color: rgba(255, 165, 0, 0.1);
                border: 1px solid #ffa500;
                color: #ffa500;
            }

            /* --- LIST WIDGET --- */
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background-color: rgba(255, 255, 255, 0.05);
                color: #ddd;
                border-radius: 12px;
                margin-bottom: 8px;
                padding: 15px;
            }
            QListWidget::item:hover {
                background-color: rgba(255, 165, 0, 0.1);
            }
            QListWidget::item:selected {
                background-color: rgba(255, 165, 0, 0.2);
                border-left: 5px solid #ff4500;
                color: white;
            }

            /* --- SCROLLBAR --- */
            QScrollBar:vertical {
                border: none; background: rgba(0,0,0,0.1); width: 8px; margin: 0px; border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 165, 0, 0.4); min-height: 20px; border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            
            /* --- MENUS --- */
            QMenu { background-color: #2b2b2b; color: white; border: 1px solid #ff9966; }
            QMenu::item { padding: 8px 25px; }
            QMenu::item:selected { background-color: #ff9966; color: black; }
        """
        # APLICA O ESTILO NA APLICAÇÃO GLOBALMENTE
        # Isso garante que Dialogs filhos herdem o estilo
        QtWidgets.QApplication.instance().setStyleSheet(style)

    # --- Lógica Mantida ---
    def load_recipes(self):
        self.recipe_list.clear()
        category = self.category_filter.currentText()
        if category == "Todas":
            cursor.execute("SELECT id, name, dollar_value, stock, category FROM recipes")
        else:
            cursor.execute("SELECT id, name, dollar_value, stock, category FROM recipes WHERE category = ?", (category,))
        for row in cursor.fetchall():
            texto = f"{row[1].upper()}  —  {row[4]}\n${row[2]:.2f}  •  Estoque: {row[3]}"
            item = QtWidgets.QListWidgetItem(texto)
            item.setData(QtCore.Qt.UserRole, row[0])
            self.recipe_list.addItem(item)

    def search_recipe(self):
        search_term = self.search_bar.text()
        self.recipe_list.clear()
        cursor.execute("SELECT id, name, dollar_value, stock, category FROM recipes WHERE name LIKE ?", ('%' + search_term + '%',))
        for row in cursor.fetchall():
            texto = f"{row[1].upper()}  —  {row[4]}\n${row[2]:.2f}  •  Estoque: {row[3]}"
            item = QtWidgets.QListWidgetItem(texto)
            item.setData(QtCore.Qt.UserRole, row[0])
            self.recipe_list.addItem(item)

    def add_recipe_and_ingredients(self):
        name, ok = QtWidgets.QInputDialog.getText(self, 'Novo Item', 'Nome do prato/bebida:')
        if ok and name:
            dollar_value, ok = QtWidgets.QInputDialog.getDouble(self, 'Preço', 'Valor ($):', decimals=2)
            if ok:
                stock, ok = QtWidgets.QInputDialog.getInt(self, 'Estoque', 'Quantidade Atual:')
                if ok:
                    categories = ["Entrada", "Prato Principal", "Doces", "Bebidas Alcolicas", "Sucos", "Salgados", "Sopas", "Produtos da Fazenda"]
                    category, ok = QtWidgets.QInputDialog.getItem(self, "Categoria", "Selecione:", categories, 0, False)
                    if ok and category:
                        cursor.execute("INSERT INTO recipes (name, dollar_value, stock, category) VALUES (?, ?, ?, ?)", (name, dollar_value, stock, category))
                        conn.commit()
                        self.load_recipes()
                        self.edit_recipe(cursor.lastrowid)

    def edit_recipe(self, recipe_id):
        dialog = EditRecipeDialog(self, recipe_id)
        # O estilo agora é global, não precisa setar manualmente aqui, mas mal não faz
        if dialog.exec_():
            self.load_recipes()

    def show_recipe_options(self, item):
        recipe_id = item.data(QtCore.Qt.UserRole)
        menu = QtWidgets.QMenu(self)
        
        edit_action = menu.addAction('Editar')
        calc_action = menu.addAction('Calcular Ingredientes')
        menu.addSeparator()
        del_action = menu.addAction('Excluir')
        
        action = menu.exec_(QtGui.QCursor.pos())
        if action == edit_action:
            self.edit_recipe(recipe_id)
        elif action == del_action:
            if QtWidgets.QMessageBox.Yes == QtWidgets.QMessageBox.question(self, "Confirmação", "Deseja realmente excluir?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No):
                self.delete_recipe(recipe_id)
        elif action == calc_action:
            self.calculate_ingredients(recipe_id)

    def delete_recipe(self, recipe_id):
        cursor.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        cursor.execute("DELETE FROM ingredients WHERE recipe_id = ?", (recipe_id,))
        conn.commit()
        self.load_recipes()

    def calculate_ingredients(self, recipe_id):
        cursor.execute("SELECT name, quantity FROM ingredients WHERE recipe_id = ?", (recipe_id,))
        ingred = cursor.fetchall()
        if ingred:
            qtd, ok = QtWidgets.QInputDialog.getInt(self, 'Calculadora', 'Quantidade de Pratos:')
            if ok:
                calc_ing = [(name, ceil(qtd / 5) * qty) for name, qty in ingred]
                dlg = CalculateDialog(self, calc_ing)
                dlg.exec_()
        else:
            QtWidgets.QMessageBox.information(self, 'Aviso', 'Sem ingredientes cadastrados.')

    def generate_pdf_report(self):
        try:
            cursor.execute("SELECT id, name, stock FROM recipes")
            recipes = cursor.fetchall()
            total_ingredients = {}
            for r in recipes:
                cursor.execute("SELECT name, quantity FROM ingredients WHERE recipe_id = ?", (r[0],))
                for name, qty in cursor.fetchall():
                    total_ingredients[name] = total_ingredients.get(name, 0) + (qty / 5) * r[2]
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "Relatorio de Estoque - Estrela do Oeste", ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", size=12)
            for ing, qtd in total_ingredients.items():
                pdf.cell(0, 10, f"{ing}: {ceil(qtd)}", ln=True)
            pdf.output("Relatorio_Estoque.pdf")
            QtWidgets.QMessageBox.information(self, "Sucesso", "PDF Gerado!")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Erro", str(e))

    def open_budget_dialog(self):
        dlg = BudgetDialog(self)
        dlg.exec_()

# --- DIALOGS (Janelas Secundárias) ---
class EditRecipeDialog(QtWidgets.QDialog):
    def __init__(self, parent, recipe_id):
        super().__init__(parent)
        self.setWindowTitle("Editar Receita")
        self.resize(500, 600)
        self.recipe_id = recipe_id
        
        # O background será aplicado via CSS Global
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(15)
        
        cursor.execute("SELECT name, dollar_value, stock, category FROM recipes WHERE id = ?", (recipe_id,))
        data = cursor.fetchone()
        
        layout.addWidget(QtWidgets.QLabel("Nome:"))
        self.name_edit = QtWidgets.QLineEdit(data[0])
        self.name_edit.textChanged.connect(lambda: self.name_edit.setText(self.name_edit.text().upper()))
        layout.addWidget(self.name_edit)
        
        h_layout = QtWidgets.QHBoxLayout()
        v1 = QtWidgets.QVBoxLayout()
        v1.addWidget(QtWidgets.QLabel("Preço ($):"))
        self.price = QtWidgets.QDoubleSpinBox()
        self.price.setValue(data[1])
        self.price.setMaximum(10000)
        v1.addWidget(self.price)
        h_layout.addLayout(v1)
        
        v2 = QtWidgets.QVBoxLayout()
        v2.addWidget(QtWidgets.QLabel("Estoque:"))
        self.stock = QtWidgets.QSpinBox()
        self.stock.setValue(data[2])
        self.stock.setMaximum(100000)
        v2.addWidget(self.stock)
        h_layout.addLayout(v2)
        layout.addLayout(h_layout)
        
        layout.addWidget(QtWidgets.QLabel("Categoria:"))
        self.cat = QtWidgets.QComboBox()
        self.cat.addItems(["Entrada", "Prato Principal", "Doces", "Bebidas Alcolicas", "Sucos", "Salgados", "Sopas", "Produtos da Fazenda"])
        self.cat.setCurrentText(data[3])
        layout.addWidget(self.cat)
        
        layout.addWidget(QtWidgets.QLabel("Ingredientes:"))
        self.ing_list = QtWidgets.QListWidget()
        layout.addWidget(self.ing_list)
        self.load_ing()
        
        # Área de Ingredientes (Estilo "Caixa")
        ing_box = QtWidgets.QFrame()
        # Estilo inline apenas para forçar o fundo transparente deste box específico se necessário
        ing_box.setStyleSheet("background: rgba(255,255,255,0.05); border-radius: 8px; padding: 5px;")
        ib_layout = QtWidgets.QHBoxLayout(ing_box)
        self.new_ing_name = QtWidgets.QLineEdit()
        self.new_ing_name.setPlaceholderText("Ingrediente...")
        self.new_ing_name.textChanged.connect(lambda: self.new_ing_name.setText(self.new_ing_name.text().upper()))
        
        cursor.execute("SELECT DISTINCT name FROM ingredients")
        comp = QtWidgets.QCompleter([r[0] for r in cursor.fetchall()])
        comp.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.new_ing_name.setCompleter(comp)
        
        ib_layout.addWidget(self.new_ing_name)
        self.new_ing_qtd = QtWidgets.QSpinBox()
        self.new_ing_qtd.setFixedWidth(60)
        self.new_ing_qtd.setMinimum(1)
        ib_layout.addWidget(self.new_ing_qtd)
        
        btn_add = QtWidgets.QPushButton("+")
        btn_add.setFixedWidth(40)
        btn_add.setObjectName("GradientButton")
        btn_add.clicked.connect(self.add_ing)
        ib_layout.addWidget(btn_add)
        layout.addWidget(ing_box)
        
        del_btn = QtWidgets.QPushButton("Remover Ingrediente")
        del_btn.setObjectName("GhostButton")
        del_btn.clicked.connect(self.del_ing)
        layout.addWidget(del_btn)
        
        btns = QtWidgets.QHBoxLayout()
        save = QtWidgets.QPushButton("Salvar")
        save.setObjectName("GradientButton")
        save.clicked.connect(self.save)
        btns.addWidget(save)
        
        cancel = QtWidgets.QPushButton("Cancelar")
        cancel.setObjectName("GhostButton")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)
        layout.addLayout(btns)

    def load_ing(self):
        self.ing_list.clear()
        cursor.execute("SELECT id, name, quantity FROM ingredients WHERE recipe_id=?", (self.recipe_id,))
        for r in cursor.fetchall():
            item = QtWidgets.QListWidgetItem(f"{r[1]} - {r[2]}")
            item.setData(QtCore.Qt.UserRole, r[0])
            self.ing_list.addItem(item)

    def add_ing(self):
        name = self.new_ing_name.text()
        if name:
            cursor.execute("INSERT INTO ingredients (recipe_id, name, quantity) VALUES (?,?,?)", (self.recipe_id, name, self.new_ing_qtd.value()))
            conn.commit()
            self.load_ing()
            self.new_ing_name.clear()

    def del_ing(self):
        cur = self.ing_list.currentItem()
        if cur:
            cursor.execute("DELETE FROM ingredients WHERE id=?", (cur.data(QtCore.Qt.UserRole),))
            conn.commit()
            self.load_ing()

    def save(self):
        cursor.execute("UPDATE recipes SET name=?, dollar_value=?, stock=?, category=? WHERE id=?", 
                       (self.name_edit.text(), self.price.value(), self.stock.value(), self.cat.currentText(), self.recipe_id))
        conn.commit()
        self.accept()

class CalculateDialog(QtWidgets.QDialog):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.setWindowTitle("Resultado")
        self.resize(300, 400)
        layout = QtWidgets.QVBoxLayout(self)
        lbl = QtWidgets.QLabel("Lista de Compras:")
        lbl.setStyleSheet("font-size: 14pt; color: #ffa500; font-weight: bold;")
        layout.addWidget(lbl)
        
        lst = QtWidgets.QListWidget()
        for n, q in data:
            lst.addItem(f"{n}: {q}")
        layout.addWidget(lst)
        
        btn = QtWidgets.QPushButton("Fechar")
        btn.setObjectName("GhostButton")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

class BudgetDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Orçamento")
        self.resize(700, 500)
        self.items = []
        
        layout = QtWidgets.QVBoxLayout(self)
        
        h_layout = QtWidgets.QHBoxLayout()
        
        left = QtWidgets.QVBoxLayout()
        left.addWidget(QtWidgets.QLabel("1. Escolha o item:"))
        self.rec_list = QtWidgets.QListWidget()
        cursor.execute("SELECT id, name, dollar_value FROM recipes")
        for r in cursor.fetchall():
            i = QtWidgets.QListWidgetItem(f"{r[1]} - ${r[2]}")
            i.setData(QtCore.Qt.UserRole, r)
            self.rec_list.addItem(i)
        left.addWidget(self.rec_list)
        
        q_layout = QtWidgets.QHBoxLayout()
        q_layout.addWidget(QtWidgets.QLabel("Qtd:"))
        self.qtd = QtWidgets.QSpinBox()
        self.qtd.setMinimum(1)
        q_layout.addWidget(self.qtd)
        left.addLayout(q_layout)
        
        add = QtWidgets.QPushButton("Adicionar >>")
        add.setObjectName("GradientButton")
        add.clicked.connect(self.add_item)
        left.addWidget(add)
        
        h_layout.addLayout(left)
        
        right = QtWidgets.QVBoxLayout()
        right.addWidget(QtWidgets.QLabel("2. Itens Selecionados:"))
        self.sel_list = QtWidgets.QListWidget()
        right.addWidget(self.sel_list)
        
        self.total_lbl = QtWidgets.QLabel("Total: $0.00")
        self.total_lbl.setStyleSheet("font-size: 18pt; color: #ff9966; font-weight: bold;")
        self.total_lbl.setAlignment(QtCore.Qt.AlignRight)
        right.addWidget(self.total_lbl)
        
        rem = QtWidgets.QPushButton("Remover")
        rem.setObjectName("GhostButton")
        rem.clicked.connect(self.rem_item)
        right.addWidget(rem)
        
        h_layout.addLayout(right)
        layout.addLayout(h_layout)
        
        gen = QtWidgets.QPushButton("Gerar PDF")
        gen.setObjectName("GradientButton")
        gen.clicked.connect(self.gen_pdf)
        layout.addWidget(gen)

    def add_item(self):
        cur = self.rec_list.currentItem()
        if cur:
            data = cur.data(QtCore.Qt.UserRole)
            q = self.qtd.value()
            sub = data[2] * q
            self.items.append((data[1], q, sub))
            self.sel_list.addItem(f"{data[1]} (x{q}) = ${sub:.2f}")
            self.update_total()

    def rem_item(self):
        row = self.sel_list.currentRow()
        if row >= 0:
            self.sel_list.takeItem(row)
            del self.items[row]
            self.update_total()

    def update_total(self):
        tot = sum(x[2] for x in self.items)
        self.total_lbl.setText(f"Total: ${tot:.2f}")

    def gen_pdf(self):
        if not self.items: return
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Orcamento", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        for n, q, v in self.items:
            pdf.cell(0, 10, f"{n} (x{q}) - ${v:.2f}", ln=True)
        pdf.ln(5)
        tot = sum(x[2] for x in self.items)
        pdf.cell(0, 10, f"TOTAL: ${tot:.2f}", ln=True, align='R')
        pdf.output("Orcamento.pdf")
        QtWidgets.QMessageBox.information(self, "Sucesso", "PDF Salvo!")
        self.accept()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ex = RecipeApp()
    ex.show()
    sys.exit(app.exec_())