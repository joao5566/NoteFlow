# plugins/paint_plugin/paint_plugin.py
from PyQt5.QtWidgets import QLabel, QVBoxLayout
from plugin_base import PluginTab

class PaintPlugin(PluginTab):
    name = "Paint"

    def __init__(self, parent=None):
        super().__init__(parent)
        # Exemplo simples: apenas uma label explicando que este é o plugin Paint
        layout = QVBoxLayout(self)
        label = QLabel("Aqui poderia estar um editor de imagens/paint", self)
        layout.addWidget(label)
        self.setLayout(layout)
