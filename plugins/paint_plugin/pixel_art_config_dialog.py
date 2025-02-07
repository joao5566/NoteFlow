#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QSpinBox, QDialogButtonBox, QDialog

class PixelArtConfigDialog(QDialog):
    def __init__(self, current_config, parent=None):
        """
        current_config: dicionário com a configuração atual do plugin.
        Exemplo:
            {
                "max_undo_history": 100,
                "default_canvas_width": 32,
                "default_canvas_height": 32,
                "default_canvas_zoom": 10
            }
        """
        super().__init__(parent)
        self.setWindowTitle("Configurações do Pixel Art")
        self.current_config = current_config.copy()  # Cópia da configuração atual
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Limite de Histórico de Undo
        layout.addWidget(QLabel("Limite de Histórico de Undo (snapshots):"))
        self.undo_history_spin = QSpinBox(self)
        self.undo_history_spin.setRange(10, 1000)  # Permite de 10 a 1000 snapshots
        self.undo_history_spin.setValue(self.current_config.get("max_undo_history", 100))
        layout.addWidget(self.undo_history_spin)
        
        # Largura Padrão do Canvas
        layout.addWidget(QLabel("Largura padrão do canvas (pixels):"))
        self.canvas_width_spin = QSpinBox(self)
        self.canvas_width_spin.setRange(16, 1024)  # Exemplo: 16 a 1024 pixels
        self.canvas_width_spin.setValue(self.current_config.get("default_canvas_width", 32))
        layout.addWidget(self.canvas_width_spin)
        
        # Altura Padrão do Canvas
        layout.addWidget(QLabel("Altura padrão do canvas (pixels):"))
        self.canvas_height_spin = QSpinBox(self)
        self.canvas_height_spin.setRange(16, 1024)  # Exemplo: 16 a 1024 pixels
        self.canvas_height_spin.setValue(self.current_config.get("default_canvas_height", 32))
        layout.addWidget(self.canvas_height_spin)
        
        # Zoom Padrão do Canvas
        layout.addWidget(QLabel("Zoom padrão do canvas:"))
        self.canvas_zoom_spin = QSpinBox(self)
        self.canvas_zoom_spin.setRange(1, 50)  # Zoom mínimo 1, máximo 50
        self.canvas_zoom_spin.setValue(self.current_config.get("default_canvas_zoom", 10))
        layout.addWidget(self.canvas_zoom_spin)
        
        # Botões OK/Cancelar
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_config(self):
        """Retorna um dicionário com a configuração definida pelo usuário."""
        return {
            "max_undo_history": self.undo_history_spin.value(),
            "default_canvas_width": self.canvas_width_spin.value(),
            "default_canvas_height": self.canvas_height_spin.value(),
            "default_canvas_zoom": self.canvas_zoom_spin.value()
        }
