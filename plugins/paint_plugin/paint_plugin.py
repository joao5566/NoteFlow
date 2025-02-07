#paint_plugin.py

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Plugin Pixel Art com Modo de Animação Integrado

- Permite trabalhar como pixel art estático (com canvas, camadas, grid, exportação PNG com escala personalizada, etc.).
- Os controles de animação (botões "Adicionar Quadro", "Play" e "Exportar GIF") ficam acessíveis na aba "Animação" do painel esquerdo.
- A pré-visualização dos frames aparece na aba "Preview" do painel direito, onde o usuário pode definir o tempo de exibição (mas não mais reordenar).
- O usuário pode alternar entre o modo estático e o modo animação.
"""
import sys, os, json, base64, copy, re
# Obtém o caminho do diretório atual (onde está o seu plugin)
plugin_dir = os.path.dirname(os.path.abspath(__file__))
vendor_path = os.path.join(plugin_dir, 'vendor')

# Insere o diretório vendor no início do sys.path, para que ele seja priorizado
if vendor_path not in sys.path:
    sys.path.insert(0, vendor_path)


from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QColorDialog, QInputDialog, QMessageBox,
    QHBoxLayout, QShortcut, QToolButton, QFrame, QListWidget, QFileDialog, QLabel, QListWidgetItem,
    QTabWidget, QSpinBox, QSplitter, QMenuBar, QMenu, QAction, QSizePolicy, QScrollArea
)
from PyQt5.QtGui import (
    QPainter, QColor, QImage, QPen, QKeySequence, QPixmap, QIcon
)
from PyQt5.QtCore import Qt, QByteArray, QBuffer, QTimer, QSize

# Se o módulo plugin_base não existir, define uma classe base dummy.
try:
    from plugin_base import PluginTab
except ModuleNotFoundError:
    class PluginTab(QWidget):
        pass

from pixel_art_canvas import PixelArtCanvas
from pixel_art_config_dialog import PixelArtConfigDialog
from pixel_art_animation import PixelArtAnimation  # Utilize o módulo modificado acima

CONFIG_FILE = "pixel_art_config.json"

def load_pixel_art_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "max_undo_history": 100,
        "default_canvas_resolution": 32,
        "default_canvas_zoom": 10
    }

def save_pixel_art_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
class ReorderableListWidget(QListWidget):
    def __init__(self, reorder_callback, parent=None):
        super().__init__(parent)
        # Habilita o drag & drop interno
        self.setDragDropMode(QListWidget.InternalMove)
        # Define o modo de seleção para que o item seja selecionável
        self.setSelectionMode(QListWidget.SingleSelection)
        # Ativa o drag
        self.setDragEnabled(True)
        # Permite aceitar itens arrastados
        self.setAcceptDrops(True)
        # Exibe o indicador de drop
        self.setDropIndicatorShown(True)
        # Define a ação padrão de drop como mover o item
        self.setDefaultDropAction(Qt.MoveAction)
        
        self.reorder_callback = reorder_callback

    def dropEvent(self, event):
        super().dropEvent(event)
        if self.reorder_callback:
            self.reorder_callback()

class PluginPixelArtTab(PluginTab):
    """
    Plugin de Pixel Art com dois modos:
      - Modo Estático: utiliza o PixelArtCanvas com controles de camadas, grid, exportação, etc.
      - Modo Animação: a interface possui uma aba "Animação" com os controles de animação.
    """
    name = "Pixel Art"

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configurações
        self.config = load_pixel_art_config()
        self.mode = "static"  # "static" ou "animation"
        
        # Cria a instância do animator
        self.animator = PixelArtAnimation(
            frame_resolution=self.config.get("default_canvas_resolution", 32),
            zoom=self.config.get("default_canvas_zoom", 10),
            parent=self
        )
        
        # Cria o QMenuBar
        self.menu_bar = self._create_menu_bar()
        
        # Cria o QSplitter horizontal para os três painéis
        main_splitter = QSplitter(Qt.Horizontal, self)
        
        # Painel esquerdo: Ferramentas, Opções e Animação (em abas)
        left_panel = self._create_tool_panel()
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setWidget(left_panel)
        main_splitter.addWidget(left_scroll)
        
        # Painel central: Apenas o canvas de desenho
        center_widget = self._create_center_panel()
        main_splitter.addWidget(center_widget)
        
        # Painel direito: Abas "Camadas" e "Preview"
        right_panel = self._create_right_panel()
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setWidget(right_panel)
        main_splitter.addWidget(right_scroll)
        
        main_splitter.setSizes([150, 600, 320])

        # Layout principal com menu e splitter
        main_layout = QVBoxLayout(self)
        main_layout.setMenuBar(self.menu_bar)
        main_layout.addWidget(main_splitter)
        self.setLayout(main_layout)
        
        # Atalhos de teclado
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.new_canvas)
        QShortcut(QKeySequence("Ctrl++"), self, activated=self.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, activated=self.zoom_out)
        QShortcut(QKeySequence("Ctrl+C"), self, activated=self.select_color)
        
        self.palette = []
        
        # NOVO: Controle para frames
        self.frame_counter = 0          # Será incrementado a cada novo frame
        self.frame_mapping = {}         # mapeia: id -> QImage

        # QTimer para atualizar a pré-visualização (aba "Preview")
        self.preview_timer = QTimer(self)
        self.preview_timer.timeout.connect(self.update_frame_list)
        # Inicialmente, o timer não está ativo

    def _create_menu_bar(self):
        menu_bar = QMenuBar(self)
        
        # Menu Arquivo
        file_menu = QMenu("Arquivo", self)
        action_new = QAction("Novo Canvas", self)
        action_new.triggered.connect(self.new_canvas)
        file_menu.addAction(action_new)
        action_load_proj = QAction("Carregar Projeto", self)
        action_load_proj.triggered.connect(self.load_project)
        file_menu.addAction(action_load_proj)
        action_save_proj = QAction("Salvar Projeto", self)
        action_save_proj.triggered.connect(self.save_project)
        file_menu.addAction(action_save_proj)
        action_save_png = QAction("Salvar como PNG", self)
        action_save_png.triggered.connect(self.save_as_png)
        file_menu.addAction(action_save_png)
        action_export_anim = QAction("Exportar GIF", self)
        action_export_anim.triggered.connect(self.export_animation)
        file_menu.addAction(action_export_anim)
        action_load_image = QAction("Carregar Imagem", self)
        action_load_image.triggered.connect(self.load_image_layer)
        file_menu.addAction(action_load_image)
        file_menu.addSeparator()
        action_export_sheet = QAction("Exportar Sprite Sheet e Frames", self)
        action_export_sheet.triggered.connect(self.export_sprite_sheet)
        file_menu.addAction(action_export_sheet)

        action_exit = QAction("Sair", self)
        action_exit.triggered.connect(self.close)
        file_menu.addAction(action_exit)
        menu_bar.addMenu(file_menu)
        
        # Menu Editar (os comandos Desfazer/Refazer foram removidos)
        edit_menu = QMenu("Editar", self)
        menu_bar.addMenu(edit_menu)

        action_undo = QAction("Desfazer", self)
        action_undo.setShortcut("Ctrl+Z")
        action_undo.triggered.connect(self.undo)
        edit_menu.addAction(action_undo)
        
        action_redo = QAction("Refazer", self)
        action_redo.setShortcut("Ctrl+Y")
        action_redo.triggered.connect(self.redo)
        edit_menu.addAction(action_redo)

        # Menu Ferramentas
        tools_menu = QMenu("Ferramentas", self)
        action_color = QAction("Escolher Cor", self)
        action_color.triggered.connect(self.select_color)
        tools_menu.addAction(action_color)
        action_brush = QAction("Tamanho do Pincel", self)
        action_brush.triggered.connect(self.select_brush_size)
        tools_menu.addAction(action_brush)
        action_toggle_grid = QAction("Alternar Grade", self)
        action_toggle_grid.triggered.connect(self.toggle_grid)
        tools_menu.addAction(action_toggle_grid)
        menu_bar.addMenu(tools_menu)
        
        return menu_bar

    def _create_tool_panel(self):
        tab_widget = QTabWidget()
        tab_widget.setMinimumWidth(150)
        
        # Aba "Ferramentas"
        ferramentas_widget = QWidget()
        ferramentas_layout = QVBoxLayout()
        ferramentas_layout.setSpacing(5)
        ferramentas_layout.setContentsMargins(5, 5, 5, 5)
        
        self.btn_tool_pen = QToolButton(self)
        self.btn_tool_pen.setText("Caneta")
        self.btn_tool_pen.setCheckable(True)
        self.btn_tool_pen.setChecked(True)
        self.btn_tool_pen.clicked.connect(lambda: self.set_tool("pen"))
        ferramentas_layout.addWidget(self.btn_tool_pen)
        
        self.btn_tool_eraser = QToolButton(self)
        self.btn_tool_eraser.setText("Borracha")
        self.btn_tool_eraser.setCheckable(True)
        self.btn_tool_eraser.clicked.connect(lambda: self.set_tool("eraser"))
        ferramentas_layout.addWidget(self.btn_tool_eraser)
        
        self.btn_tool_bucket = QToolButton(self)
        self.btn_tool_bucket.setText("Balde")
        self.btn_tool_bucket.setCheckable(True)
        self.btn_tool_bucket.clicked.connect(lambda: self.set_tool("bucket"))
        ferramentas_layout.addWidget(self.btn_tool_bucket)
        
        self.btn_tool_circle = QToolButton(self)
        self.btn_tool_circle.setText("Círculo")
        self.btn_tool_circle.setCheckable(True)
        self.btn_tool_circle.clicked.connect(lambda: self.set_tool("circle"))
        ferramentas_layout.addWidget(self.btn_tool_circle)
        
        self.btn_tool_line = QToolButton(self)
        self.btn_tool_line.setText("Linha")
        self.btn_tool_line.setCheckable(True)
        self.btn_tool_line.clicked.connect(lambda: self.set_tool("line"))
        ferramentas_layout.addWidget(self.btn_tool_line)
        
        self.btn_tool_rectangle = QToolButton(self)
        self.btn_tool_rectangle.setText("Retângulo")
        self.btn_tool_rectangle.setCheckable(True)
        self.btn_tool_rectangle.clicked.connect(lambda: self.set_tool("rectangle"))
        ferramentas_layout.addWidget(self.btn_tool_rectangle)
        
        self.btn_tool_move = QToolButton(self)
        self.btn_tool_move.setText("Mover")
        self.btn_tool_move.setCheckable(True)
        self.btn_tool_move.clicked.connect(lambda: self.set_tool("move"))
        ferramentas_layout.addWidget(self.btn_tool_move)
        
        self.btn_tool_copy = QToolButton(self)
        self.btn_tool_copy.setText("Copiar")
        self.btn_tool_copy.setCheckable(True)
        self.btn_tool_copy.clicked.connect(lambda: self.set_tool("copy"))
        ferramentas_layout.addWidget(self.btn_tool_copy)
        
        self.btn_toggle_mode = QPushButton("Modo: Arte Estática", self)
        self.btn_toggle_mode.clicked.connect(self.toggle_mode)
        ferramentas_layout.addWidget(self.btn_toggle_mode)
        
        ferramentas_layout.addStretch()
        ferramentas_widget.setLayout(ferramentas_layout)
        tab_widget.addTab(ferramentas_widget, "Ferramentas")
        
        # Aba "Opções"
        opcoes_widget = QWidget()
        opcoes_layout = QVBoxLayout()
        opcoes_layout.setSpacing(5)
        opcoes_layout.setContentsMargins(5, 5, 5, 5)
        
        self.btn_new = QPushButton("Novo Canvas", self)
        self.btn_new.clicked.connect(self.new_canvas)
        opcoes_layout.addWidget(self.btn_new)
        
        self.btn_clear = QPushButton("Limpar Tela", self)
        self.btn_clear.clicked.connect(self.canvas_clear)
        opcoes_layout.addWidget(self.btn_clear)
        
        self.btn_color = QPushButton("Escolher Cor", self)
        self.btn_color.clicked.connect(self.select_color)
        opcoes_layout.addWidget(self.btn_color)
        
        self.btn_brush_size = QPushButton("Tamanho do Pincel", self)
        self.btn_brush_size.clicked.connect(self.select_brush_size)
        opcoes_layout.addWidget(self.btn_brush_size)
        
        # Os botões de Desfazer e Refazer foram removidos
        
        self.btn_zoom_in = QPushButton("Zoom In", self)
        self.btn_zoom_in.clicked.connect(self.zoom_in)
        opcoes_layout.addWidget(self.btn_zoom_in)
        
        self.btn_zoom_out = QPushButton("Zoom Out", self)
        self.btn_zoom_out.clicked.connect(self.zoom_out)
        opcoes_layout.addWidget(self.btn_zoom_out)
        
        self.btn_toggle_grid = QPushButton("Ocultar Grade", self)
        self.btn_toggle_grid.clicked.connect(self.toggle_grid)
        opcoes_layout.addWidget(self.btn_toggle_grid)
        
        opcoes_layout.addStretch()
        opcoes_widget.setLayout(opcoes_layout)
        tab_widget.addTab(opcoes_widget, "Opções")

        # Aba "Animação" com os controles
        anim_widget = QWidget()
        anim_layout = QVBoxLayout()
        anim_layout.setSpacing(5)
        anim_layout.setContentsMargins(5, 5, 5, 5)
        
        self.btn_add_frame = QPushButton("Adicionar Quadro", self)
        self.btn_add_frame.clicked.connect(self.add_current_frame)
        anim_layout.addWidget(self.btn_add_frame)
        
        self.btn_play_anim = QPushButton("Play", self)
        self.btn_play_anim.clicked.connect(self.play_animation)
        anim_layout.addWidget(self.btn_play_anim)
        
        self.btn_export_anim = QPushButton("Exportar GIF", self)
        self.btn_export_anim.clicked.connect(self.export_animation)
        anim_layout.addWidget(self.btn_export_anim)

        self.btn_export_sheet = QPushButton("Exportar Sprite Sheet e Frames", self)
        self.btn_export_sheet.clicked.connect(self.export_sprite_sheet)
        anim_layout.addWidget(self.btn_export_sheet)


        anim_layout.addStretch()
        anim_widget.setLayout(anim_layout)
        tab_widget.addTab(anim_widget, "Animação")
            
        return tab_widget

    def refresh_layer_list(self):
        self.layer_list.clear()
        for layer in self.canvas.layers:
            self.layer_list.addItem(layer["name"])


    def _create_center_panel(self):
        """
        Cria a área central contendo apenas o canvas.
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.canvas = PixelArtCanvas(
            resolution=self.config.get("default_canvas_resolution", 32),
            zoom=self.config.get("default_canvas_zoom", 10),
            parent=self
        )
        self.canvas.layerListChanged.connect(self.refresh_layer_list)
        layout.addWidget(self.canvas)
        
        return panel

    def _create_right_panel(self):
        tab_widget = QTabWidget()
        tab_widget.setMinimumWidth(200)
        
        # Aba "Camadas"
        layers_panel = QFrame()
        layers_layout = QVBoxLayout()
        
        self.layer_list = QListWidget(self)
        self.layer_list.setFixedWidth(180)
        self.layer_list.setUniformItemSizes(True)
        self.layer_list.setSpacing(5)
        self.layer_list.setIconSize(QSize(30, 30))
        self.layer_list.setCurrentRow(0)
        self.layer_list.currentRowChanged.connect(self.on_layer_selection_changed)
        layers_layout.addWidget(self.layer_list)
        
        self.btn_add_layer = QPushButton("Adicionar Camada", self)
        self.btn_add_layer.clicked.connect(self.add_layer)
        layers_layout.addWidget(self.btn_add_layer)
        
        self.btn_remove_layer = QPushButton("Remover Camada", self)
        self.btn_remove_layer.clicked.connect(self.remove_layer)
        layers_layout.addWidget(self.btn_remove_layer)
        
        self.btn_merge_layers = QPushButton("Mesclar Camadas", self)
        self.btn_merge_layers.clicked.connect(self.merge_layers)
        layers_layout.addWidget(self.btn_merge_layers)


        self.btn_move_up = QPushButton("Mover para Cima", self)
        self.btn_move_up.clicked.connect(self.move_layer_up)
        layers_layout.addWidget(self.btn_move_up)
        
        self.btn_move_down = QPushButton("Mover para Baixo", self)
        self.btn_move_down.clicked.connect(self.move_layer_down)
        layers_layout.addWidget(self.btn_move_down)
        
        self.btn_rename_layer = QPushButton("Renomear Camada", self)
        self.btn_rename_layer.clicked.connect(self.rename_layer)
        layers_layout.addWidget(self.btn_rename_layer)
        
        paleta_label = QLabel("Paleta de Cores:")
        layers_layout.addWidget(paleta_label)
        
        self.palette_list = QListWidget(self)
        self.palette_list.setFixedWidth(180)
        layers_layout.addWidget(self.palette_list)
        self.palette_list.itemClicked.connect(self.select_color_from_palette)
        
        self.btn_add_color = QPushButton("Adicionar Cor", self)
        self.btn_add_color.clicked.connect(self.add_color_to_palette)
        layers_layout.addWidget(self.btn_add_color)
        
        self.btn_remove_color = QPushButton("Remover Cor", self)
        self.btn_remove_color.clicked.connect(self.remove_color_from_palette)
        layers_layout.addWidget(self.btn_remove_color)
        
        self.btn_save_palette = QPushButton("Salvar Paleta", self)
        self.btn_save_palette.clicked.connect(self.save_palette)
        layers_layout.addWidget(self.btn_save_palette)
        
        self.btn_load_palette = QPushButton("Carregar Paleta", self)
        self.btn_load_palette.clicked.connect(self.load_palette)
        layers_layout.addWidget(self.btn_load_palette)
        
        layers_panel.setLayout(layers_layout)
        
        # Aba "Preview"
        preview_panel = QFrame()
        preview_layout = QVBoxLayout()
        
        # Define o tamanho do widget de preview para 300x300 pixels
        self.animator.setFixedSize(QSize(300, 300))
        preview_layout.addWidget(self.animator)
        
        label_frames = QLabel("Frames:")
        preview_layout.addWidget(label_frames)
        
            # Cria a nossa lista reordenável de frames
        self.frame_list_widget = ReorderableListWidget(self.reorder_frames, self)
        self.frame_list_widget.setFixedWidth(180)
        self.frame_list_widget.setFixedHeight(150)
        self.frame_list_widget.setUniformItemSizes(True)
        self.frame_list_widget.setSpacing(5)
        self.frame_list_widget.setIconSize(QSize(50, 50))
        preview_layout.addWidget(self.frame_list_widget)
        
                # Layout horizontal para os botões de mover frame
        move_buttons_layout = QHBoxLayout()

        up_button = QPushButton("↑", self)
        up_button.setToolTip("Mover frame para cima")
        up_button.clicked.connect(self.move_selected_frame_up)
        move_buttons_layout.addWidget(up_button)

        down_button = QPushButton("↓", self)
        down_button.setToolTip("Mover frame para baixo")
        down_button.clicked.connect(self.move_selected_frame_down)
        move_buttons_layout.addWidget(down_button)

        preview_layout.addLayout(move_buttons_layout)
        # Removido: Botão de aplicar ordem de frames
        
        # NOVO: Botão para remover o frame selecionado
        self.btn_remove_frame = QPushButton("Remover Quadro", self)
        self.btn_remove_frame.clicked.connect(self.remove_selected_frame)
        preview_layout.addWidget(self.btn_remove_frame)
        
        label_tempo = QLabel("Tempo (ms):")
        preview_layout.addWidget(label_tempo)
        
        self.spin_timing = QSpinBox(self)
        self.spin_timing.setRange(50, 1000)
        self.spin_timing.setValue(100)
        preview_layout.addWidget(self.spin_timing)
        
        preview_panel.setLayout(preview_layout)
        
        tab_widget.addTab(layers_panel, "Camadas")
        tab_widget.addTab(preview_panel, "Preview")
        
        self.preview_panel = preview_panel
        return tab_widget


    def move_selected_frame_up(self):
        selected = self.frame_list_widget.currentRow()
        if selected <= 0:
            return  # Não é possível mover o primeiro item para cima
        # Troca o frame selecionado com o anterior na lista de frames
        self.animator.frames[selected], self.animator.frames[selected - 1] = \
            self.animator.frames[selected - 1], self.animator.frames[selected]
        # Atualiza a lista de frames
        self.update_frame_list()
        # Seleciona o novo índice do frame movido
        self.frame_list_widget.setCurrentRow(selected - 1)

    def move_selected_frame_down(self):
        selected = self.frame_list_widget.currentRow()
        if selected < 0 or selected >= len(self.animator.frames) - 1:
            return  # Não é possível mover o último item para baixo
        # Troca o frame selecionado com o próximo na lista de frames
        self.animator.frames[selected], self.animator.frames[selected + 1] = \
            self.animator.frames[selected + 1], self.animator.frames[selected]
        # Atualiza a lista de frames
        self.update_frame_list()
        # Seleciona o novo índice do frame movido
        self.frame_list_widget.setCurrentRow(selected + 1)


    def update_frame_list(self):
        self.frame_list_widget.clear()
        # Percorre os frames na ordem atual e recria os itens com seus IDs
        for index, frame in enumerate(self.animator.frames):
            unique_id = None
            for id_key, img in self.frame_mapping.items():
                # Use '==' em vez de 'is' para comparar o conteúdo das imagens
                if img == frame:
                    unique_id = id_key
                    break
            if unique_id is None:
                continue
            item = QListWidgetItem(f"Frame {index+1} (id:{unique_id})")
            thumb = QPixmap.fromImage(frame).scaled(50, 50, Qt.KeepAspectRatio, Qt.FastTransformation)
            item.setIcon(QIcon(thumb))
            item.setData(Qt.UserRole, unique_id)
            self.frame_list_widget.addItem(item)
    

    def reorder_frames(self):
        """
        Atualiza a lista de frames (self.animator.frames) de acordo com a nova ordem
        definida pelo usuário na lista reordenável (self.frame_list_widget).
        """
        new_frames = []
        # Itera sobre os itens da lista na ordem atual
        for i in range(self.frame_list_widget.count()):
            item = self.frame_list_widget.item(i)
            uid = item.data(Qt.UserRole)
            # Usa o dicionário frame_mapping para obter a QImage correspondente
            if uid in self.frame_mapping:
                new_frames.append(self.frame_mapping[uid])
        # Atualiza a ordem dos frames na animação
        self.animator.frames = new_frames
        # (Opcional) Se desejar, reinicia o índice do frame atual:
        self.animator.current_frame_index = 0


    def undo(self):
        self.canvas.undo()
        self.refresh_layer_list()

    def redo(self):
        self.canvas.redo()
        self.refresh_layer_list()


    def toggle_mode(self):
        """
        Alterna entre o modo estático e o modo animação.
        Nesta versão, os controles de animação permanecem acessíveis na aba "Animação";
        o botão de alternância apenas altera o texto e a lógica interna, se necessário.
        """
        if self.mode == "static":
            self.mode = "animation"
            self.btn_toggle_mode.setText("Modo: Animação")
            self.preview_timer.start(100)
        else:
            self.mode = "static"
            self.btn_toggle_mode.setText("Modo: Arte Estática")
            self.preview_timer.stop()
        self.reload_interface()

    def reload_interface(self):
        if self.layout() is not None:
            self.layout().invalidate()
            self.layout().activate()
        self.updateGeometry()
        self.adjustSize()
        self.repaint()

    def add_current_frame(self):
        merged = QImage(self.canvas.canvas_width, self.canvas.canvas_height, QImage.Format_ARGB32)
        merged.fill(Qt.transparent)
        painter = QPainter(merged)
        for layer in self.canvas.layers:
            if layer["visible"]:
                painter.drawImage(0, 0, layer["image"])
        painter.end()
        
        # Adiciona o frame
        unique_id = self.frame_counter
        self.frame_counter += 1
        self.animator.frames.append(merged)
        
        # Atualiza o mapping
        self.frame_mapping[unique_id] = merged
        
        item = QListWidgetItem(f"Frame {len(self.animator.frames)} (id:{unique_id})")
        thumb = QPixmap.fromImage(merged).scaled(50, 50, Qt.KeepAspectRatio, Qt.FastTransformation)
        item.setIcon(QIcon(thumb))
        item.setData(Qt.UserRole, unique_id)
        self.frame_list_widget.addItem(item)
        QMessageBox.information(self, "Adicionar Quadro", "Frame adicionado à animação!")

    def remove_selected_frame(self):
        index = self.frame_list_widget.currentRow()
        if index < 0:
            QMessageBox.warning(self, "Remover Quadro", "Selecione um frame para remover.")
            return

        reply = QMessageBox.question(self, "Remover Quadro",
                                    "Tem certeza que deseja remover este frame?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Remove o item da QListWidget
            item = self.frame_list_widget.takeItem(index)
            frame_id = item.data(Qt.UserRole)
            # Remove o frame do mapeamento, se existir
            if frame_id in self.frame_mapping:
                del self.frame_mapping[frame_id]
            # Remove o frame da lista do animator
            if index < len(self.animator.frames):
                del self.animator.frames[index]
            # Ajusta o índice do frame atual, se necessário
            if self.animator.current_frame_index >= len(self.animator.frames):
                self.animator.current_frame_index = max(0, len(self.animator.frames) - 1)
            self.animator.update()

    def play_animation(self):
        if not hasattr(self, 'playing') or not self.playing:
            interval = self.spin_timing.value()
            self.animator.play(interval)
            self.playing = True
            self.btn_play_anim.setText("Stop")
        else:
            self.animator.stop()
            self.playing = False
            self.btn_play_anim.setText("Play")

    def export_animation(self):
        try:
            import imageio
        except ImportError:
            QMessageBox.warning(self, "Exportar GIF", "O módulo 'imageio' não está instalado.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar GIF", "", "GIF (*.gif)")
        if not path:
            return
        if not path.lower().endswith(".gif"):
            path += ".gif"
        frames_np = []
        try:
            import numpy as np
            for frame in self.animator.frames:
                img = frame.convertToFormat(QImage.Format_RGB888)
                width, height = img.width(), img.height()
                ptr = img.bits()
                ptr.setsize(height * width * 3)
                arr = np.array(ptr).reshape(height, width, 3)
                frames_np.append(arr)
            imageio.mimsave(path, frames_np, duration=self.spin_timing.value()/1000.0)
            QMessageBox.information(self, "Exportar GIF", f"GIF exportado com sucesso para:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Exportar GIF", f"Erro ao exportar GIF:\n{str(e)}")

    def export_sprite_sheet(self):
        # Verifica se há frames para exportar
        if not self.animator.frames:
            QMessageBox.warning(self, "Exportar Sprite Sheet", "Não há frames na animação para exportar.")
            return

        # Pergunta ao usuário o número de colunas desejado para o sprite sheet
        columns, ok = QInputDialog.getInt(self, "Exportar Sprite Sheet",
                                          "Número de colunas para o sprite sheet:", 5, 1)
        if not ok:
            return

        # Considera que todos os frames têm o mesmo tamanho (igual ao do canvas)
        frame_width = self.canvas.canvas_width
        frame_height = self.canvas.canvas_height
        total_frames = len(self.animator.frames)
        import math
        rows = math.ceil(total_frames / columns)

        # Cria o sprite sheet com dimensões calculadas
        sprite_sheet_width = columns * frame_width
        sprite_sheet_height = rows * frame_height
        sprite_sheet = QImage(sprite_sheet_width, sprite_sheet_height, QImage.Format_ARGB32)
        sprite_sheet.fill(Qt.transparent)
        
        painter = QPainter(sprite_sheet)
        for i, frame in enumerate(self.animator.frames):
            col = i % columns
            row = i // columns
            x = col * frame_width
            y = row * frame_height
            painter.drawImage(x, y, frame)
        painter.end()

        # Solicita o caminho para salvar o sprite sheet
        sheet_path, _ = QFileDialog.getSaveFileName(self, "Salvar Sprite Sheet", "", "PNG Image (*.png)")
        if sheet_path:
            if not sheet_path.lower().endswith(".png"):
                sheet_path += ".png"
            if sprite_sheet.save(sheet_path, "PNG"):
                QMessageBox.information(self, "Sprite Sheet Salvo", f"Sprite sheet salvo com sucesso em:\n{sheet_path}")
            else:
                QMessageBox.critical(self, "Erro", "Falha ao salvar o sprite sheet.")

        # Solicita ao usuário a pasta onde salvar cada frame individualmente
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Pasta para Exportar Frames")
        if folder:
            for i, frame in enumerate(self.animator.frames):
                frame_path = os.path.join(folder, f"frame_{i+1:03d}.png")
                frame.save(frame_path, "PNG")
            QMessageBox.information(self, "Frames Exportados", f"Os frames foram exportados com sucesso para:\n{folder}")


    def set_tool(self, tool: str):
        self.canvas.tool_mode = tool
        for btn in [self.btn_tool_pen, self.btn_tool_eraser, self.btn_tool_bucket,
                    self.btn_tool_circle, self.btn_tool_line, self.btn_tool_rectangle,
                    self.btn_tool_move, self.btn_tool_copy]:
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

    def toggle_grid(self):
        self.canvas.toggle_grid()
        if self.canvas.show_grid:
            self.btn_toggle_grid.setText("Ocultar Grade")
        else:
            self.btn_toggle_grid.setText("Mostrar Grade")

    def new_canvas(self):
        width, ok1 = QInputDialog.getInt(
            self, "Novo Canvas",
            "Informe a largura (em pixels) do canvas:",
            min=1, value=self.canvas.canvas_width
        )
        if not ok1:
            return
        height, ok2 = QInputDialog.getInt(
            self, "Novo Canvas",
            "Informe a altura (em pixels) do canvas:",
            min=1, value=self.canvas.canvas_height
        )
        if not ok2:
            return
        self.canvas.push_undo()
        self.canvas.new_canvas(width, height)
        self.refresh_layer_list()
        self.layer_list.setCurrentRow(0)


    def canvas_clear(self):
        self.canvas.push_undo()
        self.canvas.clear_canvas()


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
        self.canvas.push_undo()
        self.canvas.add_layer("Layer")
        self.refresh_layer_list()
        self.layer_list.setCurrentRow(self.canvas.current_layer_index)


    def remove_layer(self):
        current = self.layer_list.currentRow()
        if current < 0:
            return
        self.canvas.push_undo()
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
            "canvas_width": self.canvas.canvas_width,
            "canvas_height": self.canvas.canvas_height,
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
        
        # ---- NOVO: Salvando os frames da animação ----
        project["animation"] = {}
        project["animation"]["frames"] = []
        for frame in self.animator.frames:
            ba = QByteArray()
            buffer = QBuffer(ba)
            buffer.open(QBuffer.WriteOnly)
            frame.save(buffer, "PNG")
            frame_str = base64.b64encode(ba.data()).decode("utf-8")
            project["animation"]["frames"].append(frame_str)
        # Salva também o contador de frames e o timing (tempo de exibição) se desejar:
        project["animation"]["frame_counter"] = self.frame_counter
        project["animation"]["timing"] = self.spin_timing.value()
        # ------------------------------------------------

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
                    "visible": layer_data.get("visible", True)
                })
            self.canvas.current_layer_index = 0
            self.refresh_layer_list()
            self.layer_list.setCurrentRow(0)
            self.palette = project.get("palette", [])
            self.refresh_palette_list()
            
            # ---- NOVO: Carregando os frames da animação ----
            if "animation" in project:
                anim = project["animation"]
                self.animator.frames = []
                self.frame_mapping.clear()  # Limpa o mapping antigo
                for index, frame_str in enumerate(anim.get("frames", [])):
                    img_data = base64.b64decode(frame_str)
                    img = QImage()
                    if img.loadFromData(img_data, "PNG"):
                        self.animator.frames.append(img)
                        self.frame_mapping[index] = img  # Associa um ID (nesse caso, o próprio índice) ao frame
                # Atualiza o contador de frames se necessário
                self.frame_counter = anim.get("frame_counter", len(self.animator.frames))
                self.spin_timing.setValue(anim.get("timing", 100))
                self.update_frame_list()  # Atualiza a lista de frames na interface

            # --------------------------------------------------

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
        scale, ok = QInputDialog.getInt(
            self, "Escala de Exportação",
            "Digite a escala para o PNG (1 = tamanho original, 2 = dobro, etc.):",
            1, 1, 100
        )
        if not ok:
            return
        merged = QImage(self.canvas.canvas_width, self.canvas.canvas_height, QImage.Format_ARGB32)
        merged.fill(Qt.transparent)
        painter = QPainter(merged)
        for layer in self.canvas.layers:
            if layer["visible"]:
                painter.drawImage(0, 0, layer["image"])
        painter.end()
        if scale != 1:
            new_width = self.canvas.canvas_width * scale
            new_height = self.canvas.canvas_height * scale
            merged = merged.scaled(new_width, new_height, Qt.IgnoreAspectRatio, Qt.FastTransformation)
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
        if new_res > self.canvas.canvas_width:
            old_width = self.canvas.canvas_width
            old_height = self.canvas.canvas_height
            for layer in self.canvas.layers:
                old_img = layer["image"]
                new_img = QImage(new_res, new_res, QImage.Format_ARGB32)
                new_img.fill(Qt.transparent)
                x = (new_res - old_width) // 2
                y = (new_res - old_height) // 2
                painter = QPainter(new_img)
                painter.drawImage(x, y, old_img)
                painter.end()
                layer["image"] = new_img
            self.canvas.canvas_width = new_res
            self.canvas.canvas_height = new_res
        canvas_width = self.canvas.canvas_width
        canvas_height = self.canvas.canvas_height
        new_layer_img = QImage(canvas_width, canvas_height, QImage.Format_ARGB32)
        new_layer_img.fill(Qt.transparent)
        painter = QPainter(new_layer_img)
        x = (canvas_width - loaded.width()) // 2
        y = (canvas_height - loaded.height()) // 2
        painter.drawImage(x, y, loaded)
        painter.end()
        new_layer = {
            "name": "Imagem Carregada",
            "image": new_layer_img,
            "visible": True
        }
        self.canvas.layers.append(new_layer)
        self.canvas.current_layer_index = len(self.canvas.layers) - 1
        self.canvas.update()
        self.refresh_layer_list()
        self.layer_list.setCurrentRow(self.canvas.current_layer_index)

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
        self.palette_list.setUniformItemSizes(True)
        self.palette_list.setSpacing(5)
        self.palette_list.setIconSize(QSize(20, 20))
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
            save_pixel_art_config(self.config)
            QMessageBox.information(self, "Configurações", "Configurações atualizadas com sucesso!")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = PluginPixelArtTab()
    window.setWindowTitle("Pixel Art")
    window.show()
    sys.exit(app.exec_())
