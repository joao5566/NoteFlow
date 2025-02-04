# -*- coding: utf-8 -*-
# calendar_widget.py

# Importações padrão
import sys
import os
import json
import importlib.util

# Importações de terceiros
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLineEdit, QScrollArea, QLabel, QMenuBar, QAction, QMessageBox,
    QDialog, QComboBox, QSpinBox, QFormLayout, QTabWidget, QCalendarWidget,
    QFileDialog, QListWidget, QListWidgetItem, QDialogButtonBox, QSplashScreen
)
from PyQt5.QtGui import QIcon, QPalette, QColor, QFont, QPixmap
from PyQt5.QtCore import QDate, Qt, QTimer

import sqlite3
import random
import pyttsx3


# Importações locais
from persistence_module import (
    load_notes, save_notes, load_reminders, save_reminders,
    load_theme, save_theme, load_tasks, save_tasks, init_db, DB_PATH
)
from tasks_table_module import TasksTableWidget
from reminder_module import ReminderManager
from gamification_module import PetGameModule
from task_module import TaskManager
from simple_excel import SimpleExcelWidget
from note_module import NoteDialog
from notes_table_module import NotesTableWidget
from theme_module import ThemeDialog
from export_module import (
    export_notes, import_notes, export_to_pdf, show_about
)
from stats_module import StatsWidget
from day_notes_dialog import DayNotesDialog
from kanban_tab import KanbanTab
from mind_map_tab import MindMapTab
import plugin_libs

# Importa a classe base para plugins
from plugin_base import PluginTab

# -----------------------------------------------
# Funções para persistência de plugins
# -----------------------------------------------
CONFIG_FILE = "loaded_plugins.json"

def load_plugin_config():
    if not os.path.exists(CONFIG_FILE):
        return []
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("plugins", [])
    except Exception as e:
        print(f"Erro ao carregar config de plugins: {e}")
        return []

def save_plugin_config(plugin_paths):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"plugins": plugin_paths}, f, indent=4)
    except Exception as e:
        print(f"Erro ao salvar config de plugins: {e}")

