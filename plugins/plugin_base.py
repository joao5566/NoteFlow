# plugin_base.py
from PyQt5.QtWidgets import QWidget

class PluginTab(QWidget):
    """Classe base para os plugins."""
    name = "Plugin Genérico"
    version = "1.0"
    author = "Desconhecido"
    description = "Nenhuma descrição disponível."

    def __init__(self, parent=None):
        super().__init__(parent)
        # Inicialize sua interface aqui

    def configure(self):
        # Se o plugin tiver opções de configuração, implemente este método
        pass
