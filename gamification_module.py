# pet_game_module.py
import sqlite3
import random
import os
import json
import sys
import shutil

from PyQt5.QtWidgets import QPushButton, QMessageBox

# Adiciona a pasta minigames ao sys.path
#sys.path.append(os.path.join(os.path.dirname(__file__), 'minigames'))
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox, QHBoxLayout, QTabWidget, QWidget, 
    QProgressBar, QSpinBox, QComboBox, QScrollArea, QGridLayout, QShortcut
)
from PyQt5.QtCore import Qt, QTimer, QPoint, QSize
from PyQt5.QtGui import QColor, QPainter, QBrush, QPen, QFont, QPolygon, QIcon, QKeySequence

from shop_module import load_shop_items, ShopModule  # Importando diretamente o que é necessário da shop_module
from cheat_menu import CheatMenu
from drawing_utils import draw_shape
from minigames_registry import get_minigames

DB_PATH = 'pet_game.db'

def get_minigames_path():
    # Diretório externo para armazenar minigames
    return os.path.expanduser("~/.pet_game/minigames_config/")


def load_minigames():
    minigames = []
    minigames_path = get_minigames_path()

    # Cria o diretório, se não existir
    if not os.path.exists(minigames_path):
        os.makedirs(minigames_path)

    # Procura por arquivos JSON no diretório
    for file_name in os.listdir(minigames_path):
        if file_name.endswith(".json"):
            try:
                with open(os.path.join(minigames_path, file_name), "r") as file:
                    game_data = json.load(file)
                    minigames.append(game_data)
            except Exception as e:
                print(f"Erro ao carregar o minijogo {file_name}: {e}")

    return minigames


def copiar_pastas_padrao():
    # Caminhos das pastas padrão
    minigames_default_path = os.path.join(os.path.dirname(__file__), "minigames")
    minigames_config_default_path = os.path.join(os.path.dirname(__file__), "minigames_config")

    # Caminhos das pastas de usuário
    minigames_user_path = os.path.expanduser("~/.pet_game/minigames")
    minigames_config_user_path = os.path.expanduser("~/.pet_game/minigames_config")

    # Copiar pasta minigames
    if os.path.exists(minigames_default_path):
        if not os.path.exists(minigames_user_path):
            os.makedirs(minigames_user_path)
        for arquivo in os.listdir(minigames_default_path):
            origem = os.path.join(minigames_default_path, arquivo)
            destino = os.path.join(minigames_user_path, arquivo)
            if not os.path.exists(destino):  # Evita sobrescrever arquivos já existentes
                shutil.copy(origem, destino)

    # Copiar pasta minigames_config
    if os.path.exists(minigames_config_default_path):
        if not os.path.exists(minigames_config_user_path):
            os.makedirs(minigames_config_user_path)
        for arquivo in os.listdir(minigames_config_default_path):
            origem = os.path.join(minigames_config_default_path, arquivo)
            destino = os.path.join(minigames_config_user_path, arquivo)
            if not os.path.exists(destino):  # Evita sobrescrever arquivos já existentes
                shutil.copy(origem, destino)

    # Mensagem de confirmação para o usuário
    QMessageBox.information(None, "Pasta Copiada", "Os minigames e configurações padrão foram copiados com sucesso para a pasta de usuário!")

# Exemplo de como adicionar o botão à interface
def adicionar_botao_copiar_pastas(layout):
    botao_copiar = QPushButton("Copiar Minigames e Configurações")
    botao_copiar.clicked.connect(copiar_pastas_padrao)
    layout.addWidget(botao_copiar)

