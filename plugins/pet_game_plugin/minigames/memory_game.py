from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer
import random
import pygame
class MemoryGame(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Jogo de Memória de Cores")
        self.resize(600, 400)

        self.sequence = []  # Sequência de cores a ser mostrada
        self.user_sequence = []  # Sequência inserida pelo usuário
        self.colors = ["Vermelho", "Azul", "Verde", "Amarelo"]
        self.color_buttons = {}  # Botões correspondentes a cada cor
        self.score = 0

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.info_label = QLabel("Clique em 'Iniciar' para começar o jogo.")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

        button_layout = QHBoxLayout()

        # Criar botões de cores
        for color in self.colors:
            button = QPushButton(color)
            button.setStyleSheet(f"background-color: {color.lower()}; color: white;")
            button.setEnabled(False)  # Inicialmente desabilitados
            button.clicked.connect(lambda _, c=color: self.handle_user_input(c))
            self.color_buttons[color] = button
            button_layout.addWidget(button)

        layout.addLayout(button_layout)

        # Botão para iniciar o jogo
        self.start_button = QPushButton("Iniciar", self)
        self.start_button.clicked.connect(self.start_game)
        layout.addWidget(self.start_button)

    def start_game(self):
        self.sequence = []
        self.user_sequence = []
        self.score = 0
        self.info_label.setText("Observe a sequência de cores!")
        self.next_round()

    def next_round(self):
        self.user_sequence = []
        new_color = random.choice(self.colors)
        self.sequence.append(new_color)
        self.show_sequence()

    def show_sequence(self):
        self.info_label.setText("Memorize a sequência!")
        self.disable_buttons()
        self.current_index = 0

        def highlight_next_color():
            if self.current_index < len(self.sequence):
                color = self.sequence[self.current_index]
                self.info_label.setText(f"{color}!")
                self.color_buttons[color].setStyleSheet(f"background-color: {color.lower()}; border: 3px solid white;")
                QTimer.singleShot(500, lambda: self.reset_button_style(color))
                self.current_index += 1
                QTimer.singleShot(700, highlight_next_color)
            else:
                self.enable_buttons()
                self.info_label.setText("Repita a sequência!")

        highlight_next_color()

    def reset_button_style(self, color):
        self.color_buttons[color].setStyleSheet(f"background-color: {color.lower()}; color: white;")

    def handle_user_input(self, color):
        self.user_sequence.append(color)
        if self.user_sequence == self.sequence[:len(self.user_sequence)]:
            if len(self.user_sequence) == len(self.sequence):
                self.score += 1
                QMessageBox.information(self, "Parabéns!", f"Você completou a sequência! Pontuação: {self.score}")
                self.next_round()
        else:
            QMessageBox.warning(self, "Erro!", f"Você errou a sequência! Pontuação final: {self.score}")
            self.disable_buttons()
            self.start_button.setEnabled(True)
            self.info_label.setText("Clique em 'Iniciar' para tentar novamente.")

    def enable_buttons(self):
        for button in self.color_buttons.values():
            button.setEnabled(True)

    def disable_buttons(self):
        for button in self.color_buttons.values():
            button.setEnabled(False)

