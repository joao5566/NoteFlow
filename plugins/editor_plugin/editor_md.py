# mind_map_plugin_tab.py
import markdown
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit,
    QScrollArea, QFileDialog, QMessageBox, QToolBar, QAction, QSpinBox,
    QColorDialog, QDialog, QFormLayout, QTextBrowser
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

# Importa a classe base para plugins
from plugin_base import PluginTab


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

        # Variáveis de estado para estilos
        self.current_text_color = "#000000"  # Cor padrão: preto
        self.editor_font_size = 12           # Tamanho de fonte padrão do editor
        self.preview_font_size = 12          # Tamanho de fonte padrão do preview

        # Título da aba
        self.layout.addWidget(QLabel("Editor de Texto"))

        # Área de texto
        self.text_area = QTextEdit(self)
        self.text_area.setFontPointSize(self.editor_font_size)
        self.layout.addWidget(self.text_area)
        self.text_area.textChanged.connect(self.update_preview)

        # Barra de ferramentas
        self.toolbar = QToolBar(self)
        self.add_actions_to_toolbar()
        self.layout.addWidget(self.toolbar)

        # Layout de botões para salvar, carregar e limpar
        self.button_layout = QHBoxLayout()
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

        # Suporte para tema (pode ser implementado conforme necessário)
        self.apply_theme()

        # Atualiza o preview inicialmente
        self.update_preview()

    def apply_theme(self):
        """Aplica o tema (aqui é mantida a implementação padrão)."""
        pass

    def add_actions_to_toolbar(self):
        """Adiciona ações à barra de ferramentas para formatação de texto."""
        undo_action = QAction("Desfazer", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.text_area.undo)
        self.toolbar.addAction(undo_action)

        redo_action = QAction("Refazer", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.text_area.redo)
        self.toolbar.addAction(redo_action)

        find_replace_action = QAction("Buscar e Substituir", self)
        find_replace_action.triggered.connect(self.open_find_replace_dialog)
        self.toolbar.addAction(find_replace_action)

        # Seleção de tamanho da fonte do editor
        self.editor_font_size_spinbox = QSpinBox(self)
        self.editor_font_size_spinbox.setValue(self.editor_font_size)
        self.editor_font_size_spinbox.setRange(6, 72)
        self.editor_font_size_spinbox.setSingleStep(1)
        self.editor_font_size_spinbox.valueChanged.connect(self.change_editor_font_size)
        self.toolbar.addWidget(QLabel("Tamanho Fonte Editor: "))
        self.toolbar.addWidget(self.editor_font_size_spinbox)

        # Seleção de tamanho da fonte do preview
        self.preview_font_size_spinbox = QSpinBox(self)
        self.preview_font_size_spinbox.setValue(self.preview_font_size)
        self.preview_font_size_spinbox.setRange(6, 72)
        self.preview_font_size_spinbox.setSingleStep(1)
        self.preview_font_size_spinbox.valueChanged.connect(self.change_preview_font_size)
        self.toolbar.addWidget(QLabel("Tamanho Fonte Preview: "))
        self.toolbar.addWidget(self.preview_font_size_spinbox)

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
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Salvar Arquivo", 
            "", 
            "Markdown Files (*.md);;Text Files (*.txt)"
        )
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
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Carregar Arquivo", 
            "", 
            "Markdown Files (*.md);;Text Files (*.txt)"
        )
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
        html_content = markdown.markdown(
            markdown_text, 
            extensions=['fenced_code', 'codehilite', 'nl2br']
        )
        css = f"""
        <style>
            .preview {{
                font-size: {self.preview_font_size}px;
                color: {self.current_text_color};
                white-space: pre-wrap;
            }}
            pre {{
                background-color: #f0f0f0;
                padding: 10px;
                border-radius: 5px;
                white-space: pre;
                font-family: monospace;
            }}
            code {{
                background-color: #f0f0f0;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: monospace;
            }}
            .codehilite {{
                background: #f0f0f0;
                padding: 10px;
                border-radius: 5px;
            }}
            .codehilite .hll {{ background-color: #ffffcc }}
        </style>
        """
        full_html = f"{css}<div class='preview'>{html_content}</div>"
        self.preview_area.setHtml(full_html)

    def change_editor_font_size(self, size):
        """Altera o tamanho da fonte no editor e atualiza o preview."""
        self.editor_font_size = size
        current_font = self.text_area.currentFont()
        current_font.setPointSize(size)
        self.text_area.setCurrentFont(current_font)
        self.update_preview()

    def change_preview_font_size(self, size):
        """Altera o tamanho da fonte no preview e atualiza o preview."""
        self.preview_font_size = size
        self.update_preview()

    def change_text_color(self):
        """Altera a cor do texto no editor e atualiza o preview."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_text_color = color.name()
            self.text_area.setTextColor(color)
            self.update_preview()


###############################################################################
# Plugin: Editor de Texto (Mind Map) como aba de plugin
###############################################################################
class PluginMindMapTab(PluginTab):
    """
    Plugin que adiciona uma aba com o Editor de Texto avançado.
    """
    name = "Editor de Texto"

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        # Instancia o editor (MindMapTab)
        self.editor = MindMapTab(self)
        layout.addWidget(self.editor)
        self.setLayout(layout)


# Variável global para o carregamento do plugin
plugin_class = PluginMindMapTab

# Código para teste independente (opcional)
def main():
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    window = PluginMindMapTab()
    window.setWindowTitle("Plugin: Editor de Texto")
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
