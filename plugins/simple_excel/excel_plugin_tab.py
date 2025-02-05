from plugin_base import PluginTab
from PyQt5.QtWidgets import QVBoxLayout
from simple_excel import SimpleExcelWidget

class PluginExcelTab(PluginTab):
    """
    Plugin que adiciona uma aba com a funcionalidade da Planilha Simples.
    """
    name = "Planilha Simples"

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        # Instancia o widget da planilha simples
        self.excel_widget = SimpleExcelWidget(self)
        layout.addWidget(self.excel_widget)
        self.setLayout(layout)

# Variável global para o carregamento do plugin
plugin_class = PluginExcelTab

# Função main para testes independentes (opcional)
def main():
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    window = PluginExcelTab()
    window.setWindowTitle("Plugin: Planilha Simples")
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
