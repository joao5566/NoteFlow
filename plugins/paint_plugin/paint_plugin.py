# plugin_pixel_art_tab.py
import sys
import json
import os
import base64
import copy  # para cópia profunda, se necessário
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
from PyQt5 import QtWidgets

from pixel_art_canvas import PixelArtCanvas
from pixel_art_config_dialog import PixelArtConfigDialog

CONFIG_FILE = "pixel_art_config.json"

def load_pixel_art_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # Valores padrão, se não existir o arquivo de configuração:
    return {
        "max_undo_history": 100,
        "default_canvas_resolution": 32,
        "default_canvas_zoom": 10
    }

def save_pixel_art_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

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

        self.config = {
            "initial_ef": 25,  # Representa 2.5
            "cards_per_session": 10,
            "auto_audio": True
        }

        # --- Primeiro: Crie o painel de camadas (lado direito) ---
        # Dessa forma, o atributo self.layer_list estará definido quando o canvas emitir o sinal.
        self.layer_list = QListWidget(self)
        self.layer_list.setFixedWidth(150)
        # Não é necessário chamar refresh_layer_list() aqui, pois será chamado pelo sinal.
        self.layer_list.setCurrentRow(0)
        self.layer_list.currentRowChanged.connect(self.on_layer_selection_changed)

        # --- Barra lateral de ferramentas (lado esquerdo) ---
        tool_layout = QVBoxLayout()
        tool_layout.setSpacing(5)
        tool_layout.setContentsMargins(5, 5, 5, 5)

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

        # --- Área central com controles e canvas ---
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
        self.btn_undo.clicked.connect(self.global_undo)
        controls_layout.addWidget(self.btn_undo)

        self.btn_redo = QPushButton("Refazer", self)
        self.btn_redo.clicked.connect(self.global_redo)
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

        config = load_pixel_art_config()
        self.canvas.new_canvas(config.get("default_canvas_resolution", 32))
        self.canvas.set_zoom(config.get("default_canvas_zoom", 10))

        # --- Adiciona o painel de camadas e paleta (lado direito) ---
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.layer_list)  # Já criado no início
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
        paleta_label = QLabel("Paleta de Cores:")
        right_layout.addWidget(paleta_label)
        self.palette_list = QListWidget(self)
        self.palette_list.setFixedWidth(150)
        right_layout.addWidget(self.palette_list)
        self.palette_list.itemClicked.connect(self.select_color_from_palette)
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

        # Atalhos de teclado
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.new_canvas)
        QShortcut(QKeySequence("Ctrl+Z"), self, activated=self.global_undo)
        QShortcut(QKeySequence("Ctrl+Y"), self, activated=self.global_redo)
        QShortcut(QKeySequence("Ctrl++"), self, activated=self.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, activated=self.zoom_out)
        QShortcut(QKeySequence("Ctrl+C"), self, activated=self.select_color)

        self.palette = []
        self.global_undo_stack = []
        self.global_redo_stack = []
        self.push_global_state()

    # --- Método para definir a ferramenta atual ---
    def set_tool(self, tool: str):
        """Define a ferramenta atual e atualiza o estado dos botões."""
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

    # --- Sistema Global de Undo/Redo ---
    def get_global_state(self):
        """
        Retorna um snapshot do estado atual do projeto.
        """
        state = {
            "resolution": self.canvas.resolution,
            "zoom": self.canvas.zoom,
            "layers": [],
            "current_layer_index": self.canvas.current_layer_index,
            "palette": self.palette.copy()
        }
        for layer in self.canvas.layers:
            state["layers"].append({
                "name": layer["name"],
                "visible": layer["visible"],
                "image": layer["image"].copy()
            })
        return state

    def refresh_layer_list(self):
        """Atualiza a lista de camadas na interface."""
        self.layer_list.clear()
        for layer in self.canvas.layers:
            self.layer_list.addItem(layer["name"])

    def set_global_state(self, state):
        """
        Restaura o estado do projeto a partir do snapshot.
        """
        self.canvas.new_canvas(state["resolution"])
        self.canvas.zoom = state["zoom"]
        self.canvas.layers = []
        for layer_state in state["layers"]:
            self.canvas.layers.append({
                "name": layer_state["name"],
                "visible": layer_state["visible"],
                "image": layer_state["image"].copy(),
                "undo_stack": [],
                "redo_stack": []
            })
        self.canvas.current_layer_index = state["current_layer_index"]
        self.palette = state["palette"].copy()
        self.refresh_layer_list()
        self.layer_list.setCurrentRow(self.canvas.current_layer_index)
        self.refresh_palette_list()
        self.canvas.update()

    def push_global_state(self):
        state = self.get_global_state()
        self.global_undo_stack.append(state)
        config = load_pixel_art_config()
        MAX_HISTORY = config.get("max_undo_history", 100)
        if len(self.global_undo_stack) > MAX_HISTORY:
            self.global_undo_stack.pop(0)
        self.global_redo_stack.clear()

    def global_undo(self):
        if len(self.global_undo_stack) > 1:
            current_state = self.get_global_state()
            self.global_redo_stack.append(current_state)
            self.global_undo_stack.pop()  # remove o estado atual
            prev_state = self.global_undo_stack[-1]
            self.set_global_state(prev_state)
        else:
            QMessageBox.information(self, "Desfazer", "Não há ações para desfazer.")

    def global_redo(self):
        if self.global_redo_stack:
            current_state = self.get_global_state()
            self.global_undo_stack.append(current_state)
            redo_state = self.global_redo_stack.pop()
            self.set_global_state(redo_state)
        else:
            QMessageBox.information(self, "Refazer", "Não há ações para refazer.")

    # --- Métodos de Operação ---
    def new_canvas(self):
        self.push_global_state()
        res, ok = QInputDialog.getInt(
            self, "Novo Canvas",
            "Informe a resolução (em pixels) do canvas (ex: 64 para 64x64):",
            min=1, value=self.canvas.resolution
        )
        if ok:
            self.canvas.new_canvas(res)
            self.refresh_layer_list()
            self.layer_list.setCurrentRow(0)
            self.push_global_state()

    def canvas_clear(self):
        self.push_global_state()
        self.canvas.clear_canvas()
        self.push_global_state()

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
            self.push_global_state()
            target_index = mapping[item]
            self.canvas.merge_with_layer(target_index)
            self.refresh_layer_list()
            self.layer_list.setCurrentRow(self.canvas.current_layer_index)
            self.push_global_state()

    def add_layer(self):
        self.push_global_state()
        self.canvas.add_layer("Layer")
        self.refresh_layer_list()
        self.layer_list.setCurrentRow(self.canvas.current_layer_index)
        self.push_global_state()

    def remove_layer(self):
        current = self.layer_list.currentRow()
        self.push_global_state()
        self.canvas.remove_layer(current)
        self.refresh_layer_list()
        self.layer_list.setCurrentRow(self.canvas.current_layer_index)
        self.push_global_state()

    def move_layer_up(self):
        current = self.layer_list.currentRow()
        if current > 0:
            self.push_global_state()
            layers = self.canvas.layers
            layers[current], layers[current - 1] = layers[current - 1], layers[current]
            self.canvas.current_layer_index = current - 1
            self.refresh_layer_list()
            self.layer_list.setCurrentRow(current - 1)
            self.canvas.update()
            self.push_global_state()

    def move_layer_down(self):
        current = self.layer_list.currentRow()
        if current < len(self.canvas.layers) - 1:
            self.push_global_state()
            layers = self.canvas.layers
            layers[current], layers[current + 1] = layers[current + 1], layers[current]
            self.canvas.current_layer_index = current + 1
            self.refresh_layer_list()
            self.layer_list.setCurrentRow(current + 1)
            self.canvas.update()
            self.push_global_state()

    def rename_layer(self):
        current = self.layer_list.currentRow()
        if current >= 0:
            new_name, ok = QInputDialog.getText(
                self, "Renomear Camada",
                "Informe o novo nome para a camada:",
                text=self.canvas.layers[current]["name"]
            )
            if ok and new_name:
                self.push_global_state()
                self.canvas.layers[current]["name"] = new_name
                self.refresh_layer_list()
                self.layer_list.setCurrentRow(current)
                self.push_global_state()

    def on_layer_selection_changed(self, row):
        self.canvas.set_current_layer(row)

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

    def zoom_in(self):
        self.canvas.set_zoom(self.canvas.zoom + 1)

    def zoom_out(self):
        self.canvas.set_zoom(self.canvas.zoom - 1)

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
            if "resolution" in project:
                res = project["resolution"]
            elif project.get("layers"):
                first_layer_data = project["layers"][0]
                img_data = base64.b64decode(first_layer_data["image"])
                img = QImage()
                if img.loadFromData(img_data, "PNG"):
                    res = img.width()
                else:
                    res = 32
            else:
                res = 32

            self.push_global_state()
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
            self.push_global_state()
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

    def load_image_layer(self):
        path, _ = QFileDialog.getOpenFileName(self, "Carregar Imagem", "", "Imagens (*.png *.jpg *.bmp *.gif)")
        if not path:
            return
        loaded = QImage(path)
        if loaded.isNull():
            QMessageBox.critical(self, "Erro", "Falha ao carregar a imagem.")
            return

        new_width = loaded.width()
        new_height = loaded.height()
        new_res = max(new_width, new_height)
        if new_res > self.canvas.resolution:
            old_res = self.canvas.resolution
            for layer in self.canvas.layers:
                old_img = layer["image"]
                new_img = QImage(new_res, new_res, QImage.Format_ARGB32)
                new_img.fill(Qt.transparent)
                x = (new_res - old_res) // 2
                y = (new_res - old_res) // 2
                painter = QPainter(new_img)
                painter.drawImage(x, y, old_img)
                painter.end()
                layer["image"] = new_img
            self.canvas.resolution = new_res

        canvas_res = self.canvas.resolution
        new_layer_img = QImage(canvas_res, canvas_res, QImage.Format_ARGB32)
        new_layer_img.fill(Qt.transparent)
        painter = QPainter(new_layer_img)
        x = (canvas_res - loaded.width()) // 2
        y = (canvas_res - loaded.height()) // 2
        painter.drawImage(x, y, loaded)
        painter.end()
        new_layer = {
            "name": "Imagem Carregada",
            "image": new_layer_img,
            "visible": True,
            "undo_stack": [],
            "redo_stack": []
        }
        self.push_global_state()
        self.canvas.layers.append(new_layer)
        self.canvas.current_layer_index = len(self.canvas.layers) - 1
        self.canvas.update()
        self.refresh_layer_list()
        self.layer_list.setCurrentRow(self.canvas.current_layer_index)
        self.push_global_state()

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
        color = QColor(item.text())
        self.canvas.set_pen_color(color)
    def configure(self):
        dialog = PixelArtConfigDialog(self.config, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            new_config = dialog.get_config()
            self.config.update(new_config)
            save_pixel_art_config(self.config)  # Salva as novas configurações no arquivo
            QMessageBox.information(self, "Configurações", "Configurações atualizadas com sucesso!")
