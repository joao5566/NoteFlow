#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLineEdit, QPushButton, QHBoxLayout, QLabel, QHeaderView, QMessageBox,QComboBox
from utils import strip_html_tags

class FlashcardsTableWidget(QWidget):
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        self.db_connection = db_connection
        self.flashcards = []          # Lista completa de flashcards
        self.filtered_flashcards = [] # Lista filtrada
        self.current_page = 0
        self.cards_per_page = 10
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        # Área superior: busca e botões de atualização/exclusão
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Buscar:", self))
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Buscar flashcards...")
        self.search_input.textChanged.connect(self.filter_flashcards)
        top_layout.addWidget(self.search_input)
        top_buttons_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Atualizar Tabela", self)
        self.refresh_button.clicked.connect(self.refresh_flashcards)
        top_buttons_layout.addWidget(self.refresh_button)
        self.delete_button = QPushButton("Excluir Selecionados", self)
        self.delete_button.clicked.connect(self.delete_selected_cards)
        top_buttons_layout.addWidget(self.delete_button)
        top_layout.addLayout(top_buttons_layout)
        main_layout.addLayout(top_layout)
        # Tabela de flashcards
        self.cards_table = QTableWidget(self)
        self.cards_table.setColumnCount(5)
        self.cards_table.setHorizontalHeaderLabels(["ID", "Baralho", "Pergunta", "Próx. Revisão", "Ações"])
        self.cards_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cards_table.setWordWrap(True)
        main_layout.addWidget(self.cards_table)
        self.cards_table.setColumnHidden(0, True)
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
        # Seletor de flashcards por página
        per_page_layout = QHBoxLayout()
        per_page_layout.addWidget(QLabel("Cards por página:", self))
        self.cards_per_page_selector = QComboBox(self)
        self.cards_per_page_selector.addItems(["10", "25", "50", "100"])
        self.cards_per_page_selector.setCurrentText(str(self.cards_per_page))
        self.cards_per_page_selector.currentIndexChanged.connect(self.change_cards_per_page)
        per_page_layout.addWidget(self.cards_per_page_selector)
        main_layout.addLayout(per_page_layout)
        self.update_cards_table()

    def load_flashcards(self):
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT cards.id, decks.name AS deck_name, cards.question, cards.due_date
            FROM cards
            JOIN decks ON cards.deck_id = decks.id
            ORDER BY decks.name, cards.due_date
        """)
        rows = cursor.fetchall()
        self.flashcards = []
        for row in rows:
            self.flashcards.append({
                "id": row["id"],
                "deck_name": row["deck_name"],
                "question": row["question"],
                "due_date": row["due_date"]
            })
        self.filtered_flashcards = list(self.flashcards)
        self.current_page = 0
        self.update_cards_table()

    def filter_flashcards(self):
        query = self.search_input.text().lower()
        if query:
            self.filtered_flashcards = [
                card for card in self.flashcards
                if query in strip_html_tags(card["question"]).lower()
                or query in card["deck_name"].lower()
                or (card["due_date"] and query in card["due_date"].lower())
            ]
        else:
            self.filtered_flashcards = list(self.flashcards)
        self.current_page = 0
        self.update_cards_table()

    def update_cards_table(self):
        self.cards_table.setRowCount(0)
        start_index = self.current_page * self.cards_per_page
        end_index = start_index + self.cards_per_page
        cards_to_display = self.filtered_flashcards[start_index:end_index]
        for card in cards_to_display:
            row = self.cards_table.rowCount()
            self.cards_table.insertRow(row)
            self.cards_table.setItem(row, 0, QTableWidgetItem(str(card["id"])))
            self.cards_table.setItem(row, 1, QTableWidgetItem(card["deck_name"]))
            clean_text = strip_html_tags(card.get("question", "")).strip()
            if not clean_text:
                clean_text = "-"
            elif len(clean_text) > 50:
                clean_text = clean_text[:50] + "..."
            self.cards_table.setItem(row, 2, QTableWidgetItem(clean_text))
            self.cards_table.setItem(row, 3, QTableWidgetItem(card["due_date"] if card["due_date"] else "Sem data"))
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            edit_button = QPushButton("Editar")
            delete_button = QPushButton("Excluir")
            edit_button.clicked.connect(lambda checked, cid=card["id"]: self.edit_card(cid))
            delete_button.clicked.connect(lambda checked, cid=card["id"]: self.delete_card(cid))
            action_layout.addWidget(edit_button)
            action_layout.addWidget(delete_button)
            self.cards_table.setCellWidget(row, 4, action_widget)
        self.update_pagination_controls()

    def update_pagination_controls(self):
        total_pages = max(1, (len(self.filtered_flashcards) + self.cards_per_page - 1) // self.cards_per_page)
        self.page_label.setText(f"Página {self.current_page + 1} de {total_pages}")
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < total_pages - 1)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_cards_table()

    def next_page(self):
        if (self.current_page + 1) * self.cards_per_page < len(self.filtered_flashcards):
            self.current_page += 1
            self.update_cards_table()

    def change_cards_per_page(self):
        self.cards_per_page = int(self.cards_per_page_selector.currentText())
        self.current_page = 0
        self.update_cards_table()

    def refresh_flashcards(self):
        self.load_flashcards()

    def delete_selected_cards(self):
        selected_rows = set(index.row() for index in self.cards_table.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "Nenhum selecionado", "Selecione ao menos um flashcard para excluir.")
            return
        reply = QMessageBox.question(
            self, "Confirmação", "Tem certeza que deseja excluir os flashcards selecionados?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return
        selected_ids = [int(self.cards_table.item(row, 0).text()) for row in selected_rows]
        cursor = self.db_connection.cursor()
        cursor.executemany("DELETE FROM cards WHERE id = ?", [(cid,) for cid in selected_ids])
        self.db_connection.commit()
        QMessageBox.information(self, "Excluídos", "Flashcards excluídos com sucesso.")
        self.refresh_flashcards()

    def edit_card(self, card_id):
        from dialogs import EditCardDialog  # Import dinâmico para evitar dependência circular
        dialog = EditCardDialog(self.db_connection, card_id, parent=self)
        if dialog.exec_():
            self.refresh_flashcards()

    def delete_card(self, card_id):
        reply = QMessageBox.question(self, "Excluir Flash Card",
                                      "Tem certeza que deseja excluir este flashcard?",
                                      QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            cursor = self.db_connection.cursor()
            cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))
            self.db_connection.commit()
            self.refresh_flashcards()
