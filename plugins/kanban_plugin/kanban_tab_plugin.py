# kanban_plugin_tab.py
from plugin_base import PluginTab
from PyQt5.QtWidgets import (
    QApplication, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QWidget, QTabWidget, QInputDialog, QMessageBox,
    QLineEdit, QComboBox, QFileDialog, QCalendarWidget, QDialog, QTextEdit,
    QColorDialog, QScrollArea, QCheckBox, QToolButton, QAction, QMenu, QMenuBar,
    QTextBrowser
)
from PyQt5.QtCore import Qt, QDate, QMimeData, QSize, pyqtSignal
from PyQt5.QtGui import QFont, QDrag, QPixmap, QIcon
import sys, csv, json, sqlite3, markdown

#########################################
# Classes auxiliares do Kanban (adaptadas)
#########################################

class ClickableTextBrowser(QTextBrowser):
    """QTextBrowser que emite um sinal ao detectar um duplo clique."""
    doubleClicked = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.IBeamCursor)
    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)

class DatabaseManager:
    """Gerenciador de banco de dados SQLite para o aplicativo Kanban."""
    def __init__(self, db_name="kanban.db"):
        self.db_name = db_name
        self.create_tables()
    def connect(self):
        return sqlite3.connect(self.db_name)
    def create_tables(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS boards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS columns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    board_id INTEGER,
                    name TEXT NOT NULL,
                    UNIQUE(board_id, name),
                    FOREIGN KEY(board_id) REFERENCES boards(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    column_id INTEGER,
                    description TEXT NOT NULL,
                    priority TEXT,
                    due_date TEXT,
                    color TEXT,
                    text_color TEXT,
                    FOREIGN KEY(column_id) REFERENCES columns(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS checklists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER,
                    item TEXT,
                    checked BOOLEAN,
                    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
                )
            """)
            conn.commit()
    def add_board(self, name):
        with self.connect() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO boards (name) VALUES (?)", (name,))
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None
    def remove_board(self, board_id):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM boards WHERE id = ?", (board_id,))
            conn.commit()
    def get_board_id(self, name):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM boards WHERE name = ?", (name,))
            result = cursor.fetchone()
            return result[0] if result else None
    def get_boards(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM boards")
            return cursor.fetchall()
    def add_column(self, board_id, name):
        with self.connect() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO columns (board_id, name) VALUES (?, ?)", (board_id, name))
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None
    def remove_column(self, column_id):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM columns WHERE id = ?", (column_id,))
            conn.commit()
    def get_columns(self, board_id):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM columns WHERE board_id = ?", (board_id,))
            return cursor.fetchall()
    def add_task(self, column_id, description, priority, due_date, color, text_color):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (column_id, description, priority, due_date, color, text_color)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (column_id, description, priority, due_date, color, text_color))
            task_id = cursor.lastrowid
            conn.commit()
            return task_id
    def add_checklist_item(self, task_id, item, checked=False):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO checklists (task_id, item, checked) VALUES (?, ?, ?)", (task_id, item, checked))
            conn.commit()
    def get_tasks_by_column(self, column_id):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, description, priority, due_date, color, text_color FROM tasks
                WHERE column_id = ?
            """, (column_id,))
            tasks = cursor.fetchall()
            task_list = []
            for task in tasks:
                task_id, description, priority, due_date, color, text_color = task
                cursor.execute("SELECT item, checked FROM checklists WHERE task_id = ?", (task_id,))
                checklist = [{'item': row[0], 'checked': bool(row[1])} for row in cursor.fetchall()]
                task_list.append({
                    'id': task_id,
                    'description': description,
                    'priority': priority,
                    'due_date': due_date,
                    'color': color,
                    'text_color': text_color,
                    'checklist': checklist
                })
            return task_list
    def get_task(self, task_id):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, description, priority, due_date, color, text_color FROM tasks
                WHERE id = ?
            """, (task_id,))
            task = cursor.fetchone()
            if task:
                task_id, description, priority, due_date, color, text_color = task
                cursor.execute("SELECT item, checked FROM checklists WHERE task_id = ?", (task_id,))
                checklist = [{'item': row[0], 'checked': bool(row[1])} for row in cursor.fetchall()]
                return {
                    'id': task_id,
                    'description': description,
                    'priority': priority,
                    'due_date': due_date,
                    'color': color,
                    'text_color': text_color,
                    'checklist': checklist
                }
            return None
    def update_task(self, task_id, description, priority, due_date, color, text_color):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tasks
                SET description = ?, priority = ?, due_date = ?, color = ?, text_color = ?
                WHERE id = ?
            """, (description, priority, due_date, color, text_color, task_id))
            conn.commit()
    def update_task_column(self, task_id, new_column_id):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE tasks SET column_id = ? WHERE id = ?", (new_column_id, task_id))
            conn.commit()
    def delete_task(self, task_id):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
    def update_checklist(self, task_id, checklist):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM checklists WHERE task_id = ?", (task_id,))
            for item in checklist:
                cursor.execute("INSERT INTO checklists (task_id, item, checked) VALUES (?, ?, ?)", (task_id, item['item'], item['checked']))
            conn.commit()

