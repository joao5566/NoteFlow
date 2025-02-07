#pixel_art_canvas.py

import sys
import json
import base64
from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QMouseEvent, QImage, QKeyEvent, QTransform,
    QPixmap, QCursor
)
from PyQt5.QtCore import Qt, QPoint, QPointF, pyqtSignal, QByteArray, QBuffer

class PixelArtCanvas(QWidget):
    # Sinal para indicar que a lista de camadas foi alterada
    layerListChanged = pyqtSignal()
    
    def __init__(self, resolution=32, zoom=10, parent=None):
        super().__init__(parent)
        self.canvas_width = resolution
        self.canvas_height = resolution
        self.zoom = zoom                  # Cada "pixel" será desenhado com tamanho zoom x zoom
        self.pen_color = Qt.black
        self.brush_size = 1               # Tamanho do pincel
        self.drawing = False              # Indica se está desenhando
        self.last_drawn_pixel = None      # Para evitar redesenhar o mesmo ponto repetidamente
        self.tool_mode = "pen"            # Ferramentas: "pen", "eraser", "bucket", "circle", "line", "rectangle", "move", "copy"
        
         # Sistema de undo/redo:
        self.undo_stack = []
        self.redo_stack = []
        # Você pode usar a configuração se existir ou um valor padrão:
        self.max_undo_history = 100

        # Variáveis para previews de formas geométricas
        self.circle_start = None
        self.circle_preview_end = None
        self.shape_start = None
        self.shape_preview_end = None

        # Para a ferramenta mover
        self.move_start_pos = None
        self.move_start_image = None

        # Para a ferramenta copiar
        self.copy_rect_start = None
        self.copy_rect_end = None

        # Variáveis para pan (navegação)
        self.pan_offset = QPoint(0, 0)
        self.panning = False
        self.last_pan_pos = None

        # Sistema de camadas: cada camada é um dicionário com "name", "image" e "visible"
        self.layers = []
        self.current_layer_index = 0

        self.show_grid = True  # Exibição da grade

        # Cria o canvas inicial (camada de fundo)
        self.new_canvas(self.canvas_width, self.canvas_height)

        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(300, 300)
        self.setCursor(self.create_custom_cursor())


    def get_state(self):
            """Retorna um snapshot do estado atual do canvas."""
            state = {
                "canvas_width": self.canvas_width,
                "canvas_height": self.canvas_height,
                "zoom": self.zoom,
                "layers": [],
                "current_layer_index": self.current_layer_index,
                "pen_color": self.pen_color.name() if isinstance(self.pen_color, QColor) else self.pen_color,
                "brush_size": self.brush_size,
                "show_grid": self.show_grid,
            }
            for layer in self.layers:
                state["layers"].append({
                    "name": layer["name"],
                    "visible": layer["visible"],
                    "image": layer["image"].copy()  # Faz uma cópia da QImage
                })
            return state

    def set_state(self, state):
        """Restaura o estado do canvas a partir do snapshot."""
        self.canvas_width = state.get("canvas_width", self.canvas_width)
        self.canvas_height = state.get("canvas_height", self.canvas_height)
        self.zoom = state.get("zoom", self.zoom)
        self.pen_color = QColor(state.get("pen_color", "#000000"))
        self.brush_size = state.get("brush_size", self.brush_size)
        self.show_grid = state.get("show_grid", self.show_grid)
        self.layers = []
        for layer in state.get("layers", []):
            self.layers.append({
                "name": layer["name"],
                "visible": layer["visible"],
                "image": layer["image"].copy()
            })
        self.current_layer_index = state.get("current_layer_index", 0)
        self.update()
        self.layerListChanged.emit()

    def push_undo(self):
        """Salva o estado atual para o undo e limpa o redo."""
        self.redo_stack.clear()
        state = self.get_state()
        self.undo_stack.append(state)
        if len(self.undo_stack) > self.max_undo_history:
            self.undo_stack.pop(0)

    def undo(self):
        if not self.undo_stack:
            return
        # Salva o estado atual no redo
        current_state = self.get_state()
        self.redo_stack.append(current_state)
        # Restaura o último estado
        state = self.undo_stack.pop()
        self.set_state(state)

    def redo(self):
        if not self.redo_stack:
            return
        # Salva o estado atual no undo
        current_state = self.get_state()
        self.undo_stack.append(current_state)
        # Restaura o estado do redo
        state = self.redo_stack.pop()
        self.set_state(state)


    def create_custom_cursor(self):
        size = 16
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
        center = QPointF(self.width() / 2, self.height() / 2)
        transform = QTransform()
        transform.translate(center.x() + self.pan_offset.x(), center.y() + self.pan_offset.y())
        transform.scale(self.zoom, self.zoom)
        transform.translate(-self.canvas_width / 2, -self.canvas_height / 2)
        return transform

    def widget_to_image(self, pos: QPoint) -> QPoint:
        transform = self.get_transform()
        inv, ok = transform.inverted()
        if not ok:
            return QPoint(-1, -1)
        mapped = inv.map(QPointF(pos))
        mapped.setX(mapped.x() - 0.5)
        mapped.setY(mapped.y() - 0.5)
        return QPoint(round(mapped.x()), round(mapped.y()))

    def new_canvas(self, width: int, height: int = None):
        if height is None:
            height = width
        self.canvas_width = width
        self.canvas_height = height
        self.layers = []
        bg_image = QImage(self.canvas_width, self.canvas_height, QImage.Format_ARGB32)
        bg_image.fill(Qt.white)
        self.layers.append({
            "name": "Background",
            "image": bg_image,
            "visible": True
        })
        self.current_layer_index = 0
        self.last_drawn_pixel = None
        self.update()
        self.layerListChanged.emit()

    def add_layer(self, name="Layer"):
        new_image = QImage(self.canvas_width, self.canvas_height, QImage.Format_ARGB32)
        new_image.fill(Qt.transparent)
        count = len(self.layers)
        layer_name = f"{name} {count}"
        self.layers.append({
            "name": layer_name,
            "image": new_image,
            "visible": True
        })
        self.current_layer_index = len(self.layers) - 1
        self.last_drawn_pixel = None
        self.update()
        self.layerListChanged.emit()

    def remove_layer(self, index):
        if 0 <= index < len(self.layers) and len(self.layers) > 1:
            del self.layers[index]
            if self.current_layer_index >= len(self.layers):
                self.current_layer_index = len(self.layers) - 1
            self.last_drawn_pixel = None
            self.update()
            self.layerListChanged.emit()

    def set_current_layer(self, index):
        if 0 <= index < len(self.layers):
            self.current_layer_index = index
            self.last_drawn_pixel = None
            self.update()

    def set_zoom(self, new_zoom: int):
        if new_zoom < 1:
            new_zoom = 1
        self.zoom = new_zoom
        self.update()

    def set_brush_size(self, size: int):
        if size < 1:
            size = 1
        self.brush_size = size
        self.update()

    def merge_with_layer(self, target_index):
        if self.current_layer_index == 0:
            QMessageBox.warning(self, "Mesclar Camadas", "Não é possível mesclar a camada de fundo.")
            return
        if target_index < 0 or target_index >= len(self.layers) or target_index == self.current_layer_index:
            return
        active_image = self.layers[self.current_layer_index]["image"]
        target_image = self.layers[target_index]["image"]
        merged = QImage(self.canvas_width, self.canvas_height, QImage.Format_ARGB32)
        merged.fill(Qt.transparent)
        painter = QPainter(merged)
        painter.drawImage(0, 0, target_image)
        painter.drawImage(0, 0, active_image)
        painter.end()
        self.layers[target_index]["image"] = merged
        if self.current_layer_index > target_index:
            del self.layers[self.current_layer_index]
            self.current_layer_index = target_index
        else:
            del self.layers[self.current_layer_index]
            self.current_layer_index = target_index - 1
        self.update()
        self.layerListChanged.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        transform = self.get_transform()
        painter.setTransform(transform)
        
        for layer in self.layers:
            if layer["visible"]:
                painter.drawImage(0, 0, layer["image"])
        
        if self.show_grid:
            pen = QPen(QColor(220, 220, 220))
            pen.setWidthF(0)
            painter.setPen(pen)
            for x in range(self.canvas_width + 1):
                painter.drawLine(x, 0, x, self.canvas_height)
            for y in range(self.canvas_height + 1):
                painter.drawLine(0, y, self.canvas_width, y)
        
        if self.tool_mode == "circle" and self.drawing and self.circle_start and self.circle_preview_end:
            dash_pen = QPen(QColor(self.pen_color))
            dash_pen.setStyle(Qt.DashLine)
            dash_pen.setWidthF(0)
            painter.setPen(dash_pen)
            cx, cy = self.circle_start.x(), self.circle_start.y()
            ex, ey = self.circle_preview_end.x(), self.circle_preview_end.y()
            radius = int(((ex - cx)**2 + (ey - cy)**2)**0.5)
            painter.drawEllipse(cx - radius, cy - radius, 2 * radius, 2 * radius)
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

    def toggle_grid(self):
        self.show_grid = not self.show_grid
        self.update()

    def draw_pixel(self, image_pos: QPoint):
        x, y = image_pos.x(), image_pos.y()
        if x < 0 or x >= self.canvas_width or y < 0 or y >= self.canvas_height:
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
        x, y = start.x(), start.y()
        if x < 0 or x >= self.canvas_width or y < 0 or y >= self.canvas_height:
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
            if cx < 0 or cx >= self.canvas_width or cy < 0 or cy >= self.canvas_height:
                continue
            if active.pixel(cx, cy) != target_color:
                continue
            active.setPixel(cx, cy, new_color_val)
            stack.extend([(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)])
        self.update()

    def draw_circle(self, start: QPoint, end: QPoint):
        cx, cy = start.x(), start.y()
        ex, ey = end.x(), end.y()
        radius = int(((ex - cx)**2 + (ey - cy)**2)**0.5)
        painter = QPainter(self.layers[self.current_layer_index]["image"])
        painter.setPen(QPen(QColor(self.pen_color), self.brush_size))
        painter.drawEllipse(cx - radius, cy - radius, 2 * radius, 2 * radius)
        painter.end()
        self.update()

    def draw_line(self, start: QPoint, end: QPoint):
        painter = QPainter(self.layers[self.current_layer_index]["image"])
        pen = QPen(QColor(self.pen_color), self.brush_size)
        painter.setPen(pen)
        painter.drawLine(start, end)
        painter.end()
        self.update()

    def draw_rectangle(self, start: QPoint, end: QPoint):
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
        if event.button() == Qt.LeftButton and not self.drawing:
            self.push_undo()  # Salva o estado antes de começar a ação
        if event.button() == Qt.LeftButton:
            if self.tool_mode == "move":
                self.drawing = True
                self.move_start_pos = event.pos()
                self.move_start_image = self.layers[self.current_layer_index]["image"].copy()
            elif self.tool_mode == "copy":
                self.drawing = True
                self.copy_rect_start = self.widget_to_image(event.pos())
                self.copy_rect_end = self.copy_rect_start
            else:
                if self.tool_mode in ("pen", "eraser"):
                    self.drawing = True
                    image_pos = self.widget_to_image(event.pos())
                    self.draw_pixel(image_pos)
                elif self.tool_mode == "bucket":
                    self.drawing = True
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
                delta_image = QPoint(round(delta_widget.x() / self.zoom), round(delta_widget.y() / self.zoom))
                new_image = QImage(self.canvas_width, self.canvas_height, QImage.Format_ARGB32)
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
                # ... (código para criar a nova camada com a região copiada)
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
            elif self.tool_mode in ("pen", "eraser", "bucket") and self.drawing:
                # Terminamos um desenho livre (pincel/borracha) ou preenchimento
                pass
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
        self.layers[0]["image"].fill(Qt.white)
        for layer in self.layers[1:]:
            layer["image"].fill(Qt.transparent)
        self.update()

    def set_pen_color(self, color):
        self.pen_color = color
