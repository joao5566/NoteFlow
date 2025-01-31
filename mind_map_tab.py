import markdown
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit,
    QScrollArea, QFileDialog, QMessageBox, QToolBar, QAction, QFontComboBox, QSpinBox,
    QColorDialog, QDialog, QFormLayout, QTextBrowser
)
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

        # Título da aba
        self.layout.addWidget(QLabel("Editor de Texto"))

        # Área de texto
        self.text_area = QTextEdit(self)  # Inicializa o QTextEdit antes da barra de ferramentas
        self.layout.addWidget(self.text_area)

        # Conecta o sinal de alteração de texto para atualizar o preview em tempo real
        self.text_area.textChanged.connect(self.update_preview)

        # Barra de ferramentas
        self.toolbar = QToolBar(self)
        self.add_actions_to_toolbar()  # Agora, self.text_area já está definido
        self.layout.addWidget(self.toolbar)  # Coloca a barra de ferramentas no topo

        # Barra de rolagem (opcional, já que QTextEdit já possui barras de rolagem)
        # Se quiser manter, certifique-se de que não está adicionando QTextEdit duas vezes
        # self.scroll_area = QScrollArea(self)
        # self.scroll_area.setWidget(self.text_area)
        # self.scroll_area.setWidgetResizable(True)
        # self.layout.addWidget(self.scroll_area)

        # Layout de botões
        self.button_layout = QHBoxLayout()

        # Botões para salvar, carregar, limpar e visualizar
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

        # Área de preview
        self.preview_area = QTextBrowser(self)
        self.preview_area.setVisible(True)  # Preview visível por padrão
        self.layout.addWidget(self.preview_area)

        # Suporte para tema padrão (tema claro ou escuro)
        self.apply_theme()

    def apply_theme(self):
        """Aplica o tema de escuro/claro ao editor (padrão do sistema)"""
        # O Qt gerencia o tema automaticamente com base nas configurações do sistema
        pass

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

    def open_find_replace_dialog(self):
        """Abre a caixa de diálogo para buscar e substituir texto."""
        dialog = FindReplaceDialog(self)
        dialog.exec_()

    def save_file(self):
        """Salva o conteúdo do editor de texto em um arquivo Markdown."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo", "", "Markdown Files (*.md);;Text Files (*.txt)")
        if file_path:
            try:
                markdown_content = self.text_area.toPlainText()
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(markdown_content)
                QMessageBox.information(self, "Sucesso", "Arquivo salvo com sucesso!")
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Erro ao salvar o arquivo: {e}")

    def load_file(self):
        """Carrega o conteúdo de um arquivo Markdown para o editor de texto."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Carregar Arquivo", "", "Markdown Files (*.md);;Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    markdown_content = file.read()
                    self.text_area.setPlainText(markdown_content)
                QMessageBox.information(self, "Sucesso", "Arquivo carregado com sucesso!")
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Erro ao carregar o arquivo: {e}")

    def clear_text(self):
        """Limpa o conteúdo do editor de texto."""
        self.text_area.clear()

    def update_preview(self):
        """Atualiza o preview em tempo real ao digitar o texto no editor."""
        markdown_text = self.text_area.toPlainText()
        
        # Converte Markdown para HTML com as extensões 'fenced_code' e 'codehilite' para blocos de código
        html_content = markdown.markdown(markdown_text, extensions=['fenced_code', 'codehilite'])
        
        # Define estilos CSS para o preview, incluindo estilos para blocos de código
        css = f"""
        <style>
            body {{
                font-size: {self.font_size_spinbox.value()}px;
                white-space: pre-wrap;  /* Preserva espaços e quebras de linha */
            }}
            pre {{
                background-color: #f0f0f0;
                padding: 10px;
                border-radius: 5px;
                white-space: pre;  /* Preserva a formatação do código */
                font-family: monospace;
            }}
            code {{
                background-color: #f0f0f0;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: monospace;
            }}
            /* Estilos para codehilite */
            .codehilite {{
                background: #f0f0f0;
                padding: 10px;
                border-radius: 5px;
            }}
            .codehilite .hll {{ background-color: #ffffcc }}
            /* Adicione mais estilos conforme necessário */
        </style>
        """
        
        # Combina o CSS com o conteúdo HTML gerado
        full_html = css + html_content
        
        # Atualiza a área de visualização com o HTML gerado
        self.preview_area.setHtml(full_html)

    def change_font(self, font):
        current_font = self.text_area.currentFont()
        current_font.setFamily(font.family())
        self.text_area.setCurrentFont(current_font)
        self.update_preview()  # Atualiza o preview para refletir a mudança

    def change_font_size(self, size):
        current_font = self.text_area.currentFont()
        current_font.setPointSize(size)
        self.text_area.setCurrentFont(current_font)
        self.update_preview()  # Atualiza o preview para refletir a mudança

    def change_text_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.text_area.setTextColor(color)
            # Atualiza a cor no preview também adicionando ao CSS
            css_color = f"color: {color.name()};"
            existing_css = self.preview_area.toHtml()
            
            # Remover estilos anteriores de cor, se existirem
            import re
            updated_css = re.sub(r'color: #[0-9A-Fa-f]{6};', '', existing_css)
            
            # Adicionar a nova cor
            new_css = f"""
                font-size: {self.font_size_spinbox.value()}px;
                white-space: pre-wrap;
                {css_color}
            """
            self.preview_area.setStyleSheet(new_css)
