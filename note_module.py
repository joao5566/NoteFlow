#note_module.py

import os
import sqlite3
import base64
import markdown
from fpdf import FPDF
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QLabel, QHBoxLayout,
    QLineEdit, QColorDialog, QFontDialog, QCheckBox, QComboBox,
    QFileDialog, QMessageBox, QTextEdit, QCompleter, QDialogButtonBox,
    QSpinBox, QInputDialog, QSplitter, QListView, QWidget
)
from PyQt5.QtCore import QTimer, Qt, QPoint
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QFont, QKeyEvent, QTextDocument
from PyQt5.QtWebEngineWidgets import QWebEngineView

# --- Classe para permitir redimensionar o popup de autocomplete ---
class ResizableListView(QListView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(50)
        self.setMaximumHeight(300)
        self.resizing = False
        self.drag_start_pos = None
        self.original_height = None
        self.setCursor(Qt.ArrowCursor)

    def mousePressEvent(self, event):
        if event.pos().y() > self.height() - 10:
            self.resizing = True
            self.drag_start_pos = event.globalPos()
            self.original_height = self.height()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.resizing:
            diff = event.globalPos().y() - self.drag_start_pos.y()
            new_height = self.original_height + diff
            new_height = max(new_height, self.minimumHeight())
            new_height = min(new_height, self.maximumHeight())
            self.setFixedHeight(new_height)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.resizing:
            self.resizing = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)

# --- Editor customizado para notas (insere espaços com Tab) ---
class CustomTextEdit(QTextEdit):
    def __init__(self, parent=None, tab_spaces=4):
        super().__init__(parent)
        self.tab_spaces = tab_spaces

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Tab:
            self.insertPlainText(" " * self.tab_spaces)
        else:
            super().keyPressEvent(event)

# --- Editor para HTML com autocomplete ---
class HTMLCompleterTextEdit(QTextEdit):
    def __init__(self, parent=None, tab_spaces=4):
        super().__init__(parent)
        self.tab_spaces = tab_spaces
        self.suggestions = [
            "<html>", "</html>",
            "<head>", "</head>",
            "<body>", "</body>",
            "<div>", "</div>",
            "<p>", "</p>",
            "<span>", "</span>",
            "<h1>", "</h1>",
            "<h2>", "</h2>",
            "<ul>", "</ul>",
            "<li>", "</li>",
            "<a href=''>", "</a>",
            "<img src=''>",
            "<style>", "</style>",
            ".teste",
            "text-align: left;", 
            "text-align: right;", 
            "text-align: center;", 
            "text-align: justify;",
            "color: #000000;", 
            "color: red;", 
            "background-color: #ffffff;", 
            "background-color: #f0f0f0;",
            "font-size: 16px;", 
            "font-family: Arial, sans-serif;",
            "margin: 0;", 
            "padding: 0;"
        ]
        self.completer = QCompleter(self.suggestions, self)
        self.completer.setPopup(ResizableListView(self))
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.activated.connect(self.insert_completion)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Tab:
            self.insertPlainText(" " * self.tab_spaces)
            return
        if (event.key() in (Qt.Key_Return, Qt.Key_Enter)) and self.completer.popup().isVisible():
            event.ignore()
            self.insert_completion(self.completer.currentCompletion())
            return
        super().keyPressEvent(event)
        self.handle_completion()

    

    def textUnderCursor(self):
        cursor = self.textCursor()
        block_text = cursor.block().text()
        pos = cursor.positionInBlock()
        text_up_to_cursor = block_text[:pos]
        words = text_up_to_cursor.split()
        print("text_up_to_cursor:", repr(text_up_to_cursor))
        print("words:", words)
        return words[-1] if words else ""


    def handle_completion(self):
        prefix = self.textUnderCursor()
        if prefix:
            self.completer.setCompletionPrefix(prefix)
            if self.completer.completionCount() > 0:
                cr = self.cursorRect()
                cr.setWidth(self.completer.popup().sizeHintForColumn(0) +
                            self.completer.popup().verticalScrollBar().sizeHint().width())
                self.completer.complete(cr)
        else:
            self.completer.popup().hide()

    def insert_completion(self, completion):
        cursor = self.textCursor()
        prefix = self.completer.completionPrefix()
        extra = len(completion) - len(prefix)
        cursor.insertText(completion[-extra:])
        self.setTextCursor(cursor)