#########################################
# Widgets do Kanban
#########################################

class TaskWidget(QWidget):
    """Representa uma única tarefa no Kanban."""
    checklist_changed = pyqtSignal(int, list)  # task_id, updated checklist
    def __init__(self, task_id, description, priority, due_date, checklist=None,
                 color="#ccffcc", text_color="#000000", parent=None, font=None):
        super().__init__(parent)
        self.task_id = task_id
        self.description = description
        self.priority = priority
        self.due_date = due_date
        self.checklist = checklist if checklist is not None else []
        self.color = color
        self.text_color = text_color
        self.font = font or QFont("Arial", 14)
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.description_browser = ClickableTextBrowser()
        self.description_browser.setReadOnly(True)
        self.description_browser.setOpenExternalLinks(True)
        self.description_browser.setStyleSheet(f"color: {self.text_color}; background-color: transparent;")
        self.description_browser.setFont(self.font)
        self.set_description(self.description)
        layout.addWidget(self.description_browser)
        self.description_browser.doubleClicked.connect(self.handle_double_click)
        self.checklist_layout = QVBoxLayout()
        self.checklist_widgets = []
        for item in self.checklist:
            cb = QCheckBox(item['item'])
            cb.setChecked(item['checked'])
            cb.setFont(self.font)
            cb.setStyleSheet(f"color: {self.text_color};")
            cb.stateChanged.connect(self.update_checklist_status)
            self.checklist_layout.addWidget(cb)
            self.checklist_widgets.append(cb)
        layout.addLayout(self.checklist_layout)
        info_layout = QHBoxLayout()
        self.priority_label = QLabel(f"Prioridade: {self.priority}")
        self.priority_label.setStyleSheet(f"color: {self.text_color};")
        self.priority_label.setFont(self.font)
        info_layout.addWidget(self.priority_label)
        self.due_date_label = QLabel(f"Prazo: {self.due_date}")
        self.due_date_label.setStyleSheet(f"color: {self.text_color};")
        self.due_date_label.setFont(self.font)
        info_layout.addWidget(self.due_date_label)
        layout.addLayout(info_layout)
        buttons_layout = QHBoxLayout()
        self.edit_button = QPushButton("Editar")
        self.edit_button.setFont(self.font)
        self.edit_button.clicked.connect(self.confirm_edit)
        buttons_layout.addWidget(self.edit_button)
        self.delete_button = QToolButton()
        self.delete_button.setText("✖")
        self.delete_button.setToolTip("Excluir Tarefa")
        self.delete_button.setStyleSheet("""
            QToolButton { border: none; color: red; font-weight: bold; font-size: 16px; }
            QToolButton:hover { color: darkred; }
        """)
        self.delete_button.clicked.connect(self.confirm_delete)
        buttons_layout.addWidget(self.delete_button)
        layout.addLayout(buttons_layout)
        self.update_color()
    def set_description(self, markdown_text):
        html = markdown.markdown(markdown_text)
        self.description_browser.setHtml(html)
    def handle_double_click(self):
        parent_list = self.parent()
        while parent_list and not hasattr(parent_list, "edit_task_by_id"):
            parent_list = parent_list.parent()
        if parent_list and hasattr(parent_list, "edit_task_by_id"):
            parent_list.edit_task_by_id(self.task_id)
    def confirm_edit(self):
        parent_list = self.parent()
        while parent_list and not hasattr(parent_list, "edit_task_by_id"):
            parent_list = parent_list.parent()
        if parent_list and hasattr(parent_list, "edit_task_by_id"):
            parent_list.edit_task_by_id(self.task_id)
    def update_checklist_status(self):
        self.checklist = [{'item': cb.text(), 'checked': cb.isChecked()} for cb in self.checklist_widgets]
        self.checklist_changed.emit(self.task_id, self.checklist)
    def update_color(self):
        self.setStyleSheet(f"background-color: {self.color}; border: 1px solid #000000; border-radius: 5px;")
    def update_text_color(self, new_color):
        self.text_color = new_color
        self.description_browser.setStyleSheet(f"color: {self.text_color}; background-color: transparent;")
        self.priority_label.setStyleSheet(f"color: {self.text_color};")
        self.due_date_label.setStyleSheet(f"color: {self.text_color};")
        for cb in self.checklist_widgets:
            cb.setStyleSheet(f"color: {self.text_color};")
    def set_font(self, font):
        self.font = font
        self.description_browser.setFont(self.font)
        self.priority_label.setFont(self.font)
        self.due_date_label.setFont(self.font)
        for cb in self.checklist_widgets:
            cb.setFont(self.font)
    def sizeHint(self):
        fixed_width = 430
        self.setFixedWidth(fixed_width)
        self.description_browser.setFixedWidth(fixed_width - 20)
        checklist_height = sum(cb.sizeHint().height() for cb in self.checklist_widgets)
        height = self.description_browser.sizeHint().height() + checklist_height + \
                 self.priority_label.sizeHint().height() + self.due_date_label.sizeHint().height() + 60
        return QSize(fixed_width, height)
    def confirm_delete(self):
        reply = QMessageBox.question(
            self, 'Confirmar Exclusão',
            "Tem certeza que deseja excluir esta tarefa?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            parent_list = self.parent()
            while parent_list and not hasattr(parent_list, "delete_task"):
                parent_list = parent_list.parent()
            if parent_list and hasattr(parent_list, "delete_task"):
                parent_list.delete_task(self.task_id)
    def clear_checklist(self):
        while self.checklist_layout.count():
            child = self.checklist_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.checklist_widgets = []

class TaskListWidget(QListWidget):
    """Lista de tarefas dentro de uma coluna Kanban."""
    def __init__(self, parent=None, kanban_board=None, column_id=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QListWidget.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.kanban_board = kanban_board
        self.column_id = column_id
        self.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ccc;")
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setSpacing(5)
        self.setUniformItemSizes(False)
        self.itemDoubleClicked.connect(self.on_item_double_clicked)
    def on_item_double_clicked(self, item):
        self.edit_task(item)
    def edit_task_by_id(self, task_id):
        for i in range(self.count()):
            item = self.item(i)
            if getattr(item, 'task_id', None) == task_id:
                self.edit_task(item)
                break
    def edit_task(self, item):
        task_widget = self.itemWidget(item)
        if not task_widget:
            return
        self.kanban_board.edit_task_dialog(self, task_widget, item)
    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item:
            task_widget = self.itemWidget(item)
            if task_widget:
                mimeData = QMimeData()
                task_id = getattr(item, 'task_id', None)
                if task_id is None:
                    QMessageBox.warning(self, "Erro", "ID da tarefa não encontrado.")
                    return
                task_data = {'task_id': task_id}
                json_data = json.dumps(task_data)
                mimeData.setData('application/x-task', json_data.encode('utf-8'))
                drag = QDrag(self)
                drag.setMimeData(mimeData)
                pixmap = task_widget.grab()
                drag.setPixmap(pixmap)
                if drag.exec_(Qt.MoveAction):
                    self.takeItem(self.row(item))
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('application/x-task'):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)
    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat('application/x-task'):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)
    def dropEvent(self, event):
        if event.mimeData().hasFormat('application/x-task'):
            json_data = event.mimeData().data('application/x-task').data().decode('utf-8')
            task_data = json.loads(json_data)
            task_id = task_data.get('task_id')
            if task_id is None:
                QMessageBox.warning(self, "Erro", "ID da tarefa não encontrado nos dados.")
                return
            self.kanban_board.db.update_task_column(task_id, self.column_id)
            task = self.kanban_board.db.get_task(task_id)
            if task:
                self.add_task_from_db(task)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
    def add_task_from_db(self, task):
        task_widget = TaskWidget(
            task_id=task['id'],
            description=task['description'],
            priority=task['priority'],
            due_date=task['due_date'],
            checklist=task['checklist'],
            color=task['color'],
            text_color=task['text_color'],
            font=self.kanban_board.default_font
        )
        task_widget.checklist_changed.connect(self.on_checklist_changed)
        list_item = QListWidgetItem(self)
        list_item.setSizeHint(task_widget.sizeHint())
        list_item.task_id = task['id']
        self.addItem(list_item)
        self.setItemWidget(list_item, task_widget)
    def on_checklist_changed(self, task_id, updated_checklist):
        self.kanban_board.db.update_checklist(task_id, updated_checklist)
    def delete_task(self, task_id):
        self.kanban_board.db.delete_task(task_id)
        for i in range(self.count()):
            item = self.item(i)
            if getattr(item, 'task_id', None) == task_id:
                self.takeItem(i)
                break

