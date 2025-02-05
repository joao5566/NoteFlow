import json
import os
import random
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox, QGroupBox,
    QScrollArea, QHBoxLayout, QWidget, QGridLayout, QProgressBar, QTabWidget, QListWidget, QListWidgetItem, QInputDialog, QTextEdit, QComboBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

import pygame

class ProgrammingClickerGame(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Programming Clicker Game")
        self.resize(900, 700)
        
        # Inicializa o tema como 'Light' por padrão
        self.current_theme = "Light"
        
        # Carrega estilos definidos
        self.styles = {
            "Dark": """
                QDialog {
                    background-color: #2b2b2b;
                    color: #f0f0f0;
                }
                QLabel {
                    font-family: "Segoe UI", sans-serif;
                }
                QPushButton {
                    background-color: #3c3f41;
                    border: none;
                    color: #f0f0f0;
                    padding: 10px;
                    border-radius: 5px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #555555;
                }
                QGroupBox {
                    border: 1px solid #555555;
                    border-radius: 5px;
                    margin-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                    color: #f0f0f0;
                    font-weight: bold;
                }
                QScrollArea {
                    border: none;
                }
                QProgressBar {
                    border: 2px solid #555555;
                    border-radius: 5px;
                    text-align: center;
                    height: 25px;
                }
                QProgressBar::chunk {
                    background-color: #00aa00;
                    width: 20px;
                }
                QListWidget {
                    background-color: #3c3f41;
                    border: none;
                }
                QListWidget::item {
                    padding: 10px;
                }
                QListWidget::item:selected {
                    background-color: #555555;
                }
            """,
            "Light": """
                QDialog {
                    background-color: #f0f0f0;
                    color: #2b2b2b;
                }
                QLabel {
                    font-family: "Segoe UI", sans-serif;
                }
                QPushButton {
                    background-color: #dcdcdc;
                    border: none;
                    color: #2b2b2b;
                    padding: 10px;
                    border-radius: 5px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #c0c0c0;
                }
                QGroupBox {
                    border: 1px solid #a9a9a9;
                    border-radius: 5px;
                    margin-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                    color: #2b2b2b;
                    font-weight: bold;
                }
                QScrollArea {
                    border: none;
                }
                QProgressBar {
                    border: 2px solid #a9a9a9;
                    border-radius: 5px;
                    text-align: center;
                    height: 25px;
                }
                QProgressBar::chunk {
                    background-color: #00aa00;
                    width: 20px;
                }
                QListWidget {
                    background-color: #ffffff;
                    border: none;
                }
                QListWidget::item {
                    padding: 10px;
                }
                QListWidget::item:selected {
                    background-color: #a9a9a9;
                }
            """,
            # Adicione mais temas aqui se desejar
        }

        # Aplica o tema atual
        self.apply_theme(self.current_theme)

        self.init_ui()
        self.init_game()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Header Section
        header = QHBoxLayout()

        # Game Title
        title = QLabel("Programming Clicker Game")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        header.addWidget(title)

        main_layout.addLayout(header)

        # Tab Widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Game Tab
        self.game_tab = QWidget()
        self.tabs.addTab(self.game_tab, "Jogo")
        game_layout = QVBoxLayout(self.game_tab)

        # Stats Section
        stats_layout = QGridLayout()

        self.code_label = QLabel("Linhas de código: 0")
        self.prestige_label = QLabel("Prestígios nesta sessão: 0")
        self.total_prestige_label = QLabel("Total de Prestígios: 0")
        self.XP_label = QLabel("XP: 0")
        self.level_label = QLabel("Nível: 1")
        self.achievement_label = QLabel("Conquistas: 0")

        stats = [
            self.code_label,
            self.prestige_label,
            self.total_prestige_label,
            self.XP_label,
            self.level_label,
            self.achievement_label
        ]

        for i, stat in enumerate(stats):
            stat.setFont(QFont("Segoe UI", 14))
            stats_layout.addWidget(stat, i // 2, i % 2)

        game_layout.addLayout(stats_layout)

        # Progress Bars
        self.level_progress = QProgressBar()
        self.level_progress.setValue(0)
        self.level_progress.setFormat("Progresso para o próximo nível: 0%")
        game_layout.addWidget(self.level_progress)

        self.prestige_progress = QProgressBar()
        self.prestige_progress.setValue(0)
        self.prestige_progress.setFormat("Progresso para o próximo prestígio: 0%")
        game_layout.addWidget(self.prestige_progress)

        # Buttons Section
        buttons_layout = QHBoxLayout()

        self.click_button = QPushButton("Escrever Código (+1 linha)")
        self.click_button.setFont(QFont("Segoe UI", 14))
        self.click_button.clicked.connect(self.write_code)
        buttons_layout.addWidget(self.click_button)

        self.prestige_button = QPushButton("Fazer Prestígio")
        self.prestige_button.setFont(QFont("Segoe UI", 14))
        self.prestige_button.clicked.connect(self.do_prestige)
        buttons_layout.addWidget(self.prestige_button)

        self.level_up_button = QPushButton("Subir de Nível")
        self.level_up_button.setFont(QFont("Segoe UI", 14))
        self.level_up_button.clicked.connect(self.level_up)
        buttons_layout.addWidget(self.level_up_button)

        # **Novo Botão "Comprar Máximo de Upgrades"**
        self.buy_max_button = QPushButton("Comprar Máximo de Upgrades")
        self.buy_max_button.setFont(QFont("Segoe UI", 14))
        self.buy_max_button.clicked.connect(self.buy_max_upgrades)
        buttons_layout.addWidget(self.buy_max_button)

        game_layout.addLayout(buttons_layout)

        # Upgrades Section
        upgrades_label = QLabel("Upgrades Disponíveis")
        upgrades_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        upgrades_label.setAlignment(Qt.AlignCenter)
        game_layout.addWidget(upgrades_label)

        # Scroll Area for Upgrades
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background-color: transparent;")  # Tornar transparente para herdar o tema

        self.upgrades_container = QWidget()
        self.upgrades_layout = QVBoxLayout()
        self.upgrades_container.setLayout(self.upgrades_layout)
        self.scroll.setWidget(self.upgrades_container)
        game_layout.addWidget(self.scroll)

        # Footer Section
        footer = QLabel("Desenvolvido por [JVRM]")
        footer.setFont(QFont("Segoe UI", 10))

        footer.setStyleSheet("color: #aaaaaa;")
        game_layout.addWidget(footer)

        # Achievements Tab
        self.achievements_tab = QWidget()
        self.tabs.addTab(self.achievements_tab, "Conquistas")
        achievements_layout = QVBoxLayout(self.achievements_tab)

        self.achievements_list = QListWidget()
        achievements_layout.addWidget(self.achievements_list)

        # Statistics Tab
        self.stats_tab = QWidget()
        self.tabs.addTab(self.stats_tab, "Estatísticas")
        stats_layout_tab = QVBoxLayout(self.stats_tab)

        self.total_code_label = QLabel("Total de linhas de código escritas: 0")
        self.total_prestige_label_stats = QLabel("Total de Prestígios: 0")
        self.highest_level_label = QLabel("Nível máximo alcançado: 1")
        self.total_xp_label = QLabel("Total de XP acumulado: 0")
        self.click_multiplier_label = QLabel("Multiplicador de Cliques: 1")
        self.auto_code_rate_label = QLabel("Linhas por Segundo (Auto Generator): 0")
        self.prestige_multiplier_label = QLabel("Multiplicador de Prestígio: 1.00x")
        self.reputation_label = QLabel("Reputação: 0")

        for label in [
            self.total_code_label, 
            self.total_prestige_label_stats, 
            self.highest_level_label, 
            self.total_xp_label,
            self.click_multiplier_label,
            self.auto_code_rate_label,
            self.prestige_multiplier_label,
            self.reputation_label
        ]:
            label.setFont(QFont("Segoe UI", 14))
            stats_layout_tab.addWidget(label)

        # Adicionar botão de feedback na aba "Estatísticas"
        self.feedback_button = QPushButton("Enviar Feedback")
        self.feedback_button.setFont(QFont("Segoe UI", 14))
        self.feedback_button.clicked.connect(self.open_feedback_form)
        stats_layout_tab.addWidget(self.feedback_button)

        # Adicionar seção de referências na aba "Estatísticas"
        self.referral_label = QLabel("Seu Código de Referência: ABC123")
        self.referral_label.setFont(QFont("Segoe UI", 14))
        stats_layout_tab.addWidget(self.referral_label)

        self.redeem_referral_button = QPushButton("Usar Código de Referência")
        self.redeem_referral_button.setFont(QFont("Segoe UI", 14))
        self.redeem_referral_button.clicked.connect(self.prompt_redeem_referral)
        stats_layout_tab.addWidget(self.redeem_referral_button)

        # Timer para geração automática de código
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.generate_auto_code)
        self.timer.start(1000)

        # Adicionar aba de Temas
        self.themes_tab = QWidget()
        self.tabs.addTab(self.themes_tab, "Temas")
        themes_layout = QVBoxLayout(self.themes_tab)

        theme_selection_layout = QHBoxLayout()
        theme_label = QLabel("Selecione um tema:")
        theme_label.setFont(QFont("Segoe UI", 14))
        theme_selection_layout.addWidget(theme_label)

        self.theme_combo = QComboBox()
        self.theme_combo.setFont(QFont("Segoe UI", 14))
        self.theme_combo.addItems(self.styles.keys())  # Adiciona os nomes dos temas disponíveis
        self.theme_combo.setCurrentText(self.current_theme)
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        theme_selection_layout.addWidget(self.theme_combo)

        themes_layout.addLayout(theme_selection_layout)

        # Opcional: Previews ou descrições dos temas podem ser adicionados aqui

    def init_game(self):
        # Game Variables
        self.lines_of_code = 0
        self.prestige_score = 0  # Linhas de código acumuladas para prestígio
        self.score = 0  # Prestígios realizados na sessão
        self.XP = 0
        self.auto_code_rate = 0
        self.click_multiplier = 1
        self.prestige_multiplier = 1.0
        self.level = 1
        self.highest_level = 1
        self.achievements = 0
        self.total_prestiges = 0
        self.prestiges_in_session = 0  # Prestígios feitos na sessão atual
        self.is_game_over = False
        self.available_upgrades = []
        self.upgrades_owned = {}
        self.total_lines_written = 0  # Estatística total de linhas escritas
        self.game_time_minutes = 0  # Tempo de jogo em minutos
        self.reputation = 0
        self.referral_code = "ABC123"  # Exemplo de código de referência
        self.leaderboard = []

        # Definição de Conquistas
        self.available_achievements = [
            # ... [Lista de conquistas existente]
        ]

        self.achievements_unlocked = set()

        self.available_trophies = [
            # Adicione troféus conforme necessário
        ]

        self.load_upgrades()
        self.load_progress()
        self.display_upgrades()
        self.display_achievements()
        self.update_ui()

        # Timer para rastrear o tempo de jogo
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.track_game_time)
        self.time_timer.start(60000)  # Atualiza a cada minuto

    def apply_theme(self, theme_name):
        """Aplica o tema selecionado."""
        style = self.styles.get(theme_name, self.styles["Dark"])
        self.setStyleSheet(style)

    def change_theme(self, theme_name):
        """Muda o tema e salva a seleção."""
        self.current_theme = theme_name
        self.apply_theme(theme_name)
        self.save_progress()  # Salva o tema selecionado

    def write_code(self):
        if self.is_game_over:
            return

        increment = self.click_multiplier * self.prestige_multiplier
        self.lines_of_code += increment
        self.prestige_score += increment
        self.total_lines_written += increment
        self.XP += increment * 0.1  # Exemplo de ganho de XP
        self.update_ui()
        self.check_prestige_progress()
        self.check_achievements()

    def generate_auto_code(self):
        if self.is_game_over or self.auto_code_rate == 0:
            return

        increment = self.auto_code_rate * self.prestige_multiplier
        self.lines_of_code += increment
        self.prestige_score += increment
        self.total_lines_written += increment
        self.XP += increment * 0.1  # Exemplo de ganho de XP
        self.update_ui()
        self.check_prestige_progress()
        self.check_achievements()

    def load_upgrades(self):
        if os.path.exists("upgrades.json"):
            with open("upgrades.json", "r") as file:
                self.available_upgrades = json.load(file)
        else:
            # Exemplo de upgrades caso o arquivo não exista
            self.available_upgrades = [
                {
                    "name": "Auto Generator I",
                    "description": "Aumenta a geração automática de código em +1 por segundo.",
                    "base_cost": 100,
                    "current_cost": 100,
                    "effect": "auto_code_rate",
                    "value": 1,
                    "category": "Geradores"
                },
                {
                    "name": "Auto Generator II",
                    "description": "Aumenta a geração automática de código em +5 por segundo.",
                    "base_cost": 500,
                    "current_cost": 500,
                    "effect": "auto_code_rate",
                    "value": 5,
                    "category": "Geradores"
                },
                # Adicione mais upgrades conforme necessário
            ]

        # Garantir que todos os upgrades tenham 'base_cost' e 'current_cost'
        for upgrade in self.available_upgrades:
            if "base_cost" not in upgrade:
                upgrade["base_cost"] = 100  # Define um valor padrão para 'base_cost'
            if "current_cost" not in upgrade:
                upgrade["current_cost"] = upgrade.get("base_cost", 100)  # Inicializa 'current_cost' com 'base_cost'
            if "level" not in upgrade:
                upgrade["level"] = 1  # Inicializa 'level' se não existir

    def display_upgrades(self):
        """Exibe os upgrades carregados na interface, organizados por categoria."""
        self.upgrades_layout.setAlignment(Qt.AlignTop)  # Alinha os upgrades no topo
        categories = {}
        for upgrade in self.available_upgrades:
            category = upgrade.get("category", "Outros")
            if category not in categories:
                categories[category] = []
            categories[category].append(upgrade)

        # Limpa a disposição atual
        while self.upgrades_layout.count():
            child = self.upgrades_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for category, upgrades in categories.items():
            group_box = QGroupBox(category)
            group_layout = QVBoxLayout()
            for upgrade in upgrades:
                owned = self.upgrades_owned.get(upgrade['name'], 0)
                button = QPushButton(
                    f"{upgrade['name']} (x{owned})\n{upgrade['description']}\nCusto: {upgrade['current_cost']} linhas"
                )
                # Correção: Use uma função auxiliar para evitar a captura tardia do valor de 'upgrade'
                button.clicked.connect(lambda checked, u=upgrade: self.buy_upgrade(u))
                button.setObjectName(upgrade['name'])
                button.setStyleSheet("""
                    QPushButton {
                        text-align: left;
                        padding: 10px;
                        margin: 5px 0;
                    }
                """)
                group_layout.addWidget(button)
            group_box.setLayout(group_layout)
            self.upgrades_layout.addWidget(group_box)

    def display_achievements(self):
        """Inicializa a lista de conquistas na aba de conquistas."""
        self.achievements_list.clear()
        for achievement in self.available_achievements:
            item_text = f"{achievement['name']}: {'Desbloqueada' if achievement['key'] in self.achievements_unlocked else 'Bloqueada'}"
            item = QListWidgetItem(item_text)
            if achievement['key'] in self.achievements_unlocked:
                item.setForeground(QColor('#00ff00'))  # Verde para desbloqueada
            else:
                item.setForeground(QColor('#ff0000'))  # Vermelho para bloqueada
            self.achievements_list.addItem(item)

    def buy_upgrade(self, upgrade):
        """Permite a compra de upgrades se o jogador tiver linhas suficientes."""
        try:
            base_cost = upgrade["base_cost"]
            current_cost = upgrade["current_cost"]
            level = upgrade.get("level", 1)
        except KeyError as e:
            QMessageBox.critical(self, "Erro de Upgrade", f"Chave faltante: {e}")
            return

        if self.lines_of_code >= current_cost:
            self.lines_of_code -= current_cost
            self.apply_upgrade(upgrade)
            upgrade["level"] = level + 1
            upgrade["current_cost"] = int(upgrade["base_cost"] * (1.5 ** upgrade["level"]))  # Custo crescente
            self.upgrades_owned[upgrade['name']] = self.upgrades_owned.get(upgrade['name'], 0) + 1
            self.update_ui()
            self.update_upgrade_button(upgrade)
            self.check_upgrade_combinations()  # Chamada para verificar combinações de upgrades
            self.save_progress()
            self.check_achievements()
        else:
            QMessageBox.warning(self, "Linhas insuficientes", "Você não tem linhas suficientes para este upgrade.")

    def buy_max_upgrades(self):
        """Permite ao jogador comprar o máximo de upgrades possíveis."""
        upgrades_bought = False  # Flag para verificar se algum upgrade foi comprado

        # Iterar sobre todos os upgrades disponíveis
        for upgrade in self.available_upgrades:
            while self.lines_of_code >= upgrade["current_cost"]:
                self.buy_upgrade(upgrade)
                upgrades_bought = True

        if upgrades_bought:
            QMessageBox.information(self, "Upgrades Comprados", "Você comprou o máximo de upgrades possíveis!")
        else:
            QMessageBox.information(self, "Nenhum Upgrade Comprável", "Você não tem linhas de código suficientes para comprar upgrades.")

    def apply_upgrade(self, upgrade):
        """Aplica o efeito do upgrade ao jogo."""
        if upgrade["effect"] == "auto_code_rate":
            self.auto_code_rate += upgrade["value"]
        elif upgrade["effect"] == "click_multiplier":
            self.click_multiplier += upgrade["value"]
        elif upgrade["effect"] == "prestige_multiplier":
            self.prestige_multiplier *= upgrade["value"]

    def update_upgrade_button(self, upgrade):
        """Atualiza o texto do botão de upgrade após a compra."""
        for i in range(self.upgrades_layout.count()):
            group_box = self.upgrades_layout.itemAt(i).widget()
            for j in range(group_box.layout().count()):
                button = group_box.layout().itemAt(j).widget()
                if button.objectName() == upgrade['name']:
                    count = self.upgrades_owned.get(upgrade['name'], 0)
                    button.setText(
                        f"{upgrade['name']} (x{count})\n{upgrade['description']}\nCusto: {upgrade['current_cost']} linhas"
                    )
                    break

    def level_up(self):
        """Permite ao jogador subir de nível se tiver linhas de código suficientes."""
        required = self.calculate_level_requirement()
        if self.lines_of_code >= required:
            self.level += 1
            self.lines_of_code -= required  # Subtrai as linhas de código necessárias para o nível
            if self.level > self.highest_level:
                self.highest_level = self.level
            # Bônus de Nível
            self.click_multiplier += 1  # Bônus no multiplicador de cliques
            self.auto_code_rate += 1    # Bônus na geração automática de código
            self.update_ui()
            self.save_progress()
            # QMessageBox.information(self, "Nível Up!", f"Parabéns! Você alcançou o nível {self.level}.")
        else:
            QMessageBox.warning(
                self,
                "Nível Bloqueado",
                f"Você precisa de pelo menos {int(required)} linhas de código para subir de nível."
            )

    def update_ui(self):
        self.code_label.setText(f"Linhas de código: {int(self.lines_of_code)}")
        self.prestige_label.setText(f"Prestígios nesta sessão: {self.prestiges_in_session}")
        self.total_prestige_label.setText(f"Total de Prestígios: {self.total_prestiges}")
        self.XP_label.setText(f"XP: {int(self.XP)}")
        self.level_label.setText(f"Nível: {self.level}")
        self.achievement_label.setText(f"Conquistas: {self.achievements}")

        # Atualizar barras de progresso
        level_requirement = self.calculate_level_requirement()
        progress_percent = (self.lines_of_code / level_requirement) * 100 if level_requirement else 0
        progress_percent = min(progress_percent, 100)
        self.level_progress.setValue(int(progress_percent))
        self.level_progress.setFormat(f"Progresso para o próximo nível: {int(progress_percent)}%")

        prestige_requirement = self.calculate_prestige_requirement()
        prestige_progress_percent = (self.prestige_score / prestige_requirement) * 100 if prestige_requirement else 0
        prestige_progress_percent = min(prestige_progress_percent, 100)
        self.prestige_progress.setValue(int(prestige_progress_percent))
        self.prestige_progress.setFormat(f"Progresso para o próximo prestígio: {int(prestige_progress_percent)}%")

        # Atualizar aba de estatísticas
        self.total_code_label.setText(f"Total de linhas de código escritas: {int(self.total_lines_written)}")
        self.total_prestige_label_stats.setText(f"Total de Prestígios: {self.total_prestiges}")
        self.highest_level_label.setText(f"Nível máximo alcançado: {self.highest_level}")
        self.total_xp_label.setText(f"Total de XP acumulado: {int(self.XP)}")
        self.click_multiplier_label.setText(f"Multiplicador de Cliques: {self.click_multiplier}")
        self.auto_code_rate_label.setText(f"Linhas por Segundo (Auto Generator): {self.auto_code_rate}")
        self.prestige_multiplier_label.setText(f"Multiplicador de Prestígio: {self.prestige_multiplier:.2f}x")
        self.reputation_label.setText(f"Reputação: {self.reputation}")

        # Atualizar aba de conquistas
        self.display_achievements()

    def do_prestige(self):
        required_lines = self.calculate_prestige_requirement()
        if self.prestige_score < required_lines:
            QMessageBox.warning(
                self, 
                "Prestígio Bloqueado", 
                f"Você precisa de pelo menos {int(required_lines)} linhas de código para fazer prestígio."
            )
            return

        # Atualiza XP e Total de Prestígios
        self.XP += self.prestige_score
        self.total_prestiges += 1
        self.prestiges_in_session += 1  # Incrementa o prestígio na sessão
        self.score = self.prestiges_in_session  # Atualiza o score para retornar ao fechar o jogo

        # Bônus de Prestígio Total
        prestige_bonus = 1 + (self.total_prestiges * 0.01)  # 1% por prestígio total
        self.prestige_multiplier *= 1.1  # Aumenta o multiplicador de prestígio em 10%
        self.prestige_multiplier *= prestige_bonus  # Aplica o bônus acumulado

        QMessageBox.information(
            self, 
            "Prestígio Realizado", 
            f"Você fez prestígio!\nTotal de Prestígios nesta sessão: {self.prestiges_in_session}\nXP Ganho: {int(self.prestige_score)}\nMultiplicador de Prestígio: {self.prestige_multiplier:.2f}x"
        )

        # Reseta o estado do jogo (exceto linhas de código)
        self.prestige_score = 0
        self.auto_code_rate = 0
        self.click_multiplier = 1
        self.level = 1
        self.achievements = 0
        self.upgrades_owned = {}
        self.clear_upgrades()
        self.display_upgrades()

        self.update_ui()
        self.save_progress()

    def calculate_level_requirement(self):
        """Calcula o número de linhas necessárias para o próximo nível."""
        return 100 * self.level

    def calculate_prestige_requirement(self):
        """Calcula o número de linhas necessárias para o próximo prestígio."""
        base_requirement = 1000
        multiplier = 1.5
        return int(base_requirement * (multiplier ** self.total_prestiges))

    def clear_upgrades(self):
        """Remove todos os grupos de upgrades da interface."""
        while self.upgrades_layout.count():
            child = self.upgrades_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def closeEvent(self, event):
        """Salva o progresso ao fechar o jogo e reseta o prestígio da sessão."""
        self.save_progress()
        self.prestiges_in_session = 0  # Reseta o prestígio da sessão
        event.accept()

    def game_over(self):
        self.is_game_over = True
        QMessageBox.information(self, "Game Over", f"Fim de jogo! Linhas de código: {int(self.lines_of_code)}")
        self.accept()  # Fecha o diálogo e retorna ao sistema principal

    def save_progress(self):
        progress = {
            "lines_of_code": self.lines_of_code,
            "prestige_score": self.prestige_score,
            "XP": self.XP,
            "auto_code_rate": self.auto_code_rate,
            "click_multiplier": self.click_multiplier,
            "prestige_multiplier": self.prestige_multiplier,
            "upgrades_owned": self.upgrades_owned,
            "level": self.level,
            "highest_level": self.highest_level,
            "achievements": self.achievements,
            "total_prestiges": self.total_prestiges,
            # "prestiges_in_session": self.prestiges_in_session,  # Removido
            "total_lines_written": self.total_lines_written,
            "achievements_unlocked": list(self.achievements_unlocked),
            "reputation": self.reputation,
            "leaderboard": self.leaderboard,
            "current_theme": self.current_theme  # Salva o tema atual
        }
        with open("clicker_progress.json", "w") as file:
            json.dump(progress, file, indent=4)

    def load_progress(self):
        if os.path.exists("clicker_progress.json"):
            with open("clicker_progress.json", "r") as file:
                progress = json.load(file)
                self.lines_of_code = progress.get("lines_of_code", 0)
                self.prestige_score = progress.get("prestige_score", 0)
                self.XP = progress.get("XP", 0)
                self.auto_code_rate = progress.get("auto_code_rate", 0)
                self.click_multiplier = progress.get("click_multiplier", 1)
                self.prestige_multiplier = progress.get("prestige_multiplier", 1.0)
                self.upgrades_owned = progress.get("upgrades_owned", {})
                self.level = progress.get("level", 1)
                self.highest_level = progress.get("highest_level", 1)
                self.achievements = progress.get("achievements", 0)
                self.total_prestiges = progress.get("total_prestiges", 0)
                # self.prestiges_in_session = progress.get("prestiges_in_session", 0)  # Removido
                self.prestiges_in_session = 0  # Inicializa como 0
                self.total_lines_written = progress.get("total_lines_written", 0)
                self.achievements_unlocked = set(progress.get("achievements_unlocked", []))
                self.reputation = progress.get("reputation", 0)
                self.leaderboard = progress.get("leaderboard", [])
                self.current_theme = progress.get("current_theme", "Light")
                self.theme_combo.setCurrentText(self.current_theme)  # Atualiza o ComboBox de temas
                self.apply_theme(self.current_theme)
                self.apply_owned_upgrades()
                self.update_ui()

    def apply_owned_upgrades(self):
        """Aplica os upgrades que o jogador já comprou ao carregar o progresso."""
        for upgrade in self.available_upgrades:
            name = upgrade['name']
            if name in self.upgrades_owned:
                count = self.upgrades_owned[name]
                for _ in range(count):
                    self.apply_upgrade(upgrade)

    def check_prestige_progress(self):
        """Atualiza a barra de progresso para o prestígio."""
        pass  # Implementar se necessário

    def check_achievements(self):
        """Verifica e atualiza conquistas com base no progresso do jogador."""
        new_achievements = []

        for achievement in self.available_achievements:
            key = achievement['key']
            if key in self.achievements_unlocked:
                continue  # Já desbloqueada

            categoria = achievement.get("category", "")
            if categoria == "Linhas de Código":
                # Extrai o número de linhas a partir da descrição
                try:
                    required = int(''.join(filter(str.isdigit, achievement['description'])))
                except ValueError:
                    required = 0
                if self.total_lines_written >= required:
                    new_achievements.append(achievement)
            elif categoria == "Nível":
                try:
                    required_level = int(''.join(filter(str.isdigit, achievement['description'])))
                except ValueError:
                    required_level = 0
                if self.level >= required_level:
                    new_achievements.append(achievement)
            elif categoria == "Prestígio":
                try:
                    required_prestiges = int(''.join(filter(str.isdigit, achievement['description'])))
                except ValueError:
                    required_prestiges = 0
                if self.total_prestiges >= required_prestiges:
                    new_achievements.append(achievement)
            elif categoria == "Upgrades":
                if "Comprou" in achievement['description']:
                    try:
                        required_upgrades = int(''.join(filter(str.isdigit, achievement['description'])))
                    except ValueError:
                        required_upgrades = 0
                    total_upgrades = sum(self.upgrades_owned.values())
                    if total_upgrades >= required_upgrades:
                        new_achievements.append(achievement)
                elif "Possui todos os upgrades" in achievement['description']:
                    # Implementar se houver conquistas desse tipo
                    pass
            elif categoria == "XP":
                try:
                    required_xp = int(''.join(filter(str.isdigit, achievement['description'])))
                except ValueError:
                    required_xp = 0
                if self.XP >= required_xp:
                    new_achievements.append(achievement)
            elif categoria == "Tempo de Jogo":
                try:
                    required_minutes = int(''.join(filter(str.isdigit, achievement['description'])))
                except ValueError:
                    required_minutes = 0
                if self.game_time_minutes >= required_minutes:
                    new_achievements.append(achievement)
            elif categoria == "Combinações":
                # Implementar condições específicas para combinações
                pass
            elif categoria == "Diversas":
                # Implementar condições variadas
                pass
            # Adicione mais categorias conforme necessário

        for achievement in new_achievements:
            self.achievements_unlocked.add(achievement['key'])
            self.achievements += 1
            self.apply_conquest_reward(achievement)
            self.update_ui()
            self.save_progress()
            QMessageBox.information(self, "Conquista!", f"Você desbloqueou a conquista: {achievement['name']}!")

    def apply_conquest_reward(self, achievement):
        """Aplica a recompensa da conquista ao jogo."""
        reward = achievement.get("reward", {})
        for key, value in reward.items():
            if key == "lines_of_code":
                self.lines_of_code += value
            elif key == "click_multiplier":
                self.click_multiplier += value
            elif key == "auto_code_rate":
                self.auto_code_rate += value
            elif key == "prestige_multiplier":
                self.prestige_multiplier *= value
            # Adicione mais tipos de recompensas conforme necessário
        self.update_ui()

    def track_game_time(self):
        """Rastreia o tempo de jogo em minutos."""
        self.game_time_minutes += 1
        self.update_ui()

    def open_feedback_form(self):
        self.feedback_dialog = FeedbackDialog(self)
        self.feedback_dialog.exec_()

    def redeem_referral_code(self, code):
        if code == self.referral_code:
            QMessageBox.warning(self, "Código Inválido", "Você não pode se referenciar.")
            return
        # Implemente lógica para verificar se o código existe
        # Exemplo simplificado:
        # Suponha que qualquer código diferente de 'ABC123' seja válido
        if code != "ABC123":
            self.lines_of_code += 500  # Recompensa para quem usou o código
            self.reputation += 10  # Recompensa de reputação
            self.update_ui()
            self.save_progress()
            QMessageBox.information(self, "Código Recompensado", "Você recebeu 500 linhas de código por usar o código de referência!")
        else:
            QMessageBox.warning(self, "Código Inválido", "O código digitado é inválido.")

    def prompt_redeem_referral(self):
        code, ok = QInputDialog.getText(self, "Redeem Referral", "Digite o código de referência:")
        if ok and code:
            self.redeem_referral_code(code)

    def run(self):
        self.exec_()
        return self.score  # Retorna o score após fechar o diálogo

    def check_upgrade_combinations(self):
        """
        Verifica combinações de upgrades e aplica bônus se certas combinações forem atendidas.
        Este método foi adicionado para evitar o erro AttributeError.
        """
        # Exemplo de implementação: Se o jogador possuir ambos "Auto Generator I" e "Click Booster I", aplicar um bônus
        if (
            self.upgrades_owned.get("Auto Generator I", 0) > 0 and
            self.upgrades_owned.get("Click Booster I", 0) > 0
        ):
            # Aplicar um bônus específico, por exemplo, aumentar o prestige_multiplier
            self.prestige_multiplier *= 1.05  # Aumenta em 5%
            QMessageBox.information(self, "Bônus de Combinação!", "Você ativou uma combinação de upgrades! Multiplicador de Prestígio aumentado em 5%.")

        # Adicione mais verificações de combinações conforme necessário

class FeedbackDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enviar Feedback")
        self.setFixedSize(400, 300)
        layout = QVBoxLayout(self)

        self.feedback_label = QLabel("Digite seu feedback:")
        layout.addWidget(self.feedback_label)

        self.feedback_text = QTextEdit()
        layout.addWidget(self.feedback_text)

        self.submit_button = QPushButton("Enviar")
        self.submit_button.clicked.connect(self.submit_feedback)
        layout.addWidget(self.submit_button)

    def submit_feedback(self):
        feedback = self.feedback_text.toPlainText()
        if feedback:
            with open("feedback.txt", "a") as file:
                file.write(feedback + "\n---\n")
            QMessageBox.information(self, "Obrigado!", "Seu feedback foi enviado. Obrigado!")
            self.close()
        else:
            QMessageBox.warning(self, "Vazio", "Por favor, digite algo antes de enviar.")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Alterado de 'kvantum' para 'Fusion' para evitar o aviso

    window = ProgrammingClickerGame()
    final_score = window.run()
    print(f"Score final (Prestígios realizados na sessão): {final_score}")
    sys.exit()

