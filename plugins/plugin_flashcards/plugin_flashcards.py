import sqlite3
import datetime
import random
import base64
import re
import os
import tempfile
import pyttsx3  # Biblioteca para TTS (ainda é usada no fallback de reprodução, se necessário)
import importlib  # Para importar dinamicamente módulos (usado na aba de estatísticas)
import numpy as np
import calendar
import matplotlib.pyplot as plt

from html.parser import HTMLParser

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLineEdit, QPushButton,
    QHBoxLayout, QLabel, QHeaderView, QMessageBox, QComboBox, QInputDialog
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, QDate, pyqtSignal

from plugin_base import PluginTab

# -----------------------------------------
# Classe auxiliar para remover tags HTML
# -----------------------------------------
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

def strip_html_tags(html):
    """Remove tags HTML do texto, inclusive conteúdo de <style>."""
    html = re.sub(r'<style.*?>.*?</style>', '', html, flags=re.DOTALL)
    stripper = HTMLTextStripper()
    stripper.feed(html)
    return stripper.get_data()

# =========================================
# Classes para redimensionamento de imagens e editor rico
# =========================================

class ResizablePixmapItem(QtWidgets.QGraphicsPixmapItem):
    def __init__(self, pixmap):
        super().__init__(pixmap)
        self.original_pixmap = pixmap
        self.setFlags(QtWidgets.QGraphicsItem.ItemIsSelectable | 
                      QtWidgets.QGraphicsItem.ItemIsMovable |
                      QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)
        self.handle_size = 10
        self.resizing = False
        self.current_handle = None
        self.setAcceptHoverEvents(True)
        self.updateHandlesPos()

    def updateHandlesPos(self):
        rect = self.boundingRect()
        self.handles = {
            'top_left': QtCore.QRectF(rect.topLeft(), QtCore.QSizeF(self.handle_size, self.handle_size)),
            'top_right': QtCore.QRectF(rect.topRight() - QtCore.QPointF(self.handle_size, 0), QtCore.QSizeF(self.handle_size, self.handle_size)),
            'bottom_left': QtCore.QRectF(rect.bottomLeft() - QtCore.QPointF(0, self.handle_size), QtCore.QSizeF(self.handle_size, self.handle_size)),
            'bottom_right': QtCore.QRectF(rect.bottomRight() - QtCore.QPointF(self.handle_size, self.handle_size), QtCore.QSizeF(self.handle_size, self.handle_size))
        }

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        if self.isSelected():
            pen = QtGui.QPen(QtCore.Qt.black, 1, QtCore.Qt.DashLine)
            painter.setPen(pen)
            for handle in self.handles.values():
                painter.drawRect(handle)

    def hoverMoveEvent(self, event):
        for handle, rect in self.handles.items():
            if rect.contains(event.pos()):
                self.setCursor(QtCore.Qt.SizeFDiagCursor)
                return
        self.setCursor(QtCore.Qt.ArrowCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        for handle, rect in self.handles.items():
            if rect.contains(event.pos()):
                self.resizing = True
                self.current_handle = handle
                self.orig_rect = self.boundingRect()
                self.orig_pos = event.pos()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.resizing and self.current_handle:
            diff = event.pos() - self.orig_pos
            if self.current_handle == 'bottom_right':
                new_width = self.orig_rect.width() + diff.x()
                new_height = self.orig_rect.height() + diff.y()
            elif self.current_handle == 'top_left':
                new_width = self.orig_rect.width() - diff.x()
                new_height = self.orig_rect.height() - diff.y()
            elif self.current_handle == 'top_right':
                new_width = self.orig_rect.width() + diff.x()
                new_height = self.orig_rect.height() - diff.y()
            elif self.current_handle == 'bottom_left':
                new_width = self.orig_rect.width() - diff.x()
                new_height = self.orig_rect.height() + diff.y()
            new_width = max(new_width, 20)
            new_height = max(new_height, 20)
            new_pixmap = self.original_pixmap.scaled(
                int(new_width), int(new_height),
                QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
            )
            self.setPixmap(new_pixmap)
            self.updateHandlesPos()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.resizing = False
        self.current_handle = None
        super().mouseReleaseEvent(event)

class ImageResizeDialog(QtWidgets.QDialog):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Redimensionar Imagem")
        self.setWindowState(QtCore.Qt.WindowMaximized)
        self.resize(600, 400)
        self.scene = QtWidgets.QGraphicsScene(self)
        self.view = QtWidgets.QGraphicsView(self.scene, self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.view)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.pixmap_item = ResizablePixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)
        self.scene.setSceneRect(self.pixmap_item.boundingRect())

    def getResizedPixmap(self):
        return self.pixmap_item.pixmap()