class KanbanBoard(QWidget):
    """Representa um único quadro Kanban."""
    def __init__(self, board_name, board_id=None, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.default_font = QFont("Arial", 14)
        self.db = DatabaseManager()
        if board_id is None:
            board_id = self.db.get_board_id(board_name)
            if board_id is None:
                board_id = self.db.add_board(board_name)
        self.board_id = board_id
        self.menu_bar = QMenuBar(self)
        self.file_menu = QMenu("Arquivo", self)
        self.task_menu = QMenu("Tarefas", self)
        self.view_menu = QMenu("Visualizar", self)
        self.menu_bar.addMenu(self.file_menu)
        self.menu_bar.addMenu(self.task_menu)
        self.menu_bar.addMenu(self.view_menu)
        export_action = QAction("Exportar Tarefas (CSV)", self)
        export_action.triggered.connect(self.export_tasks)
        self.file_menu.addAction(export_action)
        import_action = QAction("Importar Tarefas (CSV)", self)
        import_action.triggered.connect(self.import_tasks)
        self.file_menu.addAction(import_action)
        add_column_action = QAction("Adicionar Coluna", self)
        add_column_action.triggered.connect(self.add_column_dialog)
        self.task_menu.addAction(add_column_action)
        self.layout.setMenuBar(self.menu_bar)
        buttons_layout = QHBoxLayout()
        self.add_task_button = QPushButton("Adicionar Tarefa", self)
        self.add_task_button.setFont(self.default_font)
        self.add_task_button.clicked.connect(self.add_task)
        buttons_layout.addWidget(self.add_task_button)
        self.add_column_button = QPushButton("Adicionar Coluna", self)
        self.add_column_button.setFont(self.default_font)
        self.add_column_button.clicked.connect(self.add_column_dialog)
        buttons_layout.addWidget(self.add_column_button)
        self.layout.addLayout(buttons_layout)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QHBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(20)
        self.scroll_layout.setContentsMargins(10, 10, 10, 10)
        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)
        self.columns = {}
        columns = self.db.get_columns(self.board_id)
        if not columns:
            for title in ["A Fazer", "Fazendo", "Concluído"]:
                self.add_column(title)
        else:
            for column in columns:
                column_id, title = column
                self.add_column(title, column_id)
        self.apply_default_font()
    def apply_default_font(self):
        for column in self.columns.values():
            column["label"].setFont(self.default_font)
            column["list"].setFont(self.default_font)
            for i in range(column["list"].count()):
                list_item = column["list"].item(i)
                task_widget = column["list"].itemWidget(list_item)
                if task_widget:
                    task_widget.set_font(self.default_font)
    def add_column(self, title, column_id=None):
        if title in self.columns:
            QMessageBox.warning(self, "Aviso", "Coluna já existe!")
            return
        if column_id is None:
            column_id = self.db.add_column(self.board_id, title)
            if column_id is None:
                QMessageBox.warning(self, "Aviso", f"A coluna '{title}' já existe no banco de dados.")
                return
        column_layout = QVBoxLayout()
        column_widget = QWidget()
        column_widget.setLayout(column_layout)
        column_widget.setFixedWidth(450)
        header_layout = QHBoxLayout()
        title_label = QLabel(title, self)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        title_label.setFont(self.default_font)
        header_layout.addWidget(title_label)
        delete_column_button = QToolButton()
        delete_column_button.setText("✖")
        delete_column_button.setToolTip(f"Excluir Coluna '{title}'")
        delete_column_button.setStyleSheet("""
            QToolButton { border: none; color: red; font-weight: bold; font-size: 16px; }
            QToolButton:hover { color: darkred; }
        """)
        delete_column_button.clicked.connect(lambda: self.remove_column(title, column_id))
        header_layout.addWidget(delete_column_button)
        column_layout.addLayout(header_layout)
        task_list = TaskListWidget(self.scroll_content, kanban_board=self, column_id=column_id)
        column_layout.addWidget(task_list)
        self.columns[title] = {"widget": column_widget, "list": task_list, "label": title_label, "id": column_id}
        self.scroll_layout.addWidget(column_widget)
        tasks = self.db.get_tasks_by_column(column_id)
        for task in tasks:
            task_list.add_task_from_db(task)
    def add_column_dialog(self):
        column_name, ok = QInputDialog.getText(self, "Nova Coluna", "Nome da Coluna:")
        if ok and column_name.strip():
            self.add_column(column_name.strip())
    def remove_column(self, title, column_id):
        reply = QMessageBox.question(
            self, 'Confirmação',
            f"Tem certeza que deseja excluir a coluna '{title}' e todas as suas tarefas?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.remove_column(column_id)
            column = self.columns.pop(title)
            column["widget"].deleteLater()
    def add_task(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Adicionar Tarefa")
        dialog.resize(600, 800)
        layout = QVBoxLayout(dialog)
        column_label = QLabel("Selecionar Coluna:")
        column_label.setFont(self.default_font)
        layout.addWidget(column_label)
        column_selector = QComboBox()
        column_selector.setFont(self.default_font)
        column_names = list(self.columns.keys())
        column_selector.addItems(column_names)
        layout.addWidget(column_selector)
        description_label = QLabel("Descrição da Tarefa:")
        description_label.setFont(self.default_font)
        layout.addWidget(description_label)
        description_input = QTextEdit()
        description_input.setFont(self.default_font)
        layout.addWidget(description_input)
        priority_label = QLabel("Prioridade:")
        priority_label.setFont(self.default_font)
        layout.addWidget(priority_label)
        priority_selector = QComboBox()
        priority_selector.addItems(["Alta", "Média", "Baixa"])
        priority_selector.setFont(self.default_font)
        layout.addWidget(priority_selector)
        due_date_label = QLabel("Prazo:")
        due_date_label.setFont(self.default_font)
        layout.addWidget(due_date_label)
        calendar = QCalendarWidget()
        calendar.setFont(self.default_font)
        layout.addWidget(calendar)
        color_label = QLabel("Cor de Fundo da Tarefa:")
        color_label.setFont(self.default_font)
        layout.addWidget(color_label)
        color_button = QPushButton("Selecionar Cor")
        color_button.setStyleSheet("background-color: #ccffcc;")
        color_button.setFont(self.default_font)
        layout.addWidget(color_button)
        text_color_label = QLabel("Cor do Texto da Tarefa:")
        text_color_label.setFont(self.default_font)
        layout.addWidget(text_color_label)
        text_color_button = QPushButton("Selecionar Cor do Texto")
        text_color_button.setStyleSheet("color: #000000;")
        text_color_button.setFont(self.default_font)
        layout.addWidget(text_color_button)
        checklist_label = QLabel("Checklist:")
        checklist_label.setFont(self.default_font)
        layout.addWidget(checklist_label)
        manage_checklist_button = QPushButton("Gerenciar Checklist")
        manage_checklist_button.setFont(self.default_font)
        layout.addWidget(manage_checklist_button)
        buttons_layout = QHBoxLayout()
        add_button = QPushButton("Adicionar")
        add_button.setFont(self.default_font)
        buttons_layout.addWidget(add_button)
        cancel_button = QPushButton("Cancelar")
        cancel_button.setFont(self.default_font)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)
        selected_color = "#ccffcc"
        selected_text_color = "#000000"
        current_checklist = []
        def select_color():
            nonlocal selected_color
            color = QColorDialog.getColor()
            if color.isValid():
                selected_color = color.name()
                color_button.setStyleSheet(f"background-color: {selected_color};")
        def select_text_color():
            nonlocal selected_text_color
            color = QColorDialog.getColor()
            if color.isValid():
                selected_text_color = color.name()
                text_color_button.setStyleSheet(f"color: {selected_text_color};")
        def manage_checklist_action():
            nonlocal current_checklist
            updated_checklist = self.manage_checklist(dialog, current_checklist)
            if updated_checklist is not None:
                current_checklist = updated_checklist
        color_button.clicked.connect(select_color)
        text_color_button.clicked.connect(select_text_color)
        manage_checklist_button.clicked.connect(manage_checklist_action)
        def add_task_action():
            description = description_input.toPlainText().strip()
            priority = priority_selector.currentText()
            due_date = calendar.selectedDate().toString("yyyy-MM-dd")
            color = selected_color
            text_color = selected_text_color
            checklist = current_checklist
            if description:
                selected_column_name = column_selector.currentText()
                selected_column = self.columns.get(selected_column_name)
                if selected_column:
                    column_id = selected_column["id"]
                    task_id = self.db.add_task(column_id, description, priority, due_date, color, text_color)
                    for item in checklist:
                        self.db.add_checklist_item(task_id, item['item'], item['checked'])
                    selected_column["list"].add_task_from_db({
                        'id': task_id,
                        'description': description,
                        'priority': priority,
                        'due_date': due_date,
                        'color': color,
                        'text_color': text_color,
                        'checklist': checklist
                    })
                    dialog.accept()
                else:
                    QMessageBox.warning(dialog, "Aviso", "Coluna selecionada não encontrada.")
            else:
                QMessageBox.warning(dialog, "Aviso", "Descrição da tarefa não pode estar vazia.")
        def cancel_action():
            dialog.reject()
        add_button.clicked.connect(add_task_action)
        cancel_button.clicked.connect(cancel_action)
        dialog.setLayout(layout)
        dialog.exec_()
    def edit_task_dialog(self, task_list_widget, task_widget, list_item):
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Tarefa")
        dialog.resize(600, 800)
        layout = QVBoxLayout(dialog)
        description_label = QLabel("Descrição da Tarefa:")
        description_label.setFont(self.default_font)
        layout.addWidget(description_label)
        description_input = QTextEdit()
        description_input.setPlainText(task_widget.description)
        description_input.setFont(self.default_font)
        layout.addWidget(description_input)
        priority_label = QLabel("Prioridade:")
        priority_label.setFont(self.default_font)
        layout.addWidget(priority_label)
        priority_selector = QComboBox()
        priority_selector.addItems(["Alta", "Média", "Baixa"])
        priority_selector.setCurrentText(task_widget.priority)
        priority_selector.setFont(self.default_font)
        layout.addWidget(priority_selector)
        due_date_label = QLabel("Prazo:")
        due_date_label.setFont(self.default_font)
        layout.addWidget(due_date_label)
        calendar = QCalendarWidget()
        calendar.setSelectedDate(QDate.fromString(task_widget.due_date, "yyyy-MM-dd"))
        calendar.setFont(self.default_font)
        layout.addWidget(calendar)
        color_label = QLabel("Cor de Fundo da Tarefa:")
        color_label.setFont(self.default_font)
        layout.addWidget(color_label)
        color_button = QPushButton("Selecionar Cor")
        color_button.setStyleSheet(f"background-color: {task_widget.color};")
        color_button.setFont(self.default_font)
        layout.addWidget(color_button)
        text_color_label = QLabel("Cor do Texto da Tarefa:")
        text_color_label.setFont(self.default_font)
        layout.addWidget(text_color_label)
        text_color_button = QPushButton("Selecionar Cor do Texto")
        text_color_button.setStyleSheet(f"color: {task_widget.text_color};")
        text_color_button.setFont(self.default_font)
        layout.addWidget(text_color_button)
        checklist_label = QLabel("Checklist:")
        checklist_label.setFont(self.default_font)
        layout.addWidget(checklist_label)
        manage_checklist_button = QPushButton("Gerenciar Checklist")
        manage_checklist_button.setFont(self.default_font)
        layout.addWidget(manage_checklist_button)
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Salvar")
        save_button.setFont(self.default_font)
        buttons_layout.addWidget(save_button)
        cancel_button = QPushButton("Cancelar")
        cancel_button.setFont(self.default_font)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)
        selected_color = task_widget.color
        selected_text_color = task_widget.text_color
        current_checklist = task_widget.checklist.copy()
        def select_color():
            nonlocal selected_color
            color = QColorDialog.getColor()
            if color.isValid():
                selected_color = color.name()
                color_button.setStyleSheet(f"background-color: {selected_color};")
        def select_text_color():
            nonlocal selected_text_color
            color = QColorDialog.getColor()
            if color.isValid():
                selected_text_color = color.name()
                text_color_button.setStyleSheet(f"color: {selected_text_color};")
        def manage_checklist_action():
            nonlocal current_checklist
            updated_checklist = self.manage_checklist(dialog, current_checklist)
            if updated_checklist is not None:
                current_checklist = updated_checklist
        color_button.clicked.connect(select_color)
        text_color_button.clicked.connect(select_text_color)
        manage_checklist_button.clicked.connect(manage_checklist_action)
        def save_task_action():
            description = description_input.toPlainText().strip()
            priority = priority_selector.currentText()
            due_date = calendar.selectedDate().toString("yyyy-MM-dd")
            color = selected_color
            text_color = selected_text_color
            checklist = current_checklist
            if description:
                task_id = task_widget.task_id
                self.db.update_task(task_id, description, priority, due_date, color, text_color)
                self.db.update_checklist(task_id, checklist)
                task_widget.description = description
                task_widget.priority = priority
                task_widget.due_date = due_date
                task_widget.color = color
                task_widget.text_color = text_color
                task_widget.checklist = checklist
                task_widget.set_description(description)
                task_widget.priority_label.setText(f"Prioridade: {priority}")
                task_widget.due_date_label.setText(f"Prazo: {due_date}")
                task_widget.update_color()
                task_widget.update_text_color(text_color)
                task_widget.clear_checklist()
                for chk in checklist:
                    cb = QCheckBox(chk['item'])
                    cb.setChecked(chk['checked'])
                    cb.setFont(self.default_font)
                    cb.setStyleSheet(f"color: {task_widget.text_color};")
                    cb.stateChanged.connect(task_widget.update_checklist_status)
                    task_widget.checklist_layout.addWidget(cb)
                    task_widget.checklist_widgets.append(cb)
                list_item.setSizeHint(task_widget.sizeHint())
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "Aviso", "Descrição da tarefa não pode estar vazia.")
        def cancel_action():
            dialog.reject()
        save_button.clicked.connect(save_task_action)
        cancel_button.clicked.connect(cancel_action)
        dialog.setLayout(layout)
        dialog.exec_()
    def manage_checklist(self, dialog, current_checklist=None):
        return self.manage_checklist_subdialog(dialog, current_checklist)
    def manage_checklist_subdialog(self, dialog, current_checklist=None):
        checklist = current_checklist.copy() if current_checklist else []
        checklist_dialog = QDialog(dialog)
        checklist_dialog.setWindowTitle("Gerenciar Checklist")
        checklist_dialog.resize(400, 500)
        layout = QVBoxLayout(checklist_dialog)
        checklist_list = QListWidget()
        for item in checklist:
            list_item = QListWidgetItem(item['item'])
            list_item.setFlags(list_item.flags() | Qt.ItemIsUserCheckable)
            list_item.setCheckState(Qt.Checked if item['checked'] else Qt.Unchecked)
            checklist_list.addItem(list_item)
        layout.addWidget(checklist_list)
        buttons_layout = QHBoxLayout()
        add_item_button = QPushButton("Adicionar Item")
        remove_item_button = QPushButton("Remover Item")
        buttons_layout.addWidget(add_item_button)
        buttons_layout.addWidget(remove_item_button)
        layout.addLayout(buttons_layout)
        save_button = QPushButton("Salvar Checklist")
        layout.addWidget(save_button)
        def add_item():
            text, ok = QInputDialog.getText(checklist_dialog, "Novo Item", "Descrição do Item:")
            if ok and text.strip():
                list_item = QListWidgetItem(text.strip())
                list_item.setFlags(list_item.flags() | Qt.ItemIsUserCheckable)
                list_item.setCheckState(Qt.Unchecked)
                checklist_list.addItem(list_item)
        def remove_item():
            selected_items = checklist_list.selectedItems()
            if not selected_items:
                return
            for item in selected_items:
                checklist_list.takeItem(checklist_list.row(item))
        def save_checklist():
            updated_checklist = []
            for i in range(checklist_list.count()):
                item = checklist_list.item(i)
                updated_checklist.append({'item': item.text(), 'checked': item.checkState() == Qt.Checked})
            nonlocal checklist
            checklist = updated_checklist
            checklist_dialog.accept()
        add_item_button.clicked.connect(add_item)
        remove_item_button.clicked.connect(remove_item)
        save_button.clicked.connect(save_checklist)
        if checklist_dialog.exec_() == QDialog.Accepted:
            return checklist
        else:
            return current_checklist
    def export_tasks(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Exportar Tarefas", "", "CSV Files (*.csv)")
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["ID", "Descrição", "Prioridade", "Prazo", "Cor", "Cor do Texto", "Checklist"])
                    for column in self.columns.values():
                        task_list = column["list"]
                        for i in range(task_list.count()):
                            item = task_list.item(i)
                            task_widget = task_list.itemWidget(item)
                            if task_widget:
                                checklist_str = "; ".join([f"{chk['item']} [{'X' if chk['checked'] else ' '}]"
                                                           for chk in task_widget.checklist])
                                writer.writerow([
                                    task_widget.task_id,
                                    task_widget.description,
                                    task_widget.priority,
                                    task_widget.due_date,
                                    task_widget.color,
                                    task_widget.text_color,
                                    checklist_str
                                ])
                QMessageBox.information(self, "Sucesso", "Tarefas exportadas com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao exportar tarefas: {e}")
    def import_tasks(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Importar Tarefas", "", "CSV Files (*.csv)")
        if filename:
            try:
                with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        description = row.get("Descrição", "").strip()
                        priority = row.get("Prioridade", "").strip()
                        due_date = row.get("Prazo", "").strip()
                        color = row.get("Cor", "#ccffcc").strip()
                        text_color = row.get("Cor do Texto", "#000000").strip()
                        checklist_str = row.get("Checklist", "").strip()
                        checklist = []
                        if checklist_str:
                            items = checklist_str.split("; ")
                            for item in items:
                                if "[X]" in item:
                                    chk_item = item.replace("[X]", "").strip()
                                    checked = True
                                else:
                                    chk_item = item.replace("[ ]", "").strip()
                                    checked = False
                                checklist.append({'item': chk_item, 'checked': checked})
                        if self.columns:
                            first_column = next(iter(self.columns.values()))
                            column_id = first_column["id"]
                            task_id = self.db.add_task(column_id, description, priority, due_date, color, text_color)
                            for chk in checklist:
                                self.db.add_checklist_item(task_id, chk['item'], chk['checked'])
                            first_column["list"].add_task_from_db({
                                'id': task_id,
                                'description': description,
                                'priority': priority,
                                'due_date': due_date,
                                'color': color,
                                'text_color': text_color,
                                'checklist': checklist
                            })
                QMessageBox.information(self, "Sucesso", "Tarefas importadas com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao importar tarefas: {e}")

class KanbanTab(QWidget):
    """Gerenciador de múltiplos quadros Kanban como sub-abas."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.db = DatabaseManager()
        self.menu_bar = QMenuBar(self)
        self.layout.setMenuBar(self.menu_bar)
        kanban_buttons_layout = QHBoxLayout()
        self.add_kanban_button = QPushButton("Adicionar Quadro Kanban", self)
        self.add_kanban_button.setFont(QFont("Arial", 14))
        self.add_kanban_button.clicked.connect(self.add_new_kanban_board)
        kanban_buttons_layout.addWidget(self.add_kanban_button)
        self.layout.addLayout(kanban_buttons_layout)
        self.kanban_tabs = QTabWidget(self)
        self.kanban_tabs.setTabsClosable(True)
        self.kanban_tabs.tabCloseRequested.connect(self.close_kanban_board)
        self.layout.addWidget(self.kanban_tabs)
        self.load_existing_boards()
    def load_existing_boards(self):
        boards = self.db.get_boards()
        if not boards:
            self.add_new_kanban_board(initial=True)
        else:
            for board in boards:
                board_id, board_name = board
                kanban_board = KanbanBoard(board_name, board_id=board_id)
                self.kanban_tabs.addTab(kanban_board, board_name)
    def add_new_kanban_board(self, initial=False):
        if initial:
            name = "Meu Quadro Kanban"
            if any(self.kanban_tabs.tabText(i) == name for i in range(self.kanban_tabs.count())):
                return
        else:
            name, ok = QInputDialog.getText(self, "Novo Quadro Kanban", "Nome do Quadro Kanban:")
            if not (ok and name.strip()):
                return
            name = name.strip()
            if any(self.kanban_tabs.tabText(i) == name for i in range(self.kanban_tabs.count())):
                QMessageBox.warning(self, "Aviso", f"O quadro '{name}' já existe.")
                return
        kanban_board = KanbanBoard(name)
        self.kanban_tabs.addTab(kanban_board, name)
        self.kanban_tabs.setCurrentWidget(kanban_board)
    def close_kanban_board(self, index):
        tab = self.kanban_tabs.widget(index)
        if isinstance(tab, KanbanBoard):
            reply = QMessageBox.question(
                self, 'Confirmar Fechamento',
                f"Tem certeza que deseja fechar o quadro Kanban '{self.kanban_tabs.tabText(index)}'?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.db.remove_board(tab.board_id)
                self.kanban_tabs.removeTab(index)
                tab.deleteLater()
        else:
            self.kanban_tabs.removeTab(index)
            tab.deleteLater()

#########################################
# Plugin Kanban
#########################################

class PluginKanbanTab(PluginTab):
    """
    Plugin que adiciona uma aba com a funcionalidade Kanban.
    """
    name = "Kanban"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        # Instancia a interface Kanban
        self.kanban = KanbanTab(self)
        layout.addWidget(self.kanban)
        self.setLayout(layout)

# Variável global para o carregamento do plugin
plugin_class = PluginKanbanTab

# Código para teste independente do plugin (opcional)
def main():
    app = QApplication(sys.argv)
    window = PluginKanbanTab()
    window.setWindowTitle("Plugin Kanban")
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
