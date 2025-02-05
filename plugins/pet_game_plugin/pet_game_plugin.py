# pet_game_plugin.py
import sqlite3
import random
import os
import json
import sys
import shutil

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QDialog, QHBoxLayout, QTabWidget, QLabel,
    QPushButton, QMessageBox, QProgressBar, QSpinBox, QComboBox,
    QScrollArea, QGridLayout, QShortcut
)
from PyQt5.QtCore import Qt, QTimer, QPoint, QSize
from PyQt5.QtGui import QColor, QPainter, QBrush, QPen, QFont, QPolygon, QIcon, QKeySequence

# Importa módulos específicos do pet e minijogos
from shop_module import load_shop_items, ShopModule

from shop_module import load_shop_items, ShopModule
from cheat_menu import CheatMenu
from drawing_utils import draw_shape
from minigames_registry import get_minigames
from plugin_base import PluginTab


# Importa a classe base para plugins
from plugin_base import PluginTab

# Define o diretório base do plugin (a pasta onde este arquivo está)
PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))

# Agora o DB será criado na pasta do plugin
DB_PATH = os.path.join(PLUGIN_DIR, 'pet_game.db')

class PetGamePlugin(PluginTab):
    name = "Mascote"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        self.init_db()
        # Variáveis de status e personalização
        self.unlocked_colors = []
        self.unlocked_bodies = ["square"]
        self.body_color = "#FFFF00"
        # Se possível, adapte ou reimplemente load_shop_items para usar caminhos relativos também.
        self.items = load_shop_items()  
        self.is_playing = False
        self.coins = 0
        self.accessories = ["glasses", "gloves"]
        self.unlocked_accessories = []
        self.equipped_accessories = []
        self.equipped_hat = None
        self.body_style = "circle"
        self.exp_boost_active = False
        self.unlocked_consumables = {}
        self.hats = self.load_hats()

        self.load_pet_status()
        self.init_ui()
        self.start_status_timer()
        self.start_energy_recovery_timer()

        # Atalho para abrir o cheat menu (opcional)
        shortcut = QShortcut(QKeySequence("Ctrl+Alt+C"), self)
        shortcut.activated.connect(self.open_cheat_menu)

    # --- Métodos auxiliares ---
    def load_hats(self):
        hats = {}
        # Constrói o caminho para a pasta "shop_items/hats" relativa à pasta do plugin
        hat_items_path = os.path.join(PLUGIN_DIR, "shop_items", "hats")
        if not os.path.exists(hat_items_path):
            QMessageBox.warning(self, "Erro", f"A pasta de chapéus não foi encontrada em:\n{hat_items_path}")
            return hats
        for file_name in os.listdir(hat_items_path):
            if file_name.endswith(".json"):
                with open(os.path.join(hat_items_path, file_name), "r", encoding="utf-8") as file:
                    hat_data = json.load(file)
                    hats[hat_data['id']] = {"color": QColor(hat_data['color']), "shape": hat_data['shape']}
        return hats

    def init_db(self):
        self.conn = sqlite3.connect(DB_PATH)
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pet_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hunger INTEGER,
                happiness INTEGER,
                energy INTEGER,
                level INTEGER,
                experience INTEGER,
                coins INTEGER,
                equipped_hat TEXT,
                equipped_accessories TEXT,
                unlocked_hats TEXT,
                unlocked_accessories TEXT,
                unlocked_consumables TEXT,
                unlocked_colors TEXT,
                body_style TEXT,
                unlocked_bodies TEXT,
                body_color TEXT
            )
        ''')
        self.conn.commit()

    def load_pet_status(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT hunger, happiness, energy, level, experience, coins, equipped_hat, equipped_accessories,
                   unlocked_hats, unlocked_accessories, unlocked_consumables, unlocked_colors, body_style, unlocked_bodies, body_color 
            FROM pet_status 
            ORDER BY id DESC LIMIT 1
        ''')
        result = cursor.fetchone()
        if result:
            (self.hunger, self.happiness, self.energy, self.level, self.experience, 
             self.coins, self.equipped_hat, equipped_accessories, unlocked_hats, 
             unlocked_accessories, unlocked_consumables, unlocked_colors, self.body_style, unlocked_bodies, self.body_color) = result

            self.unlocked_hats = unlocked_hats.split(",") if unlocked_hats else []
            self.unlocked_accessories = unlocked_accessories.split(",") if unlocked_accessories else []
            self.unlocked_consumables = json.loads(unlocked_consumables) if unlocked_consumables else {}
            self.unlocked_colors = unlocked_colors.split(",") if unlocked_colors else []
            self.unlocked_bodies = unlocked_bodies.split(",") if unlocked_bodies else ["square"]
            self.equipped_accessories = equipped_accessories.split(",") if equipped_accessories else []
        else:
            self.hunger = 100
            self.happiness = 100
            self.energy = 100
            self.level = 1
            self.experience = 0
            self.coins = 0
            self.equipped_hat = None
            self.unlocked_hats = []
            self.unlocked_accessories = []
            self.unlocked_consumables = {}
            self.unlocked_colors = []
            self.body_style = "square"
            self.unlocked_bodies = ["square"]
            self.body_color = "#FFFF00"
            self.equipped_accessories = []
            self.save_pet_status()
            self.is_playing = False

    def save_pet_status(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO pet_status (
                hunger, happiness, energy, level, experience, coins, 
                equipped_hat, equipped_accessories, unlocked_hats, unlocked_accessories, 
                unlocked_consumables, unlocked_colors, body_style, unlocked_bodies, body_color
            ) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.hunger, self.happiness, self.energy, self.level, self.experience, self.coins, 
            self.equipped_hat, ",".join(self.equipped_accessories), ",".join(self.unlocked_hats), 
            ",".join(self.unlocked_accessories), json.dumps(self.unlocked_consumables), ",".join(self.unlocked_colors),
            self.body_style, ",".join(self.unlocked_bodies), 
            self.body_color
        ))
        self.conn.commit()

    # --- Criação da interface do plugin ---
    def init_ui(self):
        layout = QVBoxLayout(self)
        # Cria um QTabWidget para organizar as abas internas do pet game
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self.init_pet_tab()
        self.init_games_tab()
        self.init_pomodoro_tab()
        self.init_shop_tab()
        self.init_pet_config_tab()
        self.setLayout(layout)

    def init_pet_tab(self):
        self.pet_tab = QWidget()
        layout = QVBoxLayout(self.pet_tab)
        font = QFont()
        font.setPointSize(14)
        # Cria o widget responsável pela renderização do pet
        self.pet_widget = self.PetWidget(self)
        layout.addWidget(self.pet_widget)
        # Adiciona status do pet
        status_font = QFont("Arial", 12)
        self.status_hunger_label = QLabel("Fome")
        self.status_hunger_label.setFont(status_font)
        layout.addWidget(self.status_hunger_label)
        self.hunger_bar = QProgressBar()
        self.hunger_bar.setMaximum(100)
        self.hunger_bar.setValue(self.hunger)
        layout.addWidget(self.hunger_bar)
        self.status_happiness_label = QLabel("Felicidade")
        self.status_happiness_label.setFont(status_font)
        layout.addWidget(self.status_happiness_label)
        self.happiness_bar = QProgressBar()
        self.happiness_bar.setMaximum(100)
        self.happiness_bar.setValue(self.happiness)
        layout.addWidget(self.happiness_bar)
        self.status_energy_label = QLabel("Energia")
        self.status_energy_label.setFont(status_font)
        layout.addWidget(self.status_energy_label)
        self.energy_bar = QProgressBar()
        self.energy_bar.setMaximum(100)
        self.energy_bar.setValue(self.energy)
        layout.addWidget(self.energy_bar)
        self.level_label = QLabel(f"Nível: {self.level} (Exp: {self.experience}/{self.get_exp_required()})")
        self.level_label.setFont(font)
        layout.addWidget(self.level_label)
        self.coins_label = QLabel(f"Moedas: {self.coins}")
        self.coins_label.setFont(font)
        layout.addWidget(self.coins_label)
        button_layout = QHBoxLayout()
        self.feed_button = QPushButton("Alimentar", self)
        self.feed_button.setFont(font)
        self.feed_button.clicked.connect(self.feed_pet)
        button_layout.addWidget(self.feed_button)
        self.play_button = QPushButton("Brincar", self)
        self.play_button.setFont(font)
        self.play_button.clicked.connect(self.play_with_pet)
        button_layout.addWidget(self.play_button)
        layout.addLayout(button_layout)
        self.tabs.addTab(self.pet_tab, "Mascote")

    def init_games_tab(self):
        self.games_tab = QWidget()
        layout = QVBoxLayout(self.games_tab)
        minigames = get_minigames()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)
        grid_layout = QGridLayout(scroll_content)
        grid_layout.setSpacing(20)
        row, col = 0, 0
        max_columns = 3
        for game in minigames:
            game_button = QPushButton(self)
            icon_path = game["icon"]
            icon = QIcon(icon_path)
            game_button.setIcon(icon)
            game_button.setIconSize(QSize(90, 90))
            game_button.setText(game["name"])
            game_button.setStyleSheet("text-align: center;")
            game_button.setFixedSize(250, 150)
            game_button.clicked.connect(lambda checked, g=game: self.open_game(g))
            grid_layout.addWidget(game_button, row, col)
            col += 1
            if col == max_columns:
                col = 0
                row += 1
        self.tabs.addTab(self.games_tab, "Minijogos")

    def init_pomodoro_tab(self):
        self.pomodoro_tab = QWidget()
        layout = QVBoxLayout(self.pomodoro_tab)
        font = QFont()
        font.setPointSize(14)
        self.study_time_label = QLabel("Tempo de estudo (minutos):")
        self.study_time_label.setFont(font)
        layout.addWidget(self.study_time_label)
        self.study_time_spinbox = QSpinBox()
        self.study_time_spinbox.setRange(1, 120)
        self.study_time_spinbox.setValue(25)
        self.study_time_spinbox.setFont(font)
        layout.addWidget(self.study_time_spinbox)
        self.break_time_label = QLabel("Tempo de pausa (minutos):")
        self.break_time_label.setFont(font)
        layout.addWidget(self.break_time_label)
        self.break_time_spinbox = QSpinBox()
        self.break_time_spinbox.setRange(1, 60)
        self.break_time_spinbox.setValue(5)
        self.break_time_spinbox.setFont(font)
        layout.addWidget(self.break_time_spinbox)
        self.start_pomodoro_button = QPushButton("Iniciar Pomodoro", self)
        self.start_pomodoro_button.setFont(font)
        self.start_pomodoro_button.clicked.connect(self.start_pomodoro)
        layout.addWidget(self.start_pomodoro_button)
        self.pomodoro_timer_label = QLabel("Tempo restante: 00:00")
        self.pomodoro_timer_label.setFont(font)
        self.pomodoro_timer_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.pomodoro_timer_label)
        self.pomodoro_timer = QTimer(self)
        self.pomodoro_timer.timeout.connect(self.update_pomodoro_timer)
        self.tabs.addTab(self.pomodoro_tab, "Pomodoro")

    def init_shop_tab(self):
        self.shop_tab = QWidget()
        layout = QVBoxLayout(self.shop_tab)
        self.shop_module = ShopModule(self)
        layout.addWidget(self.shop_module)
        self.tabs.addTab(self.shop_tab, "Loja")

    def init_pet_config_tab(self):
        self.pet_config_tab = QWidget()
        layout = QVBoxLayout(self.pet_config_tab)
        font = QFont()
        font.setPointSize(12)
        label = QLabel("Intervalo de queda das necessidades (segundos):")
        label.setFont(font)
        layout.addWidget(label)
        self.status_interval_spinbox = QSpinBox()
        self.status_interval_spinbox.setRange(10, 3600)
        self.status_interval_spinbox.setValue(60)
        self.status_interval_spinbox.setFont(font)
        layout.addWidget(self.status_interval_spinbox)
        update_button = QPushButton("Atualizar Intervalo", self)
        update_button.setFont(font)
        update_button.clicked.connect(self.update_status_interval)
        layout.addWidget(update_button)
        self.tabs.addTab(self.pet_config_tab, "Config. Pet")

    # --- Métodos de funcionamento ---
    def update_status_interval(self):
        new_interval_sec = self.status_interval_spinbox.value()
        new_interval_ms = new_interval_sec * 1000
        self.status_timer.setInterval(new_interval_ms)
        QMessageBox.information(self, "Configuração", f"Intervalo atualizado para {new_interval_sec} segundos.")

    def open_game(self, game):
        game_class = game["class"]
        game_instance = game_class()
        if hasattr(game_instance, "exec_"):
            game_instance.exec_()
            score = game_instance.score
        elif hasattr(game_instance, "run"):
            score = game_instance.run()
        xp_reward_interval = game.get("xp_reward_interval", None)
        coin_reward_interval = game.get("coin_reward_interval", None)
        xp_reward = (score // xp_reward_interval["points"]) * xp_reward_interval["xp"] if xp_reward_interval else 0
        coin_reward = (score // coin_reward_interval["points"]) * coin_reward_interval["coins"] if coin_reward_interval else 0
        self.coins += coin_reward
        self.gain_experience(xp_reward)
        QMessageBox.information(
            self,
            "Minijogo Completo",
            f"Você ganhou {coin_reward} moedas e {xp_reward} de experiência!"
        )
        self.save_pet_status()

    def open_cheat_menu(self):
        self.cheat_menu = CheatMenu(self)
        self.cheat_menu.exec_()

    def start_pomodoro(self):
        self.study_time = self.study_time_spinbox.value() * 60
        self.break_time = self.break_time_spinbox.value() * 60
        self.remaining_time = self.study_time
        self.is_study_phase = True
        self.pomodoro_timer.start(1000)
        self.update_pomodoro_timer()

    def update_pomodoro_timer(self):
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        self.pomodoro_timer_label.setText(f"Tempo restante: {minutes:02}:{seconds:02}")
        if self.remaining_time > 0:
            self.remaining_time -= 1
        else:
            if self.is_study_phase:
                QMessageBox.information(self, "Pomodoro", "Tempo de estudo acabou! Hora da pausa.")
                self.remaining_time = self.break_time
                self.is_study_phase = False
            else:
                QMessageBox.information(self, "Pomodoro", "Pausa finalizada! Hora de voltar ao estudo.")
                self.pomodoro_timer.stop()

    def start_status_timer(self):
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.decrease_status)
        self.status_timer.start(self.status_interval_spinbox.value() * 1000)

    def start_energy_recovery_timer(self):
        self.energy_recovery_timer = QTimer(self)
        self.energy_recovery_timer.timeout.connect(self.recover_energy)
        self.energy_recovery_timer.start(5000)

    def recover_energy(self):
        if not self.is_playing and self.energy < 100:
            self.energy = min(100, self.energy + 5)
            self.update_status_bars()

    def decrease_status(self):
        self.hunger = max(0, self.hunger - 5)
        self.happiness = max(0, self.happiness - 3)
        self.energy = max(0, self.energy - 4)
        self.update_status_bars()
        self.save_pet_status()

    def update_status_bars(self):
        self.hunger_bar.setValue(self.hunger)
        self.happiness_bar.setValue(self.happiness)
        self.energy_bar.setValue(self.energy)
        exp_required = self.get_exp_required()
        self.level_label.setText(f"Nível: {self.level} (Exp: {self.experience}/{exp_required})")
        self.coins_label.setText(f"Moedas: {self.coins}")
        self.pet_widget.update_mood()
        self.pet_widget.update()

    def feed_pet(self):
        if self.hunger < 100:
            self.hunger = min(100, self.hunger + 3)
            self.update_status_bars()
            self.save_pet_status()
        else:
            QMessageBox.information(self, "Alimentar", "O mascote já está satisfeito!")

    def play_with_pet(self):
        if self.energy > 10:
            self.is_playing = True
            self.happiness = min(100, self.happiness + 15)
            self.energy = max(0, self.energy - 10)
            self.coins += 2
            self.gain_experience(10)
            self.update_status_bars()
            self.save_pet_status()
            QTimer.singleShot(10000, self.stop_playing)
        else:
            QMessageBox.warning(self, "Brincar", "O mascote está muito cansado para brincar.")

    def get_exp_required(self):
        return 100 + (self.level - 1) * 50

    def stop_playing(self):
        self.is_playing = False

    def gain_experience(self, amount):
        self.experience += amount
        exp_required = self.get_exp_required()
        while self.experience >= exp_required:
            self.experience -= exp_required
            self.level += 1
            self.coins += 10
            QMessageBox.information(self, "Nível Up!", f"Seu mascote subiu para o nível {self.level} e ganhou 10 moedas!")
            exp_required = self.get_exp_required()
        self.update_status_bars()
        self.save_pet_status()

    # --- Classe interna para renderização do pet ---
    class PetWidget(QWidget):
        def __init__(self, pet_game):
            super().__init__()
            self.pet_game = pet_game
            self.setFixedSize(150, 150)
            self.mood = "happy"

        def update_mood(self):
            if self.pet_game.happiness >= 80:
                self.mood = "happy"
            elif self.pet_game.happiness >= 50:
                self.mood = "neutral"
            else:
                self.mood = "sad"

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            body_color = QColor(self.pet_game.body_color or "#FFFF00")
            body_shape = self.pet_game.body_style or "circle"
            painter.setBrush(QBrush(body_color, Qt.SolidPattern))
            if body_shape == "circle":
                painter.drawEllipse(20, 20, 110, 110)
            elif body_shape == "square":
                painter.drawRect(20, 20, 110, 110)
            elif body_shape == "triangle":
                points = [QPoint(75, 20), QPoint(20, 130), QPoint(130, 130)]
                painter.drawPolygon(QPolygon(points))
            painter.setBrush(QBrush(Qt.black, Qt.SolidPattern))
            painter.drawEllipse(50, 50, 10, 10)
            painter.drawEllipse(90, 50, 10, 10)
            if self.pet_game.equipped_hat and self.pet_game.equipped_hat in self.pet_game.hats:
                hat = self.pet_game.hats[self.pet_game.equipped_hat]
                painter.setBrush(QBrush(hat["color"], Qt.SolidPattern))
                if hat["shape"] == "triangle":
                    points = [QPoint(75, 1), QPoint(50, 40), QPoint(100, 40)]
                    painter.drawPolygon(QPolygon(points))
                elif hat["shape"] == "circle":
                    painter.drawEllipse(60, 1, 30, 30)
                elif hat["shape"] == "square":
                    painter.drawRect(60, 1, 30, 30)
                elif hat["shape"] == "star":
                    points = [
                        QPoint(75, 1), QPoint(85, 40), QPoint(115, 40),
                        QPoint(90, 60), QPoint(100, 90), QPoint(75, 70),
                        QPoint(50, 90), QPoint(60, 60), QPoint(35, 40),
                        QPoint(65, 40)
                    ]
                    painter.drawPolygon(QPolygon(points))
            for accessory_id in self.pet_game.equipped_accessories:
                accessory = next((i for i in self.pet_game.items if i["id"] == accessory_id), None)
                if accessory:
                    color = QColor(accessory.get("color", "#000000"))
                    painter.setPen(QPen(Qt.black, 2))
                    painter.setBrush(QBrush(color, Qt.SolidPattern))
                    if accessory["type"] == "accessory" and accessory["shape"] == "glove":
                        painter.drawEllipse(15, 90, 20, 20)
                        painter.drawEllipse(115, 90, 20, 20)
                    if accessory["type"] == "accessory" and accessory["shape"] == "glasses":
                        painter.drawRect(45, 50, 20, 10)
                        painter.drawRect(85, 50, 20, 10)
                        painter.drawLine(65, 55, 85, 55)
            painter.setPen(QPen(Qt.black, 3))
            if self.mood == "happy":
                painter.drawArc(50, 70, 50, 20, 0, -180 * 16)
            elif self.mood == "neutral":
                painter.drawLine(60, 90, 90, 90)
            elif self.mood == "sad":
                painter.drawArc(50, 90, 50, 20, 0, -180 * 16)

# Variável exigida pelo sistema de plugins para identificar a classe do plugin
plugin_class = PetGamePlugin

# --- Para testes independentes (opcional) ---
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = PetGamePlugin()
    window.setWindowTitle("Mascote")
    window.show()
    sys.exit(app.exec_())
