from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QLabel, QHBoxLayout,
    QListWidget, QListWidgetItem, QMessageBox, QDateEdit, QFormLayout, QLineEdit
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QTextDocument

from note_module import NoteDialog  # Certifique-se de que NoteDialog está disponível

class DayNotesDialog(QDialog):
    """Diálogo para visualizar e gerenciar múltiplas notas de um dia."""
    def __init__(self, parent, note_date, notes):
        super().__init__(parent)
        self.setWindowTitle(f"Notas para {note_date}")
        # Adiciona os botões de maximizar e minimizar
        self.setWindowFlags(self.windowFlags() |
                            Qt.WindowMaximizeButtonHint |
                            Qt.WindowMinimizeButtonHint)
        # Define o diálogo como não modal:
        self.setModal(False)

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
        self.close_button.clicked.connect(self.accept)  # Mantém um botão para fechar de forma controlada
        self.buttons_layout.addWidget(self.close_button)

        self.layout.addLayout(self.buttons_layout)

    def populate_notes(self):
        """Popula a lista com as notas existentes."""
        self.notes_list.clear()
        for idx, note in enumerate(self.notes, start=1):
            # Se a nota estiver em Markdown, utiliza raw_text; caso contrário, usa text.
            if note.get("is_markdown", 0) == 1:
                content = note.get("raw_text", "")
            else:
                content = note.get("text", "")
            display_text = f"{idx}. {self.strip_html(content)[:50]}..."
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, note)
            self.notes_list.addItem(item)

    def add_note(self):
        """Abre o diálogo para adicionar uma nova nota de forma não modal."""
        dialog = NoteDialog(self, mode="edit", note_date=self.note_date)
        dialog.setModal(False)
        # Conecta o sinal finished para capturar o resultado quando o diálogo for fechado
        dialog.finished.connect(lambda result, d=dialog: self.on_add_note_finished(result, d))
        dialog.show()

    def on_add_note_finished(self, result, dialog):
        """Tratamento do fechamento do diálogo de adição de nota."""
        if result == QDialog.Accepted:
            new_note = dialog.get_note_data()
            if dialog.is_markdown_mode:
                new_note["is_markdown"] = 1
                new_note["raw_text"] = new_note["text"]
            else:
                new_note["is_markdown"] = 0
            self.notes.append(new_note)
            self.populate_notes()

    def edit_note(self):
        """Abre o diálogo para editar a nota selecionada de forma não modal."""
        selected_item = self.notes_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Seleção Inválida", "Por favor, selecione uma nota para editar.")
            return

        note = selected_item.data(Qt.UserRole)
        if "is_markdown" not in note:
            note["is_markdown"] = 0

        dialog = NoteDialog(self, mode="edit", note_date=self.note_date)
        dialog.set_note_data(note)
        dialog.setModal(False)
        dialog.finished.connect(lambda result, d=dialog, n=note: self.on_edit_note_finished(result, d, n))
        dialog.show()

    def on_edit_note_finished(self, result, dialog, note):
        """Tratamento do fechamento do diálogo de edição de nota."""
        if result == QDialog.Accepted:
            updated_note = dialog.get_note_data()
            updated_note["id"] = note.get("id")
            updated_note["is_markdown"] = note.get("is_markdown", 0)
            if dialog.is_markdown_mode:
                updated_note["raw_text"] = updated_note["text"]
            for idx, n in enumerate(self.notes):
                if n.get("id") == note.get("id"):
                    self.notes[idx] = updated_note
                    break
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

    # O método closeEvent pode permanecer sem alteração, ou ser ajustado conforme a necessidade.
    # Por exemplo, se preferir que o fechamento via "X" não force automaticamente a aceitação,
    # basta não chamar self.accept() aqui.
