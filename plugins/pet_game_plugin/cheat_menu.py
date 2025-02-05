from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt5.QtCore import Qt

class CheatMenu(QDialog):
    def __init__(self, pet_game, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Menu de Cheats")
        self.resize(300, 400)  # Tamanho maior para acomodar mais opções
        self.pet_game = pet_game  # Referência ao módulo principal para alterar status e moedas
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Botão para adicionar 1000 moedas
        add_coins_button = QPushButton("Adicionar 1000 Moedas")
        add_coins_button.clicked.connect(self.add_coins)
        layout.addWidget(add_coins_button)

        # Botão para adicionar 5000 moedas
        add_big_coins_button = QPushButton("Adicionar 5000 Moedas")
        add_big_coins_button.clicked.connect(self.add_big_coins)
        layout.addWidget(add_big_coins_button)

        # Botão para aumentar 1 nível
        level_up_button = QPushButton("Aumentar 1 Nível")
        level_up_button.clicked.connect(self.level_up)
        layout.addWidget(level_up_button)

        # Botão para definir nível para 99
        set_level_99_button = QPushButton("Definir Nível para 99")
        set_level_99_button.clicked.connect(self.set_level_99)
        layout.addWidget(set_level_99_button)

        # Botão para restaurar status
        restore_status_button = QPushButton("Restaurar Status")
        restore_status_button.clicked.connect(self.restore_status)
        layout.addWidget(restore_status_button)

        # Botão para ganhar 50 de experiência
        gain_exp_button = QPushButton("Ganhar 50 de Experiência")
        gain_exp_button.clicked.connect(self.gain_experience)
        layout.addWidget(gain_exp_button)

        # Botão para resetar progresso
        reset_progress_button = QPushButton("Resetar Progresso")
        reset_progress_button.clicked.connect(self.reset_progress)
        layout.addWidget(reset_progress_button)

        # Botão para alternar modo invencível
        toggle_invincible_button = QPushButton("Alternar Modo Invencível")
        toggle_invincible_button.clicked.connect(self.toggle_invincible)
        layout.addWidget(toggle_invincible_button)

        # Botão para desbloquear todos os itens
        unlock_all_button = QPushButton("Desbloquear Todos os Itens")
        unlock_all_button.clicked.connect(self.unlock_all_items)
        layout.addWidget(unlock_all_button)

    def add_coins(self):
        self.pet_game.coins += 1000
        QMessageBox.information(self, "Cheat Ativado", "1000 moedas adicionadas!")
        self.pet_game.update_status_bars()
        self.pet_game.save_pet_status()

    def add_big_coins(self):
        self.pet_game.coins += 5000
        QMessageBox.information(self, "Cheat Ativado", "5000 moedas adicionadas!")
        self.pet_game.update_status_bars()
        self.pet_game.save_pet_status()

    def level_up(self):
        self.pet_game.level += 1
        QMessageBox.information(self, "Cheat Ativado", f"Seu mascote subiu para o nível {self.pet_game.level}!")
        self.pet_game.update_status_bars()
        self.pet_game.save_pet_status()

    def set_level_99(self):
        self.pet_game.level = 99
        self.pet_game.experience = 0
        QMessageBox.information(self, "Cheat Ativado", "Nível definido para 99!")
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
        self.pet_game.gain_experience(50)  # Ganhar 50 de experiência
        QMessageBox.information(self, "Cheat Ativado", "Você ganhou 50 de experiência!")
        self.pet_game.save_pet_status()

    def reset_progress(self):
        # Reseta os status do pet para os valores iniciais
        self.pet_game.hunger = 100
        self.pet_game.happiness = 100
        self.pet_game.energy = 100
        self.pet_game.level = 1
        self.pet_game.experience = 0
        self.pet_game.coins = 0
        self.pet_game.equipped_hat = None
        self.pet_game.unlocked_hats = []
        self.pet_game.unlocked_accessories = []
        self.pet_game.unlocked_consumables = {}
        self.pet_game.unlocked_colors = []
        self.pet_game.body_style = "square"
        self.pet_game.unlocked_bodies = ["square"]
        self.pet_game.body_color = "#FFFF00"
        self.pet_game.equipped_accessories = []
        QMessageBox.information(self, "Cheat Ativado", "Progresso resetado!")
        self.pet_game.update_status_bars()
        self.pet_game.save_pet_status()

    def toggle_invincible(self):
        # Alterna o modo invencível
        if not hasattr(self.pet_game, "invincible"):
            self.pet_game.invincible = False
        self.pet_game.invincible = not self.pet_game.invincible
        state = "ativado" if self.pet_game.invincible else "desativado"
        QMessageBox.information(self, "Cheat Ativado", f"Modo Invencível {state}!")
        self.pet_game.save_pet_status()

    def unlock_all_items(self):
        # Desbloqueia todos os chapéus disponíveis
        self.pet_game.unlocked_hats = list(self.pet_game.hats.keys())
        # Desbloqueia todos os acessórios, assumindo que self.pet_game.items contém itens do tipo "accessory"
        all_accessory_ids = [item["id"] for item in self.pet_game.items if item.get("type") == "accessory"]
        self.pet_game.unlocked_accessories = all_accessory_ids
        QMessageBox.information(self, "Cheat Ativado", "Todos os itens foram desbloqueados!")
        self.pet_game.update_status_bars()
        self.pet_game.save_pet_status()
