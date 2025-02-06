from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal

class PluginTab(QWidget):
    # Sinal que pode ser emitido para notificar que o plugin foi atualizado
    updated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def refresh(self):
        """Método que pode ser sobrescrito para atualizar a interface do plugin."""
        self.updated.emit()

    def configure(self):
        """
        Se o plugin tiver opções de configuração, este método pode
        ser sobrescrito para abrir uma interface de configuração.
        """
        pass
