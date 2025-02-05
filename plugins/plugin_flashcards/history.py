#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QPushButton, QComboBox, QHeaderView

class HistoryTableWidget(QWidget):
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        self.db_connection = db_connection
        self.history_records = []  # Lista completa dos registros
        self.current_page = 0
        self.records_per_page = 10
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Campo de busca (opcional, para filtrar)
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Buscar no Histórico:", self))
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Digite o ID ou data (YYYY-MM-DD)...")
        self.search_input.textChanged.connect(self.filter_history)
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)
        
        # Tabela do histórico
        self.table = QTableWidget(self)
        self.table.setColumnCount(6)
        headers = [
            ("ID do Card", "Identificador único do flash card."),
            ("Data da Revisão", "Data em que a revisão foi realizada."),
            ("Qualidade", "Nota atribuída à revisão (0 a 5)."),
            ("Fator EF", "Fator de Facilidade (quanto maior, mais fácil é lembrar)."),
            ("Repetições", "Número de vezes que o card foi revisado."),
            ("Intervalo (dias)", "Intervalo em dias até a próxima revisão.")
        ]
        self.table.setHorizontalHeaderLabels([h[0] for h in headers])
        header = self.table.horizontalHeader()
        for i, (_, tip) in enumerate(headers):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
            self.table.horizontalHeaderItem(i).setToolTip(tip)
        self.table.setAlternatingRowColors(True)
        main_layout.addWidget(self.table)
        
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
        
        # Seletor de registros por página
        per_page_layout = QHBoxLayout()
        per_page_layout.addWidget(QLabel("Registros por página:", self))
        self.per_page_selector = QComboBox(self)
        self.per_page_selector.addItems(["10", "25", "50", "100"])
        self.per_page_selector.setCurrentText(str(self.records_per_page))
        self.per_page_selector.currentIndexChanged.connect(self.change_records_per_page)
        per_page_layout.addWidget(self.per_page_selector)
        main_layout.addLayout(per_page_layout)
        
        self.load_history()
    
    def load_history(self):
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT card_id, review_date, quality, ef, repetitions, interval
            FROM review_history
            ORDER BY review_date DESC
        """)
        self.history_records = cursor.fetchall()
        self.current_page = 0
        self.populate_table(self.history_records)
    
    def populate_table(self, records):
        self.table.setRowCount(0)
        start_index = self.current_page * self.records_per_page
        end_index = start_index + self.records_per_page
        for record in records[start_index:end_index]:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(record["card_id"])))
            self.table.setItem(row, 1, QTableWidgetItem(record["review_date"]))
            self.table.setItem(row, 2, QTableWidgetItem(str(record["quality"])))
            self.table.setItem(row, 3, QTableWidgetItem(str(record["ef"])))
            self.table.setItem(row, 4, QTableWidgetItem(str(record["repetitions"])))
            self.table.setItem(row, 5, QTableWidgetItem(str(record["interval"])))
            for col in range(6):
                self.table.item(row, col).setTextAlignment(QtCore.Qt.AlignCenter)
        self.update_pagination_controls()
    
    def update_pagination_controls(self):
        total_pages = max(1, (len(self.history_records) + self.records_per_page - 1) // self.records_per_page)
        self.page_label.setText(f"Página {self.current_page + 1} de {total_pages}")
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < total_pages - 1)
    
    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.populate_table(self.history_records)
    
    def next_page(self):
        if (self.current_page + 1) * self.records_per_page < len(self.history_records):
            self.current_page += 1
            self.populate_table(self.history_records)
    
    def change_records_per_page(self):
        self.records_per_page = int(self.per_page_selector.currentText())
        self.current_page = 0
        self.populate_table(self.history_records)
    
    def filter_history(self):
        query = self.search_input.text().strip().lower()
        if query:
            filtered = [
                record for record in self.history_records
                if query in str(record["card_id"]).lower() or query in record["review_date"].lower()
            ]
        else:
            filtered = self.history_records
        self.current_page = 0
        self.populate_table(filtered)
