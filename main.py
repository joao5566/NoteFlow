# calendar_widget.py

# Importações padrão
import sys

# Importações de terceiros
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLineEdit, QScrollArea, QLabel, QMenuBar, QAction, QMessageBox,
    QDialog, QComboBox, QSpinBox, QFormLayout, QTabWidget,
    QCalendarWidget  # Adicionado
)
from PyQt5.QtGui import QIcon, QPalette, QColor
from PyQt5.QtCore import QDate, Qt, QTimer
import sqlite3  # Importação adicionada

# Importações locais
from persistence_module import (
    load_notes, save_notes, load_reminders, save_reminders,
    load_theme, save_theme, load_tasks, save_tasks, init_db, DB_PATH  # DB_PATH adicionado
)
from tasks_table_module import TasksTableWidget
from reminder_module import ReminderManager
from gamification_module import PetGameModule
from task_module import TaskManager
from simple_excel import SimpleExcelWidget
from note_module import NoteDialog
from notes_table_module import NotesTableWidget
from theme_module import ThemeDialog
from motivation_module import show_random_motivation
from export_module import (
    export_notes, import_notes, export_to_pdf, show_about
)
from stats_module import StatsWidget  # Certifique-se de que StatsWidget está disponível
from day_notes_dialog import DayNotesDialog  # Novo módulo
from kanban_tab import KanbanTab


# --------------------------------------------------
# Definição de Diálogos
# --------------------------------------------------

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
        self.calendar.setMaximumDate(QDate(9999, 12, 31))  # Definir data máxima, se necessário
        self.calendar.setMinimumDate(QDate(1900, 1, 1))    # Definir data mínima, se necessário

        # Se uma data inicial foi fornecida, selecione-a no calendário
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

# --------------------------------------------------
# Definição da Janela Principal
# --------------------------------------------------

