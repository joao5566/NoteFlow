# terminal_tab.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTabWidget
from PyQt5.QtCore import QProcess

class TerminalTab(QWidget):
    """Aba de Terminal integrada usando QProcess e Alacritty."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # Configura o terminal
        self.process = QProcess(self)
        self.process.setProgram("alacritty")
        self.process.setArguments([])  # Adicione argumentos, se necessário
        self.process.start()

        # Conectar a saída do processo para lidar com o terminal
        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.readyReadStandardError.connect(self.handle_error)

        # Adicionando um rótulo explicativo
        self.layout.addWidget(QLabel("Terminal Integrado"))

    def handle_output(self):
        """Processa a saída do terminal."""
        output = self.process.readAllStandardOutput().data().decode()
        print(output)  # Aqui você pode processar a saída do terminal

    def handle_error(self):
        """Processa os erros do terminal."""
        error = self.process.readAllStandardError().data().decode()
        print(error)  # Aqui você pode processar os erros do terminal

