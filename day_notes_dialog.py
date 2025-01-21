# day_notes_dialog.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QLabel, QHBoxLayout,
    QListWidget, QListWidgetItem, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextDocument
from note_module import NoteDialog  # Certifique-se de que NoteDialog está disponível

class DayNotesDialog(QDialog):
    """Diálogo para visualizar e gerenciar múltiplas notas de um dia."""

    def __init__(self, parent, note_date, notes):
        super().__init__(parent)
        self.setWindowTitle(f"Notas para {note_date}")
        self.note_date = note_date
        self.notes = notes.copy()  # Lista de dicionários de notas

        self.layout = QVBoxLayout(self)

        # Lista de notas
        self.notes_list = QListWidget(self)
        self.populate_notes()
        self.layout.addWidget(self.notes_list)

        # Botões de ação
        self.buttons_layout = QHBoxLayout()

        self.add_button = QPushButton("Adicionar Nota", self)
        self.add_button.clicked.connect(self.add_note)
        self.buttons_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Editar Nota", self)
        self.edit_button.clicked.connect(self.edit_note)
        self.buttons_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Deletar Nota", self)
        self.delete_button.clicked.connect(self.delete_note)
        self.buttons_layout.addWidget(self.delete_button)

        self.close_button = QPushButton("Fechar", self)
        self.close_button.clicked.connect(self.accept)  # Conecta ao accept
        self.buttons_layout.addWidget(self.close_button)

        self.layout.addLayout(self.buttons_layout)

    def populate_notes(self):
        """Popula a lista com as notas existentes."""
        self.notes_list.clear()
        for idx, note in enumerate(self.notes, start=1):
            display_text = f"{idx}. {self.strip_html(note['text'])[:50]}..."
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, note)
            self.notes_list.addItem(item)

    def add_note(self):
        """Abre o diálogo para adicionar uma nova nota."""
        dialog = NoteDialog(self, mode="edit", note_date=self.note_date)
        if dialog.exec_() == QDialog.Accepted:
            new_note = dialog.get_note_data()
            self.notes.append(new_note)
            self.populate_notes()

    def edit_note(self):
        """Abre o diálogo para editar a nota selecionada."""
        selected_item = self.notes_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Seleção Inválida", "Por favor, selecione uma nota para editar.")
            return
        note = selected_item.data(Qt.UserRole)
        dialog = NoteDialog(self, mode="edit", note_date=self.note_date)
        dialog.set_note_data(note)
        if dialog.exec_() == QDialog.Accepted:
            updated_note = dialog.get_note_data()
            index = self.notes.index(note)
            self.notes[index] = updated_note
            self.populate_notes()

    def delete_note(self):
        """Deleta a nota selecionada."""
        selected_item = self.notes_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Seleção Inválida", "Por favor, selecione uma nota para deletar.")
            return
        note = selected_item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "Confirmação", "Tem certeza de que deseja deletar esta nota?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.notes.remove(note)
            self.populate_notes()

    def get_notes(self):
        """Retorna a lista atualizada de notas."""
        return self.notes

    def strip_html(self, html):
        """Remove tags HTML e retorna o texto puro."""
        doc = QTextDocument()
        doc.setHtml(html)
        return doc.toPlainText()

    def closeEvent(self, event):
        """
        Sobrescreve o método closeEvent para tratar o fechamento via botão "X" como uma aceitação.

        Isso garante que as notas sejam salvas mesmo se o usuário fechar o diálogo sem usar o botão "Fechar".
        """
        self.accept()  # Trata o fechamento como aceitação
        event.accept()  # Confirma o evento de fechamento

class DateRangeDialog(QDialog):
    """Diálogo para selecionar um intervalo de datas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecionar Intervalo de Datas")
        self.layout = QVBoxLayout(self)

        # Widget de seleção de data inicial
        self.start_date_edit = QDateEdit(self)
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())
        self.layout.addWidget(QLabel("Data Inicial:", self))
        self.layout.addWidget(self.start_date_edit)

        # Widget de seleção de data final
        self.end_date_edit = QDateEdit(self)
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.layout.addWidget(QLabel("Data Final:", self))
        self.layout.addWidget(self.end_date_edit)

        # Botões de ação
        buttons_layout = QHBoxLayout()
        self.export_button = QPushButton("Exportar", self)
        self.export_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.export_button)

        self.cancel_button = QPushButton("Cancelar", self)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        self.layout.addLayout(buttons_layout)

    def get_dates(self):
        """Retorna as datas selecionadas."""
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        return start_date, end_date

class EditNoteDialog(QDialog):
    """Diálogo para adicionar ou editar uma nota."""

    def __init__(self, date="", text="", categories=None, tags=None, parent=None):
        """
        Inicializa o EditNoteDialog.

        Args:
            date (str, optional): Data da nota no formato 'yyyy-MM-dd'.
            text (str, optional): Texto da nota.
            categories (list, optional): Lista de categorias.
            tags (list, optional): Lista de tags.
            parent (QWidget, optional): Widget pai.
        """
        super().__init__(parent)
        self.setWindowTitle("Adicionar/Editar Nota")
        self.layout = QFormLayout(self)

        # Entrada para data
        self.date_edit = QDateEdit(self)
        self.date_edit.setCalendarPopup(True)
        if date:
            self.date_edit.setDate(QDate.fromString(date, "yyyy-MM-dd"))
        else:
            self.date_edit.setDate(QDate.currentDate())
        self.layout.addRow("Data:", self.date_edit)

        # Entrada para texto da nota
        self.text_input = QLineEdit(self)
        self.text_input.setText(text)
        self.layout.addRow("Texto:", self.text_input)

        # Entrada para categorias
        self.categories_input = QLineEdit(self)
        self.categories_input.setText(", ".join(categories) if categories else "")
        self.layout.addRow("Categorias (separadas por vírgula):", self.categories_input)

        # Entrada para tags
        self.tags_input = QLineEdit(self)
        self.tags_input.setText(", ".join(tags) if tags else "")
        self.layout.addRow("Tags (separadas por vírgula):", self.tags_input)

        # Botões de ação
        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Salvar", self)
        self.save_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancelar", self)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        self.layout.addRow(buttons_layout)

    def get_data(self):
        """Retorna os dados inseridos pelo usuário."""
        date = self.date_edit.date().toString("yyyy-MM-dd")
        text = self.text_input.text().strip()
        categories = [cat.strip() for cat in self.categories_input.text().split(",")] if self.categories_input.text() else []
        tags = [tag.strip() for tag in self.tags_input.text().split(",")] if self.tags_input.text() else []
        return date, text, categories, tags

    def set_note_data(self, note):
        """Define os dados da nota para edição."""
        self.date_edit.setDate(QDate.fromString(note['date'], "yyyy-MM-dd"))
        self.text_input.setText(note['text'])
        self.categories_input.setText(", ".join(note['categories']))
        self.tags_input.setText(", ".join(note['tags']))

