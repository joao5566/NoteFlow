from PyQt5.QtWidgets import QDialog, QFormLayout, QPushButton, QColorDialog, QHBoxLayout, QMessageBox, QApplication, QComboBox
from PyQt5.QtGui import QPalette, QColor
from persistence_module import save_theme  # Importando a função save_theme
import sys

class ThemeDialog(QDialog):
    def __init__(self, current_theme, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Personalizar Tema")
        self.layout = QFormLayout(self)
        self.theme = current_theme.copy()  # Criar uma cópia do tema atual para manipulação

        self.predefined_themes = {
            "Padrão Claro": {"background": "#ffffff", "button": "#cccccc", "marked_day": "#ffcccc", "text": "#000000", "dark_mode": False},
            "Padrão Claro Claro": {"background": "#f0f0f0", "button": "#e0e0e0", "marked_day": "#ff9999", "text": "#333333", "dark_mode": False},
            "Ametista Claro": {"background": "#f1e6f5", "button": "#d4a8e6", "marked_day": "#e699cc", "text": "#660066", "dark_mode": False},
            "Café Claro": {"background": "#f2e0d6", "button": "#d6ad91", "marked_day": "#d18f5a", "text": "#4e2c00", "dark_mode": False},
            "Fogo Claro": {"background": "#ffeeee", "button": "#ffcccc", "marked_day": "#ff6666", "text": "#660000", "dark_mode": False},
            "Azul Claro": {"background": "#cfe3f7", "button": "#aacce6", "marked_day": "#5fa8df", "text": "#003366", "dark_mode": False},
            "Turquesa Claro": {"background": "#e1f7fa", "button": "#80deea", "marked_day": "#00bcd4", "text": "#00796b", "dark_mode": False},
            "Lavanda Claro": {"background": "#f6eaf6", "button": "#e0c8e9", "marked_day": "#b39ddb", "text": "#4a148c", "dark_mode": False},
            "Chocolate Claro": {"background": "#f6ebd9", "button": "#dcbf9b", "marked_day": "#b88c5f", "text": "#3e2723", "dark_mode": False},
            "Verde Escuro Claro": {"background": "#d9f7d4", "button": "#c0e5c6", "marked_day": "#99cc66", "text": "#2e7d32", "dark_mode": False},
            "Coral Claro": {"background": "#ffefd5", "button": "#ffcccc", "marked_day": "#ff6347", "text": "#c0392b", "dark_mode": False},
            "Lima Claro": {"background": "#f0f9e8", "button": "#c8e6c9", "marked_day": "#8bc34a", "text": "#33691e", "dark_mode": False},
            "Charcoal Claro": {"background": "#e0e0e0", "button": "#b3b3b3", "marked_day": "#999999", "text": "#333333", "dark_mode": False},
            "Bambu Claro": {"background": "#f8f1c4", "button": "#c7e157", "marked_day": "#b59b38", "text": "#4e4d24", "dark_mode": False},
            "Gelo Claro": {"background": "#f0f0f0", "button": "#e0e0e0", "marked_day": "#c0c0c0", "text": "#333333", "dark_mode": False},
            "Aqua Claro": {"background": "#e0f7fa", "button": "#80deea", "marked_day": "#00bcd4", "text": "#004d40", "dark_mode": False},
            "Vinho Claro": {"background": "#f5e1e6", "button": "#d49cb3", "marked_day": "#ff4d6d", "text": "#800020", "dark_mode": False},
            "Café Claro Claro": {"background": "#e9e3d5", "button": "#d6c4b0", "marked_day": "#a1887f", "text": "#4e2c00", "dark_mode": False},
            "Limão Claro": {"background": "#eaf9e6", "button": "#c8e6c9", "marked_day": "#66bb6a", "text": "#1b5e20", "dark_mode": False},
            "Escarlate Claro": {"background": "#ffeeee", "button": "#e57373", "marked_day": "#ff3f3f", "text": "#8b0000", "dark_mode": False},
            "Azul Claro Claro": {"background": "#e0e8f7", "button": "#88b8d1", "marked_day": "#4f84bc", "text": "#002f5f", "dark_mode": False},
            "Cinza Claro Claro": {"background": "#f7f7f7", "button": "#dcdcdc", "marked_day": "#a0a0a0", "text": "#212121", "dark_mode": False}
        }



        self.theme_selector = QComboBox(self)
        self.theme_selector.addItems(self.predefined_themes.keys())
        self.theme_selector.currentIndexChanged.connect(self.select_predefined_theme)
        self.layout.addRow("Esquemas de Cores:", self.theme_selector)

        # Botões para alterar as cores
        self.bg_color_button = QPushButton("Alterar Cor de Fundo")
        self.bg_color_button.clicked.connect(lambda: self.change_color("background"))
        self.layout.addRow("Cor de Fundo:", self.bg_color_button)

        self.button_color_button = QPushButton("Alterar Cor dos Botões")
        self.button_color_button.clicked.connect(lambda: self.change_color("button"))
        self.layout.addRow("Cor dos Botões:", self.button_color_button)

        self.marked_day_color_button = QPushButton("Alterar Cor dos Dias Marcados")
        self.marked_day_color_button.clicked.connect(lambda: self.change_color("marked_day"))
        self.layout.addRow("Cor dos Dias Marcados:", self.marked_day_color_button)

        self.text_color_button = QPushButton("Alterar Cor do Texto")
        self.text_color_button.clicked.connect(lambda: self.change_color("text"))
        self.layout.addRow("Cor do Texto:", self.text_color_button)

        # Botão para alternar entre modo claro e escuro
        self.dark_mode_button = QPushButton("Ativar Modo Claro")
        self.dark_mode_button.clicked.connect(self.toggle_dark_mode)
        self.layout.addRow("Modo de Exibição:", self.dark_mode_button)

        # Botões de ação
        self.action_buttons_layout = QHBoxLayout()

        self.save_button = QPushButton("Salvar Tema")
        self.save_button.clicked.connect(self.save_and_restart)
        self.action_buttons_layout.addWidget(self.save_button)

        self.restore_button = QPushButton("Restaurar Padrão")
        self.restore_button.clicked.connect(self.restore_default_theme)
        self.action_buttons_layout.addWidget(self.restore_button)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        self.action_buttons_layout.addWidget(self.cancel_button)

        self.layout.addRow(self.action_buttons_layout)

    def change_color(self, key):
        """ Abre um diálogo para selecionar a cor e atualiza o tema com pré-visualização ao vivo. """
        color = QColorDialog.getColor()
        if color.isValid():
            self.theme[key] = color.name()
            self.apply_preview()

    def toggle_dark_mode(self):
        """ Alterna entre modo claro e escuro com pré-visualização ao vivo. """
        if self.theme.get("dark_mode", False):
            self.theme = self.predefined_themes["Padrão Claro"].copy()
            self.dark_mode_button.setText("Ativar Modo Escuro")
        else:
            self.theme = self.predefined_themes["Padrão Escuro"].copy()
            self.dark_mode_button.setText("Ativar Modo Claro")
        self.apply_preview()

    def apply_preview(self):
        """ Aplica uma pré-visualização do tema na interface. """
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(self.theme["background"]))
        palette.setColor(QPalette.Button, QColor(self.theme["button"]))
        palette.setColor(QPalette.Text, QColor(self.theme["text"]))
        palette.setColor(QPalette.WindowText, QColor(self.theme["text"]))
        palette.setColor(QPalette.Highlight, QColor(self.theme["marked_day"]))
        palette.setColor(QPalette.HighlightedText, QColor(self.theme["text"]))
        QApplication.instance().setPalette(palette)

        menu_style = f"QMenu, QMenuBar {{ background-color: {self.theme['background']}; color: {self.theme['text']}; }}"
        menu_style += f"QMenu::item {{ background-color: {self.theme['button']}; }}"
        menu_style += f"QMenu::item:selected {{ background-color: {self.theme['marked_day']}; color: {self.theme['text']}; }}"
        QApplication.instance().setStyleSheet(menu_style)

        # Forçar atualização dos widgets para aplicar o tema imediatamente
        for widget in QApplication.instance().allWidgets():
            widget.update()
            # Recriar ou atualizar botões dos dias marcados
            if widget.objectName() == "marked_day_button":
                widget.setStyleSheet(f"background-color: {self.theme['marked_day']}; color: {self.theme['text']};")

    def select_predefined_theme(self):
        """ Aplica o tema predefinido selecionado no combobox. """
        theme_name = self.theme_selector.currentText()
        self.theme = self.predefined_themes[theme_name].copy()
        self.apply_preview()

    def get_theme(self):
        """ Retorna o tema atualizado. """
        return self.theme

    def restore_default_theme(self):
        """ Restaura o tema para os valores padrões e aplica a pré-visualização. """
        self.theme = self.predefined_themes["Padrão Claro"].copy()
        self.dark_mode_button.setText("Ativar Modo Escuro")
        self.apply_preview()
        QMessageBox.information(self, "Tema Restaurado", "O tema foi restaurado para o padrão.")

    def load_theme(self):
        """ Carrega o tema salvo anteriormente e aplica. """
        self.theme = save_theme.load_saved_theme()
        self.apply_preview()

    def delete_theme(self):
        """ Remove o tema salvo e restaura o padrão. """
        save_theme.delete_saved_theme()
        self.restore_default_theme()

    def save_and_restart(self):
        """ Salva o tema e reinicia o aplicativo. """
        save_theme(self.theme)
        QMessageBox.information(self, "Reiniciar Aplicativo", "O aplicativo será reiniciado para aplicar o tema.")
        qapp = QApplication.instance()
        qapp.quit()
        sys.exit(0)

