from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt5.QtCore import Qt

class CheatMenu(QDialog):
    def __init__(self, pet_game, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Menu de Cheats")
        self.resize(300, 200)
        self.pet_game = pet_game  # Referência ao módulo principal para alterar status e moedas

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Botão para adicionar moedas
        add_coins_button = QPushButton("Adicionar 1000 Moedas")
        add_coins_button.clicked.connect(self.add_coins)
        layout.addWidget(add_coins_button)

        # Botão para aumentar o nível
        level_up_button = QPushButton("Aumentar Nível")
        level_up_button.clicked.connect(self.level_up)
        layout.addWidget(level_up_button)

        # Botão para restaurar status
        restore_status_button = QPushButton("Restaurar Status")
        restore_status_button.clicked.connect(self.restore_status)
        layout.addWidget(restore_status_button)

        # Botão para ganhar experiência
        gain_exp_button = QPushButton("Ganhar 50 de Experiência")
        gain_exp_button.clicked.connect(self.gain_experience)
        layout.addWidget(gain_exp_button)

    def add_coins(self):
        self.pet_game.coins += 1000
        QMessageBox.information(self, "Cheat Ativado", "100 moedas adicionadas!")
        self.pet_game.update_status_bars()
        self.pet_game.save_pet_status()

    def level_up(self):
        self.pet_game.level += 1
        QMessageBox.information(self, "Cheat Ativado", f"Seu mascote subiu para o nível {self.pet_game.level}!")
        self.pet_game.update_status_bars()
        self.pet_game.save_pet_status()

    def restore_status(self):
        self.pet_game.hunger = 100
        self.pet_game.happiness = 100
        self.pet_game.energy = 100
        QMessageBox.information(self, "Cheat Ativado", "Todos os status foram restaurados!")
        self.pet_game.update_status_bars()
        self.pet_game.save_pet_status()

    def gain_experience(self):
        self.pet_game.gain_experience(50000)
        QMessageBox.information(self, "Cheat Ativado", "Você ganhou 50 de experiência!")
        self.pet_game.save_pet_status()