class PetGameModule(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = sqlite3.connect("pet_game.db")  # Inicializa a conexão com o banco de dados
        #self.hats = self.load_hats()  # Carrega os chapéus e atribui ao atributo 'hats'
        self.init_db()
        self.setWindowTitle("Pet Virtual e Minijogos")
        self.resize(800, 600)  # Aumentei o tamanho para acomodar mais abas e itens
        
        
        self.unlocked_colors = []  # Adicione isso ao inicializar o módulo

        self.unlocked_bodies = ["square"]  # Corpo quadrado como padrão inicial
        self.body_color = "#FFFF00"  # Cor padrão inicial (amarelo)
        self.items = load_shop_items()  # Carrega os itens da loja

        self.is_playing = False  # Inicializa o atributo is_playing
        self.coins = 0  # Inicializa a quantidade de moedas
        
        self.accessories = ["glasses", "gloves"]  # Acessórios disponíveis
        self.unlocked_accessories = []  # Acessórios desbloqueados
        self.equipped_accessories = []  # Inicializa a lista de acessórios equipados

        self.equipped_hat = None  # Nenhum chapéu equipado inicialmente
        self.equipped_accessory = None  # Nenhum acessório equipado inicialmente
        self.body_style = "circle"  # Estilo de corpo inicial
        self.exp_boost_active = False  # Controle do boost de experiência
        
        # Adiciona o atributo unlocked_consumables
        self.unlocked_consumables = {}  # Dicionário para consumíveis com quantidade
        
        self.hats = self.load_hats() 

        self.init_db()
        self.load_pet_status()
        self.init_ui()
        self.start_status_timer()
        self.start_energy_recovery_timer()

        shortcut = QShortcut(QKeySequence("Ctrl+Alt+C"), self)
        shortcut.activated.connect(self.open_cheat_menu)
        
    def load_hats(self):
        hats = {}
        hat_items_path = "shop_items/hats"
        if not os.path.exists(hat_items_path):
            QMessageBox.warning(None, "Erro", "A pasta de chapéus não foi encontrada.")
            return hats

        for file_name in os.listdir(hat_items_path):
            if file_name.endswith(".json"):
                with open(os.path.join(hat_items_path, file_name), "r") as file:
                    hat_data = json.load(file)
                    hats[hat_data['id']] = {"color": QColor(hat_data['color']), "shape": hat_data['shape']}
        return hats


    def init_db(self):
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
            # Carregar consumíveis como dicionário
            self.unlocked_consumables = json.loads(unlocked_consumables) if unlocked_consumables else {}
            self.unlocked_colors = unlocked_colors.split(",") if unlocked_colors else []  # Adicionado
            self.unlocked_bodies = unlocked_bodies.split(",") if unlocked_bodies else ["square"]
            self.equipped_accessories = equipped_accessories.split(",") if equipped_accessories else []
        else:
            # Valores padrão se não houver registro no banco de dados
            self.hunger = 100
            self.happiness = 100
            self.energy = 100
            self.level = 1
            self.experience = 0
            self.coins = 0
            self.equipped_hat = None
            self.unlocked_hats = []
            self.unlocked_accessories = []
            self.unlocked_consumables = {}  # Inicialize como dicionário
            self.unlocked_colors = []  # Inicialize como lista vazia
            self.body_style = "square"
            self.unlocked_bodies = ["square"]
            self.body_color = "#FFFF00"  # Cor padrão amarelo
            self.equipped_accessories = []  # Nenhum acessório equipado inicialmente
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
            ",".join(self.unlocked_accessories), json.dumps(self.unlocked_consumables), ",".join(self.unlocked_colors),  # Adicionado
            self.body_style, ",".join(self.unlocked_bodies), 
            self.body_color
        ))
        self.conn.commit()
            

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.init_pet_tab()
        self.init_games_tab()
        self.init_pomodoro_tab()
        self.init_shop_tab()
        
         # Adiciona o botão para copiar minigames padrão
        config_tab = QWidget()
        config_layout = QVBoxLayout(config_tab) 
        adicionar_botao_copiar_pastas(config_layout)  # Chama a função correta que adiciona o botão

        self.tabs.addTab(config_tab, "Configurações")

        layout.addWidget(self.tabs)


    def init_pet_tab(self):
        self.pet_tab = QWidget()
        layout = QVBoxLayout(self.pet_tab)
        
        font = QFont()
        font.setPointSize(14)
        
        self.pet_widget = PetWidget(self)
        layout.addWidget(self.pet_widget)

        # Status bars
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

        # Botões de interação
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


    def equip_hat(self, hat_name):
        if hat_name in self.hats:  # Verifica se o chapéu existe
            self.equipped_hat = hat_name
            self.pet_widget.update()  # Redesenha o widget
        else:
            QMessageBox.warning(self, "Erro", f"O chapéu {hat_name} não existe.")
        self.save_pet_status()
 

    def init_games_tab(self):
        self.games_tab = QWidget()
        layout = QVBoxLayout(self.games_tab)

        #minigames = load_minigames()  # Carrega os minigames dinamicamente
         # Carrega os minijogos
        minigames = get_minigames()

        # Criar a área de rolagem
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Permite que o conteúdo se ajuste ao tamanho da área
        layout.addWidget(scroll_area)

        # Widget para segurar o conteúdo da rolagem
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)

        # Layout para exibir os minigames como miniaturas
        grid_layout = QGridLayout(scroll_content)
        grid_layout.setSpacing(20)

        # Adicionando os minigames com miniaturas e títulos
        row, col = 0, 0
        max_columns = 3  # Número de colunas por linha (ajuste conforme necessário)

        for game in minigames:
            game_button = QPushButton(self)
            
            # Definir o ícone a partir do JSON
            icon_path = game["icon"]
            icon = QIcon(icon_path)  # Usando o caminho do ícone
            game_button.setIcon(icon)
            game_button.setIconSize(QSize(90, 90))  # Tamanho do ícone
            
            # Definindo o texto com o nome do jogo
            game_button.setText(game["name"])
            
            # Alinhando o texto no centro usando CSS
            game_button.setStyleSheet("text-align: center;")
            
            # Definindo o tamanho fixo do botão
            game_button.setFixedSize(250, 150)  # Tamanho do botão ajustado para 120x120 pixels

            # Ações quando o botão for clicado
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

        # Inicializa a loja diretamente na aba
        self.shop_module = ShopModule(self)
        layout.addWidget(self.shop_module)

        self.tabs.addTab(self.shop_tab, "Loja")
        

    
    def open_game(self, game):
        # Acessa diretamente a classe do jogo do registro
        game_class = game["class"]
        game_instance = game_class()

        # Verifica se o jogo usa PyQt ou Pygame
        if hasattr(game_instance, "exec_"):  # Minijogo baseado em PyQt
            game_instance.exec_()
            score = game_instance.score
        elif hasattr(game_instance, "run"):  # Minijogo baseado em Pygame
            score = game_instance.run()

        # Calcula as recompensas
        xp_reward_interval = game.get("xp_reward_interval", None)
        coin_reward_interval = game.get("coin_reward_interval", None)

        if xp_reward_interval:
            points_per_xp = xp_reward_interval["points"]
            xp_per_interval = xp_reward_interval["xp"]
            xp_reward = (score // points_per_xp) * xp_per_interval
        else:
            xp_reward = 0

        if coin_reward_interval:
            points_per_coin = coin_reward_interval["points"]
            coins_per_interval = coin_reward_interval["coins"]
            coin_reward = (score // points_per_coin) * coins_per_interval
        else:
            coin_reward = 0

        # Aplica as recompensas ao jogador
        self.coins += coin_reward
        self.gain_experience(xp_reward)

        QMessageBox.information(
            self,
            "Minijogo Completo",
            f"Você ganhou {coin_reward} moedas e {xp_reward} de experiência!"
        )

        self.save_pet_status()


    def open_shop(self):
        self.shop = ShopModule(self)
        self.shop.exec_()

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

    #def update_hat_selector(self):
        """Atualiza o combo box de chapéus com os chapéus desbloqueados."""
        #self.hat_selector.clear()
        #self.hat_selector.addItems(["Selecionar chapéu"] + self.unlocked_hats)
        #self.hat_selector.setCurrentText("Selecionar chapéu" if not self.equipped_hat else self.equipped_hat)

    
   
    def start_status_timer(self):
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.decrease_status)
        self.status_timer.start(60000)

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

    def feed_pet(self):
        if self.hunger < 100:
            self.hunger = min(100, self.hunger + 3)
            # QMessageBox.information(self, "Alimentar", "Você alimentou o mascote! Ele está mais feliz agora.")
            self.update_status_bars()
            self.save_pet_status()
            # Atualizar a aba de consumíveis comprados para refletir a nova fome
            self.refresh_consumables_comprados_tab()
        else:
            QMessageBox.information(self, "Alimentar", "O mascote já está satisfeito!")

    def play_with_pet(self):
        if self.energy > 10:
            self.is_playing = True
            self.happiness = min(100, self.happiness + 15)
            self.energy = max(0, self.energy - 10)
            self.coins += 2
            self.gain_experience(10)
            # QMessageBox.information(self, "Brincar", "Você brincou com o mascote e ganhou 5 moedas!")
            self.update_status_bars()
            self.save_pet_status()
            QTimer.singleShot(10000, self.stop_playing)
            # Atualizar a aba de consumíveis comprados para refletir os novos status
            self.refresh_consumables_comprados_tab()
        else:
            QMessageBox.warning(self, "Brincar", "O mascote está muito cansado para brincar.")
    
    def get_exp_required(self):
        return 100 + (self.level - 1) * 50

    def stop_playing(self):
        self.is_playing = False
        # Atualizar a aba de consumíveis comprados para refletir os novos status
        self.refresh_consumables_comprados_tab()

    def gain_experience(self, amount):
        self.experience += amount
        exp_required = 100 + (self.level - 1) * 50

        while self.experience >= exp_required:
            self.experience -= exp_required
            self.level += 1
            self.coins += 10
            QMessageBox.information(self, "Nível Up!", f"Seu mascote subiu para o nível {self.level} e ganhou 10 moedas!")
            exp_required = 100 + (self.level - 1) * 50

        self.update_status_bars()
        self.save_pet_status()

    def open_tetris_game(self):
        self.tetris_game = TetrisGame(self)
        self.tetris_game.exec_()

        # Calcula as recompensas com base na pontuação
        xp_reward = self.tetris_game.score * 1 # 1 XP por ponto
        gold_reward = self.tetris_game.score // 10  # 1 moeda a cada 10 pontos

        # Aplica as recompensas ao jogador
        self.coins += gold_reward
        self.gain_experience(xp_reward)

        # Exibe a mensagem de recompensas
        QMessageBox.information(
            self,
            "Minijogo Completo",
            f"Você ganhou {gold_reward} moedas e {xp_reward} de experiência!"
        )
        
        self.save_pet_status()

    def refresh_consumables_comprados_tab(self):
        # Acessar o módulo de loja e chamar refresh_purchased_consumables
        for i in range(self.shop_module.tabs.count()):
            if self.shop_module.tabs.tabText(i) == "Consumíveis Comprados":
                consumables_comprados_tab = self.shop_module.tabs.widget(i)
                self.shop_module.refresh_purchased_consumables()
                break


class PetWidget(QWidget):
    def __init__(self, pet_game):
        super().__init__()
        self.pet_game = pet_game
        self.setFixedSize(150, 150)
        self.mood = "normal"

    # Atualização no método 'paintEvent'
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Desenhar o corpo do pet
        body_color = QColor(self.pet_game.body_color or "#FFFF00")  # Cor padrão amarelo
        body_shape = self.pet_game.body_style or "circle"  # Shape padrão círculo
        painter.setBrush(QBrush(body_color, Qt.SolidPattern))
        if body_shape == "circle":
            painter.drawEllipse(20, 20, 110, 110)
        elif body_shape == "square":
            painter.drawRect(20, 20, 110, 110)
        elif body_shape == "triangle":
            points = [QPoint(75, 20), QPoint(20, 130), QPoint(130, 130)]
            painter.drawPolygon(QPolygon(points))

        # Desenhar os olhos do pet
        painter.setBrush(QBrush(Qt.black, Qt.SolidPattern))
        painter.drawEllipse(50, 50, 10, 10)  # Olho esquerdo
        painter.drawEllipse(90, 50, 10, 10)  # Olho direito

        # Desenhar chapéu (se equipado)
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
    

        # Desenhar acessórios (se equipados)
        for accessory_id in self.pet_game.equipped_accessories:
            accessory = next((i for i in self.pet_game.items if i["id"] == accessory_id), None)
            if accessory:
                color = QColor(accessory.get("color", "#000000"))
                painter.setPen(QPen(Qt.black, 2))
                painter.setBrush(QBrush(color, Qt.SolidPattern))

                # if accessory["type"] == "gloves":  # Verificando se é uma luva
                if accessory["type"] == "accessory" and accessory["shape"] == "glove":
                    painter.drawEllipse(15, 90, 20, 20)  # Luva esquerda
                    painter.drawEllipse(115, 90, 20, 20)  # Luva direita
                # elif accessory["type"] == "glasses":  # Verificando se é um óculos
                if accessory["type"] == "accessory" and accessory["shape"] == "glasses":
                    painter.drawRect(45, 50, 20, 10)  # Lente esquerda
                    painter.drawRect(85, 50, 20, 10)  # Lente direita
                    painter.drawLine(65, 55, 85, 55)  # Ponte dos óculos


        # Desenhar boca dependendo do humor
        painter.setPen(QPen(Qt.black, 3))
        if self.mood == "happy":
            painter.drawArc(50, 80, 50, 20, 0, 180 * 16)  # Sorriso
        elif self.mood == "playful":
            painter.drawArc(50, 90, 50, 20, 0, -180 * 16)  # Boca brincalhona
        else:
            painter.drawLine(60, 90, 90, 90)  # Boca neutra   


    def update_status_display(self):
        # Atualize a exibição do status conforme necessário
        pass






if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Criar um objeto QFont com tamanho 30
    font = QFont()
    font.setPointSize(30)  # Define o tamanho da fonte
    app.setFont(font)  # Aplica a fonte a toda a aplicação

    window = PetGameModule()
    window.show()
    sys.exit(app.exec_())