class CalendarApp(QMainWindow):
    """Aplicativo de Calendário Interativo com Notas."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calendário Interativo com Notas")
        self.resize(800, 600)

        # Inicializa o banco de dados
        init_db()

        # Carrega dados persistentes
        self.notes = load_notes()  # {'2025-04-27': [{'id':1, 'text': 'Nota 1', 'category': 'Categoria1', 'tags': ['tag1']}, ...], ...}
        self.tasks = load_tasks()
        self.reminders = load_reminders()
        self.current_date = QDate.currentDate()
        self.theme = self.ensure_theme_integrity(load_theme())

        # Configuração da interface e tema
        self.init_ui()
        self.apply_global_theme()
        show_random_motivation(self)

        # Configuração do timer para lembretes
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start(60000)  # Verifica lembretes a cada minuto

    # ------------------------------
    # Métodos de Tema
    # ------------------------------

    def ensure_theme_integrity(self, theme):
        """Garante que o tema carregado possui todas as chaves necessárias."""
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
        """Aplica o tema global à aplicação."""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(self.theme["background"]))
        palette.setColor(QPalette.Button, QColor(self.theme["button"]))
        palette.setColor(QPalette.Text, QColor(self.theme["text"]))
        palette.setColor(QPalette.WindowText, QColor(self.theme["text"]))
        QApplication.instance().setPalette(palette)

        # Estilo dos menus
        menu_style = (
            f"QMenu, QMenuBar {{ background-color: {self.theme['background']}; color: {self.theme['text']}; }}"
            f"QMenu::item {{ background-color: {self.theme['button']}; }}"
            f"QMenu::item:selected {{ background-color: {self.theme['marked_day']}; color: {self.theme['text']}; }}"
        )
        QApplication.instance().setStyleSheet(menu_style)

    # ------------------------------
    # Inicialização da Interface
    # ------------------------------

    def init_ui(self):
        """Inicializa os componentes da interface do usuário."""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Configuração das abas
        self.tabs = QTabWidget(self)
        self.layout.addWidget(self.tabs)

        # Inicializa as diferentes abas
        self.init_calendar_tab()
        self.init_notes_tab()
        self.init_tasks_tab()
        self.init_stats_tab()
        self.init_excel_tab()
        self.init_pet_game_tab()
         # Adiciona a aba Kanban
        self.init_kanban_tab() 
        # Configuração do menu
        self.init_menu()

        # Atualiza o calendário inicialmente
        self.refresh_calendar()
    

    

    def init_calendar_tab(self):
        """Configura a aba do calendário."""
        self.calendar_tab = QWidget()
        self.calendar_layout = QVBoxLayout(self.calendar_tab)
        self.tabs.addTab(self.calendar_tab, "Calendário")

        # Layout de controles (pesquisa, lembrete, seletores de data)
        self.controls_layout = QHBoxLayout()

        # Campo de pesquisa de notas
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Pesquisar notas...")
        self.search_input.textChanged.connect(self.search_notes)
        self.controls_layout.addWidget(self.search_input)

        # Botão para definir lembrete
        self.reminder_button = QPushButton(QIcon("icons/reminder.png"), "Definir Lembrete", self)
        self.reminder_button.clicked.connect(self.open_reminder_dialog)
        self.controls_layout.addWidget(self.reminder_button)

        # Seletor de mês
        self.month_selector = QComboBox(self)
        self.month_selector.addItems([
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ])
        self.month_selector.setCurrentIndex(self.current_date.month() - 1)
        self.month_selector.currentIndexChanged.connect(self.update_calendar)
        self.controls_layout.addWidget(self.month_selector)

        # Seletor de ano
        self.year_selector = QSpinBox(self)
        self.year_selector.setRange(1900, 2100)
        self.year_selector.setValue(self.current_date.year())
        self.year_selector.valueChanged.connect(self.update_calendar)
        self.controls_layout.addWidget(self.year_selector)

        self.calendar_layout.addLayout(self.controls_layout)

        # Área de rolagem para o calendário
        self.scroll_area = QScrollArea(self)
        self.scroll_area_widget = QWidget()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_area_widget)
        self.calendar_layout.addWidget(self.scroll_area)

        # Layout da grade do calendário
        self.calendar_grid_layout = QGridLayout(self.scroll_area_widget)
        self.scroll_area_widget.setLayout(self.calendar_grid_layout)
    

    
    
    def init_notes_tab(self):
        """Configura a aba da tabela de notas."""
        self.notes_tab = NotesTableWidget(self)
        self.notes_tab.load_notes(self.notes)  # Carrega as notas no widget
        self.tabs.addTab(self.notes_tab, "Tabela de Notas")
    
    def init_tasks_tab(self):
        """Configura a aba da tabela de tarefas."""
        self.tasks_tab = TasksTableWidget(self)
        self.tabs.addTab(self.tasks_tab, "Tabela de Tarefas")

    def init_stats_tab(self):
        """Configura a aba de estatísticas."""
        self.stats_tab = StatsWidget(self)
        self.tabs.addTab(self.stats_tab, "Estatísticas")
    

    def init_kanban_tab(self):
        """Adiciona a aba Kanban ao QTabWidget."""
        self.kanban_tab = KanbanTab(self)
        self.tabs.addTab(self.kanban_tab, "Kanban")

    def init_excel_tab(self):
        """Configura a aba da planilha simples."""
        self.excel_tab = SimpleExcelWidget(self)
        self.tabs.addTab(self.excel_tab, "Planilha Simples")

    def init_pet_game_tab(self):
        """Configura a aba do mascote virtual."""
        self.pet_game_tab = PetGameModule(self)
        self.tabs.addTab(self.pet_game_tab, "Mascote Virtual")

    # ------------------------------
    # Configuração do Menu
    # ------------------------------

    def init_menu(self):
        """Inicializa a barra de menus."""
        menubar = self.menuBar()

        # Menu de Lembretes e Tarefas
        reminders_tasks_menu = menubar.addMenu("Lembretes e Tarefas")

        # Ação para gerenciar lembretes
        reminder_manager_action = QAction("Gerenciar Lembretes", self)
        reminder_manager_action.triggered.connect(self.open_reminder_manager)
        reminders_tasks_menu.addAction(reminder_manager_action)

        # Ação para gerenciar tarefas
        task_manager_action = QAction("Gerenciar Tarefas", self)
        task_manager_action.triggered.connect(self.open_task_manager)
        reminders_tasks_menu.addAction(task_manager_action)

        # Menu de Importação e Exportação
        import_export_menu = menubar.addMenu("Importar e Exportar")

        # Ação para exportar para PDF
        export_pdf_action = QAction("Exportar para PDF", self)
        export_pdf_action.triggered.connect(lambda: export_to_pdf(self))
        import_export_menu.addAction(export_pdf_action)

        # Ação para exportar notas
        export_action = QAction("Exportar Notas", self)
        export_action.triggered.connect(lambda: export_notes(self))
        import_export_menu.addAction(export_action)

        # Ação para importar notas
        import_action = QAction("Importar Notas", self)
        import_action.triggered.connect(lambda: import_notes(self, self.refresh_calendar))
        import_export_menu.addAction(import_action)

        # Menu de Configurações
        config_menu = menubar.addMenu("Configurações")

        # Ação para personalizar o tema
        theme_action = QAction("Personalizar Tema", self)
        theme_action.triggered.connect(self.open_theme_dialog)
        config_menu.addAction(theme_action)

        # Ação para sair
        exit_action = QAction("Sair", self)
        exit_action.triggered.connect(self.close)
        config_menu.addAction(exit_action)

        # Menu de Ajuda
        help_menu = menubar.addMenu("Ajuda")

        # Ação sobre
        about_action = QAction("Sobre", self)
        about_action.triggered.connect(lambda: show_about(self))
        help_menu.addAction(about_action)

    # ------------------------------
    # Métodos de Calendário
    # ------------------------------

    def refresh_calendar(self):
        """Atualiza a exibição do calendário."""
        self.notes = load_notes()
        year = self.current_date.year()
        month = self.current_date.month()
        days_in_month = QDate(year, month, 1).daysInMonth()

        # Limpa o calendário atual
        for i in reversed(range(self.calendar_grid_layout.count())):
            widget = self.calendar_grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Adiciona os dias ao calendário
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
        """Atualiza o calendário com base nos seletores de mês e ano."""
        selected_month = self.month_selector.currentIndex() + 1
        selected_year = self.year_selector.value()
        self.current_date = QDate(selected_year, selected_month, 1)
        self.refresh_calendar()

    def style_button(self, button, date_str):
        """Estiliza o botão do dia com base nas notas."""
        notes = self.notes.get(date_str, [])
        if notes:
            # Se pelo menos uma nota estiver marcada como "feito"
            if any("feito" in note.get("tags", []) for note in notes):
                button.setStyleSheet(f"background-color: {self.theme['marked_day']}; color: {self.theme['text']};")
            else:
                button.setStyleSheet(f"background-color: {self.theme['button']}; color: {self.theme['text']};")
        else:
            button.setStyleSheet(f"background-color: {self.theme['background']}; color: {self.theme['text']};")

    # ------------------------------
    # Métodos de Diálogo
    # ------------------------------

    def open_theme_dialog(self):
        """Abre o diálogo para personalizar o tema."""
        dialog = ThemeDialog(self.theme, self)
        if dialog.exec_() == QDialog.Accepted:
            self.theme = self.ensure_theme_integrity(dialog.get_theme())
            self.apply_global_theme()
            save_theme(self.theme)

    def open_note_dialog(self, note_date):
        """Abre o diálogo mostrando todas as notas do dia e permite adicionar novas notas."""
        day_notes = self.notes.get(note_date, [])
        dialog = DayNotesDialog(self, note_date, day_notes)
        if dialog.exec_() == QDialog.Accepted:
            # Atualiza as notas após possíveis adições/edições
            updated_notes = dialog.get_notes()
            if updated_notes:
                self.notes[note_date] = updated_notes
            else:
                if note_date in self.notes:
                    del self.notes[note_date]
            save_notes(self.notes)
            self.refresh_calendar()

    def open_reminder_dialog(self):
        """Abre o diálogo para definir um novo lembrete."""
        dialog = ReminderDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            date, message = dialog.get_reminder()
            if self.validate_reminder(date, message):
                # Salva o lembrete no banco de dados
                with sqlite3.connect(DB_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO reminders (date, message) VALUES (?, ?)",
                        (date, message)
                    )
                    conn.commit()
                # Atualiza a lista de lembretes
                self.reminders = load_reminders()
            else:
                # A validação já exibe uma mensagem de erro
                pass

    # ------------------------------
    # Métodos de Busca
    # ------------------------------

    def search_notes(self, text):
        """Filtra as notas com base no texto de busca."""
        for i in range(self.calendar_grid_layout.count()):
            button = self.calendar_grid_layout.itemAt(i).widget()
            if button:
                day = int(button.text())
                date = QDate(self.current_date.year(), self.current_date.month(), day)
                date_str = date.toString("yyyy-MM-dd")
                notes = self.notes.get(date_str, [])
                # Verifica se alguma nota contém o texto buscado
                if any(text.lower() in self.strip_html(note['text']).lower() for note in notes):
                    button.setStyleSheet(f"background-color: {self.theme['marked_day']}; color: {self.theme['text']};")
                else:
                    self.style_button(button, date_str)

    # ------------------------------
    # Métodos de Lembretes e Tarefas
    # ------------------------------

    def check_reminders(self):
        """Verifica se há lembretes para o dia atual."""
        today_str = QDate.currentDate().toString("yyyy-MM-dd")
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT message FROM reminders WHERE date = ?", (today_str,))
            rows = cursor.fetchall()
            for row in rows:
                QMessageBox.information(self, "Lembrete", row[0])

    def open_task_manager(self):
        """Abre o gerenciador de tarefas."""
        self.tasks = load_tasks()
        manager = TaskManager(self.tasks, save_tasks)
        if manager.exec_() == QDialog.Accepted:
            self.tasks = load_tasks()
            save_tasks(self.tasks)
            # Atualize outras partes do aplicativo, se necessário

    def open_reminder_manager(self):
        """Abre o gerenciador de lembretes."""
        self.reminders = load_reminders()
        manager = ReminderManager(self.reminders, save_reminders)
        if manager.exec_() == QDialog.Accepted:
            self.reminders = load_reminders()
            save_reminders(self.reminders)

    # ------------------------------
    # Métodos de Estatísticas
    # ------------------------------

    def view_stats(self):
        """Exibe as estatísticas (não está sendo usado atualmente)."""
        dialog = StatsDialog(self)
        dialog.exec_()

# --------------------------------------------------
# Ponto de Entrada do Aplicativo
# --------------------------------------------------

def main():
    """Função principal para iniciar o aplicativo."""
    app = QApplication(sys.argv)
    window = CalendarApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

