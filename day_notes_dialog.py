from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QLabel, QHBoxLayout,
    QListWidget, QListWidgetItem, QMessageBox, QDateEdit, QFormLayout, QLineEdit
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QTextDocument

from note_module import NoteDialog
from persistence_module import load_notes, save_notes  # Importa suas funções de persistência

class DayNotesDialog(QDialog):
    """Diálogo para visualizar e gerenciar múltiplas notas de um dia."""
    def __init__(self, parent, note_date, notes):
        super().__init__(parent)
        self.setWindowTitle(f"Notas para {note_date}")
        self.setWindowFlags(self.windowFlags() |
                            Qt.WindowMaximizeButtonHint |
                            Qt.WindowMinimizeButtonHint)
        self.setModal(False)

        self.note_date = note_date
        # Supondo que as notas recebidas já sejam para este dia (lista)
        self.notes = notes.copy()

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
        self.close_button.clicked.connect(self.accept)
        self.buttons_layout.addWidget(self.close_button)

        self.layout.addLayout(self.buttons_layout)

    def populate_notes(self):
        """Popula a lista com as notas existentes."""
        self.notes_list.clear()
        for idx, note in enumerate(self.notes, start=1):
            if int(note.get("is_markdown", 0)) == 1:
                content = note.get("raw_text", "")
            else:
                content = note.get("text", "")
            display_text = f"{idx}. {self.strip_html(content)[:50]}..."
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, note)
            self.notes_list.addItem(item)

    def add_note(self):
        """Pergunta ao usuário qual modo deseja utilizar e cria a nota com base na escolha."""
        reply = QMessageBox.question(
            self,
            "Modo de Criação",
            "Deseja criar a nota em Markdown?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            # Cria uma nota markdown padrão
            default_text = "# Nova Nota Markdown"
            new_note = {
                "text": default_text,
                "raw_text": default_text,
                "is_markdown": 1,
                "date": self.note_date,
                "categories": [],
                "tags": [],
                "custom_css": ""
            }
            # Adiciona a nota à lista local e salva no banco
            self.notes.append(new_note)
            self.populate_notes()
            self._save_changes()

            # Agora abre o diálogo de edição com essa nota já salva
            dialog = NoteDialog(self, mode="edit", note_date=self.note_date)
            dialog.set_note_data(new_note)
            dialog.setModal(False)
            dialog.finished.connect(lambda result, d=dialog, n=new_note: self.on_edit_note_finished(result, d, n))
            dialog.show()
        else:
            # Caso o usuário opte por não usar Markdown, abre o diálogo normalmente
            dialog = NoteDialog(self, mode="edit", note_date=self.note_date)
            dialog.setModal(False)
            dialog.finished.connect(lambda result, d=dialog: self.on_add_note_finished(result, d))
            dialog.show()

    def on_add_note_finished(self, result, dialog):
        """Tratamento do fechamento do diálogo de adição de nota (não Markdown)."""
        if result == QDialog.Accepted:
            new_note = dialog.get_note_data()
            new_note["is_markdown"] = 0  # Garante que a nota não é Markdown
            new_note["date"] = self.note_date
            self.notes.append(new_note)
            self.populate_notes()
            self._save_changes()

    def edit_note(self):
        """Abre o diálogo para editar a nota selecionada."""
        selected_item = self.notes_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Seleção Inválida", "Por favor, selecione uma nota para editar.")
            return

        note = selected_item.data(Qt.UserRole)
        # Recarrega a nota atualizada do banco (ou da estrutura persistida) com base no id
        updated_note = self._get_note_from_db(note.get("id"))
        if updated_note is None:
            # Se não encontrar, utiliza a nota atual
            updated_note = note

        dialog = NoteDialog(self, mode="edit", note_date=self.note_date)
        dialog.set_note_data(updated_note)
        dialog.setModal(False)
        dialog.finished.connect(lambda result, d=dialog, n=updated_note: self.on_edit_note_finished(result, d, n))
        dialog.show()

    def on_edit_note_finished(self, result, dialog, note):
        """Tratamento do fechamento do diálogo de edição de nota."""
        if result == QDialog.Accepted:
            updated_note = dialog.get_note_data()
            updated_note["id"] = note.get("id")
            # Se o diálogo estiver no modo markdown, atualiza o campo raw_text
            if dialog.is_markdown_mode:
                updated_note["raw_text"] = updated_note["text"]
            # Se o usuário mudar o modo de markdown, atualize a flag
            else:
                updated_note["is_markdown"] = 0

            updated_note["date"] = self.note_date
            for idx, n in enumerate(self.notes):
                if n.get("id") == note.get("id"):
                    self.notes[idx] = updated_note
                    break
            self.populate_notes()
            self._save_changes()

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
            self._save_changes()

    def _save_changes(self):
        """Atualiza o banco de dados com as notas deste dia."""
        # Carrega todas as notas persistidas (para não sobrescrever as de outros dias)
        all_notes = load_notes()  # all_notes é um dicionário: {data: [notas]}
        all_notes[self.note_date] = self.notes  # Atualiza ou adiciona as notas deste dia
        save_notes(all_notes)

    def _get_note_from_db(self, note_id):
        """Busca a nota com o id especificado a partir do banco (ou da estrutura persistida)."""
        all_notes = load_notes()
        notes_of_day = all_notes.get(self.note_date, [])
        for n in notes_of_day:
            if n.get("id") == note_id:
                return n
        return None

    def get_notes(self):
        """Retorna a lista atualizada de notas."""
        return self.notes

    def strip_html(self, html):
        """Remove tags HTML e retorna o texto puro."""
        doc = QTextDocument()
        doc.setHtml(html)
        return doc.toPlainText()