class RichTextEditor(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.toolbar = QtWidgets.QToolBar(self)
        layout.addWidget(self.toolbar)

        bold_action = QtWidgets.QAction("B", self)
        bold_action.setShortcut("Ctrl+B")
        bold_action.triggered.connect(self.toggle_bold)
        self.toolbar.addAction(bold_action)

        italic_action = QtWidgets.QAction("I", self)
        italic_action.setShortcut("Ctrl+I")
        italic_action.triggered.connect(self.toggle_italic)
        self.toolbar.addAction(italic_action)

        underline_action = QtWidgets.QAction("U", self)
        underline_action.setShortcut("Ctrl+U")
        underline_action.triggered.connect(self.toggle_underline)
        self.toolbar.addAction(underline_action)

        color_action = QtWidgets.QAction("Cor", self)
        color_action.triggered.connect(self.change_color)
        self.toolbar.addAction(color_action)

        self.font_combo = QtWidgets.QFontComboBox(self)
        self.font_combo.currentFontChanged.connect(self.change_font)
        self.toolbar.addWidget(self.font_combo)

        self.font_size_combo = QComboBox(self)
        for size in [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]:
            self.font_size_combo.addItem(str(size), size)
        self.font_size_combo.setCurrentText("12")
        self.font_size_combo.currentIndexChanged.connect(self.change_font_size)
        self.toolbar.addWidget(self.font_size_combo)

        image_action = QtWidgets.QAction("Inserir Imagem", self)
        image_action.triggered.connect(self.insert_image)
        self.toolbar.addAction(image_action)

        self.text_edit = ResizableImageTextEdit(self)
        layout.addWidget(self.text_edit)
        self.setLayout(layout)

    def toggle_bold(self):
        fmt = self.text_edit.currentCharFormat()
        weight = QtGui.QFont.Bold if fmt.fontWeight() != QtGui.QFont.Bold else QtGui.QFont.Normal
        fmt.setFontWeight(weight)
        self.text_edit.mergeCurrentCharFormat(fmt)

    def toggle_italic(self):
        fmt = self.text_edit.currentCharFormat()
        fmt.setFontItalic(not fmt.fontItalic())
        self.text_edit.mergeCurrentCharFormat(fmt)

    def toggle_underline(self):
        fmt = self.text_edit.currentCharFormat()
        fmt.setFontUnderline(not fmt.fontUnderline())
        self.text_edit.mergeCurrentCharFormat(fmt)

    def change_color(self):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            fmt = self.text_edit.currentCharFormat()
            fmt.setForeground(QtGui.QBrush(color))
            self.text_edit.mergeCurrentCharFormat(fmt)

    def change_font(self, font):
        fmt = self.text_edit.currentCharFormat()
        fmt.setFont(font)
        self.text_edit.mergeCurrentCharFormat(fmt)

    def change_font_size(self):
        size = int(self.font_size_combo.currentData())
        fmt = self.text_edit.currentCharFormat()
        fmt.setFontPointSize(size)
        self.text_edit.mergeCurrentCharFormat(fmt)

    def insert_image(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Selecionar Imagem", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            with open(file_path, "rb") as image_file:
                image_data = image_file.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            if file_path.lower().endswith(".png"):
                mime = "image/png"
            elif file_path.lower().endswith((".jpg", ".jpeg")):
                mime = "image/jpeg"
            elif file_path.lower().endswith(".bmp"):
                mime = "image/bmp"
            elif file_path.lower().endswith(".gif"):
                mime = "image/gif"
            else:
                mime = "application/octet-stream"
            html_img = f'<img src="data:{mime};base64,{base64_data}" alt="Imagem" />'
            cursor = self.text_edit.textCursor()
            cursor.insertHtml(html_img)

    def toHtml(self):
        return self.text_edit.toHtml()

    def setHtml(self, html):
        self.text_edit.setHtml(html)

class ResizableImageTextEdit(QtWidgets.QTextEdit):
    def mouseDoubleClickEvent(self, event):
        cursor = self.cursorForPosition(event.pos())
        fmt = cursor.charFormat()
        if fmt.isImageFormat():
            image_format = fmt.toImageFormat()
            image_src = image_format.name()
            if image_src.startswith("data:"):
                try:
                    header, base64_data = image_src.split(",", 1)
                except ValueError:
                    return super().mouseDoubleClickEvent(event)
                image_data = base64.b64decode(base64_data)
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(image_data)
                dialog = ImageResizeDialog(pixmap, self)
                if dialog.exec_() == QtWidgets.QDialog.Accepted:
                    new_pixmap = dialog.getResizedPixmap()
                    buffer = QtCore.QBuffer()
                    buffer.open(QtCore.QIODevice.WriteOnly)
                    new_pixmap.save(buffer, "PNG")
                    new_base64 = base64.b64encode(buffer.data()).decode('utf-8')
                    new_src = f"data:image/png;base64,{new_base64}"
                    new_format = QtGui.QTextImageFormat()
                    new_format.setName(new_src)
                    cursor.select(QtGui.QTextCursor.WordUnderCursor)
                    cursor.removeSelectedText()
                    cursor.insertImage(new_format)
        else:
            super().mouseDoubleClickEvent(event)

# -----------------------------------------
# Diálogos para adicionar/editar flashcards (com opção de áudio)
# -----------------------------------------
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
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.add_card)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def select_audio(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
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
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.update_card)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def select_audio(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
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

# -----------------------------------------
# Tabela de Gerenciamento de Flash Cards com Busca, Paginação e Ações
# -----------------------------------------
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

# -----------------------------------------
# Aba de Estatísticas (Dashboard e Histórico de Revisões)
# -----------------------------------------
class StatisticsTab(QWidget):
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        self.db_connection = db_connection
        self.filtered_reviews = []  # Dados filtrados da tabela review_history
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        # Cria um QTabWidget para separar Dashboard e Histórico
        self.tabs = QtWidgets.QTabWidget(self)
        layout.addWidget(self.tabs)

        # Aba Dashboard
        self.dashboard_tab = QWidget(self)
        self.setup_dashboard_tab()
        self.tabs.addTab(self.dashboard_tab, "Dashboard")

        # Aba Histórico
        self.history_tab = QWidget(self)
        self.setup_history_tab()
        self.tabs.addTab(self.history_tab, "Histórico de Revisões")

    def setup_dashboard_tab(self):
        dash_layout = QVBoxLayout(self.dashboard_tab)
        # Linha de seleção de tipo de gráfico
        graph_selection_layout = QHBoxLayout()
        graph_selection_layout.addWidget(QLabel("Tipo de Gráfico:", self))
        self.graph_type_combo = QComboBox(self)
        # Adicione os tipos de gráfico desejados:
        self.graph_type_combo.addItems([
            "Revisões por Dia (Barras)",
            "Revisões por Dia (Linhas)",
            "Heatmap por Ano",
            "Heatmap de Vários Anos",
            "Comparativo de Revisões por Dias da Semana - Barras",
            "Comparativo de Revisões por Dias da Semana - Linhas",
            "Comparativo de Revisões por Dias da Semana - Pizza",
            "Procrastinação (Pizza)"
        ])
        graph_selection_layout.addWidget(self.graph_type_combo)
        dash_layout.addLayout(graph_selection_layout)

        # Filtros: Anos, Meses e Semanas (baseados na coluna review_date)
        filter_layout = QHBoxLayout()
        self.year_list = QtWidgets.QListWidget(self)
        self.year_list.setSelectionMode(QtWidgets.QListWidget.MultiSelection)
        filter_layout.addWidget(QLabel("Anos:"))
        filter_layout.addWidget(self.year_list)
        self.year_list.itemSelectionChanged.connect(self.update_months)

        self.month_list = QtWidgets.QListWidget(self)
        self.month_list.setSelectionMode(QtWidgets.QListWidget.MultiSelection)
        filter_layout.addWidget(QLabel("Meses:"))
        filter_layout.addWidget(self.month_list)
        self.month_list.itemSelectionChanged.connect(self.update_weeks)

        self.week_list = QtWidgets.QListWidget(self)
        self.week_list.setSelectionMode(QtWidgets.QListWidget.MultiSelection)
        filter_layout.addWidget(QLabel("Semanas:"))
        filter_layout.addWidget(self.week_list)

        self.update_button = QPushButton("Atualizar Estatísticas", self)
        self.update_button.clicked.connect(self.plot_selected_graph)
        filter_layout.addWidget(self.update_button)
        dash_layout.addLayout(filter_layout)

        # Área para o gráfico (usando matplotlib)
        matplotlib = importlib.import_module("matplotlib")
        matplotlib.use("Qt5Agg")
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.figure import Figure

        self.figure = Figure(figsize=(6, 4))
        self.canvas = FigureCanvas(self.figure)
        dash_layout.addWidget(self.canvas)

        # Carrega os filtros iniciais
        self.update_years()

    def update_years(self):
        """Atualiza a lista de anos com base na coluna review_date da tabela review_history."""
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT DISTINCT strftime('%Y', review_date) AS year FROM review_history ORDER BY year")
        years = [row["year"] for row in cursor.fetchall()]
        self.year_list.clear()
        for year in years:
            self.year_list.addItem(year)
        self.month_list.clear()
        self.week_list.clear()

    def update_months(self):
        selected_years = [item.text() for item in self.year_list.selectedItems()]
        if not selected_years:
            self.month_list.clear()
            self.week_list.clear()
            self.month_list.setEnabled(False)
            self.week_list.setEnabled(False)
            return
        placeholders = ", ".join(["?"] * len(selected_years))
        query = f"SELECT DISTINCT strftime('%m', review_date) AS month FROM review_history WHERE strftime('%Y', review_date) IN ({placeholders}) ORDER BY month"
        cursor = self.db_connection.cursor()
        cursor.execute(query, selected_years)
        months = [row["month"] for row in cursor.fetchall()]
        self.month_list.clear()
        for m in sorted(months):
            self.month_list.addItem(f"{int(m):02d}")
        self.month_list.setEnabled(True)
        self.week_list.clear()
        self.week_list.setEnabled(False)

    def update_weeks(self):
        selected_years = [item.text() for item in self.year_list.selectedItems()]
        selected_months = [item.text() for item in self.month_list.selectedItems()]
        if not selected_years or not selected_months:
            self.week_list.clear()
            self.week_list.setEnabled(False)
            return
        # Supondo semanas de 1 a 5
        self.week_list.clear()
        for week in range(1, 6):
            self.week_list.addItem(str(week))
        self.week_list.setEnabled(True)

    def filter_reviews(self):
        """Filtra as revisões com base nos filtros selecionados."""
        selected_years = [item.text() for item in self.year_list.selectedItems()]
        selected_months = [item.text() for item in self.month_list.selectedItems()]
        selected_weeks = [int(item.text()) for item in self.week_list.selectedItems()]
        query = "SELECT * FROM review_history"
        conditions = []
        params = []
        if selected_years:
            placeholders = ", ".join(["?"] * len(selected_years))
            conditions.append(f"strftime('%Y', review_date) IN ({placeholders})")
            params.extend(selected_years)
        if selected_months:
            placeholders = ", ".join(["?"] * len(selected_months))
            conditions.append(f"strftime('%m', review_date) IN ({placeholders})")
            params.extend(selected_months)
        if selected_weeks:
            week_conditions = []
            for week in selected_weeks:
                # Considera que a semana do mês é dada por ((dia-1)/7)+1
                week_conditions.append(f"((CAST(strftime('%d', review_date) AS INTEGER)-1)/7 + 1) = {week}")
            conditions.append("(" + " OR ".join(week_conditions) + ")")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY review_date"
        cursor = self.db_connection.cursor()
        cursor.execute(query, params)
        self.filtered_reviews = cursor.fetchall()

    def plot_selected_graph(self):
        """Seleciona e plota o gráfico conforme o tipo escolhido."""
        self.filter_reviews()
        graph_type = self.graph_type_combo.currentText()
        self.figure.clear()
        # Dicionário de métodos de plotagem
        plot_methods = {
            "Revisões por Dia (Barras)": self.plot_revisions_bar,
            "Revisões por Dia (Linhas)": self.plot_revisions_line,
            "Heatmap por Ano": self.plot_heatmap_for_year,
            "Heatmap de Vários Anos": self.plot_heatmap,
            "Comparativo de Revisões por Dias da Semana - Barras": self.plot_weekday_bar_chart,
            "Comparativo de Revisões por Dias da Semana - Linhas": self.plot_weekday_line_chart,
            "Comparativo de Revisões por Dias da Semana - Pizza": self.plot_weekday_pie_chart,
            "Procrastinação (Pizza)": self.plot_procrastination_chart
        }
        plot_method = plot_methods.get(graph_type, None)
        if plot_method:
            if graph_type == "Heatmap por Ano":
                # Para Heatmap por Ano, solicitar ano (pode ser digitado em um diálogo ou em um campo)
                text, ok = QInputDialog.getText(self, "Entrada", "Digite o ano desejado:")
                if ok and text.isdigit():
                    plot_method(int(text))
                else:
                    QMessageBox.warning(self, "Entrada Inválida", "Por favor, digite um ano válido.")
                    return
            else:
                plot_method()
        self.canvas.draw()

    def plot_revisions_bar(self):
        """Plota um gráfico de barras com o número de revisões por dia."""
        counts = {}
        for row in self.filtered_reviews:
            date = row["review_date"]
            counts[date] = counts.get(date, 0) + 1
        dates = sorted(counts.keys())
        rev_counts = [counts[date] for date in dates]

        ax = self.figure.add_subplot(111)
        ax.bar(dates, rev_counts, color='skyblue')
        ax.set_title("Revisões por Dia (Barras)")
        ax.set_xlabel("Data")
        ax.set_ylabel("Número de Revisões")
        ax.tick_params(axis='x', rotation=45)
        self.figure.tight_layout()

    def plot_revisions_line(self):
        """Plota um gráfico de linhas com o número de revisões por dia."""
        counts = {}
        for row in self.filtered_reviews:
            date = row["review_date"]
            counts[date] = counts.get(date, 0) + 1
        dates = sorted(counts.keys())
        rev_counts = [counts[date] for date in dates]

        ax = self.figure.add_subplot(111)
        ax.plot(dates, rev_counts, marker='o', linestyle='-', color='purple')
        ax.set_title("Revisões por Dia (Linhas)")
        ax.set_xlabel("Data")
        ax.set_ylabel("Número de Revisões")
        ax.tick_params(axis='x', rotation=45)
        self.figure.tight_layout()

    def plot_heatmap_for_year(self, year):
        """Plota um heatmap de revisões para um único ano, com cada linha representando um mês."""
        dates = [
            QDate.fromString(row["review_date"], "yyyy-MM-dd") for row in self.filtered_reviews
            if QDate.fromString(row["review_date"], "yyyy-MM-dd").year() == year
        ]
        if not dates:
            QMessageBox.warning(self, "Sem dados", f"Não há revisões para exibir no ano {year}.")
            return
        heatmap_data = np.zeros((12, 31), dtype=int)
        for date in dates:
            month_index = date.month() - 1
            day_index = date.day() - 1
            heatmap_data[month_index, day_index] += 1
        ax = self.figure.add_subplot(111)
        cax = ax.imshow(heatmap_data, cmap='YlGn', aspect='auto', vmin=0, vmax=heatmap_data.max())
        ax.set_xticks(np.arange(31))
        ax.set_xticklabels([str(i + 1) for i in range(31)])
        ax.set_yticks(np.arange(12))
        ax.set_yticklabels([QtCore.QDate.longMonthName(i + 1) for i in range(12)])
        ax.set_title(f"Heatmap de Revisões - {year}")
        ax.set_xlabel("Dias do Mês")
        ax.set_ylabel("Meses")
        self.figure.colorbar(cax, orientation='vertical', label='Número de Revisões')

    def plot_heatmap(self):
        """Plota um heatmap com a contagem de revisões por mês ao longo de vários anos."""
        dates = [QDate.fromString(row["review_date"], "yyyy-MM-dd") for row in self.filtered_reviews]
        if not dates:
            QMessageBox.warning(self, "Sem dados", "Não há revisões para exibir no período selecionado.")
            return
        selected_years = sorted(set(date.year() for date in dates))
        months = list(range(1, 13))
        heatmap_data = np.zeros((len(selected_years), len(months)), dtype=int)
        for date in dates:
            year_index = selected_years.index(date.year())
            month_index = date.month() - 1
            heatmap_data[year_index, month_index] += 1
        ax = self.figure.add_subplot(111)
        cax = ax.imshow(heatmap_data, cmap='YlGn', aspect='auto')
        ax.set_xticks(np.arange(len(months)))
        ax.set_xticklabels([QtCore.QDate.shortMonthName(m) for m in months])
        ax.set_yticks(np.arange(len(selected_years)))
        ax.set_yticklabels([str(year) for year in selected_years])
        ax.set_title("Heatmap de Revisões por Mês e Ano")
        ax.set_xlabel("Meses")
        ax.set_ylabel("Anos")
        self.figure.colorbar(cax, orientation='vertical', label='Número de Revisões')

    def plot_weekday_bar_chart(self):
        """Plota um gráfico de barras mostrando o número de revisões por dia da semana."""
        weekday_counts = {day: 0 for day in calendar.day_name}
        for row in self.filtered_reviews:
            date = QDate.fromString(row["review_date"], "yyyy-MM-dd")
            weekday = calendar.day_name[date.dayOfWeek() - 1]
            weekday_counts[weekday] += 1
        days = list(weekday_counts.keys())
        counts = list(weekday_counts.values())
        ax = self.figure.add_subplot(111)
        bars = ax.bar(days, counts, color='skyblue')
        ax.set_title("Revisões por Dia da Semana (Barras)")
        ax.set_xlabel("Dias da Semana")
        ax.set_ylabel("Número de Revisões")
        ax.set_ylim(0, max(counts) + 5)
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height}', xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom')

    def plot_weekday_line_chart(self):
        """Plota um gráfico de linhas mostrando a tendência de revisões por dia da semana ao longo das semanas."""
        from collections import defaultdict
        week_day_counts = defaultdict(lambda: defaultdict(int))
        for row in self.filtered_reviews:
            date = QDate.fromString(row["review_date"], "yyyy-MM-dd")
            week_number = date.weekNumber()[0]
            weekday = calendar.day_name[date.dayOfWeek() - 1]
            week_day_counts[week_number][weekday] += 1
        if not week_day_counts:
            QMessageBox.warning(self, "Sem dados", "Não há revisões para exibir no gráfico de linhas.")
            return
        weeks = sorted(week_day_counts.keys())
        days = list(calendar.day_name)
        day_trends = {day: [] for day in days}
        for week in weeks:
            for day in days:
                day_trends[day].append(week_day_counts[week].get(day, 0))
        ax = self.figure.add_subplot(111)
        for day, counts in day_trends.items():
            ax.plot(weeks, counts, marker='o', label=day)
        ax.set_title("Tendência de Revisões por Dia da Semana (Linhas)")
        ax.set_xlabel("Número da Semana")
        ax.set_ylabel("Número de Revisões")
        ax.legend(title="Dias")
        ax.grid(True)

    def plot_weekday_pie_chart(self):
        """Plota um gráfico de pizza mostrando a proporção de revisões por dia da semana."""
        weekday_counts = {day: 0 for day in calendar.day_name}
        for row in self.filtered_reviews:
            date = QDate.fromString(row["review_date"], "yyyy-MM-dd")
            weekday = calendar.day_name[date.dayOfWeek() - 1]
            weekday_counts[weekday] += 1
        labels = list(weekday_counts.keys())
        sizes = list(weekday_counts.values())
        if sum(sizes) == 0:
            QMessageBox.warning(self, "Sem dados", "Não há revisões para exibir no gráfico de pizza.")
            return
        ax = self.figure.add_subplot(111)
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired.colors)
        ax.set_title("Revisões por Dia da Semana (Pizza)")
        ax.axis('equal')

    def plot_procrastination_chart(self):
        """Plota um gráfico de pizza: Procrastinação (dias revisados vs não revisados no mês atual)."""
        dates = [QDate.fromString(row["review_date"], "yyyy-MM-dd") for row in self.filtered_reviews]
        if not dates:
            QMessageBox.information(self, "Sem dados", "Não há revisões para exibir.")
            return
        current_date = QDate.currentDate()
        total_days = current_date.daysInMonth()
        reviewed_days = { (date.year(), date.month(), date.day()) for date in dates }
        num_reviewed = len(reviewed_days)
        num_not_reviewed = total_days - num_reviewed
        ax = self.figure.add_subplot(111)
        ax.pie([num_reviewed, num_not_reviewed], labels=["Revisados", "Não Revisados"],
               autopct='%1.1f%%', colors=["#66b3ff", "#ff9999"])
        ax.set_title("Procrastinação (Mês Atual)")
        ax.axis('equal')

    def plot_comparative_chart(self):
        """Plota um gráfico comparativo de revisões por dia da semana (barras)."""
        weekday_counts = {day: 0 for day in calendar.day_name}
        for row in self.filtered_reviews:
            date = QDate.fromString(row["review_date"], "yyyy-MM-dd")
            weekday = calendar.day_name[date.dayOfWeek() - 1]
            weekday_counts[weekday] += 1
        labels = list(weekday_counts.keys())
        counts = list(weekday_counts.values())
        ax = self.figure.add_subplot(111)
        ax.bar(labels, counts, color='mediumseagreen')
        ax.set_title("Comparativo de Revisões por Dia da Semana")
        ax.set_xlabel("Dias da Semana")
        ax.set_ylabel("Número de Revisões")
        ax.tick_params(axis='x', rotation=45)

    def setup_history_tab(self):
        history_layout = QVBoxLayout(self.history_tab)
        self.history_table = QTableWidget(self)
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels(["Card ID", "Data", "Qualidade", "EF", "Repetições", "Intervalo"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        history_layout.addWidget(self.history_table)
        self.load_history()

    def load_history(self):
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT card_id, review_date, quality, ef, repetitions, interval
            FROM review_history
            ORDER BY review_date DESC
        """)
        rows = cursor.fetchall()
        self.history_table.setRowCount(0)
        for row in rows:
            r = self.history_table.rowCount()
            self.history_table.insertRow(r)
            self.history_table.setItem(r, 0, QTableWidgetItem(str(row["card_id"])))
            self.history_table.setItem(r, 1, QTableWidgetItem(row["review_date"]))
            self.history_table.setItem(r, 2, QTableWidgetItem(str(row["quality"])))
            self.history_table.setItem(r, 3, QTableWidgetItem(str(row["ef"])))
            self.history_table.setItem(r, 4, QTableWidgetItem(str(row["repetitions"])))
            self.history_table.setItem(r, 5, QTableWidgetItem(str(row["interval"])))

# -----------------------------------------
# Plugin de Flash Cards Avançado com Revisão, Gerenciamento e Estatísticas
# -----------------------------------------
class PluginFlashCards(PluginTab):
    name = "Flash Cards Avançado"

    def __init__(self, parent=None):
        super().__init__(parent)
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

        # Para reprodução de áudio
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
        deck_layout.addWidget(QtWidgets.QLabel("Selecione o Baralho:", self.review_tab))
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
            self.stats_tab.load_history()

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

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication, QInputDialog
    import sys
    app = QApplication(sys.argv)
    conn = sqlite3.connect("flashcards.db")
    conn.row_factory = sqlite3.Row
    widget = FlashcardsTableWidget(conn)
    widget.load_flashcards()
    widget.show()
    sys.exit(app.exec_())