# -----------------------------------------------
# Diálogo para Lembretes
# -----------------------------------------------
class ReminderDialog(QDialog):
    """Diálogo para definir um lembrete."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Definir Lembrete")
        self.layout = QVBoxLayout(self)

        # Layout para data
        date_layout = QHBoxLayout()
        self.date_label = QLabel("Data:", self)
        date_layout.addWidget(self.date_label)

        self.calendar = QCalendarWidget(self)
        self.calendar.setGridVisible(True)
        self.calendar.setMaximumDate(QDate(9999, 12, 31))
        self.calendar.setMinimumDate(QDate(1900, 1, 1))
        if hasattr(self, 'initial_date') and self.initial_date:
            parsed_date = QDate.fromString(self.initial_date, "yyyy-MM-dd")
            if parsed_date.isValid():
                self.calendar.setSelectedDate(parsed_date)
        else:
            self.calendar.setSelectedDate(QDate.currentDate())
        date_layout.addWidget(self.calendar)
        self.layout.addLayout(date_layout)

        # Campo de mensagem
        self.message_input = QLineEdit(self)
        self.message_input.setPlaceholderText("Mensagem do lembrete")
        self.layout.addWidget(QLabel("Mensagem:", self))
        self.layout.addWidget(self.message_input)

        # Botões de ação
        self.buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Salvar", self)
        self.save_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancelar", self)
        self.cancel_button.clicked.connect(self.reject)
        self.buttons_layout.addWidget(self.save_button)
        self.buttons_layout.addWidget(self.cancel_button)
        self.layout.addLayout(self.buttons_layout)

    def get_reminder(self):
        """Retorna a data e a mensagem do lembrete."""
        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        message = self.message_input.text().strip()
        return selected_date, message

# -----------------------------------------------
# Diálogo Gerenciador de Plugins (Recursivo)
# -----------------------------------------------
class PluginManagerDialog(QDialog):
    """
    Diálogo que lista os plugins disponíveis na pasta padrão (por exemplo, "plugins")
    procurando em cada subpasta o arquivo 'main.py' e permitindo carregar o plugin.
    """
    def __init__(self, parent=None, plugin_folder="plugins"):
        super().__init__(parent)
        self.setWindowTitle("Gerenciar Plugins")
        self.resize(400, 300)
        self.plugin_folder = plugin_folder
        self.parent_app = parent  # Referência para a janela principal

        self.layout = QVBoxLayout(self)
        self.list_widget = QListWidget(self)
        self.layout.addWidget(self.list_widget)

        self.button_box = QDialogButtonBox(self)

        self.add_button = self.button_box.addButton("Adicionar Plugin", QDialogButtonBox.ActionRole)
        self.update_list_button = self.button_box.addButton("Atualizar Lista de Plugs", QDialogButtonBox.ActionRole)
        self.close_button = self.button_box.addButton(QDialogButtonBox.Close)

        self.layout.addWidget(self.button_box)

        self.add_button.clicked.connect(self.add_plugin)
        self.update_list_button.clicked.connect(self.atualizar_lista_plugins)
        self.close_button.clicked.connect(self.accept)
        self.list_widget.itemDoubleClicked.connect(self.load_selected_plugin)
        self.populate_list()

    def populate_list(self):
        """Procura por subpastas que contenham 'main.py' e preenche a lista."""
        self.list_widget.clear()
        if not os.path.exists(self.plugin_folder):
            os.makedirs(self.plugin_folder)
        for item in os.listdir(self.plugin_folder):
            item_path = os.path.join(self.plugin_folder, item)
            if os.path.isdir(item_path):
                main_file = os.path.join(item_path, "main.py")
                if os.path.exists(main_file):
                    rel_path = os.path.relpath(main_file, self.plugin_folder)
                    list_item = QListWidgetItem(rel_path)
                    list_item.setData(Qt.UserRole, main_file)
                    self.list_widget.addItem(list_item)

    def load_selected_plugin(self, item):
        """Carrega o plugin correspondente ao item selecionado."""
        plugin_file = item.data(Qt.UserRole)
        self.parent_app.load_plugin_file(plugin_file)

    def atualizar_lista_plugins(self):
        """Atualiza a lista de plugins e fecha o app, sem reiniciar automaticamente."""
        if not os.path.exists(self.plugin_folder):
            os.makedirs(self.plugin_folder)

        novos_plugins = []
        for item in os.listdir(self.plugin_folder):
            item_path = os.path.join(self.plugin_folder, item)
            if os.path.isdir(item_path):
                main_file = os.path.join(item_path, "main.py")
                if os.path.exists(main_file):
                    abs_path = os.path.abspath(main_file)
                    novos_plugins.append(abs_path)

        save_plugin_config(novos_plugins)
        self.populate_list()
        QMessageBox.information(
            self,
            "Atualizado",
            "A lista de plugins foi atualizada. Por favor, reinicie o aplicativo manualmente."
        )
        self.parent_app.close()

    def add_plugin(self):
        """
        Abre um diálogo para o usuário selecionar a pasta do plugin
        (que deve conter um arquivo 'main.py') e copia-a para a pasta padrão.
        """
        plugin_folder_selected = QFileDialog.getExistingDirectory(self, "Selecione a pasta do plugin")
        if plugin_folder_selected:
            try:
                if not os.path.exists(self.plugin_folder):
                    os.makedirs(self.plugin_folder)
                base_name = os.path.basename(plugin_folder_selected)
                dest_path = os.path.join(self.plugin_folder, base_name)
                import shutil
                shutil.copytree(plugin_folder_selected, dest_path)
                self.populate_list()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao adicionar plugin:\n{e}")

# -----------------------------------------------
# Classe Principal - CalendarApp
# -----------------------------------------------
class CalendarApp(QMainWindow):
    """Aplicativo de Calendário Interativo com Notas."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calendário Interativo com Notas")
        self.resize(800, 600)

        # Inicializa o banco de dados
        init_db()

        # Carrega dados persistentes
        self.notes = load_notes()
        self.tasks = load_tasks()
        self.reminders = load_reminders()
        self.current_date = QDate.currentDate()
        self.theme = self.ensure_theme_integrity(load_theme())

        # Configuração da interface e tema
        self.init_ui()
        self.apply_global_theme()

        # Timer para lembretes
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start(60000)

        # Exibe a motivação
        self.show_random_motivation_label()

        # Carrega os plugins persistidos dinamicamente
        self.load_persistent_plugins()

        # Garante que a aba do Calendário seja a ativa na inicialização
        self.tabs.setCurrentWidget(self.calendar_tab)

    # ------------------------------
    # Métodos de Tema
    # ------------------------------



    def ensure_theme_integrity(self, theme):
        default_theme = {
            "background": "#ffffff",
            "button": "#cccccc",
            "marked_day": "#ffcccc",
            "text": "#000000",
            "dark_mode": False
        }
        for key, value in default_theme.items():
            if key not in theme:
                theme[key] = value
        return theme

    def apply_global_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(self.theme["background"]))
        palette.setColor(QPalette.Button, QColor(self.theme["button"]))
        palette.setColor(QPalette.Text, QColor(self.theme["text"]))
        palette.setColor(QPalette.WindowText, QColor(self.theme["text"]))
        QApplication.instance().setPalette(palette)

        menu_style = (
            f"QMenu, QMenuBar {{ background-color: {self.theme['background']}; color: {self.theme['text']}; }}"
            f"QMenu::item {{ background-color: {self.theme['button']}; }}"
            f"QMenu::item:selected {{ background-color: {self.theme['marked_day']}; color: {self.theme['text']}; }}"
        )
        QApplication.instance().setStyleSheet(menu_style)

        font_size = int(self.theme.get("font_size", 12))
        font = QFont()
        font.setPointSize(font_size)
        QApplication.setFont(font)

    # ------------------------------
    # Inicialização da Interface com Lazy Load nas Abas

    def show_random_motivation_label(self):
        motivations = [
            "Continue se esforçando!",
            "Todo dia é uma nova oportunidade!",
            "Consistência é a chave para o sucesso.",
            "Pequenos passos levam a grandes mudanças.",
            "Acredite no processo e continue avançando!",
            "Você é mais forte do que imagina.",
            "Grandes coisas levam tempo.",
            "Não tenha medo de falhar, tenha medo de não tentar.",
            "O sucesso é a soma de pequenos esforços repetidos diariamente.",
            "Cada dia é uma chance de fazer melhor.",
            "Seja paciente. Tudo vem ao seu tempo.",
            "A determinação de hoje constrói o sucesso de amanhã.",
            "Mesmo o menor progresso é um passo à frente.",
            "Lembre-se de por que você começou.",
            "Você é capaz de superar qualquer desafio.",
            "Não se compare com os outros, compare-se com quem você era ontem.",
            "Mantenha o foco e nunca desista.",
            "Desafios são oportunidades disfarçadas.",
            "O aprendizado nunca é desperdiçado.",
            "A coragem não é a ausência de medo, mas a decisão de seguir em frente apesar dele.",
            "O impossível é apenas uma questão de opinião.",
            "A jornada é tão importante quanto o destino.",
            "O segredo do sucesso é começar.",
            "Permita-se crescer, mesmo que isso signifique sair da zona de conforto.",
            "As dificuldades preparam pessoas comuns para destinos extraordinários.",
            "Não importa o quão devagar você vá, desde que não pare.",
            "Persista, a próxima tentativa pode ser a que dará certo.",
            "Seja a mudança que você quer ver no mundo.",
            "A única maneira de alcançar o impossível é acreditar que é possível.",
            "Seu esforço de hoje define suas conquistas de amanhã."
        ]
        message = random.choice(motivations)
        self.motivation_label.setText(message)

    # ------------------------------
    def init_ui(self):
        self.setWindowIcon(QIcon('icone.ico'))
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.motivation_label = QLabel("", self)
        self.motivation_label.setStyleSheet("font-size: 18px; color: green;")
        self.layout.addWidget(self.motivation_label)
        
        self.tabs = QTabWidget(self)
        self.layout.addWidget(self.tabs)

        # Carrega imediatamente a aba Calendário (essencial)
        self.init_calendar_tab()

        # Define as demais abas para carregamento sob demanda (lazy load)
        # Mapeia o título da aba à função de inicialização correspondente
        self.lazy_tabs = {
            "Tabela de Notas": self.init_notes_tab,
            "Tabela de Tarefas": self.init_tasks_tab,
            "Estatísticas": self.init_stats_tab,
            "Planilha Simples": self.init_excel_tab,
            "Mascote Virtual": self.init_pet_game_tab,
            "Kanban": self.init_kanban_tab,
            "Editor de Texto": self.init_mind_map_tab
        }
        # Cria abas placeholder para cada uma das abas lazy
        for tab_name in self.lazy_tabs:
            placeholder = QWidget()
            placeholder.loaded = False  # marca como não carregado
            self.tabs.addTab(placeholder, tab_name)
        # Conecta o sinal para detectar mudança de aba
        self.tabs.currentChanged.connect(self.on_tab_changed)

        self.init_menu()
        self.refresh_calendar()

    def on_tab_changed(self, index):
        """Quando o usuário muda de aba, carrega seu conteúdo se ainda não estiver carregado."""
        tab_name = self.tabs.tabText(index)
        if tab_name in self.lazy_tabs:
            current_widget = self.tabs.widget(index)
            if not getattr(current_widget, "loaded", False):
                new_widget = self.lazy_tabs[tab_name](lazy=True)
                new_widget.loaded = True
                self.tabs.removeTab(index)
                self.tabs.insertTab(index, new_widget, tab_name)
                self.tabs.setCurrentIndex(index)

    # ------------------------------
    # Funções de Inicialização das Abas
    # Cada função aceita o parâmetro lazy (se True, apenas retorna o widget)
    # ------------------------------
    def init_calendar_tab(self, lazy=False):
        self.calendar_tab = QWidget()
        self.calendar_layout = QVBoxLayout(self.calendar_tab)
        # Controles de pesquisa, mês e ano
        self.controls_layout = QHBoxLayout()
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Pesquisar notas...")
        self.search_input.textChanged.connect(self.search_notes)
        self.controls_layout.addWidget(self.search_input)

        self.month_selector = QComboBox(self)
        self.month_selector.addItems([
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ])
        self.month_selector.setCurrentIndex(self.current_date.month() - 1)
        self.month_selector.currentIndexChanged.connect(self.update_calendar)
        self.controls_layout.addWidget(self.month_selector)

        self.year_selector = QSpinBox(self)
        self.year_selector.setRange(1900, 2100)
        self.year_selector.setValue(self.current_date.year())
        self.year_selector.valueChanged.connect(self.update_calendar)
        self.controls_layout.addWidget(self.year_selector)

        self.calendar_layout.addLayout(self.controls_layout)

        self.scroll_area = QScrollArea(self)
        self.scroll_area_widget = QWidget()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_area_widget)
        self.calendar_layout.addWidget(self.scroll_area)

        self.calendar_grid_layout = QGridLayout(self.scroll_area_widget)
        self.scroll_area_widget.setLayout(self.calendar_grid_layout)
        
        if not lazy:
            self.tabs.addTab(self.calendar_tab, "Calendário")
        else:
            return self.calendar_tab

    def init_notes_tab(self, lazy=False):
        self.notes_tab = NotesTableWidget(self)
        self.notes_tab.load_notes(self.notes)
        if not lazy:
            self.tabs.addTab(self.notes_tab, "Tabela de Notas")
        else:
            return self.notes_tab

    def init_tasks_tab(self, lazy=False):
        self.tasks_tab = TasksTableWidget(self)
        if not lazy:
            self.tabs.addTab(self.tasks_tab, "Tabela de Tarefas")
        else:
            return self.tasks_tab

    def init_stats_tab(self, lazy=False):
        self.stats_tab = StatsWidget(self)
        if not lazy:
            self.tabs.addTab(self.stats_tab, "Estatísticas")
        else:
            return self.stats_tab

    def init_excel_tab(self, lazy=False):
        self.excel_tab = SimpleExcelWidget(self)
        if not lazy:
            self.tabs.addTab(self.excel_tab, "Planilha Simples")
        else:
            return self.excel_tab

    def init_pet_game_tab(self, lazy=False):
        self.pet_game_tab = PetGameModule(self)
        if not lazy:
            self.tabs.addTab(self.pet_game_tab, "Mascote Virtual")
        else:
            return self.pet_game_tab

    def init_kanban_tab(self, lazy=False):
        self.kanban_tab = KanbanTab(self)
        if not lazy:
            self.tabs.addTab(self.kanban_tab, "Kanban")
        else:
            return self.kanban_tab

    def init_mind_map_tab(self, lazy=False):
        self.mind_map_tab = MindMapTab(self)
        if not lazy:
            self.tabs.addTab(self.mind_map_tab, "Editor de Texto")
        else:
            return self.mind_map_tab

    # ------------------------------
    # Configuração do Menu
    # ------------------------------
    def init_menu(self):
        menubar = self.menuBar()

        # Menu de Lembretes e Tarefas
        reminders_tasks_menu = menubar.addMenu("Lembretes e Tarefas")
        reminder_manager_action = QAction("Gerenciar Lembretes", self)
        reminder_manager_action.triggered.connect(self.open_reminder_manager)
        reminders_tasks_menu.addAction(reminder_manager_action)
        task_manager_action = QAction("Gerenciar Tarefas", self)
        task_manager_action.triggered.connect(self.open_task_manager)
        reminders_tasks_menu.addAction(task_manager_action)

        # Menu de Importação e Exportação
        import_export_menu = menubar.addMenu("Importar e Exportar")
        export_pdf_action = QAction("Exportar para PDF", self)
        export_pdf_action.triggered.connect(lambda: export_to_pdf(self))
        import_export_menu.addAction(export_pdf_action)
        export_action = QAction("Exportar Notas", self)
        export_action.triggered.connect(lambda: export_notes(self))
        import_export_menu.addAction(export_action)
        import_action = QAction("Importar Notas", self)
        import_action.triggered.connect(lambda: import_notes(self, self.refresh_calendar))
        import_export_menu.addAction(import_action)

        # Menu de Configurações
        config_menu = menubar.addMenu("Configurações")
        theme_action = QAction("Personalizar Tema", self)
        theme_action.triggered.connect(self.open_theme_dialog)
        config_menu.addAction(theme_action)
        exit_action = QAction("Sair", self)
        exit_action.triggered.connect(self.close)
        config_menu.addAction(exit_action)

        # Menu de Plugins aprimorado
        plugins_menu = menubar.addMenu("Plugins")
        manage_plugins_action = QAction("Gerenciar Plugins", self)
        manage_plugins_action.triggered.connect(self.open_plugin_manager)
        plugins_menu.addAction(manage_plugins_action)
        add_plugin_action = QAction("Adicionar Plugin (Arquivo)", self)
        add_plugin_action.triggered.connect(self.load_plugin)
        plugins_menu.addAction(add_plugin_action)

        # Menu de Ajuda
        help_menu = menubar.addMenu("Ajuda")
        about_action = QAction("Sobre", self)
        about_action.triggered.connect(lambda: show_about(self))
        help_menu.addAction(about_action)

    # ------------------------------
    # Métodos de Plugin
    # ------------------------------
    def load_plugin_file(self, plugin_file):
        try:
            plugin_dir = os.path.dirname(plugin_file)
            if plugin_dir not in sys.path:
                sys.path.insert(0, plugin_dir)
            
            module_name = os.path.splitext(os.path.basename(plugin_file))[0]
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if plugin_dir in sys.path:
                sys.path.remove(plugin_dir)
            
            plugin_class = getattr(module, "plugin_class", None)
            if plugin_class is None:
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, PluginTab) and attr is not PluginTab:
                        plugin_class = attr
                        break

            if plugin_class is None:
                QMessageBox.warning(self, "Erro", "Nenhuma classe de plugin válida encontrada no arquivo.")
                return

            plugin_instance = plugin_class(self)
            self.tabs.addTab(plugin_instance, plugin_instance.name)
            self.tabs.setCurrentWidget(plugin_instance)
            
            plugins_list = load_plugin_config()
            if plugin_file not in plugins_list:
                plugins_list.append(plugin_file)
                save_plugin_config(plugins_list)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao carregar plugin", f"Ocorreu um erro:\n{e}")

    def load_plugin(self):
        plugin_file, _ = QFileDialog.getOpenFileName(self, "Selecione o arquivo do plugin", "", "Python Files (*.py)")
        if plugin_file:
            self.load_plugin_file(plugin_file)

    def open_plugin_manager(self):
        dlg = PluginManagerDialog(self)
        dlg.exec_()

    def load_persistent_plugins(self):
        plugins_list = load_plugin_config()
        for plugin_file in plugins_list:
            if os.path.exists(plugin_file):
                self.load_plugin_file(plugin_file)
            else:
                print(f"Arquivo de plugin não encontrado: {plugin_file}")

    # ------------------------------
    # Métodos de Calendário e Diálogos
    # ------------------------------
    def refresh_calendar(self):
        self.notes = load_notes()
        year = self.current_date.year()
        month = self.current_date.month()
        days_in_month = QDate(year, month, 1).daysInMonth()

        for i in reversed(range(self.calendar_grid_layout.count())):
            widget = self.calendar_grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        for day in range(1, days_in_month + 1):
            button = QPushButton(str(day), self)
            date = QDate(year, month, day)
            date_str = date.toString("yyyy-MM-dd")
            button.clicked.connect(lambda _, d=date_str: self.open_note_dialog(d))
            self.style_button(button, date_str)
            row = (day - 1) // 7
            col = (day - 1) % 7
            self.calendar_grid_layout.addWidget(button, row, col)

    def update_calendar(self):
        selected_month = self.month_selector.currentIndex() + 1
        selected_year = self.year_selector.value()
        self.current_date = QDate(selected_year, selected_month, 1)
        self.refresh_calendar()

    def style_button(self, button, date_str):
        notes = self.notes.get(date_str, [])
        if notes:
            if any("feito" in note.get("tags", []) for note in notes):
                button.setStyleSheet(f"background-color: {self.theme['marked_day']}; color: {self.theme['text']};")
            else:
                button.setStyleSheet(f"background-color: {self.theme['button']}; color: {self.theme['text']};")
        else:
            button.setStyleSheet(f"background-color: {self.theme['background']}; color: {self.theme['text']};")

    def open_theme_dialog(self):
        dialog = ThemeDialog(self.theme, self)
        if dialog.exec_() == QDialog.Accepted:
            self.theme = self.ensure_theme_integrity(dialog.get_theme())
            self.apply_global_theme()
            save_theme(self.theme)

    def open_note_dialog(self, note_date):
        # Recarrega todas as notas do DB para garantir que estão atualizadas
        all_notes = load_notes()
        day_notes = all_notes.get(note_date, [])
        dialog = DayNotesDialog(self, note_date, day_notes)
        dialog.setModal(False)  # Torna o diálogo não modal
        # Conecta o sinal 'finished' para tratar quando o diálogo for fechado
        dialog.finished.connect(lambda result, d=dialog, nd=note_date: self.after_note_dialog(result, d, nd))
        dialog.show()


    def after_note_dialog(self, result, dialog, note_date):
        # Se o usuário fechou o diálogo com "Aceitar"
        if result == QDialog.Accepted:
            updated_notes = dialog.get_notes()
            if updated_notes:
                self.notes[note_date] = updated_notes
            else:
                if note_date in self.notes:
                    del self.notes[note_date]
            save_notes(self.notes)
            self.refresh_calendar()


    def open_reminder_dialog(self):
        dialog = ReminderDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            date, message = dialog.get_reminder()
            if self.validate_reminder(date, message):
                with sqlite3.connect(DB_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO reminders (date, message) VALUES (?, ?)", (date, message))
                    conn.commit()
                self.reminders = load_reminders()

    def search_notes(self, text):
        for i in range(self.calendar_grid_layout.count()):
            button = self.calendar_grid_layout.itemAt(i).widget()
            if button:
                day = int(button.text())
                date = QDate(self.current_date.year(), self.current_date.month(), day)
                date_str = date.toString("yyyy-MM-dd")
                notes = self.notes.get(date_str, [])
                if any(text.lower() in note['text'].lower() for note in notes):
                    button.setStyleSheet(f"background-color: {self.theme['marked_day']}; color: {self.theme['text']};")
                else:
                    self.style_button(button, date_str)

    def check_reminders(self):
        today_str = QDate.currentDate().toString("yyyy-MM-dd")
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT message FROM reminders WHERE date = ?", (today_str,))
            rows = cursor.fetchall()
            for row in rows:
                QMessageBox.information(self, "Lembrete", row[0])

    def open_task_manager(self):
        self.tasks = load_tasks()
        manager = TaskManager(self.tasks, save_tasks)
        if manager.exec_() == QDialog.Accepted:
            self.tasks = load_tasks()
            save_tasks(self.tasks)

    def open_reminder_manager(self):
        self.reminders = load_reminders()
        manager = ReminderManager(self.reminders, save_reminders)
        if manager.exec_() == QDialog.Accepted:
            self.reminders = load_reminders()
            save_reminders(self.reminders)

# -----------------------------------------------
# Ponto de Entrada do Aplicativo com Splash Screen
# -----------------------------------------------
def main():
    app = QApplication(sys.argv)
    
    # Cria a splash screen
    splash_image = "splash.png"  # Substitua pelo caminho da sua imagem, se disponível.
    if os.path.exists(splash_image):
        pixmap = QPixmap(splash_image)
    else:
        pixmap = QPixmap(400, 300)
        pixmap.fill(QColor("white"))
    
    splash = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
    splash.showMessage("Carregando o aplicativo...", Qt.AlignBottom | Qt.AlignCenter, Qt.black)
    splash.show()
    app.processEvents()
    
    window = CalendarApp()
    window.show()
    app.setStyle("Fusion")
    splash.finish(window)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
