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
#from gamification_module import PetGameModule  # Aba antiga removida!
from task_module import TaskManager
#from simple_excel import SimpleExcelWidget  # REMOVIDO: Excel agora é plugin
from note_module import NoteDialog
from notes_table_module import NotesTableWidget
from theme_module import ThemeDialog
from export_module import (
    export_notes, import_notes, export_to_pdf, show_about
)
from stats_module import StatsWidget
from day_notes_dialog import DayNotesDialog
#from kanban_tab import KanbanTab  # REMOVIDO: Não iremos mais carregar o Kanban no main.
# Removida a importação do editor de texto (MindMapTab) para que ele seja carregado apenas como plugin
#import plugin_libs

# Importa a classe base para plugins
from plugin_base import PluginTab
from plugin_system import (
    load_plugin_config,
    save_plugin_config,
    get_plugin_info,  # Alterado de get_plugin_name para get_plugin_info
    load_plugin_instance,
    load_plugin_file_lazy,
    PluginManagerDialog
)

# ====================================================================
# Classe Principal - CalendarApp
# ====================================================================
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

        # Carrega os plugins persistidos dinamicamente (via lazy load)
        self.load_persistent_plugins()

        # Garante que a aba do Calendário seja a ativa na inicialização
        self.tabs.setCurrentWidget(self.calendar_tab)

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
            "A única maneira de alcançar o impossível é acreditar que é possível."
        ]
        import random
        message = random.choice(motivations)
        self.motivation_label.setText(message)

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

        # Outras abas internas são carregadas sob demanda (lazy load)
        self.lazy_tabs = {
            "Tabela de Notas": self.init_notes_tab,
            "Tabela de Tarefas": self.init_tasks_tab,
            "Estatísticas": self.init_stats_tab
        }
        for tab_name in self.lazy_tabs:
            placeholder = QWidget()
            placeholder.loaded = False
            placeholder.is_plugin = False  # Indica que é uma aba interna
            placeholder.original_tab_name = tab_name
            self.tabs.addTab(placeholder, tab_name)
        # Sinal de mudança de aba para lazy load
        self.tabs.currentChanged.connect(self.on_tab_changed)

        self.init_menu()
        self.refresh_calendar()

    def on_tab_changed(self, index):
        """
        Ao trocar de aba, carrega o conteúdo correspondente.
        Se a aba for de plugin (is_plugin=True) e não carregada, carrega o plugin.
        Se for uma aba interna lazy (is_plugin=False), carrega a página interna.
        """
        self.tabs.blockSignals(True)
        try:
            current_widget = self.tabs.widget(index)
            if getattr(current_widget, "is_plugin", False) and not getattr(current_widget, "loaded", False):
                plugin_instance = load_plugin_instance(self, current_widget.plugin_file)
                if plugin_instance is not None:
                    plugin_instance.loaded = True
                    self.tabs.removeTab(index)
                    self.tabs.insertTab(index, plugin_instance, plugin_instance.name)
                    self.tabs.setCurrentIndex(index)
            elif not getattr(current_widget, "is_plugin", False):
                if not getattr(current_widget, "loaded", False):
                    original_name = getattr(current_widget, "original_tab_name", self.tabs.tabText(index))
                    if original_name in self.lazy_tabs:
                        new_widget = self.lazy_tabs[original_name](lazy=True)
                        new_widget.loaded = True
                        self.tabs.removeTab(index)
                        self.tabs.insertTab(index, new_widget, original_name)
                        self.tabs.setCurrentIndex(index)
        finally:
            self.tabs.blockSignals(False)

    def init_calendar_tab(self, lazy=False):
        self.calendar_tab = QWidget()
        self.calendar_layout = QVBoxLayout(self.calendar_tab)
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

    def init_menu(self):
        menubar = self.menuBar()
        reminders_tasks_menu = menubar.addMenu("Lembretes e Tarefas")
        reminder_manager_action = QAction("Gerenciar Lembretes", self)
        reminder_manager_action.triggered.connect(self.open_reminder_manager)
        reminders_tasks_menu.addAction(reminder_manager_action)
        task_manager_action = QAction("Gerenciar Tarefas", self)
        task_manager_action.triggered.connect(self.open_task_manager)
        reminders_tasks_menu.addAction(task_manager_action)

        import_export_menu = menubar.addMenu("Importar e Exportar")
        export_action = QAction("Exportar Notas", self)
        export_action.triggered.connect(lambda: export_notes(self))
        import_export_menu.addAction(export_action)
        import_action = QAction("Importar Notas", self)
        import_action.triggered.connect(lambda: import_notes(self, self.refresh_calendar))
        import_export_menu.addAction(import_action)

        config_menu = menubar.addMenu("Configurações")
        theme_action = QAction("Personalizar Tema", self)
        theme_action.triggered.connect(self.open_theme_dialog)
        config_menu.addAction(theme_action)
        exit_action = QAction("Sair", self)
        exit_action.triggered.connect(self.close)
        config_menu.addAction(exit_action)

        plugins_menu = menubar.addMenu("Plugins")
        manage_plugins_action = QAction("Gerenciar Plugins", self)
        manage_plugins_action.triggered.connect(self.open_plugin_manager)
        plugins_menu.addAction(manage_plugins_action)
        

        help_menu = menubar.addMenu("Ajuda")
        about_action = QAction("Sobre", self)
        about_action.triggered.connect(lambda: show_about(self))
        help_menu.addAction(about_action)

    # ----- Métodos para carregamento de plugins via Lazy Loading -----
    def load_plugin_instance(self, plugin_file):
        return load_plugin_instance(self, plugin_file)

    def load_plugin_file_lazy(self, plugin_file):
        placeholder = load_plugin_file_lazy(self, plugin_file)
        self.tabs.addTab(placeholder, placeholder.windowTitle())

    def load_plugin(self):
        plugin_file, _ = QFileDialog.getOpenFileName(self, "Selecione o arquivo do plugin", "", "Python Files (*.py)")
        if plugin_file:
            self.load_plugin_file_lazy(plugin_file)

    def open_plugin_manager(self):
        dlg = PluginManagerDialog(self)
        dlg.exec_()

    def load_persistent_plugins(self):
        plugin_entries = load_plugin_config()
        for entry in plugin_entries:
            # Verifica se o plugin está habilitado
            if entry.get("enabled", True):
                plugin_file = entry["file"]
                if os.path.exists(plugin_file):
                    self.load_plugin_file_lazy(plugin_file)
                else:
                    print(f"Arquivo de plugin não encontrado: {plugin_file}")

    # ---------------------------------------------------------------------

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
        all_notes = load_notes()
        day_notes = all_notes.get(note_date, [])
        dialog = DayNotesDialog(self, note_date, day_notes)
        dialog.setModal(False)
        dialog.finished.connect(lambda result, d=dialog, nd=note_date: self.after_note_dialog(result, d, nd))
        dialog.show()

    def after_note_dialog(self, result, dialog, note_date):
        if result == QDialog.Accepted:
            updated_notes = dialog.get_notes()
            if updated_notes:
                self.notes[note_date] = updated_notes
            else:
                if note_date in self.notes:
                    del self.notes[note_date]
            save_notes(self.notes)
            self.refresh_calendar()

   

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

def main():
    app = QApplication(sys.argv)
    
    # Cria a splash screen
    splash_image = "splash.png"
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
