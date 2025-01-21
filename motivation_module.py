import random
from PyQt5.QtWidgets import QMessageBox

def show_random_motivation(parent):
    motivations = [
        "Continue se esforçando!",
        "Todo dia é uma nova oportunidade!",
        "Consistência é a chave para o sucesso.",
        "Pequenos passos levam a grandes mudanças.",
        "Acredite no processo e continue avançando!",
        "Você é mais forte do que imagina.",
        "Grandes coisas levam tempo.",
        "Não tenha medo de falhar, tenha medo de não tentar.",
        "O sucesso é a soma de pequenos esforços repetidos diariamente.",
        "Cada dia é uma chance de fazer melhor.",
        "Seja paciente. Tudo vem ao seu tempo.",
        "A determinação de hoje constrói o sucesso de amanhã.",
        "Mesmo o menor progresso é um passo à frente.",
        "Lembre-se de por que você começou.",
        "Você é capaz de superar qualquer desafio.",
        "Não se compare com os outros, compare-se com quem você era ontem.",
        "Mantenha o foco e nunca desista.",
        "Desafios são oportunidades disfarçadas.",
        "O aprendizado nunca é desperdiçado.",
        "A coragem não é a ausência de medo, mas a decisão de seguir em frente apesar dele.",
        "O impossível é apenas uma questão de opinião.",
        "A jornada é tão importante quanto o destino.",
        "O segredo do sucesso é começar.",
        "Permita-se crescer, mesmo que isso signifique sair da zona de conforto.",
        "As dificuldades preparam pessoas comuns para destinos extraordinários.",
        "Não importa o quão devagar você vá, desde que não pare.",
        "Persista, a próxima tentativa pode ser a que dará certo.",
        "Seja a mudança que você quer ver no mundo.",
        "A única maneira de alcançar o impossível é acreditar que é possível.",
        "Seu esforço de hoje define suas conquistas de amanhã."
    ]
    QMessageBox.information(parent, "Motivação", random.choice(motivations))


# Como usar este módulo no app principal:
# 1. Importe a função show_random_motivation.
# 2. Chame a função para exibir uma mensagem motivacional.
#
# Exemplo:
# show_random_motivation(self)

