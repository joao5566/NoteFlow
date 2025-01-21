from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QPainter, QBrush, QKeyEvent
import random
import pygame
class SnakeGame(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Jogo da Cobrinha")
        self.resize(400, 400)
        self.init_ui()
        self.init_game()
        self.is_paused = True  # O jogo começa pausado

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.score_label = QLabel("Pontuação: 0")
        self.pause_label = QLabel("Pressione ESPAÇO para começar")
        self.pause_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.score_label)
        layout.addWidget(self.pause_label)
        
        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_game)
        self.timer.start(150)

    def init_game(self):
        self.snake = [(5, 5)]  # Lista de segmentos da cobrinha (x, y)
        self.food = (random.randint(0, 19), random.randint(0, 19))
        self.direction = (0, 1)  # Direção inicial: para baixo
        self.score = 0
        self.is_game_over = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(QBrush(Qt.green, Qt.SolidPattern))

        # Desenha a cobrinha
        for segment in self.snake:
            x, y = segment
            painter.drawRect(x * 20, y * 20, 20, 20)

        # Desenha a comida
        painter.setBrush(QBrush(Qt.red, Qt.SolidPattern))
        fx, fy = self.food
        painter.drawRect(fx * 20, fy * 20, 20, 20)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        
        if key == Qt.Key_Space:
            self.is_paused = not self.is_paused
            if self.is_paused:
                self.pause_label.setText("Pressione ESPAÇO para começar")
            else:
                self.pause_label.setText("")
            return
        
        if self.is_paused:
            return  # Não permite movimentar enquanto o jogo estiver pausado

        if key == Qt.Key_Up and self.direction != (0, 1):
            self.direction = (0, -1)
        elif key == Qt.Key_Down and self.direction != (0, -1):
            self.direction = (0, 1)
        elif key == Qt.Key_Left and self.direction != (1, 0):
            self.direction = (-1, 0)
        elif key == Qt.Key_Right and self.direction != (-1, 0):
            self.direction = (1, 0)

    def update_game(self):
        if self.is_paused or self.is_game_over:
            return

        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        # Verifica colisão com as bordas
        if not (0 <= new_head[0] < 20 and 0 <= new_head[1] < 20):
            self.game_over()
            return

        # Verifica colisão com o próprio corpo
        if new_head in self.snake:
            self.game_over()
            return

        self.snake.insert(0, new_head)

        # Verifica se comeu a comida
        if new_head == self.food:
            self.score += 10
            self.score_label.setText(f"Pontuação: {self.score}")
            self.food = (random.randint(0, 19), random.randint(0, 19))
        else:
            self.snake.pop()

        self.update()

    def game_over(self):
        self.is_game_over = True
        QMessageBox.information(self, "Game Over", f"Fim de jogo! Sua pontuação: {self.score}")
        self.close()

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = SnakeGame()
    window.show()
    sys.exit(app.exec_())