# --- Editor para Markdown com autocomplete ---
class MarkdownCompleterTextEdit(CustomTextEdit):
    def __init__(self, parent=None, tab_spaces=4):
        super().__init__(parent, tab_spaces)
        self.suggestions = [
            "# ", "## ", "### ", "#### ", "##### ", "###### ",
            "- ", "* ", "+ ", "> ", "```", "```",
            "**", "__", "*", "_", "~~", "<div></div>"
        ]
        self.completer = QCompleter(self.suggestions, self)
        self.completer.setPopup(ResizableListView(self))
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.activated.connect(self.insert_completion)

    def keyPressEvent(self, event: QKeyEvent):
        if (event.key() in (Qt.Key_Tab, Qt.Key_Return, Qt.Key_Enter)) and self.completer.popup().isVisible():
            event.ignore()
            self.insert_completion(self.completer.currentCompletion())
            return
        if event.key() == Qt.Key_Tab:
            self.insertPlainText(" " * self.tab_spaces)
            return
        super().keyPressEvent(event)
        self.handle_completion()

    def textUnderCursor(self):
        cursor = self.textCursor()
        block_text = cursor.block().text()
        pos = cursor.positionInBlock()
        text_up_to_cursor = block_text[:pos]
        words = text_up_to_cursor.split()
        return words[-1] if words else ""


    def handle_completion(self):
        prefix = self.textUnderCursor()
        if prefix:
            self.completer.setCompletionPrefix(prefix)
            if self.completer.completionCount() > 0:
                cr = self.cursorRect()
                cr.setWidth(self.completer.popup().sizeHintForColumn(0) +
                            self.completer.popup().verticalScrollBar().sizeHint().width())
                self.completer.complete(cr)
        else:
            self.completer.popup().hide()

    def insert_completion(self, completion):
        cursor = self.textCursor()
        prefix = self.completer.completionPrefix()
        extra = len(completion) - len(prefix)
        cursor.insertText(completion[-extra:])
        self.setTextCursor(cursor)

# --- Container com QSplitter para permitir redimensionar "arrastando" ---
class DraggableEditorContainer(QSplitter):
    def __init__(self, widget, parent=None):
        super().__init__(Qt.Vertical, parent)
        self.widget = widget
        self.spacer = QWidget(self)
        self.spacer.setMinimumHeight(20)
        self.addWidget(self.widget)
        self.addWidget(self.spacer)
        self.setSizes([300, 20])

# --- Janela externa para preview ---
class ExternalPreviewWindow(QDialog):
    def __init__(self, content="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preview Externo")
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.resize(800, 600)
        self.layout = QVBoxLayout(self)
        self.preview = QWebEngineView(self)
        self.layout.addWidget(self.preview)
        self.setContent(content)

    def setContent(self, html):
        self.preview.setHtml(html)

