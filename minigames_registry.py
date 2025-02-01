# minigames_registry.py

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
            "file": "block_stack.py",
            "class": BlockStack,
            "icon": "game_icons/block.png",
            "xp_reward_interval": {"points": 10, "xp": 1},
            "coin_reward_interval": {"points": 10, "coins": 1},
        },
        {
            "id": "clicker",
            "name": "Programming Clicker",
            "file": "cpp_idle_clicker.py",
            "class": ProgrammingClickerGame,
            "icon": "game_icons/cpp.png",
            "xp_reward_interval": {"points": 1, "xp": 30},
            "coin_reward_interval": {"points": 1, "coins": 50},
        },
        {
            "id": "defender",
            "name": "Defesa das formas",
            "file": "defender.py",
            "class": DefesaDasFormas,
            "icon": "game_icons/defender.png",
            "xp_reward_interval": {"points": 5, "xp": 1},
            "coin_reward_interval": {"points": 5, "coins": 1},
        },
        {
            "id": "flappy",
            "name": "Flappy pet (Pygame)",
            "file": "flappy.py",
            "class": FlappyPetGame,
            "icon": "game_icons/flappy.png",
            "xp_reward_interval": {"points": 1, "xp": 10},
            "coin_reward_interval": {"points": 1, "coins": 5},
        },
        {
            "id": "memory_1",
            "name": "Jogo da memória",
            "file": "memory.py",
            "class": MemoryGame1,
            "icon": "game_icons/memory1.png",
            "xp_reward_interval": {"points": 10, "xp": 1},
            "coin_reward_interval": {"points": 10, "coins": 1},
        },
        {
            "id": "memory_game",
            "name": "Jogo de Memória",
            "file": "memory_game.py",
            "class": MemoryGame,
            "icon": "game_icons/memori.png",
            "xp_reward_interval": {"points": 1, "xp": 1},
            "coin_reward_interval": {"points": 2, "coins": 1},
        },
        {
            "id": "pong",
            "name": "Pong",
            "file": "pong.py",
            "class": PongGame,
            "icon": "game_icons/pong.png",
            "xp_reward_interval": {"points": 1, "xp": 5},
            "coin_reward_interval": {"points": 1, "coins": 10},
        },
        {
            "id": "snake_game",
            "name": "Jogo da Cobrinha",
            "file": "snake_game.py",
            "class": SnakeGame,
            "icon": "game_icons/snake.png",
            "xp_reward_interval": {"points": 1, "xp": 1},
            "coin_reward_interval": {"points": 1, "coins": 1},
        },
        {
            "id": "formaTower",
            "name": "Forma Tower",
            "file": "forma_tower.py",
            "class": IceTowerGame,
            "icon": "game_icons/stack.png",
            "xp_reward_interval": {"points": 1, "xp": 5},
            "coin_reward_interval": {"points": 1, "coins": 10},
        },{
            "id": "SlidingPuzzleGame",
            "name": "Puzzle Deslizante",
            "file": "SlidingPuzzleGame.py",
            "class": SlidingPuzzleGame,
            "icon": "game_icons/sliding.png",
            "xp_reward_interval": {"points": 1, "xp": 5},
            "coin_reward_interval": {"points": 1, "coins": 10},
        },
    ]
