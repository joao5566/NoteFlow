# note_module.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QLabel, QHBoxLayout,
    QLineEdit, QTextEdit, QColorDialog, QFontDialog, QCheckBox, QComboBox, QFileDialog, QMessageBox
)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QFont
import os
import sqlite3
from fpdf import FPDF

DB_PATH = "data.db"

class NoteDialog(QDialog):
    """Diálogo para criar ou editar uma nota."""

    def __init__(self, parent=None, mode="view", note_date=None):
        super().__init__(parent)
        self.setWindowTitle("Nota")
        self.layout = QVBoxLayout(self)
        self.mode = mode
        self.note_date = note_date

        # Campo de texto para a nota
        self.note_edit = QTextEdit(self)
        self.note_edit.setReadOnly(mode == "view")
        self.layout.addWidget(self.note_edit)

        # Layout para botões de formatação
        if mode == "edit":
            self.format_buttons_layout = QHBoxLayout()
            self.layout.addLayout(self.format_buttons_layout)
            self.add_format_buttons()

        # Campo para categorias da nota
        self.category_input = QLineEdit(self)
        self.category_input.setReadOnly(mode == "view")
        self.layout.addWidget(QLabel("Categorias (separadas por vírgula):"))
        self.layout.addWidget(self.category_input)

        # Campo para tags da nota
        self.tags_input = QLineEdit(self)
        self.tags_input.setReadOnly(mode == "view")
        self.layout.addWidget(QLabel("Tags (separadas por vírgula):"))
        self.layout.addWidget(self.tags_input)

        # Checkbox para marcar como feito
        if mode == "edit":
            self.done_checkbox = QCheckBox("Marcar como Feito", self)
            self.done_checkbox.stateChanged.connect(self.toggle_done_tag)
            self.layout.addWidget(self.done_checkbox)

        # Layout para botões de ação
        self.action_buttons_layout = QHBoxLayout()
        self.layout.addLayout(self.action_buttons_layout)

        if mode == "edit":
            self.add_save_button()
        else:
            self.add_view_buttons()

        # Configuração do auto-save
        if mode == "edit":
            self.auto_save_timer = QTimer(self)
            self.auto_save_timer.timeout.connect(self.auto_save_note)
            self.auto_save_timer.start(60000)

    def add_format_buttons(self):
        """Adiciona botões de formatação de texto."""
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

    def add_save_button(self):
        """Adiciona o botão de salvar."""
        self.save_button = QPushButton("Salvar", self)
        self.save_button.clicked.connect(self.handle_save)
        self.action_buttons_layout.addWidget(self.save_button)

    def add_view_buttons(self):
        """Adiciona botões de visualização."""
        self.edit_button = QPushButton("Editar", self)
        self.edit_button.clicked.connect(self.enable_edit_mode)
        self.action_buttons_layout.addWidget(self.edit_button)

        self.export_button = QPushButton("Exportar como PDF", self)
        self.export_button.clicked.connect(self.export_to_pdf)
        self.action_buttons_layout.addWidget(self.export_button)

    def handle_save(self):
        """Valida e salva a nota."""
        if self.validate_note_data():
            # Salva a nota no banco de dados
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                if self.mode == "edit" and hasattr(self, 'note_id'):
                    # Atualiza a nota existente
                    cursor.execute(
                        "UPDATE notes SET text = ?, categories = ?, tags = ? WHERE id = ?",
                        (self.note_edit.toHtml(), ",".join(self.category_input.text().split(",")), ",".join(self.tags_input.text().split(",")), self.note_id)
                    )
                else:
                    # Insere uma nova nota
                    cursor.execute(
                        "INSERT INTO notes (date, text, categories, tags) VALUES (?, ?, ?, ?)",
                        (self.note_date, self.note_edit.toHtml(), ",".join(self.category_input.text().split(",")), ",".join(self.tags_input.text().split(",")))
                    )
                conn.commit()
            QMessageBox.information(self, "Sucesso", "Nota salva com sucesso.")
            self.accept()

    def validate_note_data(self):
        """Valida os dados da nota."""
        if not self.note_edit.toPlainText().strip():
            QMessageBox.warning(self, "Aviso", "A nota não pode estar vazia.")
            return False
        return True

    def export_to_pdf(self):
        """Exporta a nota atual como um arquivo PDF."""
        path, _ = QFileDialog.getSaveFileName(self, "Exportar Nota como PDF", "nota.pdf", "Arquivos PDF (*.pdf)")
        if path:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, self.strip_html(self.note_edit.toHtml()))
            pdf.output(path)
            QMessageBox.information(self, "Exportação Concluída", f"Nota exportada como PDF em '{path}'")

    def toggle_done_tag(self, state):
        """Adiciona ou remove a tag 'feito' com base no estado do checkbox."""
        tags = [tag.strip() for tag in self.tags_input.text().split(",") if tag.strip()]
        if state == Qt.Checked:
            if "feito" not in tags:
                tags.append("feito")
        else:
            if "feito" in tags:
                tags.remove("feito")
        self.tags_input.setText(",".join(tags))

    def auto_save_note(self):
        """Salva automaticamente a nota em um arquivo HTML."""
        path = os.path.join(os.getcwd(), "auto_save_note.html")
        with open(path, "w") as file:
            file.write(self.note_edit.toHtml())
        print(f"Nota salva automaticamente em {path}")

    def get_note_data(self):
        """Retorna os dados da nota."""
        tags = [tag.strip() for tag in self.tags_input.text().split(",") if tag.strip()]
        return {
            "text": self.note_edit.toHtml(),
            "categories": [cat.strip() for cat in self.category_input.text().split(",") if cat.strip()],
            "tags": tags
        }

    def set_note_data(self, data):
        """Define os dados da nota no diálogo."""
        self.note_edit.setHtml(data.get("text", ""))
        self.category_input.setText(", ".join(data.get("categories", [])))
        self.tags_input.setText(", ".join(data.get("tags", [])))
        if self.mode == "edit":
            self.done_checkbox.setChecked("feito" in data.get("tags", []))
            # Armazena o ID da nota para atualização
            self.note_id = data.get("id")

    def enable_edit_mode(self):
        """Habilita o modo de edição da nota."""
        self.mode = "edit"
        self.note_edit.setReadOnly(False)
        self.category_input.setReadOnly(False)
        self.tags_input.setReadOnly(False)
        self.done_checkbox.setVisible(True)

        # Remove botões de visualização e adiciona botões de edição
        for i in reversed(range(self.action_buttons_layout.count())):
            widget = self.action_buttons_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.add_format_buttons()
        self.add_save_button()

    def change_text_color(self):
        """Altera a cor do texto selecionado."""
        color = QColorDialog.getColor()
        if color.isValid():
            cursor = self.note_edit.textCursor()
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            if cursor.hasSelection():
                cursor.mergeCharFormat(fmt)
            else:
                self.note_edit.setCurrentCharFormat(fmt)

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
        """Alterna o negrito do texto selecionado."""
        cursor = self.note_edit.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Bold if cursor.charFormat().fontWeight() != QFont.Bold else QFont.Normal)
        cursor.mergeCharFormat(fmt)

    def toggle_italic(self):
        """Alterna o itálico do texto selecionado."""
        cursor = self.note_edit.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontItalic(not cursor.charFormat().fontItalic())
        cursor.mergeCharFormat(fmt)

    def toggle_underline(self):
        """Alterna o sublinhado do texto selecionado."""
        cursor = self.note_edit.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not cursor.charFormat().fontUnderline())
        cursor.mergeCharFormat(fmt)

    def strip_html(self, html):
        """Remove tags HTML e retorna o texto puro."""
        from PyQt5.QtGui import QTextDocument
        doc = QTextDocument()
        doc.setHtml(html)
        return doc.toPlainText()

