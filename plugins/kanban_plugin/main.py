# plugins/plugin_help/main.py

import sys
import os

# Para execução independente, adiciona o diretório pai ao sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from kanban_tab_plugin import PluginKanbanTab

# Define a variável global que será usada como ponto de entrada do plugin
plugin_class = PluginKanbanTab

# Se desejar, você pode definir também uma função para testar o plugin de forma independente:
def main():
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = PluginKanbanTab()
    window.setWindowTitle("Ajuda Plugins")
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
