import os
import sqlite3
import base64
import markdown
from fpdf import FPDF
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QLabel, QHBoxLayout,
    QLineEdit, QColorDialog, QFontDialog, QCheckBox, QComboBox,
    QFileDialog, QMessageBox, QTextBrowser, QInputDialog, QTextEdit
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QFont, QKeyEvent, QTextDocument

# Subclasse de QTextEdit para inserir espaços ao pressionar Tab
class CustomTextEdit(QTextEdit):
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Tab:
            # Insere 4 espaços; ajuste conforme desejado
            self.insertPlainText("    ")
        else:
            super().keyPressEvent(event)

DB_PATH = "data.db"

class NoteDialog(QDialog):
    """Diálogo para criar ou editar uma nota com suporte a Markdown."""
    def __init__(self, parent=None, mode="view", note_date=None):
        super().__init__(parent)
        self.setWindowTitle("Nota")
        # Define flags para os botões de minimizar, maximizar e fechar
        self.setWindowFlags(self.windowFlags() |
                            Qt.WindowMaximizeButtonHint |
                            Qt.WindowMinimizeButtonHint)
                            
        self.layout = QVBoxLayout(self)
        self.mode = mode
        self.note_date = note_date
        self.is_markdown_mode = False  # Se True, opera em modo Markdown (texto puro)
        self.current_text_color = "#000000"  # Cor padrão para o preview
        self.preview_font_size = 12  # Tamanho da fonte para o preview
        # Variável para armazenar regras CSS personalizadas (apenas o conteúdo interno, sem <style> tags)
        self.header_css = ""

        # Usa CustomTextEdit para melhorar a edição (especialmente a tecla Tab)
        self.note_edit = CustomTextEdit(self)
        self.note_edit.setReadOnly(mode == "view")
        self.layout.addWidget(self.note_edit)

        # Barra de ferramentas (desfazer, refazer, buscar) no modo edição
        if mode == "edit":
            self.editor_tools_layout = QHBoxLayout()
            self.undo_button = QPushButton("Desfazer", self)
            self.undo_button.clicked.connect(self.note_edit.undo)
            self.editor_tools_layout.addWidget(self.undo_button)

            self.redo_button = QPushButton("Refazer", self)
            self.redo_button.clicked.connect(self.note_edit.redo)
            self.editor_tools_layout.addWidget(self.redo_button)

            self.find_edit = QLineEdit(self)
            self.find_edit.setPlaceholderText("Buscar...")
            self.editor_tools_layout.addWidget(self.find_edit)

            self.find_button = QPushButton("Buscar", self)
            self.find_button.clicked.connect(self.find_text)
            self.editor_tools_layout.addWidget(self.find_button)

            self.layout.addLayout(self.editor_tools_layout)

        # Checkbox para habilitar o modo Markdown (modo edição)
        if mode == "edit":
            self.markdown_checkbox = QCheckBox("Usar Markdown", self)
            self.markdown_checkbox.stateChanged.connect(self.toggle_markdown_mode)
            self.layout.addWidget(self.markdown_checkbox)

        # Área de pré-visualização (inicialmente oculta)
        self.preview_browser = QTextBrowser(self)
        self.preview_browser.setVisible(False)
        self.layout.addWidget(self.preview_browser)

        # Barra de formatação (modo edição)
        if mode == "edit":
            self.format_buttons_layout = QHBoxLayout()
            self.layout.addLayout(self.format_buttons_layout)
            self.add_format_buttons()

        # Campos para categorias e tags
        self.layout.addWidget(QLabel("Categorias (separadas por vírgula):"))
        self.category_input = QLineEdit(self)
        self.category_input.setReadOnly(mode == "view")
        self.layout.addWidget(self.category_input)

        self.layout.addWidget(QLabel("Tags (separadas por vírgula):"))
        self.tags_input = QLineEdit(self)
        self.tags_input.setReadOnly(mode == "view")
        self.layout.addWidget(self.tags_input)

        # Checkbox para marcar como feito (modo edição)
        if mode == "edit":
            self.done_checkbox = QCheckBox("Marcar como Feito", self)
            self.done_checkbox.stateChanged.connect(self.toggle_done_tag)
            self.layout.addWidget(self.done_checkbox)

        # Botões de ação (salvar ou visualizar)
        self.action_buttons_layout = QHBoxLayout()
        self.layout.addLayout(self.action_buttons_layout)
        if mode == "edit":
            self.add_save_button()
        else:
            self.add_view_buttons()

        # Auto-save (modo edição)
        if mode == "edit":
            self.auto_save_timer = QTimer(self)
            self.auto_save_timer.timeout.connect(self.auto_save_note)
            self.auto_save_timer.start(60000)

    def add_format_buttons(self):
        """Adiciona botões de formatação (para rich text)."""
        self.color_button = QPushButton("Cor do Texto", self)
        self.color_button.clicked.connect(self.change_text_color)
        self.format_buttons_layout.addWidget(self.color_button)

        self.font_button = QPushButton("Alterar Fonte", self)
        self.font_button.clicked.connect(self.change_font)
        self.format_buttons_layout.addWidget(self.font_button)

        self.font_size_combo = QComboBox(self)
        self.font_size_combo.addItems([str(size) for size in range(8, 30)])
        self.font_size_combo.setCurrentText("12")
        self.font_size_combo.currentTextChanged.connect(self.change_font_size)
        self.format_buttons_layout.addWidget(QLabel("Tamanho da Fonte:"))
        self.format_buttons_layout.addWidget(self.font_size_combo)

        self.bold_button = QPushButton("Negrito", self)
        self.bold_button.clicked.connect(self.toggle_bold)
        self.format_buttons_layout.addWidget(self.bold_button)

        self.italic_button = QPushButton("Itálico", self)
        self.italic_button.clicked.connect(self.toggle_italic)
        self.format_buttons_layout.addWidget(self.italic_button)

        self.underline_button = QPushButton("Sublinhado", self)
        self.underline_button.clicked.connect(self.toggle_underline)
        self.format_buttons_layout.addWidget(self.underline_button)

        self.image_button = QPushButton("Inserir Imagem", self)
        self.image_button.clicked.connect(self.insert_image)
        self.format_buttons_layout.addWidget(self.image_button)

        # Botão para configurar regras personalizadas
        self.header_style_button = QPushButton("Regras Personalizadas", self)
        self.header_style_button.clicked.connect(self.configure_headers)
        self.format_buttons_layout.addWidget(self.header_style_button)

    def configure_headers(self):
        """Abre um diálogo para que o usuário insira regras CSS personalizadas.
        O valor armazenado será apenas o conteúdo interno do CSS (sem <style> tags).
        Atualiza o preview imediatamente."""
        current_css = self.header_css
        if current_css.startswith("<style>") and current_css.endswith("</style>"):
            current_css = current_css[len("<style>"):-len("</style>")]
        if not current_css.strip():
            current_css = "h1 { font-size: 36px; color: black; }"
        css_text, ok = QInputDialog.getMultiLineText(
            self, "Regras Personalizadas",
            "Insira as regras CSS para personalizar seus elementos (ex: h1, h2, h3, .custom-title, etc.):",
            current_css
        )
        if ok:
            self.header_css = css_text.strip()  # Armazena somente o conteúdo interno
            if self.is_markdown_mode:
                self.update_markdown_preview()

    def insert_image(self):
        """Insere uma imagem convertida para Base64 no editor."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Imagem", "", "Imagens (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        if file_path:
            with open(file_path, "rb") as image_file:
                encoded_bytes = base64.b64encode(image_file.read())
                encoded_string = encoded_bytes.decode("utf-8")
            alt_text, ok = QInputDialog.getText(self, "Descrição da Imagem", "Digite a descrição da imagem:")
            if not ok or not alt_text.strip():
                alt_text = "imagem"
            width_str, ok = QInputDialog.getText(self, "Largura da Imagem", "Digite a largura (px) ou deixe em branco para tamanho natural:")
            if ok and width_str.strip():
                try:
                    width = int(width_str)
                    style_attr = f'style="width:{width}px;"'
                except ValueError:
                    style_attr = ""
            else:
                style_attr = ""
            ext = os.path.splitext(file_path)[1].lower()
            if ext in [".jpg", ".jpeg"]:
                mime = "image/jpeg"
            elif ext == ".gif":
                mime = "image/gif"
            elif ext == ".bmp":
                mime = "image/bmp"
            else:
                mime = "image/png"
            data_uri = f"data:{mime};base64,{encoded_string}"
            cursor = self.note_edit.textCursor()
            image_html = f'<img src="{data_uri}" alt="{alt_text}" {style_attr} />'
            cursor.insertHtml(image_html)

    def add_save_button(self):
        """Adiciona o botão de salvar."""
        self.save_button = QPushButton("Salvar", self)
        self.save_button.clicked.connect(self.handle_save)
        self.action_buttons_layout.addWidget(self.save_button)

    def add_view_buttons(self):
        """Adiciona botões de visualização (modo não edição)."""
        self.edit_button = QPushButton("Editar", self)
        self.edit_button.clicked.connect(self.enable_edit_mode)
        self.action_buttons_layout.addWidget(self.edit_button)

        self.export_button = QPushButton("Exportar como PDF", self)
        self.export_button.clicked.connect(self.export_to_pdf)
        self.action_buttons_layout.addWidget(self.export_button)

    def handle_save(self):
        """Valida e salva a nota."""
        if self.validate_note_data():
            if self.is_markdown_mode:
                raw_content = self.note_edit.toPlainText()
                html_content = raw_content  # Ambos recebem o mesmo valor
            else:
                html_content = self.note_edit.toHtml()
                raw_content = ""
            categories = ",".join([cat.strip() for cat in self.category_input.text().split(",") if cat.strip()])
            tags = ",".join([tag.strip() for tag in self.tags_input.text().split(",") if tag.strip()])
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                if self.mode == "edit" and hasattr(self, 'note_id'):
                    cursor.execute(
                        "UPDATE notes SET text = ?, raw_text = ?, categories = ?, tags = ?, is_markdown = ?, custom_css = ? WHERE id = ?",
                        (html_content, raw_content, categories, tags, int(self.is_markdown_mode), self.header_css, self.note_id)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO notes (date, text, raw_text, categories, tags, is_markdown, custom_css) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (self.note_date, html_content, raw_content, categories, tags, int(self.is_markdown_mode), self.header_css)
                    )
                conn.commit()
            QMessageBox.information(self, "Sucesso", "Nota salva com sucesso.")
            self.accept()

    def validate_note_data(self):
        """Valida se a nota não está vazia."""
        if not self.note_edit.toPlainText().strip():
            QMessageBox.warning(self, "Aviso", "A nota não pode estar vazia.")
            return False
        return True

    def export_to_pdf(self):
        """Exporta a nota para PDF."""
        path, _ = QFileDialog.getSaveFileName(self, "Exportar Nota como PDF", "nota.pdf", "Arquivos PDF (*.pdf)")
        if path:
            content = self.get_current_content()
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, self.strip_html(content))
            pdf.output(path)
            QMessageBox.information(self, "Exportação Concluída", f"Nota exportada como PDF em '{path}'")

    def toggle_done_tag(self, state):
        """Adiciona ou remove a tag 'feito'."""
        tags = [tag.strip() for tag in self.tags_input.text().split(",") if tag.strip()]
        if state == Qt.Checked:
            if "feito" not in tags:
                tags.append("feito")
        else:
            if "feito" in tags:
                tags.remove("feito")
        self.tags_input.setText(",".join(tags))

    def auto_save_note(self):
        """Realiza o auto-save da nota."""
        content = self.get_current_content()
        path = os.path.join(os.getcwd(), "auto_save_note.html")
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)
        print(f"Nota salva automaticamente em {path}")

    def get_current_content(self):
        """
        Gera o conteúdo atual da nota.
        Se o modo Markdown estiver ativo, converte o texto com markdown e adiciona os estilos CSS,
        incluindo as regras personalizadas (envolvidas em uma única tag <style>);
        caso contrário, retorna o HTML do editor.
        """
        raw_text = self.note_edit.toPlainText()
        if self.is_markdown_mode:
            html_content = markdown.markdown(
                raw_text,
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
            # Envolve o CSS personalizado em uma única tag <style> se existir
            header_style = f"<style>{self.header_css}</style>" if self.header_css else ""
            full_html = f"{header_style}{css}<div class='preview'>{html_content}</div>"
            return full_html
        else:
            return self.note_edit.toHtml()

    def get_note_data(self):
        """Retorna os dados atuais da nota, incluindo as regras personalizadas."""
        tags = [tag.strip() for tag in self.tags_input.text().split(",") if tag.strip()]
        if self.is_markdown_mode:
            note_text = self.note_edit.toPlainText()
        else:
            note_text = self.get_current_content()
        return {
            "text": note_text,
            "categories": [cat.strip() for cat in self.category_input.text().split(",") if cat.strip()],
            "tags": tags,
            "custom_css": self.header_css
        }

    def set_note_data(self, data):
        """Popula os campos do diálogo com os dados da nota."""
        is_md = int(data.get("is_markdown", 0))
        if is_md == 1:
            self.note_edit.setPlainText(data.get("raw_text", ""))
            self.is_markdown_mode = True
            if self.mode == "edit":
                self.markdown_checkbox.setChecked(True)
        else:
            self.note_edit.setHtml(data.get("text", ""))
            self.is_markdown_mode = False

        self.category_input.setText(", ".join(data.get("categories", [])))
        self.tags_input.setText(", ".join(data.get("tags", [])))
        # Carrega as regras personalizadas salvas na nota
        self.header_css = data.get("custom_css", "")
        if self.mode == "edit":
            self.done_checkbox.setChecked("feito" in data.get("tags", []))
            self.note_id = data.get("id")
        # Atualiza o preview se estiver em modo Markdown, mesmo que o texto não tenha sido alterado
        if self.is_markdown_mode:
            self.update_markdown_preview()

    def enable_edit_mode(self):
        """Ativa o modo de edição da nota."""
        self.mode = "edit"
        self.note_edit.setReadOnly(False)
        self.category_input.setReadOnly(False)
        self.tags_input.setReadOnly(False)
        self.done_checkbox.setVisible(True)
        for i in reversed(range(self.action_buttons_layout.count())):
            widget = self.action_buttons_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.add_format_buttons()
        self.add_save_button()

    def toggle_markdown_mode(self, state):
        """Ativa ou desativa o modo Markdown e atualiza a pré-visualização."""
        if state == Qt.Checked:
            self.is_markdown_mode = True
            # Não desabilita os botões para manter a barra ativa
            self.preview_browser.setVisible(True)
            self.note_edit.textChanged.connect(self.update_markdown_preview)
            self.update_markdown_preview()
        else:
            self.is_markdown_mode = False
            self.set_format_buttons_enabled(True)
            self.preview_browser.setVisible(False)
            try:
                self.note_edit.textChanged.disconnect(self.update_markdown_preview)
            except TypeError:
                pass

    def set_format_buttons_enabled(self, enabled):
        """Habilita ou desabilita os botões de formatação."""
        for i in range(self.format_buttons_layout.count()):
            widget = self.format_buttons_layout.itemAt(i).widget()
            if widget:
                widget.setEnabled(enabled)

    def update_markdown_preview(self):
        """Atualiza a pré-visualização do Markdown."""
        html = self.get_current_content()
        self.preview_browser.setHtml(html)

    def change_text_color(self):
        """Altera a cor do texto selecionado."""
        from PyQt5.QtWidgets import QColorDialog
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_text_color = color.name()
            cursor = self.note_edit.textCursor()
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            if cursor.hasSelection():
                cursor.mergeCharFormat(fmt)
            else:
                self.note_edit.setCurrentCharFormat(fmt)
            if self.is_markdown_mode:
                self.update_markdown_preview()

    def change_font(self):
        """Altera a fonte do texto selecionado."""
        font, ok = QFontDialog.getFont()
        if ok:
            cursor = self.note_edit.textCursor()
            fmt = QTextCharFormat()
            fmt.setFont(font)
            if cursor.hasSelection():
                cursor.mergeCharFormat(fmt)
            else:
                self.note_edit.setCurrentCharFormat(fmt)

    def change_font_size(self, size):
        """Altera o tamanho da fonte do texto selecionado."""
        cursor = self.note_edit.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontPointSize(int(size))
        if cursor.hasSelection():
            cursor.mergeCharFormat(fmt)
        else:
            self.note_edit.setCurrentCharFormat(fmt)

    def toggle_bold(self):
        """Alterna o negrito no texto selecionado."""
        cursor = self.note_edit.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Bold if cursor.charFormat().fontWeight() != QFont.Bold else QFont.Normal)
        cursor.mergeCharFormat(fmt)

    def toggle_italic(self):
        """Alterna o itálico no texto selecionado."""
        cursor = self.note_edit.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontItalic(not cursor.charFormat().fontItalic())
        cursor.mergeCharFormat(fmt)

    def toggle_underline(self):
        """Alterna o sublinhado no texto selecionado."""
        cursor = self.note_edit.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not cursor.charFormat().fontUnderline())
        cursor.mergeCharFormat(fmt)

    def strip_html(self, html):
        """Remove tags HTML e retorna o texto puro."""
        doc = QTextDocument()
        doc.setHtml(html)
        return doc.toPlainText()

    def find_text(self):
        """Procura a string no conteúdo da nota, deslocando o cursor para a ocorrência encontrada.
        Se não encontrar, move o cursor para o início e tenta novamente; se ainda assim não encontrar,
        informa o usuário."""
        search_str = self.find_edit.text()  # Usando o QLineEdit criado para busca
        if not search_str:
            return

        # Tenta encontrar a ocorrência a partir da posição atual do cursor
        found = self.note_edit.find(search_str)
        if not found:
            # Move o cursor para o início do documento e tenta novamente
            self.note_edit.moveCursor(QTextCursor.Start)
            found = self.note_edit.find(search_str)
            if not found:
                QMessageBox.information(self, "Buscar", "Nenhuma ocorrência encontrada.")




if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    # Aqui você pode testar a interface criando uma janela de NoteDialog
    window = NoteDialog(mode="edit", note_date="2023-08-28")
    window.show()
    sys.exit(app.exec_())
