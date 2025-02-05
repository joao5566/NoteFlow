#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import datetime
import tempfile
import base64
import os
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QInputDialog, QMessageBox
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl
from plugin_base import PluginTab  # Certifique-se de que plugin_base.py está acessível

from dialogs import AddCardDialog
from management import FlashcardsTableWidget
from config_dialog import FlashCardsConfigDialog
from history import HistoryTableWidget
from statistics import StatisticsTab

class PluginFlashCards(PluginTab):
    name = "Flash Cards Avançado"
    version = "1.0"
    author = "joao5566"
    description = "Plugin avançado de flash cards com revisão, gerenciamento, estatísticas e opções de configuração."
    name = "Flash cards"

    def __init__(self, parent=None):
        super().__init__(parent)
        # Configuração padrão do plugin (pode ser persistida em arquivo)
        self.config = {
            "initial_ef": 25,  # Representa 2.5
            "cards_per_session": 10,
            "auto_audio": True
        }
        self.db_connection = sqlite3.connect("flashcards.db")
        self.db_connection.row_factory = sqlite3.Row
        self.create_tables()
        self.tab_widget = QtWidgets.QTabWidget(self)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.tab_widget)
        # Aba de Revisão
        self.review_tab = QWidget(self)
        self.setup_review_tab()
        self.tab_widget.addTab(self.review_tab, "Revisão")
        # Aba de Gerenciamento
        self.manage_tab = QWidget(self)
        manage_layout = QVBoxLayout(self.manage_tab)
        buttons_layout = QHBoxLayout()
        create_deck_btn = QPushButton("Criar Baralho", self.manage_tab)
        create_deck_btn.clicked.connect(self.create_deck)
        buttons_layout.addWidget(create_deck_btn)
        add_card_btn = QPushButton("Adicionar Flash Card", self.manage_tab)
        add_card_btn.clicked.connect(self.open_add_card_dialog)
        buttons_layout.addWidget(add_card_btn)
        manage_layout.addLayout(buttons_layout)
        self.flashcards_table = FlashcardsTableWidget(self.db_connection, self)
        manage_layout.addWidget(self.flashcards_table)
        self.tab_widget.addTab(self.manage_tab, "Gerenciamento")
        # Aba de Estatísticas
        self.stats_tab = StatisticsTab(self.db_connection, self)
        self.tab_widget.addTab(self.stats_tab, "Estatísticas")
        self.setLayout(main_layout)
        self.current_deck_id = None
        self.current_card = None
        self.session_cards = []
        # Player de áudio
        self.player = QMediaPlayer()

    def create_tables(self):
        cursor = self.db_connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS decks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deck_id INTEGER NOT NULL,
                question TEXT,
                answer TEXT,
                audio TEXT,
                ef REAL DEFAULT 2.5,
                repetitions INTEGER DEFAULT 0,
                interval INTEGER DEFAULT 0,
                due_date TEXT,
                FOREIGN KEY(deck_id) REFERENCES decks(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS review_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id INTEGER NOT NULL,
                review_date TEXT NOT NULL,
                quality INTEGER,
                ef REAL,
                repetitions INTEGER,
                interval INTEGER,
                FOREIGN KEY(card_id) REFERENCES cards(id)
            )
        ''')
        self.db_connection.commit()

    def setup_review_tab(self):
        layout = QVBoxLayout(self.review_tab)
        deck_layout = QHBoxLayout()
        deck_layout.addWidget(QLabel("Selecione o Baralho:", self.review_tab))
        self.deck_selector = QtWidgets.QComboBox(self.review_tab)
        self.load_decks_into_selector()
        deck_layout.addWidget(self.deck_selector)
        layout.addLayout(deck_layout)
        self.start_review_button = QPushButton("Iniciar Revisão", self.review_tab)
        self.start_review_button.clicked.connect(self.start_review)
        layout.addWidget(self.start_review_button)
        self.scroll_area = QtWidgets.QScrollArea(self.review_tab)
        self.scroll_area.setWidgetResizable(True)
        content_widget = QWidget()
        self.card_layout = QVBoxLayout(content_widget)
        self.question_label = QLabel("", content_widget)
        self.question_label.setAlignment(QtCore.Qt.AlignCenter)
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.card_layout.addWidget(self.question_label)
        self.answer_label = QLabel("", content_widget)
        self.answer_label.setAlignment(QtCore.Qt.AlignCenter)
        self.answer_label.setWordWrap(True)
        self.answer_label.setStyleSheet("font-size: 16px;")
        self.answer_label.hide()
        self.card_layout.addWidget(self.answer_label)
        self.scroll_area.setWidget(content_widget)
        layout.addWidget(self.scroll_area)
        buttons_layout = QHBoxLayout()
        self.show_answer_button = QPushButton("Mostrar Resposta", self.review_tab)
        self.show_answer_button.clicked.connect(self.show_answer)
        self.show_answer_button.setEnabled(False)
        buttons_layout.addWidget(self.show_answer_button)
        self.listen_button = QPushButton("Ouvir", self.review_tab)
        self.listen_button.clicked.connect(self.play_audio)
        self.listen_button.setEnabled(False)
        buttons_layout.addWidget(self.listen_button)
        layout.addLayout(buttons_layout)
        rating_layout = QHBoxLayout()
        self.again_button = QPushButton("Again", self.review_tab)
        self.again_button.clicked.connect(lambda: self.rate_card(0))
        self.again_button.setEnabled(False)
        rating_layout.addWidget(self.again_button)
        self.hard_button = QPushButton("Difícil", self.review_tab)
        self.hard_button.clicked.connect(lambda: self.rate_card(3))
        self.hard_button.setEnabled(False)
        rating_layout.addWidget(self.hard_button)
        self.good_button = QPushButton("Fácil", self.review_tab)
        self.good_button.clicked.connect(lambda: self.rate_card(4))
        self.good_button.setEnabled(False)
        rating_layout.addWidget(self.good_button)
        layout.addLayout(rating_layout)

    def load_decks_into_selector(self):
        self.deck_selector.clear()
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT id, name FROM decks")
        decks = cursor.fetchall()
        for deck in decks:
            self.deck_selector.addItem(deck["name"], deck["id"])

    def start_review(self):
        deck_id = self.deck_selector.currentData()
        if deck_id is None:
            QMessageBox.warning(self, "Erro", "Selecione um baralho para revisar.")
            return
        self.current_deck_id = deck_id
        today = datetime.date.today().isoformat()
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT * FROM cards
            WHERE deck_id = ? AND (due_date IS NULL OR due_date <= ?)
            ORDER BY due_date
        """, (self.current_deck_id, today))
        self.session_cards = list(cursor.fetchall())
        if not self.session_cards:
            QMessageBox.information(self, "Revisão", "Nenhum flash card para revisão no momento.")
            self.question_label.setText("")
            self.answer_label.hide()
            self.show_answer_button.setEnabled(False)
            self.listen_button.setEnabled(False)
            self.again_button.setEnabled(False)
            self.hard_button.setEnabled(False)
            self.good_button.setEnabled(False)
            return
        self.load_next_card()

    def load_next_card(self):
        if self.session_cards:
            self.current_card = self.session_cards.pop(0)
            self.question_label.setText(self.current_card["question"])
            self.answer_label.setText(self.current_card["answer"])
            self.answer_label.hide()
            self.show_answer_button.setEnabled(True)
            self.listen_button.setEnabled(True)
            self.again_button.setEnabled(False)
            self.hard_button.setEnabled(False)
            self.good_button.setEnabled(False)
        else:
            self.question_label.setText("Revisão concluída!")
            self.answer_label.hide()
            self.show_answer_button.setEnabled(False)
            self.listen_button.setEnabled(False)
            self.again_button.setEnabled(False)
            self.hard_button.setEnabled(False)
            self.good_button.setEnabled(False)
            self.stats_tab.plot_selected_graph()

    def show_answer(self):
        self.answer_label.show()
        self.again_button.setEnabled(True)
        self.hard_button.setEnabled(True)
        self.good_button.setEnabled(True)
        self.show_answer_button.setEnabled(False)

    def play_audio(self):
        if self.current_card is None:
            return
        audio_data = self.current_card["audio"] if self.current_card["audio"] is not None else ""
        if audio_data:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            temp_file.write(base64.b64decode(audio_data))
            temp_file.close()
            url = QUrl.fromLocalFile(temp_file.name)
            self.player.setMedia(QMediaContent(url))
            self.player.play()

    def rate_card(self, quality):
        if self.current_card is None:
            return
        card_id = self.current_card["id"]
        ef = self.current_card["ef"]
        repetitions = self.current_card["repetitions"]
        interval = self.current_card["interval"]
        if quality == 0:  # "Again"
            repetitions = 0
            interval = 1
            next_review_date = datetime.date.today()
            due_date = next_review_date.isoformat()
            self.session_cards.append(dict(self.current_card))
        else:
            repetitions += 1
            if repetitions == 1:
                interval = 1
            elif repetitions == 2:
                interval = 6 if quality == 4 else 3
            else:
                interval = round(interval * ef)
            ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            if ef < 1.3:
                ef = 1.3
            next_review_date = datetime.date.today() + datetime.timedelta(days=interval)
            due_date = next_review_date.isoformat()
        cursor = self.db_connection.cursor()
        cursor.execute("""
            UPDATE cards 
            SET ef = ?, repetitions = ?, interval = ?, due_date = ? 
            WHERE id = ?
        """, (ef, repetitions, interval, due_date, card_id))
        self.db_connection.commit()
        cursor.execute("""
            INSERT INTO review_history (card_id, review_date, quality, ef, repetitions, interval)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (card_id, datetime.date.today().isoformat(), quality, ef, repetitions, interval))
        self.db_connection.commit()
        self.load_next_card()

    def create_deck(self):
        text, ok = QInputDialog.getText(self, "Criar Baralho", "Nome do Baralho:")
        if ok and text:
            try:
                cursor = self.db_connection.cursor()
                cursor.execute("INSERT INTO decks (name) VALUES (?)", (text.strip(),))
                self.db_connection.commit()
                QMessageBox.information(self, "Sucesso", "Baralho criado com sucesso.")
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Erro", "Um baralho com esse nome já existe.")
            self.load_decks_into_selector()

    def open_add_card_dialog(self):
        dialog = AddCardDialog(self.db_connection, parent=self)
        if dialog.exec_():
            self.flashcards_table.refresh_flashcards()

    def configure(self):
        dialog = FlashCardsConfigDialog(self.config, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            new_config = dialog.get_config()
            self.config.update(new_config)
            QMessageBox.information(self, "Configurações", "Configurações atualizadas com sucesso!")
