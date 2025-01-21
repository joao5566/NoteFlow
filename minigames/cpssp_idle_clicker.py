import json
import os
import random
import math
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QBrush, QColor

import pygame
class ProgrammingClickerGame(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Programming Clicker Game")
        self.resize(400, 600)
        
        self.init_ui()
        self.load_upgrades()
        self.load_progress()
        self.auto_code_timer = QTimer(self)
        self.auto_code_timer.timeout.connect(self.generate_auto_code)
        self.auto_code_timer.start(1000)  # Gera linhas de código automaticamente a cada segundo

        # Configuração de recompensas de prestígio
        self.xp_reward_interval = {"points": 10, "xp": 1}
        self.coin_reward_interval = {"points": 10, "coins": 1}

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.code_label = QLabel("Linhas de código: 0")
        self.level_label = QLabel("Nível: 1")
        self.xp_label = QLabel("XP: 0")
        self.prestige_label = QLabel("Prestígios: 0")
        
        self.click_button = QPushButton("Escrever Código (+1 linha)")
        self.click_button.clicked.connect(self.write_code)

        self.prestige_button = QPushButton("Fazer Prestígio")
        self.prestige_button.clicked.connect(self.do_prestige)
        
        layout.addWidget(self.code_label)
        layout.addWidget(self.level_label)
        layout.addWidget(self.xp_label)
        layout.addWidget(self.prestige_label)
        layout.addWidget(self.click_button)
        layout.addWidget(self.prestige_button)

        self.upgrades_layout = QVBoxLayout()
        layout.addLayout(self.upgrades_layout)

        self.setLayout(layout)

        self.level = 1
        self.xp = 0
        self.lines_of_code = 0  # Linhas de código acumuladas
        self.score = 0  # Usado como número de prestígios realizados
        self.auto_code_rate = 0  # Linhas automáticas por segundo
        self.click_multiplier = 1  # Multiplicador de linhas por clique
        self.upgrades = {}  # Dicionário de upgrades comprados
        self.prestige_count = 0  # Contador de prestígios realizados

    def write_code(self):
        self.lines_of_code += self.click_multiplier  # Incrementa a pontuação com o multiplicador
        self.xp += 1
        
        if self.xp >= self.get_xp_required():
            self.level_up()
        
        self.update_ui()
        self.save_progress()

    def generate_auto_code(self):
        if self.auto_code_rate > 0:
            self.lines_of_code += self.auto_code_rate
            self.update_ui()
            self.save_progress()

    def load_upgrades(self):
        if os.path.exists("upgrades.json"):
            with open("upgrades.json", "r") as file:
                self.available_upgrades = json.load(file)
        else:
            self.available_upgrades = []

        self.display_upgrades()

    def display_upgrades(self):
        for upgrade in self.available_upgrades:
            button = QPushButton(f"{upgrade['name']} (0) - Custo: {upgrade['cost']} linhas")
            button.clicked.connect(lambda checked, u=upgrade: self.buy_upgrade(u))
            button.setObjectName(upgrade['name'])
            self.upgrades_layout.addWidget(button)

    def buy_upgrade(self, upgrade):
        if self.lines_of_code >= upgrade["cost"]:
            self.lines_of_code -= upgrade["cost"]
            self.apply_upgrade(upgrade)
            self.upgrades[upgrade['name']] = self.upgrades.get(upgrade['name'], 0) + 1
            upgrade["cost"] = int(upgrade["cost"] * 1.5)  # Escalonamento exponencial do custo
            self.update_upgrade_button(upgrade)
        else:
            QMessageBox.warning(self, "Linhas insuficientes", "Você não tem linhas de código suficientes para este upgrade.")

        self.update_ui()
        self.save_progress()

    def update_upgrade_button(self, upgrade):
        for i in range(self.upgrades_layout.count()):
            button = self.upgrades_layout.itemAt(i).widget()
            if button.objectName() == upgrade['name']:
                count = self.upgrades.get(upgrade['name'], 0)
                button.setText(f"{upgrade['name']} ({count}) - Custo: {upgrade['cost']} linhas")
                break

    def apply_upgrade(self, upgrade):
        if upgrade["effect"] == "auto_code_rate":
            self.auto_code_rate += upgrade["value"]
        elif upgrade["effect"] == "click_multiplier":
            self.click_multiplier += upgrade["value"]

    def level_up(self):
        self.level += 1
        self.xp = 0

    def get_xp_required(self):
        return 10 + (self.level - 1) * 5

    def update_ui(self):
        self.code_label.setText(f"Linhas de código: {self.lines_of_code}")
        self.level_label.setText(f"Nível: {self.level}")
        self.xp_label.setText(f"XP: {self.xp}/{self.get_xp_required()}")
        self.prestige_label.setText(f"Prestígios: {self.prestige_count}")
        self.update_upgrade_buttons()

    def update_upgrade_buttons(self):
        for i in range(self.upgrades_layout.count()):
            button = self.upgrades_layout.itemAt(i).widget()
            upgrade = self.available_upgrades[i]
            button.setEnabled(self.lines_of_code >= upgrade["cost"])

            #self.accept()  # Fecha o diálogo e retorna ao sistema principal
    
    def do_prestige(self):
        if self.lines_of_code < 100:  # Exigir uma pontuação mínima para fazer prestígio
            QMessageBox.warning(self, "Prestígio Bloqueado", "Você precisa de pelo menos 100 linhas de código para fazer prestígio.")
            return

        # Calcula as recompensas\ com base nos intervalos configurados
        points_per_xp = self.xp_reward_interval["points"]
        xp_per_interval = self.xp_reward_interval["xp"]
        pet_xp_reward = (self.prestige_count // points_per_xp) * xp_per_interval

        points_per_coin = self.coin_reward_interval["points"]
        coins_per_interval = self.coin_reward_interval["coins"]
        pet_coins_reward = (self.prestige_count // points_per_coin) * coins_per_interval

        QMessageBox.information(self, "Prestígio Concluído!", f"Você ganhou {pet_xp_reward} XP e {pet_coins_reward} moedas para o pet!")

        # Envia as recompensas para o sistema do pet
        if self.parent() and hasattr(self.parent(), 'gain_experience'):
            self.parent().gain_experience(pet_xp_reward)
            self.parent().coins += pet_coins_reward
            self.parent().update_status_bars()
            self.parent().save_pet_status()

        self.prestige_count += 1
        self.score = self.prestige_count  # Atualiza o score com o número de prestígios

        self.lines_of_code = 0
        self.level = 1
        self.xp = 0
        self.auto_code_rate = 0
        self.click_multiplier = 1
        self.upgrades = {}

        self.update_ui()
        self.save_progress()
        self.accept()  # Fecha o diálogo e retorna ao sistema principal



    #self.close
    def save_progress(self):
        progress = {
            "level": self.level,
            "xp": self.xp,
            "lines_of_code": self.lines_of_code,
            "auto_code_rate": self.auto_code_rate,
            "click_multiplier": self.click_multiplier,
            "upgrades": self.upgrades,
            "prestige_count": self.prestige_count,
            "score": self.score
        }
        with open("clicker_progress.json", "w") as file:
            json.dump(progress, file)

    def load_progress(self):
        if os.path.exists("clicker_progress.json"):
            with open("clicker_progress.json", "r") as file:
                progress = json.load(file)
                self.level = progress.get("level", 1)
                self.xp = progress.get("xp", 0)
                self.lines_of_code = progress.get("lines_of_code", 0)
                self.auto_code_rate = progress.get("auto_code_rate", 0)
                self.click_multiplier = progress.get("click_multiplier", 1)
                self.upgrades = progress.get("upgrades", {})
                self.prestige_count = progress.get("prestige_count", 0)
                self.score = progress.get("score", 0)
                self.update_ui()
    
    def init_game(self):
        """Inicializa ou reinicia o jogo."""
        self.level = 1
        self.xp = 0
        self.lines_of_code = 0
        self.auto_code_rate = 0
        self.click_multiplier = 1
        self.upgrades = {}
        self.prestige_count = 0

        self.update_ui()  # Atualiza a interface com os valores iniciais
        self.save_progress()  # Salva o estado inicial no arquivo de progresso


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor("#ADD8E6"), Qt.SolidPattern))
        painter.drawRect(0, 0, self.width(), self.height())

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = ProgrammingClickerGame()
    window.show()
    sys.exit(app.exec_())


