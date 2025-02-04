#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bootstrap para exibir uma splash screen customizada com barra de progresso, mensagens dinâmicas com fundo e efeito de fade-out,
e depois carregar o aplicativo principal.
"""

import sys
import os
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation
from PyQt5.QtGui import QPixmap, QColor, QFont
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QProgressBar

# Importa o QWebEngineView logo no início (para evitar erros de inicialização)
from PyQt5.QtWebEngineWidgets import QWebEngineView

class CustomSplashScreen(QWidget):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        # Remove a borda e garante que a janela fique sempre no topo
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        # Permite transparência (opcional)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Layout principal
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(10)

        # Label com a imagem da splash
        self.image_label = QLabel(self)
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
        else:
            # Cria um pixmap padrão se a imagem não for encontrada
            pixmap = QPixmap(400, 300)
            pixmap.fill(QColor("white"))
        self.image_label.setPixmap(pixmap)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.image_label)

        # Label para mensagens de carregamento com fundo semi-transparente
        self.message_label = QLabel("Carregando o aplicativo...", self)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setFont(QFont("Arial", 12))
        # Aplica um estilo com fundo preto semi-transparente e texto branco
        self.message_label.setStyleSheet("""
            background-color: rgba(0, 0, 0, 150);
            color: white;
            padding: 5px;
            border-radius: 5px;
        """)
        self.layout.addWidget(self.message_label)

        # Barra de progresso
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.layout.addWidget(self.progress_bar)

        # Atributo para armazenar a animação (evita coleta prematura)
        self.fade_animation = None

    def update_progress(self, value, message=None):
        """Atualiza a barra de progresso e, se fornecida, a mensagem exibida."""
        self.progress_bar.setValue(value)
        if message:
            self.message_label.setText(message)

def main():
    app = QApplication(sys.argv)

    # Caminho da imagem da splash screen
    splash_image = "splash.png"
    splash = CustomSplashScreen(splash_image)
    splash.show()

    # Definindo as etapas de carregamento: (porcentagem, mensagem)
    steps = [
        (10, "Carregando módulos básicos..."),
        (30, "Inicializando a interface..."),
        (50, "Carregando plugins..."),
        (70, "Carregando recursos adicionais..."),
        (90, "Finalizando configuração..."),
        (100, "Pronto!")
    ]
    current_step = 0
    progress = 0
    timer = QTimer()

    def update_loading():
        nonlocal progress, current_step
        progress += 5  # Incrementa 5% a cada atualização (ajuste conforme necessário)
        if current_step < len(steps) and progress >= steps[current_step][0]:
            splash.update_progress(progress, steps[current_step][1])
            current_step += 1
        else:
            splash.update_progress(progress)

        if progress >= 100:
            timer.stop()
            # Animação de fade-out para a splash screen
            splash.fade_animation = QPropertyAnimation(splash, b"windowOpacity")
            splash.fade_animation.setDuration(500)  # Duração do fade-out em milissegundos
            splash.fade_animation.setStartValue(1.0)
            splash.fade_animation.setEndValue(0.0)
            splash.fade_animation.start()
            splash.fade_animation.finished.connect(lambda: splash.close())
            
            # Importa e exibe o aplicativo principal após a splash
            from calendar_widget import CalendarApp  # Seu módulo principal
            window = CalendarApp()
            window.show()
            app.setStyle("Fusion")
            app.main_window = window

    timer.timeout.connect(update_loading)
    timer.start(200)  # Atualiza a cada 200 ms (ajuste conforme necessário)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
