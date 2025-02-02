# plugin_base.py
from PyQt5.QtWidgets import QWidget

class PluginTab(QWidget):
    """
    Classe base que todo plugin deve herdar.
    Cada plugin deve definir:
      - o atributo 'name', que será o título da aba;
      - sua própria interface (normalmente construída no __init__).
    """
    name = "Plugin Base"

    def __init__(self, parent=None):
        super().__init__(parent)
