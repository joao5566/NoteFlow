import os

# Determina o diretório onde este módulo está localizado
module_dir = os.path.dirname(os.path.abspath(__file__))

# Função auxiliar para construir o caminho de um arquivo dentro da pasta "minigames"
def minigame_file(filename):
    # Assume que os arquivos dos minijogos estão na subpasta "minigames"
    return os.path.join(module_dir, "minigames", filename)

# Função auxiliar para construir o caminho de um ícone dentro da pasta "game_icons"
def game_icon(icon_filename):
    # Assume que os ícones estão na subpasta "game_icons" dentro da pasta "minigames"
    return os.path.join(module_dir, "minigames", "game_icons", icon_filename)

from minigames.block_stack import BlockStack
from minigames.cpp_idle_clicker import ProgrammingClickerGame
from minigames.defender import DefesaDasFormas
from minigames.flappy import FlappyPetGame
from minigames.memory import MemoryGame1 as MemoryGame1
from minigames.memory_game import MemoryGame as MemoryGame
from minigames.forma_tower import StackGame as IceTowerGame
from minigames.pong import PongGame
from minigames.snake_game import SnakeGame
from minigames.SlidingPuzzleGame import SlidingPuzzleGame

# Registro dos minijogos
def get_minigames():
    return [
        {
            "id": "block_stack",
            "name": "Block Stack",
            "file": minigame_file("block_stack.py"),
            "class": BlockStack,
            "icon": game_icon("block.png"),
            "xp_reward_interval": {"points": 10, "xp": 1},
            "coin_reward_interval": {"points": 10, "coins": 1},
        },
        {
            "id": "clicker",
            "name": "Programming Clicker",
            "file": minigame_file("cpp_idle_clicker.py"),
            "class": ProgrammingClickerGame,
            "icon": game_icon("cpp.png"),
            "xp_reward_interval": {"points": 1, "xp": 30},
            "coin_reward_interval": {"points": 1, "coins": 50},
        },
        {
            "id": "defender",
            "name": "Defesa das formas",
            "file": minigame_file("defender.py"),
            "class": DefesaDasFormas,
            "icon": game_icon("defender.png"),
            "xp_reward_interval": {"points": 5, "xp": 1},
            "coin_reward_interval": {"points": 5, "coins": 1},
        },
        {
            "id": "flappy",
            "name": "Flappy pet (Pygame)",
            "file": minigame_file("flappy.py"),
            "class": FlappyPetGame,
            "icon": game_icon("flappy.png"),
            "xp_reward_interval": {"points": 1, "xp": 10},
            "coin_reward_interval": {"points": 1, "coins": 5},
        },
        {
            "id": "memory_1",
            "name": "Jogo da memória",
            "file": minigame_file("memory.py"),
            "class": MemoryGame1,
            "icon": game_icon("memory1.png"),
            "xp_reward_interval": {"points": 10, "xp": 1},
            "coin_reward_interval": {"points": 10, "coins": 1},
        },
        {
            "id": "memory_game",
            "name": "Jogo de Memória",
            "file": minigame_file("memory_game.py"),
            "class": MemoryGame,
            "icon": game_icon("memori.png"),
            "xp_reward_interval": {"points": 1, "xp": 1},
            "coin_reward_interval": {"points": 2, "coins": 1},
        },
        {
            "id": "pong",
            "name": "Pong",
            "file": minigame_file("pong.py"),
            "class": PongGame,
            "icon": game_icon("pong.png"),
            "xp_reward_interval": {"points": 1, "xp": 5},
            "coin_reward_interval": {"points": 1, "coins": 10},
        },
        {
            "id": "snake_game",
            "name": "Jogo da Cobrinha",
            "file": minigame_file("snake_game.py"),
            "class": SnakeGame,
            "icon": game_icon("snake.png"),
            "xp_reward_interval": {"points": 1, "xp": 1},
            "coin_reward_interval": {"points": 1, "coins": 1},
        },
        {
            "id": "formaTower",
            "name": "Forma Tower",
            "file": minigame_file("forma_tower.py"),
            "class": IceTowerGame,
            "icon": game_icon("stack.png"),
            "xp_reward_interval": {"points": 1, "xp": 5},
            "coin_reward_interval": {"points": 1, "coins": 10},
        },
        {
            "id": "SlidingPuzzleGame",
            "name": "Puzzle Deslizante",
            "file": minigame_file("SlidingPuzzleGame.py"),
            "class": SlidingPuzzleGame,
            "icon": game_icon("sliding.png"),
            "xp_reward_interval": {"points": 1, "xp": 5},
            "coin_reward_interval": {"points": 1, "coins": 10},
        },
    ]
