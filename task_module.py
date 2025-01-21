# task_module.py

import json
import sqlite3  # Importação adicionada
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QLabel, QLineEdit, QCheckBox, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView, QDateEdit
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor

from persistence_module import DB_PATH  # Importação adicionada

class TaskManager(QDialog):
    """Diálogo para gerenciar múltiplas tarefas diárias."""
    
    def __init__(self, tasks, save_tasks_callback, parent=None):
        """
        Inicializa o TaskManager.

        Args:
            tasks (dict): Dicionário de tarefas onde a chave é o ID e o valor é um dict com 'name', 'completed', 'creation_date', 'completion_date'.
            save_tasks_callback (function): Função de callback para salvar tarefas após alterações.
            parent (QWidget, optional): Widget pai.
        """
        super().__init__(parent)
        self.setWindowTitle("Gerenciar Tarefas Diárias")
        self.resize(600, 400)
        self.tasks = tasks  # Dicionário: {id: {"name": ..., "completed": ..., "creation_date": ..., "completion_date": ...}}
        self.save_tasks_callback = save_tasks_callback
        self.init_ui()

    def init_ui(self):
        """Inicializa os componentes da interface."""
        self.layout = QVBoxLayout(self)

        # Botão para selecionar data
        choose_date_button = QPushButton("Selecionar Data", self)
        choose_date_button.clicked.connect(self.choose_date)
        self.layout.addWidget(choose_date_button)

        # Tabela de tarefas
        self.task_table = QTableWidget(self)
        self.task_table.setColumnCount(3)  # ID, Tarefa, Concluída
        self.task_table.setHorizontalHeaderLabels(["ID", "Tarefa", "Concluída"])
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.task_table.setColumnHidden(0, True)  # Ocultar a coluna "ID"
        self.task_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.task_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Evitar edição direta
        self.layout.addWidget(self.task_table)
        self.load_tasks()

        # Campo de entrada para nova tarefa
        self.add_task_input = QLineEdit(self)
        self.add_task_input.setPlaceholderText("Digite uma nova tarefa...")
        self.layout.addWidget(self.add_task_input)

        # Botões de ação (Adicionar, Excluir)
        button_layout = QHBoxLayout()
        add_task_button = QPushButton("Adicionar Tarefa", self)
        add_task_button.clicked.connect(self.add_task)
        button_layout.addWidget(add_task_button)

        delete_task_button = QPushButton("Apagar Tarefas Concluídas", self)
        delete_task_button.clicked.connect(self.delete_completed_tasks)
        button_layout.addWidget(delete_task_button)

        self.layout.addLayout(button_layout)

    def load_tasks(self, selected_date=None):
        """Carrega as tarefas para a data selecionada (ou o dia atual, se nenhuma data for passada)."""
        self.task_table.setRowCount(0)

        if selected_date is None:
            selected_date = QDate.currentDate().toString("yyyy-MM-dd")
        for task_id, task in self.tasks.items():
            if task['creation_date'] != selected_date:
                continue

            row = self.task_table.rowCount()
            self.task_table.insertRow(row)

            # Coluna ID (oculta)
            self.task_table.setItem(row, 0, QTableWidgetItem(str(task_id)))

            # Coluna Tarefa
            task_item = QTableWidgetItem(task['name'])
            if task['completed']:
                task_item.setForeground(QColor("gray"))
                font = task_item.font()
                font.setStrikeOut(True)
                task_item.setFont(font)
            self.task_table.setItem(row, 1, task_item)

            # Coluna Concluída
            checkbox = QCheckBox(self)
            checkbox.setChecked(task['completed'])
            checkbox.stateChanged.connect(self.update_task_completion)
            self.task_table.setCellWidget(row, 2, checkbox)

    def add_task(self):
        """Adiciona uma nova tarefa."""
        task_name = self.add_task_input.text().strip()

        if not task_name:
            QMessageBox.warning(self, "Entrada inválida", "O nome da tarefa não pode estar vazio.")
            return

        # Permitir tarefas com nomes duplicados; identificar por ID
        creation_date = QDate.currentDate().toString("yyyy-MM-dd")

        # Inserir no banco de dados e obter o ID gerado
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO tasks (name, completed, creation_date, completion_date) VALUES (?, ?, ?, ?)",
                    (task_name, 0, creation_date, None)
                )
                conn.commit()
                new_id = cursor.lastrowid
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Erro de Banco de Dados", f"Ocorreu um erro ao adicionar a tarefa: {e}")
            return

        # Atualizar a estrutura de tarefas
        self.tasks[new_id] = {
            "name": task_name,
            "completed": False,
            "creation_date": creation_date,
            "completion_date": None
        }

        # Salvar e recarregar a tabela
        self.save_tasks_callback(self.tasks)
        self.load_tasks()
        self.add_task_input.clear()

    def update_task_completion(self, state):
        """Atualiza o status de conclusão da tarefa."""
        # Obter a célula onde a mudança ocorreu
        checkbox = self.sender()
        if checkbox is None:
            return

        # Encontrar a linha onde o checkbox está
        for row in range(self.task_table.rowCount()):
            widget = self.task_table.cellWidget(row, 2)
            if widget == checkbox:
                task_id_item = self.task_table.item(row, 0)
                if task_id_item is None:
                    return
                task_id = int(task_id_item.text())
                break
        else:
            return  # Checkbox não encontrado

        # Atualizar o status da tarefa
        self.tasks[task_id]['completed'] = (state == Qt.Checked)

        # Atualizar a data de conclusão se necessário
        if self.tasks[task_id]['completed']:
            self.tasks[task_id]['completion_date'] = QDate.currentDate().toString("yyyy-MM-dd")
        else:
            self.tasks[task_id]['completion_date'] = None

        # Salvar as tarefas atualizadas
        self.save_tasks_callback(self.tasks)

        # Recarregar a tabela para refletir as mudanças de estilo
        self.load_tasks()

    def delete_completed_tasks(self):
        """Exclui todas as tarefas concluídas."""
        completed_tasks = [task_id for task_id, task in self.tasks.items() if task['completed']]
        if not completed_tasks:
            QMessageBox.information(self, "Info", "Não há tarefas concluídas para apagar.")
            return

        # Confirmar exclusão
        reply = QMessageBox.question(
            self, "Confirmação",
            "Tem certeza de que deseja excluir todas as tarefas concluídas?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        # Excluir do banco de dados
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.executemany("DELETE FROM tasks WHERE id = ?", [(task_id,) for task_id in completed_tasks])
                conn.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Erro de Banco de Dados", f"Ocorreu um erro ao excluir as tarefas: {e}")
            return

        # Remover da estrutura de tarefas
        for task_id in completed_tasks:
            del self.tasks[task_id]

        # Salvar e recarregar a tabela
        self.save_tasks_callback(self.tasks)
        self.load_tasks()

    def choose_date(self):
        """Permite ao usuário escolher uma data para exibir as tarefas."""
        date_dialog = QDialog(self)
        date_dialog.setWindowTitle("Selecionar Data")
        layout = QVBoxLayout(date_dialog)

        date_edit = QDateEdit(date_dialog)
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.currentDate())
        layout.addWidget(date_edit)

        button_box = QHBoxLayout()
        ok_button = QPushButton("OK", date_dialog)
        ok_button.clicked.connect(lambda: date_dialog.accept())
        button_box.addWidget(ok_button)

        cancel_button = QPushButton("Cancelar", date_dialog)
        cancel_button.clicked.connect(lambda: date_dialog.reject())
        button_box.addWidget(cancel_button)

        layout.addLayout(button_box)

        if date_dialog.exec_() == QDialog.Accepted:
            selected_date_str = date_edit.date().toString("yyyy-MM-dd")
            self.load_tasks(selected_date_str)

