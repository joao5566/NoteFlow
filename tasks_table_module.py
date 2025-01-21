# tasks_table_widget.py

import sys
import sqlite3
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLineEdit, QPushButton,
    QHBoxLayout, QLabel, QHeaderView, QMessageBox, QComboBox, QCheckBox
)
#from PyQt5.QtCore import Qt
from PyQt5.QtCore import Qt, QDate

from PyQt5.QtGui import QColor

DB_PATH = "data.db"

class TasksTableWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = {}  # Dicionário de tarefas: {id: {"name": ..., "completed": ..., "creation_date": ...}}
        self.filtered_tasks = {}
        self.current_page = 0
        self.tasks_per_page = 10

        self.init_ui()
        self.refresh_tasks()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Área superior com busca e botões
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Buscar:", self))
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Buscar tarefas...")
        self.search_input.textChanged.connect(self.filter_tasks)
        top_layout.addWidget(self.search_input)

        top_buttons_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Atualizar Tabela", self)
        self.refresh_button.clicked.connect(self.refresh_tasks)
        top_buttons_layout.addWidget(self.refresh_button)

        self.delete_button = QPushButton("Excluir Tarefa(s)", self)
        self.delete_button.clicked.connect(self.delete_selected_tasks)
        top_buttons_layout.addWidget(self.delete_button)

        top_layout.addLayout(top_buttons_layout)
        main_layout.addLayout(top_layout)

        # Tabela de tarefas
        self.tasks_table = QTableWidget(self)
        self.tasks_table.setColumnCount(4)  # ID, Tarefa, Concluída, Data de Criação
        self.tasks_table.setHorizontalHeaderLabels(["ID", "Tarefa", "Concluída", "Data de Criação"])
        self.tasks_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tasks_table.setWordWrap(True)
        self.tasks_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tasks_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Evitar edição direta
        main_layout.addWidget(self.tasks_table)

        # Ocultar a coluna "ID"
        self.tasks_table.setColumnHidden(0, True)

        # Ajuste automático das colunas
        self.tasks_table.resizeColumnsToContents()

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

        # Seletor de quantidade de tarefas por página
        tasks_per_page_layout = QHBoxLayout()
        tasks_per_page_label = QLabel("Tarefas por página:", self)
        tasks_per_page_layout.addWidget(tasks_per_page_label)

        self.tasks_per_page_selector = QComboBox(self)
        self.tasks_per_page_selector.addItems(["10", "25", "50", "100"])
        self.tasks_per_page_selector.setCurrentText(str(self.tasks_per_page))
        self.tasks_per_page_selector.currentIndexChanged.connect(self.change_tasks_per_page)
        tasks_per_page_layout.addWidget(self.tasks_per_page_selector)

        main_layout.addLayout(tasks_per_page_layout)

    def load_tasks(self):
        """Carrega as tarefas do banco de dados para exibição na tabela."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, completed, creation_date FROM tasks")
                rows = cursor.fetchall()

            self.tasks = {
                row[0]: {
                    "name": row[1],
                    "completed": bool(row[2]),
                    "creation_date": row[3]
                }
                for row in rows
            }
            self.filtered_tasks = self.tasks.copy()
            self.update_tasks_table()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Erro de Banco de Dados", f"Ocorreu um erro ao carregar as tarefas: {e}")

    def filter_tasks(self):
        """Filtra as tarefas com base no texto de busca."""
        query = self.search_input.text().lower()

        if query:
            self.filtered_tasks = {
                task_id: task for task_id, task in self.tasks.items()
                if query in task["name"].lower() or query in task["creation_date"].lower()
            }
        else:
            self.filtered_tasks = self.tasks.copy()

        self.current_page = 0
        self.update_tasks_table()

    def update_tasks_table(self):
        """Atualiza a tabela de tarefas com base na página atual."""
        self.tasks_table.setRowCount(0)
        start_index = self.current_page * self.tasks_per_page
        end_index = start_index + self.tasks_per_page
        tasks_to_display = list(self.filtered_tasks.items())[start_index:end_index]

        for task_id, task in tasks_to_display:
            row = self.tasks_table.rowCount()
            self.tasks_table.insertRow(row)

            # Coluna ID (oculta)
            id_item = QTableWidgetItem(str(task_id))
            id_item.setFlags(id_item.flags() ^ Qt.ItemIsEditable)
            self.tasks_table.setItem(row, 0, id_item)

            # Coluna Tarefa
            task_item = QTableWidgetItem(task["name"])
            task_item.setFlags(task_item.flags() ^ Qt.ItemIsEditable)
            if task["completed"]:
                task_item.setForeground(QColor("gray"))
                font = task_item.font()
                font.setStrikeOut(True)
                task_item.setFont(font)
            self.tasks_table.setItem(row, 1, task_item)

            # Coluna Concluída
            completed_checkbox = QCheckBox(self)
            completed_checkbox.setChecked(task["completed"])
            completed_checkbox.stateChanged.connect(self.update_task_completion)
            # Armazenar o ID da tarefa no checkbox para referência
            completed_checkbox.task_id = task_id
            self.tasks_table.setCellWidget(row, 2, completed_checkbox)

            # Coluna Data de Criação
            date_item = QTableWidgetItem(task["creation_date"])
            date_item.setFlags(date_item.flags() ^ Qt.ItemIsEditable)
            self.tasks_table.setItem(row, 3, date_item)

        self.update_pagination_controls()

    def update_pagination_controls(self):
        """Atualiza os controles de paginação."""
        total_tasks = len(self.filtered_tasks)
        total_pages = max(1, (total_tasks + self.tasks_per_page - 1) // self.tasks_per_page)
        self.page_label.setText(f"Página {self.current_page + 1} de {total_pages}")
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled((self.current_page + 1) * self.tasks_per_page < total_tasks)

    def prev_page(self):
        """Vai para a página anterior."""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_tasks_table()

    def next_page(self):
        """Vai para a próxima página."""
        if (self.current_page + 1) * self.tasks_per_page < len(self.filtered_tasks):
            self.current_page += 1
            self.update_tasks_table()

    def change_tasks_per_page(self):
        """Altera a quantidade de tarefas exibidas por página com base na seleção do usuário."""
        self.tasks_per_page = int(self.tasks_per_page_selector.currentText())
        self.current_page = 0
        self.update_tasks_table()

    def refresh_tasks(self):
        """Recarrega as tarefas do banco de dados e atualiza a tabela."""
        self.load_tasks()

    def delete_selected_tasks(self):
        """Exclui as tarefas selecionadas na tabela e remove do banco de dados."""
        selected_rows = set(index.row() for index in self.tasks_table.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "Nenhuma tarefa selecionada", "Por favor, selecione ao menos uma tarefa para excluir.")
            return

        # Confirmar exclusão
        reply = QMessageBox.question(
            self, "Confirmação",
            "Tem certeza de que deseja excluir as tarefas selecionadas?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        # Coletar IDs das tarefas selecionadas
        task_ids_to_delete = []
        for row in selected_rows:
            id_item = self.tasks_table.item(row, 0)
            if id_item:
                task_id = int(id_item.text())
                task_ids_to_delete.append(task_id)

        if not task_ids_to_delete:
            QMessageBox.warning(self, "Erro", "Não foi possível identificar as tarefas selecionadas.")
            return

        # Excluir as tarefas do banco de dados
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.executemany("DELETE FROM tasks WHERE id = ?", [(task_id,) for task_id in task_ids_to_delete])
                conn.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Erro de Banco de Dados", f"Ocorreu um erro ao excluir as tarefas: {e}")
            return

        # Remover as tarefas da estrutura de dados
        for task_id in task_ids_to_delete:
            if task_id in self.tasks:
                del self.tasks[task_id]

        QMessageBox.information(self, "Tarefas Excluídas", "As tarefas selecionadas foram excluídas com sucesso.")
        self.refresh_tasks()

    def update_task_completion(self, state):
        """Atualiza o status de conclusão da tarefa no banco de dados."""
        checkbox = self.sender()
        if not hasattr(checkbox, 'task_id'):
            return

        task_id = checkbox.task_id
        new_status = (state == Qt.Checked)

        # Atualizar o status na estrutura de dados
        if task_id in self.tasks:
            self.tasks[task_id]['completed'] = new_status
            if new_status:
                self.tasks[task_id]['completion_date'] = QDate.currentDate().toString("yyyy-MM-dd")
            else:
                self.tasks[task_id]['completion_date'] = None
        else:
            QMessageBox.warning(self, "Erro", "Tarefa não encontrada.")
            return

        # Atualizar o banco de dados
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE tasks SET completed = ?, completion_date = ? WHERE id = ?",
                    (int(new_status), self.tasks[task_id]['completion_date'], task_id)
                )
                conn.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Erro de Banco de Dados", f"Ocorreu um erro ao atualizar a tarefa: {e}")
            return

        # Recarregar a tabela para refletir as mudanças de estilo
        self.load_tasks()

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = TasksTableWidget()
    window.show()
    sys.exit(app.exec_())

