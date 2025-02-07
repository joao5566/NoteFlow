#pixel_art_animation.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Módulo de Animação para o Plugin de Pixel Art

Este módulo implementa a classe PixelArtAnimation, que permite:
  - Criar e gerenciar vários frames de uma animação;
  - Capturar uma imagem (QImage) e adicioná-la como um novo frame;
  - Reproduzir a animação (play/stop) utilizando um QTimer;
  - Exportar a animação para GIF (utilizando o módulo 'imageio', se instalado).

Nesta versão, a classe sobrescreve o método paintEvent para desenhar o frame atual escalonado
e também sobrescreve sizeHint() para sugerir um tamanho maior (por exemplo, 300×300 pixels).
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QImage
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtWidgets import QSizePolicy

class PixelArtAnimation(QWidget):
    def __init__(self, frame_resolution=32, zoom=10, parent=None):
        """
        Inicializa o editor de animação.
        
        :param frame_resolution: Resolução (em pixels) de cada frame.
        :param zoom: Fator de zoom para o desenho original (por exemplo, 10 gera um "frame original" de 32*10=320px).
        :param parent: Widget pai.
        """
        super().__init__(parent)
        self.frame_resolution = frame_resolution
        self.zoom = zoom
        self.frames = []  # Lista de QImage representando cada frame
        self.current_frame_index = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)
        
        # Configure a política de tamanho para Fixed e defina um tamanho mínimo desejado
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setMinimumSize(300, 300)
        
        # Inicializa com um frame em branco
        self.add_frame()

    def sizeHint(self):
        # Retorna a sugestão de tamanho para o widget (por exemplo, 300x300 pixels)
        return QSize(300, 300)

    def add_frame(self):
        """Adiciona um novo frame em branco à animação."""
        image = QImage(self.frame_resolution, self.frame_resolution, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        self.frames.append(image)
        self.current_frame_index = len(self.frames) - 1
        self.update()

    def add_frame_from_image(self, image: QImage):
        """
        Adiciona um frame à animação a partir de uma imagem.
        Se a imagem não tiver a resolução adequada, ela é redimensionada.
        """
        from PyQt5.QtCore import QSize
        if image.size() != QSize(self.frame_resolution, self.frame_resolution):
            image = image.scaled(self.frame_resolution, self.frame_resolution,
                                 Qt.IgnoreAspectRatio, Qt.FastTransformation)
        self.frames.append(image)
        self.current_frame_index = len(self.frames) - 1
        self.update()

    def next_frame(self):
        """Avança para o próximo frame e atualiza a visualização (usado pelo QTimer)."""
        if self.frames:
            self.current_frame_index = (self.current_frame_index + 1) % len(self.frames)
            self.update()

    def play(self, interval=100):
        """
        Inicia a reprodução da animação.
        
        :param interval: Intervalo entre os frames (em milissegundos).
        """
        if not self.timer.isActive():
            self.timer.start(interval)

    def stop(self):
        """Para a reprodução da animação."""
        if self.timer.isActive():
            self.timer.stop()

    def paintEvent(self, event):
        if not self.frames:
            return

        painter = QPainter(self)
        
        # Obtenha o frame atual e suas dimensões reais
        frame = self.frames[self.current_frame_index]
        orig_width = frame.width()
        orig_height = frame.height()
        
        # Dimensões disponíveis no widget de preview
        widget_width = self.width()
        widget_height = self.height()
        
        # Calcula o fator de escala para que o frame caiba dentro do widget (mantendo a proporção)
        scale_x = widget_width / orig_width
        scale_y = widget_height / orig_height
        scale = min(scale_x, scale_y)
        
        # Calcula as novas dimensões e o deslocamento para centralizar o frame
        new_width = orig_width * scale
        new_height = orig_height * scale
        offset_x = (widget_width - new_width) / 2
        offset_y = (widget_height - new_height) / 2
        
        # Centraliza e aplica a escala
        painter.translate(offset_x, offset_y)
        painter.scale(scale, scale)
        
        # Desenha o frame na posição (0,0)
        painter.drawImage(0, 0, frame)


