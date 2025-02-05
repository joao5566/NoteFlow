#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import base64
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QComboBox, QPushButton, QDialogButtonBox, QMessageBox, QInputDialog
from image_editor import RichTextEditor
from PyQt5.QtWidgets import QFileDialog

# Diálogo para adicionar flashcards
class AddCardDialog(QtWidgets.QDialog):
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        self.db_connection = db_connection
        self.audio_data = ""  # Armazena o áudio (base64) selecionado
        self.setWindowTitle("Adicionar Flash Card")
        self.setWindowState(QtCore.Qt.WindowMaximized)
        self.resize(600, 400)
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        # Seletor de Baralho
        layout.addWidget(QLabel("Selecione o Baralho:", self))
        self.deck_selector = QComboBox(self)
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT id, name FROM decks")
        decks = cursor.fetchall()
        if decks:
            for deck in decks:
                self.deck_selector.addItem(deck["name"], deck["id"])
        else:
            self.deck_selector.addItem("Nenhum baralho disponível", -1)
        layout.addWidget(self.deck_selector)
        # Editor da Pergunta
        layout.addWidget(QLabel("Pergunta:", self))
        self.question_editor = RichTextEditor(self)
        layout.addWidget(self.question_editor)
        # Editor da Resposta
        layout.addWidget(QLabel("Resposta:", self))
        self.answer_editor = RichTextEditor(self)
        layout.addWidget(self.answer_editor)
        # Botão para selecionar arquivo de áudio manualmente
        self.add_audio_button = QPushButton("Adicionar Áudio (Arquivo)", self)
        self.add_audio_button.clicked.connect(self.select_audio)
        layout.addWidget(self.add_audio_button)
        # Botões OK/Cancelar
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.add_card)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def select_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Áudio", "", "Audio Files (*.mp3 *.wav *.ogg)"
        )
        if file_path:
            with open(file_path, "rb") as f:
                self.audio_data = base64.b64encode(f.read()).decode('utf-8')
            QMessageBox.information(self, "Áudio", "Áudio selecionado com sucesso.")

    def add_card(self):
        deck_id = self.deck_selector.currentData()
        if deck_id == -1:
            QMessageBox.warning(self, "Erro", "Cadastre um baralho antes de adicionar flash cards.")
            return
        question_html = self.question_editor.toHtml()
        answer_html = self.answer_editor.toHtml()
        if not question_html.strip() or not answer_html.strip():
            QMessageBox.warning(self, "Erro", "Os campos de pergunta e resposta são obrigatórios.")
            return
        today = datetime.date.today().isoformat()
        cursor = self.db_connection.cursor()
        cursor.execute("""
            INSERT INTO cards (deck_id, question, answer, audio, ef, repetitions, interval, due_date)
            VALUES (?, ?, ?, ?, 2.5, 0, 0, ?)
        """, (deck_id, question_html, answer_html, self.audio_data, today))
        self.db_connection.commit()
        self.accept()

# Diálogo para editar flashcards
class EditCardDialog(QtWidgets.QDialog):
    def __init__(self, db_connection, card_id, parent=None):
        super().__init__(parent)
        self.db_connection = db_connection
        self.card_id = card_id
        self.audio_data = ""  # Para atualizar o áudio, se desejar
        self.setWindowTitle("Editar Flash Card")
        self.setWindowState(QtCore.Qt.WindowMaximized)
        self.resize(600, 400)
        self.setModal(True)
        self.setup_ui()
        self.load_card_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Selecione o Baralho:", self))
        self.deck_selector = QComboBox(self)
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT id, name FROM decks")
        decks = cursor.fetchall()
        for deck in decks:
            self.deck_selector.addItem(deck["name"], deck["id"])
        layout.addWidget(self.deck_selector)
        layout.addWidget(QLabel("Pergunta:", self))
        self.question_editor = RichTextEditor(self)
        layout.addWidget(self.question_editor)
        layout.addWidget(QLabel("Resposta:", self))
        self.answer_editor = RichTextEditor(self)
        layout.addWidget(self.answer_editor)
        self.add_audio_button = QPushButton("Adicionar/Atualizar Áudio", self)
        self.add_audio_button.clicked.connect(self.select_audio)
        layout.addWidget(self.add_audio_button)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.update_card)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def select_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Áudio", "", "Audio Files (*.mp3 *.wav *.ogg)"
        )
        if file_path:
            with open(file_path, "rb") as f:
                self.audio_data = base64.b64encode(f.read()).decode('utf-8')
            QMessageBox.information(self, "Áudio", "Áudio selecionado com sucesso.")

    def load_card_data(self):
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT * FROM cards WHERE id = ?", (self.card_id,))
        card = cursor.fetchone()
        if card:
            index = self.deck_selector.findData(card["deck_id"])
            if index >= 0:
                self.deck_selector.setCurrentIndex(index)
            self.question_editor.setHtml(card["question"])
            self.answer_editor.setHtml(card["answer"])
            self.audio_data = card["audio"] or ""

    def update_card(self):
        deck_id = self.deck_selector.currentData()
        question_html = self.question_editor.toHtml()
        answer_html = self.answer_editor.toHtml()
        if not question_html.strip() or not answer_html.strip():
            QMessageBox.warning(self, "Erro", "Os campos de pergunta e resposta são obrigatórios.")
            return
        cursor = self.db_connection.cursor()
        cursor.execute("""
            UPDATE cards 
            SET deck_id = ?, question = ?, answer = ?, audio = ?
            WHERE id = ?
        """, (deck_id, question_html, answer_html, self.audio_data, self.card_id))
        self.db_connection.commit()
        self.accept()
