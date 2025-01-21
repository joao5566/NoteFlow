# kanban_tab.py

import sys
import csv
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QWidget, QTabWidget, QInputDialog, QMessageBox,
    QLineEdit, QComboBox, QMenuBar, QMenu, QAction, QFileDialog, QCalendarWidget,
    QDialog, QTextEdit, QColorDialog, QScrollArea
)
from PyQt5.QtCore import Qt, QDate, QMimeData, QSize
from PyQt5.QtGui import QFont, QColor, QDrag, QPixmap, QIcon


class TaskWidget(QWidget):
    def __init__(self, description, priority, due_date, color="#ccffcc", text_color="#000000", parent=None, font=None):
        super().__init__(parent)
        self.description = description
        self.priority = priority
        self.due_date = due_date
        self.color = color  # Cor de fundo
        self.text_color = text_color  # Cor do texto
        self.font = font or QFont("Arial", 14)  # Fonte padrão

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Descrição da Tarefa
        self.description_label = QLabel(self.description)
        self.description_label.setWordWrap(True)  # Permite quebra de linha
        self.description_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.description_label.setStyleSheet(f"color: {self.text_color};")
        self.description_label.setFont(self.font)
        layout.addWidget(self.description_label)

        # Informações Adicionais
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

        # Definir Cor de Fundo com Base na Cor Selecionada
        self.update_color()

    def update_color(self):
        self.setStyleSheet(f"background-color: {self.color}; border: 1px solid #000000; border-radius: 5px;")

    def update_text_color(self, new_color):
        self.text_color = new_color
        self.description_label.setStyleSheet(f"color: {self.text_color};")
        self.priority_label.setStyleSheet(f"color: {self.text_color};")
        self.due_date_label.setStyleSheet(f"color: {self.text_color};")

    def set_font(self, font):
        self.font = font
        self.description_label.setFont(self.font)
        self.priority_label.setFont(self.font)
        self.due_date_label.setFont(self.font)

    def sizeHint(self):
        # Definir a largura fixa do widget
        fixed_width = 430  # 450 (largura da coluna) - 20 (margens e paddings)
        self.setFixedWidth(fixed_width)

        # Ajustar a altura com base no conteúdo
        # Usar layout para calcular o tamanho
        self.description_label.setFixedWidth(fixed_width - 20)  # Ajustar de acordo com o layout
        height = self.description_label.sizeHint().height() + \
                 self.priority_label.sizeHint().height() + \
                 self.due_date_label.sizeHint().height() + \
                 40  # Margens e espaçamentos
        return QSize(fixed_width, height)


