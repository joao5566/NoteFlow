# notes_table_module.py

import sys
import sqlite3
import re
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLineEdit, QPushButton,
    QHBoxLayout, QLabel, QHeaderView, QMessageBox, QComboBox, QDialog
)
from PyQt5.QtCore import Qt
from html.parser import HTMLParser

# Importa a classe NoteDialog para edição de notas
from note_module import NoteDialog

class NotesTableWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.notes = []  # Lista de notas carregadas como dicionários
        self.filtered_notes = [] 
        self.current_page = 0
        self.notes_per_page = 10

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Área superior com busca e botões
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Buscar:", self))
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Buscar notas...")
        self.search_input.textChanged.connect(self.filter_notes)
        top_layout.addWidget(self.search_input)

        # Botões para atualizar, editar e excluir
        top_buttons_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Atualizar Tabela", self)
        self.refresh_button.clicked.connect(self.refresh_notes)
        top_buttons_layout.addWidget(self.refresh_button)

        self.edit_button = QPushButton("Editar Nota", self)
        self.edit_button.clicked.connect(self.edit_selected_note)
        top_buttons_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Excluir Nota(s)", self)
        self.delete_button.clicked.connect(self.delete_selected_notes)
        top_buttons_layout.addWidget(self.delete_button)
        top_layout.addLayout(top_buttons_layout)

        main_layout.addLayout(top_layout)

        # Tabela de notas
        self.notes_table = QTableWidget(self)
        self.notes_table.setColumnCount(5)  # Colunas: ID, Data, Texto, Categorias, Tags
        self.notes_table.setHorizontalHeaderLabels(["ID", "Data", "Texto", "Categorias", "Tags"])
        self.notes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.notes_table.setWordWrap(True)  # Permitir quebra de linha
        main_layout.addWidget(self.notes_table)

        # Ocultar a coluna "ID" para o usuário
        self.notes_table.setColumnHidden(0, True)

        # Controles de paginação
        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("Anterior", self)
        self.prev_button.clicked.connect(self.prev_page)
        pagination_layout.addWidget(self.prev_button)

        self.page_label = QLabel(self)
        pagination_layout.addWidget(self.page_label)

        self.next_button = QPushButton("Próxima", self)
        self.next_button.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.next_button)

        main_layout.addLayout(pagination_layout)

        # Seletor de quantidade de notas por página
        notes_per_page_layout = QHBoxLayout()
        notes_per_page_label = QLabel("Notas por página:", self)
        notes_per_page_layout.addWidget(notes_per_page_label)

        self.notes_per_page_selector = QComboBox(self)
        self.notes_per_page_selector.addItems(["10", "25", "50", "100"])
        self.notes_per_page_selector.setCurrentText(str(self.notes_per_page))
        self.notes_per_page_selector.currentIndexChanged.connect(self.change_notes_per_page)
        notes_per_page_layout.addWidget(self.notes_per_page_selector)

        main_layout.addLayout(notes_per_page_layout)

        self.update_notes_table()

    def load_notes(self, notes):
        """Carrega as notas para exibição na tabela.
        Espera que 'notes' seja um dicionário onde cada chave é uma data e o valor uma lista de notas."""
        self.notes = []
        for date_str, notes_list in notes.items():
            for note in notes_list:
                self.notes.append({
                    "id": note.get("id"),
                    "date": date_str,
                    "text": note.get("text", ""),
                    "raw_text": note.get("raw_text", note.get("text", "")),
                    "categories": note.get("categories", []),
                    "tags": note.get("tags", []),
                    "is_markdown": note.get("is_markdown", 0)
                })
        self.filtered_notes = list(self.notes)
        self.update_notes_table()

    def filter_notes(self):
        """Filtra as notas com base no texto de busca."""
        query = self.search_input.text().lower()
       
        if query:
            self.filtered_notes = [
                note for note in self.notes
                if query in (self.strip_html_tags(note["text"]) if note.get("is_markdown", 0) == 0 else note["text"]).lower()
                or query in note["date"].lower()
                or query in ", ".join(note.get("categories", [])).lower()
                or query in ", ".join(note.get("tags", [])).lower()
            ]
        else:
            self.filtered_notes = list(self.notes)

        self.current_page = 0
        self.update_notes_table()
        
    
    class HTMLTextStripper(HTMLParser):
        """Classe para remover tags HTML do texto."""
        def __init__(self):
            super().__init__()
            self.reset()
            self.fed = []

        def handle_data(self, d):
            self.fed.append(d)

        def get_data(self):
            return ''.join(self.fed)

    def strip_html_tags(self, html):
        """Remove tags HTML do texto."""
        html = re.sub(r'<style.*?>.*?</style>', '', html, flags=re.DOTALL)
        stripper = self.HTMLTextStripper()
        stripper.feed(html)
        return stripper.get_data()

    def update_notes_table(self):
        """Atualiza a tabela de notas com base na página atual."""
        self.notes_table.setRowCount(0)
        start_index = self.current_page * self.notes_per_page
        end_index = start_index + self.notes_per_page
        notes_to_display = self.filtered_notes[start_index:end_index]

        for note in notes_to_display:
            row = self.notes_table.rowCount()
            self.notes_table.insertRow(row)
            # Coluna ID
            self.notes_table.setItem(row, 0, QTableWidgetItem(str(note['id'])))
            # Coluna Data
            self.notes_table.setItem(row, 1, QTableWidgetItem(note['date']))
            # Coluna Texto: se for markdown, mostra o texto puro (raw_text); caso contrário, remove as tags HTML
            if note.get("is_markdown", 0) == 1:
                display_text = note.get("raw_text", note.get("text", "")).strip()
            else:
                display_text = self.strip_html_tags(note.get("text", "")).strip()
            self.notes_table.setItem(row, 2, QTableWidgetItem(display_text))
            # Coluna Categorias
            self.notes_table.setItem(row, 3, QTableWidgetItem(", ".join(note.get("categories", []))))
            # Coluna Tags
            self.notes_table.setItem(row, 4, QTableWidgetItem(", ".join(note.get("tags", []))))
        self.update_pagination_controls()

    def update_pagination_controls(self):
        """Atualiza os controles de paginação."""
        total_pages = max(1, (len(self.filtered_notes) + self.notes_per_page - 1) // self.notes_per_page)
        self.page_label.setText(f"Página {self.current_page + 1} de {total_pages}")
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < total_pages - 1)

    def prev_page(self):
        """Vai para a página anterior."""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_notes_table()

    def next_page(self):
        """Vai para a próxima página."""
        if (self.current_page + 1) * self.notes_per_page < len(self.filtered_notes):
            self.current_page += 1
            self.update_notes_table()

    def change_notes_per_page(self):
        """Altera a quantidade de notas exibidas por página."""
        self.notes_per_page = int(self.notes_per_page_selector.currentText())
        self.current_page = 0
        self.update_notes_table()

    def refresh_notes(self):
        """Recarrega as notas do banco de dados e atualiza a tabela."""
        with sqlite3.connect("data.db") as conn:
            cursor = conn.cursor()
            # Agora selecionamos também raw_text
            cursor.execute("SELECT id, date, text, raw_text, categories, tags, is_markdown FROM notes")
            rows = cursor.fetchall()

        self.notes = []
        for row in rows:
            note_id, date, text, raw_text, categories, tags, is_markdown = row
            self.notes.append({
                "id": note_id,
                "date": date,
                "text": text,
                "raw_text": raw_text if raw_text and raw_text.strip() != "" else text,
                "categories": categories.split(", ") if categories else [],
                "tags": tags.split(", ") if tags else [],
                "is_markdown": is_markdown
            })
        self.filter_notes()

    def delete_selected_notes(self):
        """Exclui as notas selecionadas na tabela e remove do banco de dados."""
        selected_rows = set(index.row() for index in self.notes_table.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "Nenhuma nota selecionada", "Por favor, selecione ao menos uma nota para excluir.")
            return

        reply = QMessageBox.question(
            self, "Confirmação", "Tem certeza de que deseja excluir as notas selecionadas?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        selected_ids = [int(self.notes_table.item(row, 0).text()) for row in selected_rows]
        with sqlite3.connect("data.db") as conn:
            cursor = conn.cursor()
            cursor.executemany("DELETE FROM notes WHERE id = ?", [(note_id,) for note_id in selected_ids])
            conn.commit()

        QMessageBox.information(self, "Notas excluídas", "As notas selecionadas foram excluídas com sucesso.")
        self.refresh_notes()

    def edit_selected_note(self):
        """Abre o diálogo para editar a nota selecionada."""
        selected_rows = set(index.row() for index in self.notes_table.selectedIndexes())
        if len(selected_rows) != 1:
            QMessageBox.warning(self, "Seleção inválida", "Por favor, selecione exatamente uma nota para editar.")
            return

        row = selected_rows.pop()
        note_id = int(self.notes_table.item(row, 0).text())
        # Procura a nota na lista local
        note_to_edit = next((note for note in self.notes if note["id"] == note_id), None)
        if note_to_edit is None:
            QMessageBox.warning(self, "Erro", "Nota não encontrada.")
            return

        # Abre o diálogo de edição com a data da nota
        dialog = NoteDialog(self, mode="edit", note_date=note_to_edit["date"])
        dialog.set_note_data(note_to_edit)
        if dialog.exec_() == QDialog.Accepted:
            updated_data = dialog.get_note_data()
            # Preserva o ID, a data e a flag is_markdown
            updated_data["id"] = note_to_edit["id"]
            updated_data["date"] = note_to_edit["date"]
            updated_data["is_markdown"] = note_to_edit.get("is_markdown", 0)
            with sqlite3.connect("data.db") as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE notes SET text = ?, raw_text = ?, categories = ?, tags = ?, is_markdown = ? WHERE id = ?",
                    (updated_data["text"], updated_data.get("raw_text", updated_data["text"]),
                     ", ".join(updated_data.get("categories", [])),
                     ", ".join(updated_data.get("tags", [])),
                     int(updated_data.get("is_markdown", 0)),
                     updated_data["id"])
                )
                conn.commit()
            QMessageBox.information(self, "Sucesso", "Nota atualizada com sucesso.")
            self.refresh_notes()

    def find_text(self):
        """Método básico para demonstração da busca."""
        search_str = self.search_input.text()
        if not search_str:
            return
        if not any(search_str.lower() in (note["text"].lower() if note.get("is_markdown", 0)==1 
                                          else self.strip_html_tags(note["text"]).lower())
                   for note in self.notes):
            QMessageBox.information(self, "Buscar", "Nenhuma ocorrência encontrada.")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = NotesTableWidget()
    window.show()
    sys.exit(app.exec_())
