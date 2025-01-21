import json
import time
import os

class CppIdleClickerGame:
    def __init__(self):
        self.coins = 0
        self.xp = 0
        self.code_per_second = 1  # Inicialmente o jogador gera 1 linha de código por segundo
        self.speed_multiplier = 1
        self.xp_multiplier = 1
        self.upgrades = []
        self.load_game_configuration()

    def load_game_configuration(self):
        # Caminho para a pasta minigames_config onde o arquivo JSON será lido
        config_path = os.path.join(os.getcwd(), 'minigames_config', 'cpp_idle_clicker.json')
        
        # Verifica se o arquivo de configuração existe na pasta minigames_config
        if not os.path.exists(config_path):
            print("Arquivo de configuração não encontrado!")
            return
        
        with open(config_path) as f:
            config = json.load(f)
            self.name = config["name"]
            self.xp_reward_interval = config["xp_reward_interval"]
            self.coin_reward_interval = config["coin_reward_interval"]
            self.upgrades = config["upgrades"]
            
    def purchase_upgrade(self, upgrade_id):
        # Encontre o upgrade correspondente
        upgrade = next((item for item in self.upgrades if item["id"] == upgrade_id), None)
        if upgrade:
            if self.coins >= upgrade["cost"]:
                # Aplica o upgrade
                self.coins -= upgrade["cost"]
                if upgrade["effect"] == "speed_multiplier":
                    self.speed_multiplier *= upgrade["value"]
                elif upgrade["effect"] == "code_per_second":
                    self.code_per_second *= upgrade["value"]
                elif upgrade["effect"] == "xp_multiplier":
                    self.xp_multiplier *= upgrade["value"]
                print(f"Upgrade {upgrade['name']} comprado! Efeito aplicado: {upgrade['description']}")
            else:
                print(f"Moedas insuficientes para comprar {upgrade['name']}")
        else:
            print("Upgrade não encontrado")

    def earn_coins(self, points):
        # Calcula o número de moedas baseado nos pontos
        coin_reward = self.coin_reward_interval["coins"]
        coins_earned = (points // self.coin_reward_interval["points"]) * coin_reward
        self.coins += coins_earned
        print(f"Ganhou {coins_earned} moedas! Total de moedas: {self.coins}")

    def earn_xp(self, points):
        # Calcula o número de XP baseado nos pontos
        xp_reward = self.xp_reward_interval["xp"]
        xp_earned = (points // self.xp_reward_interval["points"]) * xp_reward * self.xp_multiplier
        self.xp += xp_earned
        print(f"Ganhou {xp_earned} XP! Total de XP: {self.xp}")

    def start_game(self):
        # Inicia o jogo e começa a gerar código
        while True:
            points = self.code_per_second * self.speed_multiplier
            print(f"Gerando {points} linhas de código por segundo...")
            self.earn_coins(points)
            self.earn_xp(points)
            time.sleep(1)  # A cada segundo o jogador ganha moedas e XP

# Testando o jogo
game = CppIdleClickerGame()
game.start_game()  # Inicia o jogo, que será rodado até ser interrompido manualmente