class TaskListWidget(QListWidget):
    def __init__(self, parent=None, kanban_tab=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QListWidget.DragDrop)  # Permitir drag and drop entre listas
        self.setDefaultDropAction(Qt.MoveAction)
        self.kanban_tab = kanban_tab
        self.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ccc;")
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setSpacing(5)  # Espaçamento entre itens
        self.setUniformItemSizes(False)  # Permitir tamanhos variados

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item:
            task_widget = self.itemWidget(item)
            if task_widget:
                mimeData = QMimeData()
                # Serializar os dados da tarefa como uma string JSON
                task_data = {
                    'description': task_widget.description,
                    'priority': task_widget.priority,
                    'due_date': task_widget.due_date,
                    'color': task_widget.color,
                    'text_color': task_widget.text_color  # Salvar a cor do texto
                }
                json_data = json.dumps(task_data)
                mimeData.setData('application/x-task', json_data.encode('utf-8'))
                
                drag = QDrag(self)
                drag.setMimeData(mimeData)
                # Opcional: definir um ícone de arrasto
                pixmap = task_widget.grab()
                drag.setPixmap(pixmap)
                
                if drag.exec_(Qt.MoveAction):
                    # Se o drag for aceito, remover o item da lista atual
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
            # Desserializar os dados da tarefa
            json_data = event.mimeData().data('application/x-task').data().decode('utf-8')
            task_data = json.loads(json_data)
            description = task_data.get('description', '')
            priority = task_data.get('priority', 'Média')
            due_date = task_data.get('due_date', '2023-01-01')
            color = task_data.get('color', '#ccffcc')
            text_color = task_data.get('text_color', '#000000')  # Novo campo
            
            # Adicionar a tarefa à lista atual
            self.add_task(description, priority, due_date, color, text_color)
            
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def add_task(self, description, priority, due_date, color="#ccffcc", text_color="#000000"):
        task_widget = TaskWidget(description, priority, due_date, color, text_color, font=self.kanban_tab.default_font)
        list_item = QListWidgetItem(self)
        list_item.setSizeHint(task_widget.sizeHint())

        self.addItem(list_item)
        self.setItemWidget(list_item, task_widget)

    def edit_task(self, item):
        task_widget = self.itemWidget(item)  # Utilizar o item diretamente
        if not task_widget:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Tarefa")
        dialog.setFixedSize(600, 700)  # Aumentado para acomodar a fonte e mais elementos
        layout = QVBoxLayout(dialog)

        description_label = QLabel("Descrição da Tarefa:")
        description_label.setFont(self.kanban_tab.default_font)
        layout.addWidget(description_label)

        description_input = QTextEdit()
        description_input.setPlainText(task_widget.description)
        description_input.setFont(self.kanban_tab.default_font)
        layout.addWidget(description_input)

        priority_label = QLabel("Prioridade:")
        priority_label.setFont(self.kanban_tab.default_font)
        layout.addWidget(priority_label)

        priority_selector = QComboBox()
        priority_selector.addItems(["Alta", "Média", "Baixa"])
        priority_selector.setCurrentText(task_widget.priority)
        priority_selector.setFont(self.kanban_tab.default_font)
        layout.addWidget(priority_selector)

        due_date_label = QLabel("Prazo:")
        due_date_label.setFont(self.kanban_tab.default_font)
        layout.addWidget(due_date_label)

        calendar = QCalendarWidget()
        calendar.setSelectedDate(QDate.fromString(task_widget.due_date, "yyyy-MM-dd"))
        calendar.setFont(self.kanban_tab.default_font)
        layout.addWidget(calendar)

        color_label = QLabel("Cor de Fundo da Tarefa:")
        color_label.setFont(self.kanban_tab.default_font)
        layout.addWidget(color_label)

        color_button = QPushButton("Selecionar Cor")
        color_button.setStyleSheet(f"background-color: {task_widget.color};")
        color_button.setFont(self.kanban_tab.default_font)
        layout.addWidget(color_button)

        text_color_label = QLabel("Cor do Texto da Tarefa:")
        text_color_label.setFont(self.kanban_tab.default_font)
        layout.addWidget(text_color_label)

        text_color_button = QPushButton("Selecionar Cor do Texto")
        text_color_button.setStyleSheet(f"color: {task_widget.text_color};")
        text_color_button.setFont(self.kanban_tab.default_font)
        layout.addWidget(text_color_button)

        selected_color = task_widget.color
        selected_text_color = task_widget.text_color

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

        color_button.clicked.connect(select_color)
        text_color_button.clicked.connect(select_text_color)

        save_button = QPushButton("Salvar")
        save_button.setFont(self.kanban_tab.default_font)
        layout.addWidget(save_button)

        def save_task_action():
            description = description_input.toPlainText().strip()
            priority = priority_selector.currentText()
            due_date = calendar.selectedDate().toString("yyyy-MM-dd")
            color = selected_color
            text_color = selected_text_color
            if description:
                task_widget.description = description
                task_widget.priority = priority
                task_widget.due_date = due_date
                task_widget.color = color
                task_widget.text_color = text_color

                task_widget.description_label.setText(description)
                task_widget.priority_label.setText(f"Prioridade: {priority}")
                task_widget.due_date_label.setText(f"Prazo: {due_date}")
                task_widget.update_color()
                task_widget.update_text_color(text_color)

                # Atualizar a fonte
                task_widget.set_font(self.kanban_tab.default_font)

                # Atualizar o sizeHint e o tamanho do item
                list_item = self.item(self.row(item))
                list_item.setSizeHint(task_widget.sizeHint())

                dialog.accept()
            else:
                QMessageBox.warning(dialog, "Aviso", "Descrição da tarefa não pode estar vazia.")

        save_button.clicked.connect(save_task_action)
        dialog.setLayout(layout)
        dialog.exec_()

    def delete_task(self, item):
        reply = QMessageBox.question(
            self, "Excluir Tarefa", f"Tem certeza que deseja excluir a tarefa?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.takeItem(self.row(item))

    def change_due_date(self, item):
        task_widget = self.itemWidget(item)
        if not task_widget:
            return

        calendar = QCalendarWidget(self)
        calendar.setSelectedDate(QDate.fromString(task_widget.due_date, "yyyy-MM-dd"))
        calendar.setFont(self.kanban_tab.default_font)
        dialog = QDialog(self)
        layout = QVBoxLayout(dialog)
        layout.addWidget(calendar)
        confirm_button = QPushButton("Confirmar", dialog)
        confirm_button.setFont(self.kanban_tab.default_font)
        layout.addWidget(confirm_button)

        def confirm_action():
            new_due_date = calendar.selectedDate().toString("yyyy-MM-dd")
            task_widget.due_date = new_due_date
            task_widget.due_date_label.setText(f"Prazo: {new_due_date}")
            dialog.accept()

        confirm_button.clicked.connect(confirm_action)

        dialog.setWindowTitle("Alterar Prazo")
        dialog.setFixedSize(600, 700)  # Aumentado para acomodar a fonte e mais elementos
        dialog.exec_()

    def change_text_color(self, item):
        task_widget = self.itemWidget(item)
        if not task_widget:
            return

        color = QColorDialog.getColor(initial=QColor(task_widget.text_color), parent=self, title="Selecionar Cor do Texto")
        if color.isValid():
            new_text_color = color.name()
            task_widget.update_text_color(new_text_color)

            # Atualizar a fonte
            task_widget.set_font(self.kanban_tab.default_font)

            # Atualizar o sizeHint e o tamanho do item
            list_item = self.item(self.row(item))
            list_item.setSizeHint(task_widget.sizeHint())

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if item:
            menu = QMenu(self)
            edit_action = menu.addAction("Editar Tarefa")
            delete_action = menu.addAction("Excluir Tarefa")
            change_due_date_action = menu.addAction("Alterar Prazo")
            change_text_color_action = menu.addAction("Alterar Cor do Texto")  # Nova ação

            action = menu.exec_(self.mapToGlobal(event.pos()))
            if action == edit_action:
                self.edit_task(item)
            elif action == delete_action:
                self.delete_task(item)
            elif action == change_due_date_action:
                self.change_due_date(item)
            elif action == change_text_color_action:
                self.change_text_color(item)


class KanbanTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # Definir uma fonte padrão confortável (por exemplo, Arial 14)
        self.default_font = QFont("Arial", 14)

        self.menu_bar = QMenuBar(self)
        self.file_menu = QMenu("Arquivo", self)
        self.task_menu = QMenu("Tarefas", self)
        self.view_menu = QMenu("Visualizar", self)
        self.menu_bar.addMenu(self.file_menu)
        self.menu_bar.addMenu(self.task_menu)
        self.menu_bar.addMenu(self.view_menu)

        export_action = QAction(QIcon("icons/export.png"), "Exportar Tarefas (CSV)", self)
        export_action.triggered.connect(self.export_tasks)
        self.file_menu.addAction(export_action)

        import_action = QAction(QIcon("icons/import.png"), "Importar Tarefas (CSV)", self)
        import_action.triggered.connect(self.import_tasks)
        self.file_menu.addAction(import_action)

        add_column_action = QAction(QIcon("icons/add_column.png"), "Adicionar Coluna", self)
        add_column_action.triggered.connect(self.add_column_dialog)
        self.task_menu.addAction(add_column_action)

        # Remover ação de alterar tamanho da fonte do menu
        # change_font_action = QAction(QIcon("icons/font_size.png"), "Alterar Tamanho da Fonte", self)
        # change_font_action.triggered.connect(self.change_font_size)
        # self.view_menu.addAction(change_font_action)

        self.layout.setMenuBar(self.menu_bar)

        # Botões: Adicionar Tarefa e Adicionar Coluna
        buttons_layout = QHBoxLayout()

        self.add_task_button = QPushButton(QIcon("icons/add_task.png"), "Adicionar Tarefa", self)
        self.add_task_button.setFont(self.default_font)
        self.add_task_button.clicked.connect(self.add_task)
        buttons_layout.addWidget(self.add_task_button)

        self.add_column_button = QPushButton(QIcon("icons/add_column.png"), "Adicionar Coluna", self)
        self.add_column_button.setFont(self.default_font)
        self.add_column_button.clicked.connect(self.add_column_dialog)
        buttons_layout.addWidget(self.add_column_button)

        # Remover o botão de alterar tamanho da fonte
        # self.change_font_button = QPushButton(QIcon("icons/font_size.png"), "Tamanho da Fonte", self)
        # self.change_font_button.clicked.connect(self.change_font_size)
        # self.change_font_button.setFont(self.default_font)
        # buttons_layout.addWidget(self.change_font_button)

        self.layout.addLayout(buttons_layout)

        # Área de rolagem para as colunas
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QHBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(20)  # Espaçamento entre colunas
        self.scroll_layout.setContentsMargins(10, 10, 10, 10)
        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)

        self.columns = {}
        for title in ["A Fazer", "Fazendo", "Concluído"]:
            self.add_column(title)

        # Aplicar a fonte padrão a todos os elementos existentes
        self.apply_default_font()

    def apply_default_font(self):
        # Aplicar a fonte padrão a todos os elementos existentes
        for column in self.columns.values():
            # Atualizar o font dos labels das colunas
            column["label"].setFont(self.default_font)
            # Atualizar o font das listas de tarefas
            column["list"].setFont(self.default_font)
            # Atualizar o font de cada TaskWidget dentro da lista
            for i in range(column["list"].count()):
                list_item = column["list"].item(i)
                task_widget = column["list"].itemWidget(list_item)
                if task_widget:
                    task_widget.set_font(self.default_font)

    def add_column(self, title):
        if title in self.columns:
            QMessageBox.warning(self, "Aviso", "Coluna já existe!")
            return

        column_layout = QVBoxLayout()
        column_widget = QWidget()
        column_widget.setLayout(column_layout)
        column_widget.setFixedWidth(450)  # Definindo largura fixa para 450 pixels

        # Layout para o título (Removido o botão de ajustar largura)
        header_layout = QHBoxLayout()
        title_label = QLabel(title, self)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        title_label.setFont(self.default_font)
        header_layout.addWidget(title_label)

        # **Remoção do botão de ajustar largura**
        # Ajustar o layout do cabeçalho apenas com o título centralizado

        column_layout.addLayout(header_layout)

        task_list = TaskListWidget(self.scroll_content, kanban_tab=self)
        column_layout.addWidget(task_list)

        delete_button = QPushButton(f"Excluir {title}", self)
        delete_button.setFont(self.default_font)
        delete_button.clicked.connect(lambda: self.remove_column(title))
        column_layout.addWidget(delete_button)

        self.columns[title] = {"widget": column_widget, "list": task_list, "label": title_label}
        self.scroll_layout.addWidget(column_widget)

    def add_column_dialog(self):
        column_name, ok = QInputDialog.getText(self, "Nova Coluna", "Nome da Coluna:")
        if ok and column_name.strip():
            self.add_column(column_name.strip())

    def remove_column(self, title):
        if title in self.columns:
            column = self.columns.pop(title)
            column["widget"].deleteLater()

    def clear_all_columns(self):
        for column_name in list(self.columns.keys()):
            self.remove_column(column_name)

    def add_task(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Adicionar Tarefa")
        dialog.setFixedSize(600, 700)  # Aumentado para acomodar a fonte e mais elementos
        layout = QVBoxLayout(dialog)

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
        color_button.setStyleSheet(f"background-color: #ccffcc;")
        color_button.setFont(self.default_font)
        layout.addWidget(color_button)

        text_color_label = QLabel("Cor do Texto da Tarefa:")
        text_color_label.setFont(self.default_font)
        layout.addWidget(text_color_label)

        text_color_button = QPushButton("Selecionar Cor do Texto")
        text_color_button.setStyleSheet(f"color: #000000;")
        text_color_button.setFont(self.default_font)
        layout.addWidget(text_color_button)

        selected_color = "#ccffcc"  # Cor padrão de fundo
        selected_text_color = "#000000"  # Cor padrão do texto

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

        color_button.clicked.connect(select_color)
        text_color_button.clicked.connect(select_text_color)

        add_button = QPushButton("Adicionar")
        add_button.setFont(self.default_font)
        layout.addWidget(add_button)

        def add_task_action():
            description = description_input.toPlainText().strip()
            priority = priority_selector.currentText()
            due_date = calendar.selectedDate().toString("yyyy-MM-dd")
            color = selected_color
            text_color = selected_text_color
            if description:
                self.columns["A Fazer"]["list"].add_task(description, priority, due_date, color, text_color)
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "Aviso", "Descrição da tarefa não pode estar vazia.")

        add_button.clicked.connect(add_task_action)
        dialog.setLayout(layout)
        dialog.exec_()

    def export_tasks(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Tarefas", "", "CSV Files (*.csv)")
        if not file_path:
            return

        if not file_path.lower().endswith(".csv"):
            file_path += ".csv"

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Coluna", "Descrição", "Prioridade", "Prazo", "Cor de Fundo", "Cor do Texto"])
                for column_name, column in self.columns.items():
                    if column["list"].count() == 0:
                        # Escrever uma linha indicando a coluna vazia
                        writer.writerow([column_name, "", "", "", "", ""])
                    else:
                        for i in range(column["list"].count()):
                            list_item = column["list"].item(i)
                            task_widget = column["list"].itemWidget(list_item)
                            if task_widget:
                                # Substituir quebras de linha por espaços para manter a integridade do CSV
                                description = task_widget.description.replace("\n", " ")
                                writer.writerow([
                                    column_name,
                                    description,
                                    task_widget.priority,
                                    task_widget.due_date,
                                    task_widget.color,
                                    task_widget.text_color
                                ])
            QMessageBox.information(self, "Exportado", f"Tarefas exportadas para {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao exportar tarefas: {e}")

    def import_tasks(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Carregar Tarefas", "", "CSV Files (*.csv)")
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                # Coletar todos os nomes de colunas únicos do arquivo
                columns_in_file = set()
                tasks = []
                for row in reader:
                    column_name = row.get("Coluna")
                    description = row.get("Descrição")
                    priority = row.get("Prioridade")
                    due_date = row.get("Prazo")
                    color = row.get("Cor de Fundo", "#ccffcc")
                    text_color = row.get("Cor do Texto", "#000000")
                    if column_name:
                        columns_in_file.add(column_name)
                        if description and priority and due_date:
                            tasks.append({
                                "column": column_name,
                                "description": description,
                                "priority": priority,
                                "due_date": due_date,
                                "color": color,
                                "text_color": text_color
                            })

            # Limpar todas as colunas existentes
            self.clear_all_columns()

            # Adicionar colunas conforme o arquivo
            for column_name in columns_in_file:
                self.add_column(column_name)

            # Adicionar tarefas nas colunas correspondentes
            for task in tasks:
                if task["column"] in self.columns:
                    self.columns[task["column"]]["list"].add_task(
                        task["description"],
                        task["priority"],
                        task["due_date"],
                        task["color"],
                        task["text_color"]
                    )

            QMessageBox.information(self, "Importado", "Tarefas importadas com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao importar tarefas: {e}")

