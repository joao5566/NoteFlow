import sys
import json
import base64
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QColorDialog, QInputDialog, QMessageBox,
    QHBoxLayout, QShortcut, QToolButton, QFrame, QListWidget, QFileDialog, QLabel, QListWidgetItem
)
from PyQt5.QtGui import (
    QPainter, QColor, QMouseEvent, QImage, QPen, QKeyEvent, QTransform, QKeySequence, QPixmap, QCursor, QIcon
)
from PyQt5.QtCore import Qt, QPoint, QPointF, pyqtSignal, QByteArray, QBuffer

# Se o módulo plugin_base não existir, definimos uma classe base dummy
try:
    from plugin_base import PluginTab
except ModuleNotFoundError:
    class PluginTab(QWidget):
        pass

class PixelArtCanvas(QWidget):
    # Sinal para indicar que a lista de camadas foi alterada
    layerListChanged = pyqtSignal()
    
    def __init__(self, resolution=32, zoom=10, parent=None):
        super().__init__(parent)
        self.resolution = resolution      # Ex: 32x32 pixels
        self.zoom = zoom                  # Cada pixel será desenhado com tamanho zoom x zoom
        self.pen_color = Qt.black
        self.brush_size = 1               # Tamanho do pincel (1 = 1 pixel; >1 desenha um bloco)
        self.drawing = False              # Indica se está desenhando
        self.last_drawn_pixel = None      # Evita redesenhar o mesmo ponto repetidamente
        # Ferramentas disponíveis: "pen", "eraser", "bucket", "circle", "line", "rectangle", "move" e "copy"
        self.tool_mode = "pen"
        
        # Variáveis para previews de formas geométricas
        self.circle_start = None
        self.circle_preview_end = None
        self.shape_start = None
        self.shape_preview_end = None

        # Para a ferramenta mover
        self.move_start_pos = None       # Posição inicial do mouse (widget)
        self.move_start_image = None     # Cópia da imagem da camada ativa

        # Para a ferramenta copiar
        self.copy_rect_start = None      # Início da seleção (em coordenadas da imagem)
        self.copy_rect_end = None        # Fim da seleção (em coordenadas da imagem)

        # Variáveis para pan (navegação)
        self.pan_offset = QPoint(0, 0)
        self.panning = False
        self.last_pan_pos = None

        # Sistema de camadas: cada camada é um dicionário com:
        #   "name": nome da camada,
        #   "image": QImage (ARGB32 para transparência),
        #   "visible": flag de visibilidade,
        #   "undo_stack": lista de imagens para undo,
        #   "redo_stack": lista de imagens para redo.
        self.layers = []
        self.current_layer_index = 0

        # Cria o canvas inicial (camada de fundo)
        self.new_canvas(self.resolution)

        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(300, 300)
        self.setCursor(self.create_custom_cursor())

    def create_custom_cursor(self):
        """Cria e retorna um cursor personalizado (crosshair) com hotspot centralizado."""
        size = 16  # Tamanho do cursor
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setPen(QPen(Qt.black, 1))
        center = size // 2
        painter.drawLine(center, 0, center, size)
        painter.drawLine(0, center, size, center)
        painter.end()
        return QCursor(pixmap, center, center)

    def get_transform(self) -> QTransform:
        """Retorna a transformação que centraliza o canvas com pan e zoom."""
        center = QPointF(self.width() / 2, self.height() / 2)
        transform = QTransform()
        transform.translate(center.x() + self.pan_offset.x(), center.y() + self.pan_offset.y())
        transform.scale(self.zoom, self.zoom)
        transform.translate(-self.resolution / 2, -self.resolution / 2)
        return transform

    def widget_to_image(self, pos: QPoint) -> QPoint:
        """Converte uma posição do widget para a posição correspondente na imagem."""
        transform = self.get_transform()
        inv, ok = transform.inverted()
        if not ok:
            return QPoint(-1, -1)
        mapped = inv.map(QPointF(pos))
        mapped.setX(mapped.x() - 0.5)
        mapped.setY(mapped.y() - 0.5)
        return QPoint(round(mapped.x()), round(mapped.y()))

    def new_canvas(self, resolution: int):
        """
        Cria um novo canvas:
         - A camada de fundo (Background) é criada preenchida de branco.
         - Limpa as camadas anteriores.
        """
        self.resolution = resolution
        self.layers = []
        bg_image = QImage(self.resolution, self.resolution, QImage.Format_ARGB32)
        bg_image.fill(Qt.white)
        self.layers.append({
            "name": "Background",
            "image": bg_image,
            "visible": True,
            "undo_stack": [],
            "redo_stack": []
        })
        self.current_layer_index = 0
        self.last_drawn_pixel = None
        self.update()
        self.layerListChanged.emit()

    def add_layer(self, name="Layer"):
        """Adiciona uma nova camada (transparente) e a torna ativa."""
        new_image = QImage(self.resolution, self.resolution, QImage.Format_ARGB32)
        new_image.fill(Qt.transparent)
        count = len(self.layers)
        layer_name = f"{name} {count}"
        self.layers.append({
            "name": layer_name,
            "image": new_image,
            "visible": True,
            "undo_stack": [],
            "redo_stack": []
        })
        self.current_layer_index = len(self.layers) - 1
        self.last_drawn_pixel = None
        self.update()
        self.layerListChanged.emit()

    def remove_layer(self, index):
        """Remove a camada indicada, desde que haja pelo menos uma restante."""
        if 0 <= index < len(self.layers) and len(self.layers) > 1:
            del self.layers[index]
            if self.current_layer_index >= len(self.layers):
                self.current_layer_index = len(self.layers) - 1
            self.last_drawn_pixel = None
            self.update()
            self.layerListChanged.emit()

    def set_current_layer(self, index):
        """Define a camada ativa."""
        if 0 <= index < len(self.layers):
            self.current_layer_index = index
            self.last_drawn_pixel = None
            self.update()

    def set_zoom(self, new_zoom: int):
        """Atualiza o fator de zoom e atualiza a visualização."""
        if new_zoom < 1:
            new_zoom = 1
        self.zoom = new_zoom
        self.update()

    def set_brush_size(self, size: int):
        """Atualiza o tamanho do pincel."""
        if size < 1:
            size = 1
        self.brush_size = size
        self.update()

    def merge_with_layer(self, target_index):
        """
        Mescla a camada ativa com a camada de índice target_index.
        A camada ativa é desenhada sobre a camada escolhida (modo SourceOver).
        Se a camada ativa for a de fundo (índice 0), a operação não é permitida.
        """
        if self.current_layer_index == 0:
            QMessageBox.warning(self, "Mesclar Camadas", "Não é possível mesclar a camada de fundo.")
            return
        if target_index < 0 or target_index >= len(self.layers) or target_index == self.current_layer_index:
            return
        active_image = self.layers[self.current_layer_index]["image"]
        target_image = self.layers[target_index]["image"]
        merged = QImage(self.resolution, self.resolution, QImage.Format_ARGB32)
        merged.fill(Qt.transparent)
        painter = QPainter(merged)
        painter.drawImage(0, 0, target_image)
        painter.drawImage(0, 0, active_image)
        painter.end()
        self.layers[target_index]["image"] = merged
        # Remove a camada ativa e atualiza o índice
        if self.current_layer_index > target_index:
            del self.layers[self.current_layer_index]
            self.current_layer_index = target_index
        else:
            del self.layers[self.current_layer_index]
            self.current_layer_index = target_index - 1
        self.update()
        self.layerListChanged.emit()

    def paintEvent(self, event):
        """Renderiza o canvas: compõe as camadas, desenha a grade e os previews (formas)."""
        painter = QPainter(self)
        transform = self.get_transform()
        painter.setTransform(transform)
        for layer in self.layers:
            if layer["visible"]:
                painter.drawImage(0, 0, layer["image"])
        # Grade
        pen = QPen(QColor(220, 220, 220))
        pen.setWidthF(0)
        painter.setPen(pen)
        for x in range(self.resolution + 1):
            painter.drawLine(x, 0, x, self.resolution)
        for y in range(self.resolution + 1):
            painter.drawLine(0, y, self.resolution, y)
        # Previews para formas geométricas
        if self.tool_mode == "circle" and self.drawing and self.circle_start and self.circle_preview_end:
            dash_pen = QPen(QColor(self.pen_color))
            dash_pen.setStyle(Qt.DashLine)
            dash_pen.setWidthF(0)
            painter.setPen(dash_pen)
            cx, cy = self.circle_start.x(), self.circle_start.y()
            ex, ey = self.circle_preview_end.x(), self.circle_preview_end.y()
            radius = int(((ex - cx)**2 + (ey - cy)**2)**0.5)
            painter.drawEllipse(cx - radius, cy - radius, 2*radius, 2*radius)
        if self.tool_mode == "line" and self.drawing and self.shape_start and self.shape_preview_end:
            dash_pen = QPen(QColor(self.pen_color))
            dash_pen.setStyle(Qt.DashLine)
            dash_pen.setWidth(self.brush_size)
            painter.setPen(dash_pen)
            painter.drawLine(self.shape_start, self.shape_preview_end)
        if self.tool_mode == "rectangle" and self.drawing and self.shape_start and self.shape_preview_end:
            dash_pen = QPen(QColor(self.pen_color))
            dash_pen.setStyle(Qt.DashLine)
            dash_pen.setWidth(self.brush_size)
            painter.setPen(dash_pen)
            x1 = min(self.shape_start.x(), self.shape_preview_end.x())
            y1 = min(self.shape_start.y(), self.shape_preview_end.y())
            x2 = max(self.shape_start.x(), self.shape_preview_end.x())
            y2 = max(self.shape_start.y(), self.shape_preview_end.y())
            painter.drawRect(x1, y1, x2 - x1, y2 - y1)
        
    def draw_pixel(self, image_pos: QPoint):
        """Desenha um pixel (ou bloco) na posição da imagem na camada ativa.
           Para 'eraser', apaga tornando a área transparente."""
        x, y = image_pos.x(), image_pos.y()
        if x < 0 or x >= self.resolution or y < 0 or y >= self.resolution:
            return
        size = self.brush_size
        offset = size // 2
        if self.last_drawn_pixel == (x, y):
            return
        painter = QPainter(self.layers[self.current_layer_index]["image"])
        if self.tool_mode == "eraser":
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(x - offset, y - offset, size, size, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        else:
            painter.fillRect(x - offset, y - offset, size, size, QColor(self.pen_color))
        painter.end()
        self.last_drawn_pixel = (x, y)
        self.update()

    def bucket_fill(self, start: QPoint, fill_color):
        """Realiza o bucket fill na camada ativa."""
        x, y = start.x(), start.y()
        if x < 0 or x >= self.resolution or y < 0 or y >= self.resolution:
            return
        fill_color_obj = QColor(fill_color)
        active = self.layers[self.current_layer_index]["image"]
        target_color = active.pixel(x, y)
        new_color_val = fill_color_obj.rgb()
        if target_color == new_color_val:
            return
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if cx < 0 or cx >= self.resolution or cy < 0 or cy >= self.resolution:
                continue
            if active.pixel(cx, cy) != target_color:
                continue
            active.setPixel(cx, cy, new_color_val)
            stack.extend([(cx+1,cy), (cx-1,cy), (cx,cy+1), (cx,cy-1)])
        self.update()

    def draw_circle(self, start: QPoint, end: QPoint):
        """Desenha um círculo na camada ativa com centro em 'start' e raio até 'end'."""
        cx, cy = start.x(), start.y()
        ex, ey = end.x(), end.y()
        radius = int(((ex - cx)**2 + (ey - cy)**2)**0.5)
        painter = QPainter(self.layers[self.current_layer_index]["image"])
        painter.setPen(QPen(QColor(self.pen_color), self.brush_size))
        painter.drawEllipse(cx - radius, cy - radius, 2*radius, 2*radius)
        painter.end()
        self.update()

    def draw_line(self, start: QPoint, end: QPoint):
        """Desenha uma linha na camada ativa do ponto 'start' até 'end'."""
        painter = QPainter(self.layers[self.current_layer_index]["image"])
        pen = QPen(QColor(self.pen_color), self.brush_size)
        painter.setPen(pen)
        painter.drawLine(start, end)
        painter.end()
        self.update()

    def draw_rectangle(self, start: QPoint, end: QPoint):
        """Desenha um retângulo na camada ativa delimitado por 'start' e 'end'."""
        painter = QPainter(self.layers[self.current_layer_index]["image"])
        pen = QPen(QColor(self.pen_color), self.brush_size)
        painter.setPen(pen)
        x1 = min(start.x(), end.x())
        y1 = min(start.y(), end.y())
        x2 = max(start.x(), end.x())
        y2 = max(start.y(), end.y())
        painter.drawRect(x1, y1, x2 - x1, y2 - y1)
        painter.end()
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            if self.tool_mode == "move":
                current_layer = self.layers[self.current_layer_index]
                current_layer["undo_stack"].append(current_layer["image"].copy())
                current_layer["redo_stack"].clear()
                self.drawing = True
                self.move_start_pos = event.pos()
                self.move_start_image = current_layer["image"].copy()
            elif self.tool_mode == "copy":
                self.drawing = True
                self.copy_rect_start = self.widget_to_image(event.pos())
                self.copy_rect_end = self.copy_rect_start
            else:
                current_layer = self.layers[self.current_layer_index]
                current_layer["undo_stack"].append(current_layer["image"].copy())
                current_layer["redo_stack"].clear()
                if self.tool_mode in ("pen", "eraser"):
                    self.drawing = True
                    image_pos = self.widget_to_image(event.pos())
                    self.draw_pixel(image_pos)
                elif self.tool_mode == "bucket":
                    image_pos = self.widget_to_image(event.pos())
                    self.bucket_fill(image_pos, self.pen_color)
                elif self.tool_mode in ("circle", "line", "rectangle"):
                    self.drawing = True
                    if self.tool_mode == "circle":
                        self.circle_start = self.widget_to_image(event.pos())
                        self.circle_preview_end = self.circle_start
                    else:
                        self.shape_start = self.widget_to_image(event.pos())
                        self.shape_preview_end = self.shape_start
        elif event.button() == Qt.MiddleButton:
            self.panning = True
            self.last_pan_pos = event.pos()
        self.setFocus()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.drawing and (event.buttons() & Qt.LeftButton):
            if self.tool_mode == "move":
                delta_widget = event.pos() - self.move_start_pos
                delta_image = QPoint(round(delta_widget.x()/self.zoom), round(delta_widget.y()/self.zoom))
                new_image = QImage(self.resolution, self.resolution, QImage.Format_ARGB32)
                new_image.fill(Qt.transparent)
                painter = QPainter(new_image)
                painter.drawImage(delta_image, self.move_start_image)
                painter.end()
                self.layers[self.current_layer_index]["image"] = new_image
                self.update()
            elif self.tool_mode == "copy":
                self.copy_rect_end = self.widget_to_image(event.pos())
                self.update()
            elif self.tool_mode in ("pen", "eraser"):
                image_pos = self.widget_to_image(event.pos())
                self.draw_pixel(image_pos)
            elif self.tool_mode == "circle" and self.circle_start:
                self.circle_preview_end = self.widget_to_image(event.pos())
                self.update()
            elif self.tool_mode in ("line", "rectangle") and self.shape_start:
                self.shape_preview_end = self.widget_to_image(event.pos())
                self.update()
        if self.panning and (event.buttons() & Qt.MiddleButton):
            delta = event.pos() - self.last_pan_pos
            self.pan_offset += delta
            self.last_pan_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            if self.tool_mode == "move" and self.drawing:
                self.drawing = False
                self.move_start_pos = None
                self.move_start_image = None
            elif self.tool_mode == "copy" and self.drawing:
                self.drawing = False
                x1 = min(self.copy_rect_start.x(), self.copy_rect_end.x())
                y1 = min(self.copy_rect_start.y(), self.copy_rect_end.y())
                x2 = max(self.copy_rect_start.x(), self.copy_rect_end.x())
                y2 = max(self.copy_rect_start.y(), self.copy_rect_end.y())
                if (x2 - x1) > 0 and (y2 - y1) > 0:
                    current_image = self.layers[self.current_layer_index]["image"]
                    copied = current_image.copy(x1, y1, x2 - x1, y2 - y1)
                    new_layer_image = QImage(self.resolution, self.resolution, QImage.Format_ARGB32)
                    new_layer_image.fill(Qt.transparent)
                    painter = QPainter(new_layer_image)
                    painter.drawImage(x1, y1, copied)
                    painter.end()
                    new_layer = {
                        "name": "Cópia",
                        "image": new_layer_image,
                        "visible": True,
                        "undo_stack": [],
                        "redo_stack": []
                    }
                    self.layers.append(new_layer)
                    self.current_layer_index = len(self.layers) - 1
                    self.tool_mode = "move"
                    self.update()
                    self.layerListChanged.emit()
                self.copy_rect_start = None
                self.copy_rect_end = None
            elif self.tool_mode == "circle" and self.drawing and self.circle_start and self.circle_preview_end:
                self.draw_circle(self.circle_start, self.circle_preview_end)
                self.circle_start = None
                self.circle_preview_end = None
            elif self.tool_mode == "line" and self.drawing and self.shape_start and self.shape_preview_end:
                self.draw_line(self.shape_start, self.shape_preview_end)
                self.shape_start = None
                self.shape_preview_end = None
            elif self.tool_mode == "rectangle" and self.drawing and self.shape_start and self.shape_preview_end:
                self.draw_rectangle(self.shape_start, self.shape_preview_end)
                self.shape_start = None
                self.shape_preview_end = None
            else:
                self.drawing = False
            self.last_drawn_pixel = None
        elif event.button() == Qt.MiddleButton:
            self.panning = False

    def keyPressEvent(self, event: QKeyEvent):
        delta = 10
        if event.key() == Qt.Key_Left:
            self.pan_offset += QPoint(delta, 0)
            self.update()
        elif event.key() == Qt.Key_Right:
            self.pan_offset += QPoint(-delta, 0)
            self.update()
        elif event.key() == Qt.Key_Up:
            self.pan_offset += QPoint(0, delta)
            self.update()
        elif event.key() == Qt.Key_Down:
            self.pan_offset += QPoint(0, -delta)
            self.update()
        elif event.key() in (Qt.Key_Plus, Qt.Key_Equal):
            self.set_zoom(self.zoom + 1)
            self.update()
        elif event.key() == Qt.Key_Minus:
            self.set_zoom(self.zoom - 1)
            self.update()
        else:
            super().keyPressEvent(event)

    def clear_canvas(self):
        """Limpa todas as camadas: a camada de fundo é branca e as demais transparentes."""
        self.layers[0]["image"].fill(Qt.white)
        for layer in self.layers[1:]:
            layer["image"].fill(Qt.transparent)
        self.update()

    def set_pen_color(self, color):
        """Define a cor usada para desenhar."""
        self.pen_color = color

    def undo(self):
        """Desfaz a última ação na camada ativa."""
        current_layer = self.layers[self.current_layer_index]
        if current_layer["undo_stack"]:
            current_layer["redo_stack"].append(current_layer["image"].copy())
            current_layer["image"] = current_layer["undo_stack"].pop()
            self.update()
        else:
            QMessageBox.information(self, "Desfazer", "Não há ações para desfazer.")

    def redo(self):
        """Refaz a última ação desfeita na camada ativa."""
        current_layer = self.layers[self.current_layer_index]
        if current_layer["redo_stack"]:
            current_layer["undo_stack"].append(current_layer["image"].copy())
            current_layer["image"] = current_layer["redo_stack"].pop()
            self.update()
        else:
            QMessageBox.information(self, "Refazer", "Não há ações para refazer.")

class PluginPixelArtTab(PluginTab):
    """
    Plugin de Pixel Art com:
      - Canvas de 1 pixel por célula com suporte a zoom, pan e camadas;
      - Ferramentas: Caneta, Borracha, Balde, Círculo, Linha, Retângulo, Mover e Copiar (com previews interativos);
      - Controles para novo canvas, Undo/Redo, seleção de cor, tamanho do pincel e mesclar camadas;
      - Painel de camadas para adicionar, remover, reordenar e renomear camadas;
      - Salvar/Carregar projeto (extensão .pap), exportar PNG e uma paleta de cores editável.
    """
    name = "Pixel Art"

    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QHBoxLayout(self)

        # Barra lateral de ferramentas (lado esquerdo)
        tool_layout = QVBoxLayout()
        tool_layout.setSpacing(5)
        tool_layout.setContentsMargins(5,5,5,5)

        self.btn_tool_pen = QToolButton(self)
        self.btn_tool_pen.setText("Caneta")
        self.btn_tool_pen.setCheckable(True)
        self.btn_tool_pen.setChecked(True)
        self.btn_tool_pen.clicked.connect(lambda: self.set_tool("pen"))
        tool_layout.addWidget(self.btn_tool_pen)

        self.btn_tool_eraser = QToolButton(self)
        self.btn_tool_eraser.setText("Borracha")
        self.btn_tool_eraser.setCheckable(True)
        self.btn_tool_eraser.clicked.connect(lambda: self.set_tool("eraser"))
        tool_layout.addWidget(self.btn_tool_eraser)

        self.btn_tool_bucket = QToolButton(self)
        self.btn_tool_bucket.setText("Balde")
        self.btn_tool_bucket.setCheckable(True)
        self.btn_tool_bucket.clicked.connect(lambda: self.set_tool("bucket"))
        tool_layout.addWidget(self.btn_tool_bucket)

        self.btn_tool_circle = QToolButton(self)
        self.btn_tool_circle.setText("Círculo")
        self.btn_tool_circle.setCheckable(True)
        self.btn_tool_circle.clicked.connect(lambda: self.set_tool("circle"))
        tool_layout.addWidget(self.btn_tool_circle)

        self.btn_tool_line = QToolButton(self)
        self.btn_tool_line.setText("Linha")
        self.btn_tool_line.setCheckable(True)
        self.btn_tool_line.clicked.connect(lambda: self.set_tool("line"))
        tool_layout.addWidget(self.btn_tool_line)

        self.btn_tool_rectangle = QToolButton(self)
        self.btn_tool_rectangle.setText("Retângulo")
        self.btn_tool_rectangle.setCheckable(True)
        self.btn_tool_rectangle.clicked.connect(lambda: self.set_tool("rectangle"))
        tool_layout.addWidget(self.btn_tool_rectangle)

        self.btn_tool_move = QToolButton(self)
        self.btn_tool_move.setText("Mover")
        self.btn_tool_move.setCheckable(True)
        self.btn_tool_move.clicked.connect(lambda: self.set_tool("move"))
        tool_layout.addWidget(self.btn_tool_move)

        self.btn_tool_copy = QToolButton(self)
        self.btn_tool_copy.setText("Copiar")
        self.btn_tool_copy.setCheckable(True)
        self.btn_tool_copy.clicked.connect(lambda: self.set_tool("copy"))
        tool_layout.addWidget(self.btn_tool_copy)

        self.tool_buttons = [
            self.btn_tool_pen, self.btn_tool_eraser, self.btn_tool_bucket,
            self.btn_tool_circle, self.btn_tool_line, self.btn_tool_rectangle,
            self.btn_tool_move, self.btn_tool_copy
        ]
        tool_layout.addStretch()
        tool_frame = QFrame()
        tool_frame.setLayout(tool_layout)
        tool_frame.setFrameShape(QFrame.StyledPanel)
        tool_frame.setFixedWidth(120)
        main_layout.addWidget(tool_frame)

        # Área central com controles e canvas
        center_layout = QVBoxLayout()
        controls_layout = QHBoxLayout()

        self.btn_new = QPushButton("Novo Canvas", self)
        self.btn_new.clicked.connect(self.new_canvas)
        controls_layout.addWidget(self.btn_new)

        self.btn_clear = QPushButton("Limpar Tela", self)
        self.btn_clear.clicked.connect(self.canvas_clear)
        controls_layout.addWidget(self.btn_clear)

        self.btn_color = QPushButton("Escolher Cor", self)
        self.btn_color.clicked.connect(self.select_color)
        controls_layout.addWidget(self.btn_color)

        self.btn_brush_size = QPushButton("Tamanho do Pincel", self)
        self.btn_brush_size.clicked.connect(self.select_brush_size)
        controls_layout.addWidget(self.btn_brush_size)

        self.btn_undo = QPushButton("Desfazer", self)
        self.btn_undo.clicked.connect(self.canvas_undo)
        controls_layout.addWidget(self.btn_undo)

        self.btn_redo = QPushButton("Refazer", self)
        self.btn_redo.clicked.connect(self.canvas_redo)
        controls_layout.addWidget(self.btn_redo)

        self.btn_zoom_in = QPushButton("Zoom In", self)
        self.btn_zoom_in.clicked.connect(self.zoom_in)
        controls_layout.addWidget(self.btn_zoom_in)

        self.btn_zoom_out = QPushButton("Zoom Out", self)
        self.btn_zoom_out.clicked.connect(self.zoom_out)
        controls_layout.addWidget(self.btn_zoom_out)

        self.btn_merge = QPushButton("Mesclar Camadas", self)
        self.btn_merge.clicked.connect(self.merge_layers)
        controls_layout.addWidget(self.btn_merge)

        # Botões para salvar projeto, carregar projeto, carregar imagem e exportar PNG
        self.btn_save_proj = QPushButton("Salvar Projeto", self)
        self.btn_save_proj.clicked.connect(self.save_project)
        controls_layout.addWidget(self.btn_save_proj)

        self.btn_load_proj = QPushButton("Carregar Projeto", self)
        self.btn_load_proj.clicked.connect(self.load_project)
        controls_layout.addWidget(self.btn_load_proj)

        self.btn_load_image = QPushButton("Carregar Imagem", self)
        self.btn_load_image.clicked.connect(self.load_image_layer)
        controls_layout.addWidget(self.btn_load_image)

        self.btn_save_png = QPushButton("Salvar como PNG", self)
        self.btn_save_png.clicked.connect(self.save_as_png)
        controls_layout.addWidget(self.btn_save_png)

        center_layout.addLayout(controls_layout)
        self.canvas = PixelArtCanvas(resolution=32, zoom=10, parent=self)
        self.canvas.layerListChanged.connect(self.refresh_layer_list)
        center_layout.addWidget(self.canvas)
        main_layout.addLayout(center_layout)

        # Painel de camadas e paleta (lado direito)
        right_layout = QVBoxLayout()

        self.layer_list = QListWidget(self)
        self.layer_list.setFixedWidth(150)
        self.refresh_layer_list()
        self.layer_list.setCurrentRow(0)
        self.layer_list.currentRowChanged.connect(self.on_layer_selection_changed)
        right_layout.addWidget(self.layer_list)

        self.btn_add_layer = QPushButton("Adicionar Camada", self)
        self.btn_add_layer.clicked.connect(self.add_layer)
        right_layout.addWidget(self.btn_add_layer)

        self.btn_remove_layer = QPushButton("Remover Camada", self)
        self.btn_remove_layer.clicked.connect(self.remove_layer)
        right_layout.addWidget(self.btn_remove_layer)

        self.btn_move_up = QPushButton("Mover para Cima", self)
        self.btn_move_up.clicked.connect(self.move_layer_up)
        right_layout.addWidget(self.btn_move_up)

        self.btn_move_down = QPushButton("Mover para Baixo", self)
        self.btn_move_down.clicked.connect(self.move_layer_down)
        right_layout.addWidget(self.btn_move_down)

        self.btn_rename_layer = QPushButton("Renomear Camada", self)
        self.btn_rename_layer.clicked.connect(self.rename_layer)
        right_layout.addWidget(self.btn_rename_layer)

        # Painel de Paleta de Cores
        paleta_label = QLabel("Paleta de Cores:")
        right_layout.addWidget(paleta_label)
        self.palette_list = QListWidget(self)
        self.palette_list.setFixedWidth(150)
        right_layout.addWidget(self.palette_list)
        # Conecta o clique do item para selecionar a cor
        self.palette_list.itemClicked.connect(self.select_color_from_palette)

        # Botões para editar a paleta
        self.btn_add_color = QPushButton("Adicionar Cor", self)
        self.btn_add_color.clicked.connect(self.add_color_to_palette)
        right_layout.addWidget(self.btn_add_color)

        self.btn_remove_color = QPushButton("Remover Cor", self)
        self.btn_remove_color.clicked.connect(self.remove_color_from_palette)
        right_layout.addWidget(self.btn_remove_color)

        self.btn_save_palette = QPushButton("Salvar Paleta", self)
        self.btn_save_palette.clicked.connect(self.save_palette)
        right_layout.addWidget(self.btn_save_palette)

        self.btn_load_palette = QPushButton("Carregar Paleta", self)
        self.btn_load_palette.clicked.connect(self.load_palette)
        right_layout.addWidget(self.btn_load_palette)

        right_frame = QFrame()
        right_frame.setLayout(right_layout)
        right_frame.setFrameShape(QFrame.StyledPanel)
        right_frame.setFixedWidth(170)
        main_layout.addWidget(right_frame)

        self.setLayout(main_layout)

        # Atalhos de teclado:
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.new_canvas)
        QShortcut(QKeySequence("Ctrl+Z"), self, activated=self.canvas_undo)
        QShortcut(QKeySequence("Ctrl+Y"), self, activated=self.canvas_redo)
        QShortcut(QKeySequence("Ctrl++"), self, activated=self.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, activated=self.zoom_out)
        QShortcut(QKeySequence("Ctrl+C"), self, activated=self.select_color)

        # Lista para armazenar as cores da paleta (armazenadas como strings hex)
        self.palette = []

    # Métodos de atualização da lista de camadas
    def refresh_layer_list(self):
        self.layer_list.clear()
        for layer in self.canvas.layers:
            self.layer_list.addItem(layer["name"])

    def set_tool(self, tool: str):
        self.canvas.tool_mode = tool
        for btn in self.tool_buttons:
            btn.setChecked(False)
        if tool == "pen":
            self.btn_tool_pen.setChecked(True)
        elif tool == "eraser":
            self.btn_tool_eraser.setChecked(True)
        elif tool == "bucket":
            self.btn_tool_bucket.setChecked(True)
        elif tool == "circle":
            self.btn_tool_circle.setChecked(True)
        elif tool == "line":
            self.btn_tool_line.setChecked(True)
        elif tool == "rectangle":
            self.btn_tool_rectangle.setChecked(True)
        elif tool == "move":
            self.btn_tool_move.setChecked(True)
        elif tool == "copy":
            self.btn_tool_copy.setChecked(True)

    def select_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.canvas.set_pen_color(color)

    def select_brush_size(self):
        size, ok = QInputDialog.getInt(
            self, "Tamanho do Pincel",
            "Informe o tamanho do pincel (quantos pixels serão desenhados de cada vez):",
            value=self.canvas.brush_size, min=1
        )
        if ok:
            self.canvas.set_brush_size(size)

    def new_canvas(self):
        res, ok = QInputDialog.getInt(
            self, "Novo Canvas",
            "Informe a resolução (em pixels) do canvas (ex: 64 para 64x64):",
            min=1, value=self.canvas.resolution
        )
        if ok:
            self.canvas.new_canvas(res)
            self.refresh_layer_list()
            self.layer_list.setCurrentRow(0)

    def canvas_clear(self):
        self.canvas.clear_canvas()

    def canvas_undo(self):
        self.canvas.undo()

    def canvas_redo(self):
        self.canvas.redo()

    def zoom_in(self):
        self.canvas.set_zoom(self.canvas.zoom + 1)

    def zoom_out(self):
        self.canvas.set_zoom(self.canvas.zoom - 1)

    def merge_layers(self):
        current_index = self.canvas.current_layer_index
        if current_index == 0:
            QMessageBox.warning(self, "Mesclar Camadas", "Não é possível mesclar a camada de fundo.")
            return
        options = []
        mapping = {}
        for i, layer in enumerate(self.canvas.layers):
            if i != current_index:
                options.append(f"{i}: {layer['name']}")
                mapping[f"{i}: {layer['name']}"] = i
        if not options:
            QMessageBox.information(self, "Mesclar Camadas", "Não há outra camada para mesclar.")
            return
        item, ok = QInputDialog.getItem(self, "Mesclar Camadas", "Selecione a camada para mesclar com a ativa:", options, 0, False)
        if ok and item:
            target_index = mapping[item]
            self.canvas.merge_with_layer(target_index)
            self.refresh_layer_list()
            self.layer_list.setCurrentRow(self.canvas.current_layer_index)

    def add_layer(self):
        self.canvas.add_layer("Layer")
        self.refresh_layer_list()
        self.layer_list.setCurrentRow(self.canvas.current_layer_index)

    def remove_layer(self):
        current = self.layer_list.currentRow()
        self.canvas.remove_layer(current)
        self.refresh_layer_list()
        self.layer_list.setCurrentRow(self.canvas.current_layer_index)

    def move_layer_up(self):
        current = self.layer_list.currentRow()
        if current > 0:
            layers = self.canvas.layers
            layers[current], layers[current - 1] = layers[current - 1], layers[current]
            self.canvas.current_layer_index = current - 1
            self.refresh_layer_list()
            self.layer_list.setCurrentRow(current - 1)
            self.canvas.update()

    def move_layer_down(self):
        current = self.layer_list.currentRow()
        if current < len(self.canvas.layers) - 1:
            layers = self.canvas.layers
            layers[current], layers[current + 1] = layers[current + 1], layers[current]
            self.canvas.current_layer_index = current + 1
            self.refresh_layer_list()
            self.layer_list.setCurrentRow(current + 1)
            self.canvas.update()

    def rename_layer(self):
        current = self.layer_list.currentRow()
        if current >= 0:
            new_name, ok = QInputDialog.getText(
                self, "Renomear Camada",
                "Informe o novo nome para a camada:",
                text=self.canvas.layers[current]["name"]
            )
            if ok and new_name:
                self.canvas.layers[current]["name"] = new_name
                self.refresh_layer_list()
                self.layer_list.setCurrentRow(current)

    def on_layer_selection_changed(self, row):
        self.canvas.set_current_layer(row)

    # Métodos de projeto
    def save_project(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Projeto", "", "Pixel Art Project (*.pap)")
        if not path:
            return
        if not path.endswith(".pap"):
            path += ".pap"
        project = {
            "resolution": self.canvas.resolution,
            "zoom": self.canvas.zoom,
            "layers": [],
            "palette": self.palette
        }
        for layer in self.canvas.layers:
            ba = QByteArray()
            buffer = QBuffer(ba)
            buffer.open(QBuffer.WriteOnly)
            layer["image"].save(buffer, "PNG")
            img_str = base64.b64encode(ba.data()).decode('utf-8')
            project["layers"].append({
                "name": layer["name"],
                "visible": layer["visible"],
                "image": img_str
            })
        try:
            with open(path, "w") as f:
                json.dump(project, f)
            QMessageBox.information(self, "Projeto Salvo", f"Projeto salvo com sucesso em:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar o projeto:\n{str(e)}")

    def load_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Carregar Projeto", "", "Pixel Art Project (*.pap)")
        if not path:
            return
        try:
            with open(path, "r") as f:
                project = json.load(f)
            res = project.get("resolution", 32)
            self.canvas.new_canvas(res)
            self.canvas.zoom = project.get("zoom", 10)
            self.canvas.layers = []
            for layer_data in project.get("layers", []):
                img_data = base64.b64decode(layer_data["image"])
                img = QImage()
                img.loadFromData(img_data, "PNG")
                self.canvas.layers.append({
                    "name": layer_data.get("name", "Layer"),
                    "image": img,
                    "visible": layer_data.get("visible", True),
                    "undo_stack": [],
                    "redo_stack": []
                })
            self.canvas.current_layer_index = 0
            self.refresh_layer_list()
            self.layer_list.setCurrentRow(0)
            self.palette = project.get("palette", [])
            self.refresh_palette_list()
            self.canvas.update()
            QMessageBox.information(self, "Projeto Carregado", "Projeto carregado com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar o projeto:\n{str(e)}")

    def save_as_png(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar como PNG", "", "PNG Image (*.png)")
        if not path:
            return
        if not path.endswith(".png"):
            path += ".png"
        merged = QImage(self.canvas.resolution, self.canvas.resolution, QImage.Format_ARGB32)
        merged.fill(Qt.transparent)
        painter = QPainter(merged)
        for layer in self.canvas.layers:
            if layer["visible"]:
                painter.drawImage(0, 0, layer["image"])
        painter.end()
        if merged.save(path, "PNG"):
            QMessageBox.information(self, "Salvo", f"Imagem PNG salva com sucesso em:\n{path}")
        else:
            QMessageBox.critical(self, "Erro", "Falha ao salvar a imagem PNG.")

    # Nova funcionalidade: carregar imagem como nova camada
    def load_image_layer(self):
        path, _ = QFileDialog.getOpenFileName(self, "Carregar Imagem", "", "Imagens (*.png *.jpg *.bmp *.gif)")
        if not path:
            return
        loaded = QImage(path)
        if loaded.isNull():
            QMessageBox.critical(self, "Erro", "Falha ao carregar a imagem.")
            return
        canvas_res = self.canvas.resolution
        new_layer_img = QImage(canvas_res, canvas_res, QImage.Format_ARGB32)
        new_layer_img.fill(Qt.transparent)
        painter = QPainter(new_layer_img)
        # Posiciona a imagem carregada centralizada na camada (se for menor ou maior, será desenhada a partir do centro)
        img_w = loaded.width()
        img_h = loaded.height()
        x = max((canvas_res - img_w) // 2, 0)
        y = max((canvas_res - img_h) // 2, 0)
        painter.drawImage(x, y, loaded)
        painter.end()
        new_layer = {
            "name": "Imagem Carregada",
            "image": new_layer_img,
            "visible": True,
            "undo_stack": [],
            "redo_stack": []
        }
        self.canvas.layers.append(new_layer)
        self.canvas.current_layer_index = len(self.canvas.layers) - 1
        self.canvas.update()
        self.refresh_layer_list()
        self.layer_list.setCurrentRow(self.canvas.current_layer_index)

    # Métodos da paleta de cores
    def add_color_to_palette(self):
        color = QColorDialog.getColor()
        if color.isValid():
            hex_color = color.name().upper()
            self.palette.append(hex_color)
            self.refresh_palette_list()

    def remove_color_from_palette(self):
        current = self.palette_list.currentRow()
        if current >= 0:
            del self.palette[current]
            self.refresh_palette_list()

    def refresh_palette_list(self):
        self.palette_list.clear()
        for col in self.palette:
            item = QListWidgetItem()
            # Cria um ícone com um quadrado da cor definida
            pixmap = QPixmap(20, 20)
            pixmap.fill(QColor(col))
            item.setIcon(QIcon(pixmap))
            item.setText(col)
            self.palette_list.addItem(item)

    def save_palette(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Paleta", "", "JSON (*.json)")
        if not path:
            return
        if not path.endswith(".json"):
            path += ".json"
        try:
            with open(path, "w") as f:
                json.dump({"palette": self.palette}, f)
            QMessageBox.information(self, "Paleta Salva", f"Paleta salva com sucesso em:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar a paleta:\n{str(e)}")

    def load_palette(self):
        path, _ = QFileDialog.getOpenFileName(self, "Carregar Paleta", "", "JSON (*.json)")
        if not path:
            return
        try:
            with open(path, "r") as f:
                data = json.load(f)
            self.palette = data.get("palette", [])
            self.refresh_palette_list()
            QMessageBox.information(self, "Paleta Carregada", "Paleta carregada com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar a paleta:\n{str(e)}")

    def select_color_from_palette(self, item):
        """Ao clicar em um item da paleta, define essa cor para o pincel."""
        color = QColor(item.text())
        self.canvas.set_pen_color(color)