# --- Diálogo para editar notas ---
class NoteDialog(QDialog):
    """Diálogo para criar ou editar uma nota com suporte a Markdown e HTML."""
    def __init__(self, parent=None, mode="view", note_date=None):
        super().__init__(parent)
        self.setWindowTitle("Nota")
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        self.layout = QVBoxLayout(self)
        self.mode = mode
        self.note_date = note_date
        self.is_markdown_mode = False
        self.current_text_color = "#000000"
        self.preview_font_size = 12
        self.header_css = ""
        self.markdown_container = None  # Container que reúne editor e preview (modo Markdown)
        self.draggable_container = None  # Container arrastável (em ambos os modos)
        self.external_preview_window = None  # Janela externa para o preview
        self.image_placeholders = {}  # Mapeia identificadores para data URIs
        self.image_counter = 0
        self.note_edit = CustomTextEdit(self)
        self.note_edit.setReadOnly(mode == "view")

        if mode == "edit":
            self.draggable_container = DraggableEditorContainer(self.note_edit)
            self.layout.addWidget(self.draggable_container)
        else:
            self.layout.addWidget(self.note_edit)

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

            self.markdown_checkbox = QCheckBox("Usar Markdown", self)
            self.markdown_checkbox.stateChanged.connect(self.toggle_markdown_mode)
            self.layout.addWidget(self.markdown_checkbox)

            # Apenas duas opções: Lado a Lado e Vertical
            self.markdown_layout_combo = QComboBox(self)
            self.markdown_layout_combo.addItems(["Lado a Lado", "Vertical"])
            self.markdown_layout_combo.setCurrentText("Lado a Lado")
            self.markdown_layout_combo.currentTextChanged.connect(self.change_markdown_layout_mode)
            self.markdown_layout_combo.setVisible(False)
            self.layout.addWidget(self.markdown_layout_combo)

            self.popup_height_spin = QSpinBox(self)
            self.popup_height_spin.setMinimum(50)
            self.popup_height_spin.setMaximum(300)
            self.popup_height_spin.setValue(150)
            self.popup_height_spin.valueChanged.connect(self.update_popup_height)
            popup_height_layout = QHBoxLayout()
            popup_height_layout.addWidget(QLabel("Altura do Popup:"))
            popup_height_layout.addWidget(self.popup_height_spin)
            self.layout.addLayout(popup_height_layout)

            # Botão para abrir preview em janela externa
            self.external_preview_button = QPushButton("Abrir preview em janela externa", self)
            self.external_preview_button.clicked.connect(self.open_external_preview)
            self.layout.addWidget(self.external_preview_button)

        self.preview_browser = QWebEngineView(self)
        self.preview_browser.setVisible(False)
        self.layout.addWidget(self.preview_browser)

        if mode == "edit":
            self.format_buttons_layout = QHBoxLayout()
            self.layout.addLayout(self.format_buttons_layout)
            self.add_format_buttons()

        self.layout.addWidget(QLabel("Categorias (separadas por vírgula):"))
        self.category_input = QLineEdit(self)
        self.category_input.setReadOnly(mode == "view")
        self.layout.addWidget(self.category_input)
        self.layout.addWidget(QLabel("Tags (separadas por vírgula):"))
        self.tags_input = QLineEdit(self)
        self.tags_input.setReadOnly(mode == "view")
        self.layout.addWidget(self.tags_input)

        if mode == "edit":
            self.done_checkbox = QCheckBox("Marcar como Feito", self)
            self.done_checkbox.stateChanged.connect(self.toggle_done_tag)
            self.layout.addWidget(self.done_checkbox)

        self.action_buttons_layout = QHBoxLayout()
        self.layout.addLayout(self.action_buttons_layout)
        if mode == "edit":
            self.add_save_button()
        else:
            self.add_view_buttons()

        if mode == "edit":
            self.auto_save_timer = QTimer(self)
            self.auto_save_timer.timeout.connect(self.auto_save_note)
            self.auto_save_timer.start(60000)

    def update_popup_height(self, height):
        if hasattr(self.note_edit, 'completer'):
            self.note_edit.completer.popup().setMaximumHeight(height)

    def add_format_buttons(self):
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
        self.header_style_button = QPushButton("Regras Personalizadas", self)
        self.header_style_button.clicked.connect(self.configure_headers)
        self.format_buttons_layout.addWidget(self.header_style_button)

    def open_external_preview(self):
        """Abre uma janela externa com o preview da nota."""
        content = self.get_current_content()
        if self.external_preview_window is None or not self.external_preview_window.isVisible():
            self.external_preview_window = ExternalPreviewWindow(content, self)
            self.external_preview_window.show()
        else:
            self.external_preview_window.setContent(content)
            self.external_preview_window.raise_()

    def configure_headers(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Regras Personalizadas")
        d_layout = QVBoxLayout(dialog)
        d_layout.addWidget(QLabel("Insira as regras CSS/HTML para personalizar seus elementos:"))
        html_editor = HTMLCompleterTextEdit(dialog, tab_spaces=4)
        html_editor.setPlainText(self.header_css if self.header_css else "h1 { font-size: 36px; color: black; }")
        d_layout.addWidget(html_editor)
        tab_layout = QHBoxLayout()
        tab_layout.addWidget(QLabel("Espaços para Tab:"))
        tab_spin = QSpinBox(dialog)
        tab_spin.setMinimum(1)
        tab_spin.setMaximum(8)
        tab_spin.setValue(4)
        tab_layout.addWidget(tab_spin)
        d_layout.addLayout(tab_layout)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        d_layout.addWidget(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec_() == QDialog.Accepted:
            self.header_css = html_editor.toPlainText().strip()
            new_tab_spaces = tab_spin.value()
            html_editor.tab_spaces = new_tab_spaces
            if self.is_markdown_mode:
                self.update_markdown_preview()

    def insert_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Selecionar Imagem", 
            "", 
            "Imagens (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        if file_path:
            alt_text, ok = QInputDialog.getText(self, "Descrição da Imagem", "Digite a descrição da imagem:")
            if not ok or not alt_text.strip():
                alt_text = "imagem"

            ext = os.path.splitext(file_path)[1].lower()
            mime = "image/png"
            if ext in [".jpg", ".jpeg"]:
                mime = "image/jpeg"
            elif ext == ".gif":
                mime = "image/gif"
            elif ext == ".bmp":
                mime = "image/bmp"
            
            # Lê e codifica a imagem em base64
            with open(file_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            data_uri = f"data:{mime};base64,{encoded_string}"
            
            cursor = self.note_edit.textCursor()
            
            if self.is_markdown_mode:
                # Cria um placeholder único para a imagem
                self.image_counter += 1
                placeholder = f"IMAGE_PLACEHOLDER_{self.image_counter}"
                # Armazena o mapeamento entre o placeholder e o data URI completo
                self.image_placeholders[placeholder] = data_uri
                # Insere a sintaxe Markdown com o placeholder
                markdown_image = f"![{alt_text}]({placeholder})"
                cursor.insertText(markdown_image)
            else:
                # Modo HTML (permanece o mesmo, ou você pode aplicar outra lógica)
                width_str, ok = QInputDialog.getText(self, "Largura da Imagem", "Digite a largura (px) ou deixe em branco:")
                if ok and width_str.strip():
                    try:
                        width = int(width_str)
                        style_attr = f'style="width:{width}px;"'
                    except ValueError:
                        style_attr = ""
                else:
                    style_attr = ""
                image_html = f'<img src="{data_uri}" alt="{alt_text}" {style_attr} />'
                cursor.insertHtml(image_html)


    def add_save_button(self):
        self.save_button = QPushButton("Salvar", self)
        self.save_button.clicked.connect(self.handle_save)
        self.action_buttons_layout.addWidget(self.save_button)

    def add_view_buttons(self):
        self.edit_button = QPushButton("Editar", self)
        self.edit_button.clicked.connect(self.enable_edit_mode)
        self.action_buttons_layout.addWidget(self.edit_button)
        self.export_button = QPushButton("Exportar como PDF", self)
        self.export_button.clicked.connect(self.export_to_pdf)
        self.action_buttons_layout.addWidget(self.export_button)

    def handle_save(self):
        if self.validate_note_data():
            # Para evitar conflitos, interrompe o auto save antes de salvar manualmente.
            if hasattr(self, 'auto_save_timer'):
                self.auto_save_timer.stop()
            try:
                if self.is_markdown_mode:
                    raw_content = self.note_edit.toPlainText()
                    # Converte o Markdown para HTML para exibição posterior.
                    html_content = markdown.markdown(raw_content, extensions=['fenced_code', 'codehilite', 'nl2br'])
                else:
                    html_content = self.note_edit.toHtml()
                    raw_content = ""
                categories = ",".join(cat.strip() for cat in self.category_input.text().split(",") if cat.strip())
                tags = ",".join(tag.strip() for tag in self.tags_input.text().split(",") if tag.strip())
                with sqlite3.connect("data.db") as conn:
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
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao salvar a nota: {e}")
                return
            QMessageBox.information(self, "Sucesso", "Nota salva com sucesso.")
            self.accept()

    def validate_note_data(self):
        if not self.note_edit.toPlainText().strip():
            QMessageBox.warning(self, "Aviso", "A nota não pode estar vazia.")
            return False
        return True

    def export_to_pdf(self):
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
        tags = [tag.strip() for tag in self.tags_input.text().split(",") if tag.strip()]
        if state == Qt.Checked:
            if "feito" not in tags:
                tags.append("feito")
        else:
            if "feito" in tags:
                tags.remove("feito")
        self.tags_input.setText(",".join(tags))

    def auto_save_note(self):
        content = self.get_current_content()
        path = os.path.join(os.getcwd(), "auto_save_note.html")
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)
        print(f"Nota salva automaticamente em {path}")

    def get_current_content(self):
        raw_text = self.note_edit.toPlainText()
        if self.is_markdown_mode:
            # Substitui cada placeholder pelo data URI completo
            for placeholder, data_uri in self.image_placeholders.items():
                raw_text = raw_text.replace(placeholder, data_uri)
            # Converte o Markdown para HTML para exibição
            html_content = markdown.markdown(raw_text, extensions=['fenced_code', 'codehilite', 'nl2br'])
            css = f"""
                <style>
                    .preview {{
                        font-size: {self.preview_font_size}px;
                        color: {self.current_text_color};
                        white-space: normal;
                        margin: 0;
                        padding: 0;
                    }}
                    p, h1, h2, h3, h4, h5, h6 {{
                        margin: 0;
                        padding: 0;
                        line-height: 1.2;
                    }}
                    pre {{
                        background-color: #f0f0f0;
                        padding: 10px;
                        border-radius: 5px;
                        white-space: pre;
                        font-family: monospace;
                        margin: 0;
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
                        margin: 0;
                    }}
                    .codehilite .hll {{ background-color: #ffffcc; }}
                </style>
            """
            header_style = f"<style>{self.header_css}</style>" if self.header_css else ""
            return f"{header_style}{css}<div class='preview'>{html_content}</div>"
        else:
            return self.note_edit.toHtml()


    def get_note_data(self):
        tags = [tag.strip() for tag in self.tags_input.text().split(",") if tag.strip()]
        if self.is_markdown_mode:
            # Retorna o conteúdo _raw_ para que o editor possa reabrir em Markdown.
            note_text = self.note_edit.toPlainText()
            return {
                "text": note_text,
                "raw_text": note_text,
                "categories": [cat.strip() for cat in self.category_input.text().split(",") if cat.strip()],
                "tags": tags,
                "custom_css": self.header_css
            }
        else:
            note_text = self.get_current_content()
            return {
                "text": note_text,
                "categories": [cat.strip() for cat in self.category_input.text().split(",") if cat.strip()],
                "tags": tags,
                "custom_css": self.header_css
            }

    def set_note_data(self, data):
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
        self.header_css = data.get("custom_css", "")
        if self.mode == "edit":
            self.done_checkbox.setChecked("feito" in data.get("tags", []))
            self.note_id = data.get("id")
        if self.is_markdown_mode:
            self.update_markdown_preview()

    def enable_edit_mode(self):
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
        if state == Qt.Checked:
            self.is_markdown_mode = True
            self.markdown_layout_combo.setVisible(True)
            
            # Armazena o conteúdo atual para repassar ao novo widget.
            current_text = self.note_edit.toPlainText()
            
            if self.draggable_container:
                self.layout.removeWidget(self.draggable_container)
                self.draggable_container.setParent(None)
                self.draggable_container.deleteLater()
                self.draggable_container = None
            
            self.note_edit.setParent(None)
            self.note_edit.deleteLater()
            
            self.note_edit = MarkdownCompleterTextEdit(self, tab_spaces=4)
            self.note_edit.setPlainText(current_text)
            self.note_edit.setReadOnly(False)
            self.note_edit.textChanged.connect(self.update_markdown_preview)
            
            try:
                self.popup_height_spin.valueChanged.disconnect()
            except Exception:
                pass
            self.popup_height_spin.valueChanged.connect(
                lambda value: self.note_edit.completer.popup().setMaximumHeight(value)
            )
            self.note_edit.completer.popup().setMaximumHeight(self.popup_height_spin.value())
            
            self.preview_browser.setVisible(True)
            self.reconfigureMarkdownLayout()
            self.update_markdown_preview()
        else:
            self.is_markdown_mode = False
            self.markdown_layout_combo.setVisible(False)
            if self.markdown_container:
                if isinstance(self.markdown_container, QSplitter):
                    self.preview_browser.setParent(self)
                if self.draggable_container:
                    self.layout.removeWidget(self.draggable_container)
                    self.draggable_container.setParent(None)
                    self.draggable_container.deleteLater()
                    self.draggable_container = None
                self.markdown_container.setParent(None)
                self.markdown_container.deleteLater()
                self.markdown_container = None
                current_text = self.note_edit.toPlainText()
            else:
                current_text = self.note_edit.toPlainText()
            
            self.note_edit = CustomTextEdit(self, tab_spaces=4)
            self.note_edit.setPlainText(current_text)
            self.note_edit.setReadOnly(False)
            self.draggable_container = DraggableEditorContainer(self.note_edit)
            self.layout.insertWidget(0, self.draggable_container)
            self.preview_browser.setVisible(False)
            try:
                self.note_edit.textChanged.disconnect(self.update_markdown_preview)
            except Exception:
                pass

    def reconfigureMarkdownLayout(self):
        # Remove container antigo, se existir
        if self.markdown_container:
            if self.draggable_container:
                self.layout.removeWidget(self.draggable_container)
                self.draggable_container.deleteLater()
                self.draggable_container = None
            self.markdown_container.setParent(None)
            self.markdown_container.deleteLater()
            self.markdown_container = None

        layout_mode = self.markdown_layout_combo.currentText() if hasattr(self, "markdown_layout_combo") else "Lado a Lado"
        if layout_mode == "Lado a Lado":
            splitter = QSplitter(Qt.Horizontal)
            splitter.addWidget(self.note_edit)
            splitter.addWidget(self.preview_browser)
            splitter.setStretchFactor(0, 1)
            splitter.setStretchFactor(1, 1)
            self.markdown_container = splitter
        elif layout_mode == "Vertical":
            splitter = QSplitter(Qt.Vertical)
            splitter.addWidget(self.note_edit)
            splitter.addWidget(self.preview_browser)
            splitter.setStretchFactor(0, 1)
            splitter.setStretchFactor(1, 1)
            self.markdown_container = splitter

        self.draggable_container = DraggableEditorContainer(self.markdown_container)
        self.layout.insertWidget(0, self.draggable_container)

    def change_markdown_layout_mode(self, mode):
        if self.is_markdown_mode:
            self.reconfigureMarkdownLayout()

    def update_markdown_preview(self):
        html = self.get_current_content()
        self.preview_browser.setHtml(html)
        if self.external_preview_window and self.external_preview_window.isVisible():
            self.external_preview_window.setContent(html)

    def change_text_color(self):
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
        cursor = self.note_edit.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontPointSize(int(size))
        if cursor.hasSelection():
            cursor.mergeCharFormat(fmt)
        else:
            self.note_edit.setCurrentCharFormat(fmt)

    def toggle_bold(self):
        cursor = self.note_edit.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Bold if cursor.charFormat().fontWeight() != QFont.Bold else QFont.Normal)
        cursor.mergeCharFormat(fmt)

    def toggle_italic(self):
        cursor = self.note_edit.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontItalic(not cursor.charFormat().fontItalic())
        cursor.mergeCharFormat(fmt)

    def toggle_underline(self):
        cursor = self.note_edit.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not cursor.charFormat().fontUnderline())
        cursor.mergeCharFormat(fmt)

    def strip_html(self, html):
        doc = QTextDocument()
        doc.setHtml(html)
        return doc.toPlainText()

    def find_text(self):
        search_str = self.find_edit.text()
        if not search_str:
            return
        found = self.note_edit.find(search_str)
        if not found:
            self.note_edit.moveCursor(QTextCursor.Start)
            found = self.note_edit.find(search_str)
            if not found:
                QMessageBox.information(self, "Buscar", "Nenhuma ocorrência encontrada.")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    window = NoteDialog(mode="edit", note_date="2023-08-28")
    window.show()
    sys.exit(app.exec_())
