from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit, QScrollArea, QFileDialog, QMessageBox, QToolBar, QAction, QFontComboBox, QSpinBox, QColorDialog, QDialog, QFormLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor


class FindReplaceDialog(QDialog):
    """Caixa de diálogo para busca e substituição."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Buscar e Substituir")
        self.layout = QFormLayout(self)

        self.find_label = QLabel("Buscar:", self)
        self.find_input = QLineEdit(self)

        self.replace_label = QLabel("Substituir por:", self)
        self.replace_input = QLineEdit(self)

        self.find_button = QPushButton("Buscar", self)
        self.replace_button = QPushButton("Substituir", self)

        self.layout.addRow(self.find_label, self.find_input)
        self.layout.addRow(self.replace_label, self.replace_input)
        self.layout.addRow(self.find_button, self.replace_button)

        self.find_button.clicked.connect(self.find_text)
        self.replace_button.clicked.connect(self.replace_text)

    def find_text(self):
        """Realiza a busca de texto."""
        find_text = self.find_input.text()
        if find_text:
            cursor = self.parent().text_area.textCursor()
            document = self.parent().text_area.document()

            # Busca o texto dentro do QTextEdit
            cursor = document.find(find_text, cursor)
            if cursor.isNull():
                QMessageBox.information(self, "Busca", "Texto não encontrado!")
            else:
                self.parent().text_area.setTextCursor(cursor)

    def replace_text(self):
        """Substitui o texto encontrado por outro."""
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()
        if find_text and replace_text:
            document = self.parent().text_area.document()
            text = self.parent().text_area.toPlainText()
            new_text = text.replace(find_text, replace_text)
            self.parent().text_area.setPlainText(new_text)


class MindMapTab(QWidget):
    """Aba para o Editor de Texto com funcionalidades avançadas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # Layout para os controles
        self.controls_layout = QHBoxLayout()

        # Título da aba
        self.layout.addWidget(QLabel("Editor de Texto"))

        # Área de texto
        self.text_area = QTextEdit(self)
        self.layout.addWidget(self.text_area)

        # Barra de rolagem
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidget(self.text_area)
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)

        # Layout de botões
        self.button_layout = QHBoxLayout()

        # Botões para salvar, carregar e limpar
        self.save_button = QPushButton("Salvar", self)
        self.save_button.clicked.connect(self.save_file)
        self.button_layout.addWidget(self.save_button)

        self.load_button = QPushButton("Carregar", self)
        self.load_button.clicked.connect(self.load_file)
        self.button_layout.addWidget(self.load_button)

        self.clear_button = QPushButton("Limpar", self)
        self.clear_button.clicked.connect(self.clear_text)
        self.button_layout.addWidget(self.clear_button)

        self.layout.addLayout(self.button_layout)

        # Barra de ferramentas
        self.toolbar = QToolBar(self)
        self.layout.addWidget(self.toolbar)

        # Adicionar ações à barra de ferramentas
        self.add_actions_to_toolbar()

    def add_actions_to_toolbar(self):
        """Adiciona ações à barra de ferramentas para formatação de texto."""
        # Ação de desfazer (Undo)
        undo_action = QAction("Desfazer", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.text_area.undo)
        self.toolbar.addAction(undo_action)

        # Ação de refazer (Redo)
        redo_action = QAction("Refazer", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.text_area.redo)
        self.toolbar.addAction(redo_action)

        # Ação de busca e substituição
        find_replace_action = QAction("Buscar e Substituir", self)
        find_replace_action.triggered.connect(self.open_find_replace_dialog)
        self.toolbar.addAction(find_replace_action)

        # Ação de negrito
        bold_action = QAction("Negrito", self)
        bold_action.setShortcut("Ctrl+B")
        bold_action.triggered.connect(self.toggle_bold)
        self.toolbar.addAction(bold_action)

        # Ação de itálico
        italic_action = QAction("Itálico", self)
        italic_action.setShortcut("Ctrl+I")
        italic_action.triggered.connect(self.toggle_italic)
        self.toolbar.addAction(italic_action)

        # Ação de sublinhado
        underline_action = QAction("Sublinhado", self)
        underline_action.setShortcut("Ctrl+U")
        underline_action.triggered.connect(self.toggle_underline)
        self.toolbar.addAction(underline_action)

        # Seleção de fonte
        self.font_combo = QFontComboBox(self)
        self.font_combo.currentFontChanged.connect(self.change_font)
        self.toolbar.addWidget(self.font_combo)

        # Seleção de tamanho da fonte
        self.font_size_spinbox = QSpinBox(self)
        self.font_size_spinbox.setValue(12)
        self.font_size_spinbox.setRange(6, 72)
        self.font_size_spinbox.valueChanged.connect(self.change_font_size)
        self.toolbar.addWidget(self.font_size_spinbox)

        # Ação para alterar a cor do texto
        color_action = QAction("Cor do Texto", self)
        color_action.triggered.connect(self.change_text_color)
        self.toolbar.addAction(color_action)

        # Ação de alinhamento à esquerda
        left_align_action = QAction("Alinhar Esquerda", self)
        left_align_action.triggered.connect(self.align_left)
        self.toolbar.addAction(left_align_action)

        # Ação de alinhamento ao centro
        center_align_action = QAction("Alinhar Centro", self)
        center_align_action.triggered.connect(self.align_center)
        self.toolbar.addAction(center_align_action)

        # Ação de alinhamento à direita
        right_align_action = QAction("Alinhar Direita", self)
        right_align_action.triggered.connect(self.align_right)
        self.toolbar.addAction(right_align_action)

    def open_find_replace_dialog(self):
        """Abre a caixa de diálogo para buscar e substituir texto."""
        dialog = FindReplaceDialog(self)
        dialog.exec_()

    def save_file(self):
        """Salva o conteúdo do editor de texto em um arquivo com formatação HTML."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo", "", "HTML Files (*.html);;Text Files (*.txt)")
        if file_path:
            # Se o arquivo não tiver extensão, adiciona .html
            if not file_path.endswith(('.html', '.htm')):
                file_path += '.html'
            try:
                # Salvando o conteúdo como HTML
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.text_area.toHtml())
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Erro ao salvar o arquivo: {e}")

    def load_file(self):
        """Carrega o conteúdo de um arquivo HTML para o editor de texto."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Carregar Arquivo", "", "HTML Files (*.html);;Text Files (*.txt)")
        if file_path:
            try:
                # Carregando o conteúdo de um arquivo HTML
                with open(file_path, 'r', encoding='utf-8') as file:
                    if file_path.endswith(('.html', '.htm')):
                        self.text_area.setHtml(file.read())
                    else:
                        self.text_area.setPlainText(file.read())
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Erro ao carregar o arquivo: {e}")

    def clear_text(self):
        """Limpa o conteúdo do editor de texto."""
        self.text_area.clear()

    def toggle_bold(self):
        """Alterna o estilo de negrito."""
        current_font = self.text_area.currentFont()
        current_font.setBold(not current_font.bold())
        self.text_area.setCurrentFont(current_font)

    def toggle_italic(self):
        """Alterna o estilo de itálico."""
        current_font = self.text_area.currentFont()
        current_font.setItalic(not current_font.italic())
        self.text_area.setCurrentFont(current_font)

    def toggle_underline(self):
        """Alterna o estilo de sublinhado."""
        current_font = self.text_area.currentFont()
        current_font.setUnderline(not current_font.underline())
        self.text_area.setCurrentFont(current_font)

    def change_font(self, font):
        """Altera a fonte do texto."""
        current_font = self.text_area.currentFont()
        current_font.setFamily(font.family())
        self.text_area.setCurrentFont(current_font)

    def change_font_size(self, size):
        """Altera o tamanho da fonte."""
        current_font = self.text_area.currentFont()
        current_font.setPointSize(size)
        self.text_area.setCurrentFont(current_font)

    def change_text_color(self):
        """Muda a cor do texto selecionado."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.text_area.setTextColor(color)

    def align_left(self):
        """Alinha o texto à esquerda."""
        self.text_area.setAlignment(Qt.AlignLeft)

    def align_center(self):
        """Alinha o texto ao centro."""
        self.text_area.setAlignment(Qt.AlignCenter)

    def align_right(self):
        """Alinha o texto à direita."""
        self.text_area.setAlignment(Qt.AlignRight)

