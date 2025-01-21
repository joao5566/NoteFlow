from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen, QPolygon
import math

def draw_shape(painter, shape, color, x, y, size):
    painter.setBrush(QBrush(QColor(color), Qt.SolidPattern))
    painter.setPen(QPen(QColor('black'), 2))  # borda preta para melhor visualização

    if shape == 'circle':
        painter.drawEllipse(x, y, size, size)
    elif shape == 'square':
        painter.drawRect(x, y, size, size)
    elif shape == 'triangle':
        points = [
            QPoint(x + size // 2, y),
            QPoint(x, y + size),
            QPoint(x + size, y + size)
        ]
        painter.drawPolygon(QPolygon(points))
    elif shape == 'pentagon':
        angle = 360 / 5
        radius = size // 2
        points = []
        for i in range(5):
            px = int(x + radius * math.cos(math.radians(angle * i - 90)))
            py = int(y + radius * math.sin(math.radians(angle * i - 90)))
            points.append(QPoint(px, py))
        painter.drawPolygon(QPolygon(points))
    elif shape == 'star':
        outer_radius = size // 2
        inner_radius = outer_radius * 0.5
        points = []
        for i in range(10):  # 10 pontos para criar uma estrela de 5 pontas
            angle = i * 36
            radius = outer_radius if i % 2 == 0 else inner_radius
            px = int(x + size // 2 + radius * math.cos(math.radians(angle)))
            py = int(y + size // 2 + radius * math.sin(math.radians(angle)))
            points.append(QPoint(px, py))
        painter.drawPolygon(QPolygon(points))


