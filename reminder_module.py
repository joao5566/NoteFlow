# reminder_manager.py

import sys
import sqlite3
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QLabel, QComboBox, QTableWidget,
    QTableWidgetItem, QMessageBox, QLineEdit, QFormLayout, QHBoxLayout, QHeaderView,
    QCalendarWidget  # Importado para o minicalendário
)
from PyQt5.QtCore import Qt, QDate
from html.parser import HTMLParser
import re

class ReminderManager(QDialog):
    """Diálogo para gerenciar múltiplos lembretes."""

    def __init__(self, reminders, save_reminders_callback, parent=None):
        """
        Inicializa o ReminderManager.

        Args:
            reminders (dict): Dicionário de lembretes onde a chave é o ID e o valor é um dict com 'date' e 'message'.
            save_reminders_callback (function): Função de callback para salvar lembretes após alterações.
            parent (QWidget, optional): Widget pai.
        """
        super().__init__(parent)
        self.setWindowTitle("Gerenciar Lembretes")
        self.reminders = reminders  # {'id1': {'date': '2025-04-27', 'message': 'Lembrete 1'}, ...}
        self.save_reminders_callback = save_reminders_callback
        self.init_ui()

    def init_ui(self):
        """Inicializa os componentes da interface."""
        self.layout = QVBoxLayout(self)

        # Botões de ação (Adicionar, Editar, Excluir)
        buttons_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Adicionar Lembrete", self)
        self.add_button.clicked.connect(self.add_reminder)
        buttons_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Editar Lembrete", self)
        self.edit_button.clicked.connect(self.edit_reminder)
        buttons_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Excluir Lembrete", self)
        self.delete_button.clicked.connect(self.delete_reminder)
        buttons_layout.addWidget(self.delete_button)

        self.layout.addLayout(buttons_layout)

        # Tabela de lembretes
        self.table = QTableWidget(self)
        self.table.setColumnCount(3)  # ID, Data, Mensagem
        self.table.setHorizontalHeaderLabels(["ID", "Data", "Mensagem"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setWordWrap(True)  # Permitir quebra de linha
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.layout.addWidget(self.table)

        # Ocultar a coluna "ID"
        self.table.setColumnHidden(0, True)

        # Carregar os lembretes na tabela
        self.load_reminders()

    def load_reminders(self):
        """Carrega os lembretes na tabela."""
        self.table.setRowCount(0)
        for reminder_id, reminder in self.reminders.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            # Coluna ID (oculta)
            self.table.setItem(row, 0, QTableWidgetItem(str(reminder_id)))
            # Coluna Data
            self.table.setItem(row, 1, QTableWidgetItem(reminder['date']))
            # Coluna Mensagem
            self.table.setItem(row, 2, QTableWidgetItem(reminder['message']))

    def add_reminder(self):
        """Abre o diálogo para adicionar um novo lembrete."""
        dialog = EditReminderDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            new_date, new_message = dialog.get_data()
            if not self.validate_reminder(new_date, new_message):
                return
            # Inserir no banco de dados
            with sqlite3.connect("data.db") as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO reminders (date, message) VALUES (?, ?)",
                    (new_date, new_message)
                )
                conn.commit()
                new_id = cursor.lastrowid
            # Atualizar a estrutura de lembretes
            self.reminders[new_id] = {"date": new_date, "message": new_message}
            # Salvar e recarregar a tabela
            self.save_reminders_callback(self.reminders)
            self.load_reminders()

    def edit_reminder(self):
        """Abre o diálogo para editar o lembrete selecionado."""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Aviso", "Selecione um lembrete para editar.")
            return

        reminder_id = int(self.table.item(selected_row, 0).text())
        reminder = self.reminders.get(reminder_id, {})
        if not reminder:
            QMessageBox.warning(self, "Erro", "Lembrete não encontrado.")
            return

        dialog = EditReminderDialog(reminder['date'], reminder['message'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            new_date, new_message = dialog.get_data()
            if not self.validate_reminder(new_date, new_message):
                return
            # Atualizar no banco de dados
            with sqlite3.connect("data.db") as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE reminders SET date = ?, message = ? WHERE id = ?",
                    (new_date, new_message, reminder_id)
                )
                conn.commit()
            # Atualizar a estrutura de lembretes
            self.reminders[reminder_id] = {"date": new_date, "message": new_message}
            # Salvar e recarregar a tabela
            self.save_reminders_callback(self.reminders)
            self.load_reminders()

    def delete_reminder(self):
        """Exclui o lembrete selecionado."""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Aviso", "Selecione um lembrete para excluir.")
            return

        reminder_id = int(self.table.item(selected_row, 0).text())
        reminder = self.reminders.get(reminder_id, {})
        if not reminder:
            QMessageBox.warning(self, "Erro", "Lembrete não encontrado.")
            return

        reply = QMessageBox.question(
            self, "Confirmação", f"Tem certeza de que deseja excluir o lembrete de {reminder['date']}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # Excluir do banco de dados
            with sqlite3.connect("data.db") as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
                conn.commit()
            # Atualizar a estrutura de lembretes
            del self.reminders[reminder_id]
            # Salvar e recarregar a tabela
            self.save_reminders_callback(self.reminders)
            self.load_reminders()

    def validate_reminder(self, date_str, message):
        """Valida os dados do lembrete."""
        if not date_str or not message:
            QMessageBox.warning(self, "Dados Inválidos", "Data e mensagem não podem estar vazias.")
            return False
        # Verificar se a data é válida
        date = QDate.fromString(date_str, "yyyy-MM-dd")
        if not date.isValid():
            QMessageBox.warning(self, "Formato Inválido", "A data selecionada não é válida.")
            return False
        return True

class EditReminderDialog(QDialog):
    """Diálogo para adicionar ou editar um lembrete."""

    def __init__(self, date="", message="", parent=None):
        """
        Inicializa o EditReminderDialog.

        Args:
            date (str, optional): Data do lembrete no formato 'yyyy-MM-dd'.
            message (str, optional): Mensagem do lembrete.
            parent (QWidget, optional): Widget pai.
        """
        super().__init__(parent)
        self.setWindowTitle("Editar Lembrete")
        self.layout = QVBoxLayout(self)

        # Layout para data
        date_layout = QHBoxLayout()
        self.date_label = QLabel("Data:", self)
        date_layout.addWidget(self.date_label)

        self.calendar = QCalendarWidget(self)
        self.calendar.setGridVisible(True)
        self.calendar.setMaximumDate(QDate(9999, 12, 31))  # Definir data máxima, se necessário
        self.calendar.setMinimumDate(QDate(1900, 1, 1))    # Definir data mínima, se necessário
        if date:
            parsed_date = QDate.fromString(date, "yyyy-MM-dd")
            if parsed_date.isValid():
                self.calendar.setSelectedDate(parsed_date)
        else:
            self.calendar.setSelectedDate(QDate.currentDate())
        date_layout.addWidget(self.calendar)
        self.layout.addLayout(date_layout)

        # Campo de mensagem
        self.message_input = QLineEdit(self)
        self.message_input.setPlaceholderText("Mensagem do lembrete")
        self.message_input.setText(message)
        form_layout = QFormLayout()
        form_layout.addRow("Mensagem:", self.message_input)
        self.layout.addLayout(form_layout)

        # Botões de ação
        self.buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Salvar", self)
        self.save_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancelar", self)
        self.cancel_button.clicked.connect(self.reject)
        self.buttons_layout.addWidget(self.save_button)
        self.buttons_layout.addWidget(self.cancel_button)
        self.layout.addLayout(self.buttons_layout)

    def get_data(self):
        """Retorna os dados inseridos pelo usuário."""
        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        message = self.message_input.text().strip()
        return selected_date, message

# Como usar este módulo no seu app principal:
# 1. Importe o ReminderManager.
# 2. Passe os lembretes e a função de salvar lembretes como parâmetros.
#
# Exemplo:
# manager = ReminderManager(self.reminders, self.save_reminders)
# manager.exec_()

