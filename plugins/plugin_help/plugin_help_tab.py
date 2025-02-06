from plugin_base import PluginTab
from PyQt5.QtWidgets import QVBoxLayout, QTextBrowser

class PluginHelpTab(PluginTab):
    """
    Plugin que adiciona uma aba de Ajuda para Plugins.
    Exibe um guia com instruções de como criar, adicionar, configurar e integrar plugins ao aplicativo.
    """
    name = "Ajuda Plugins"
    version = "1.1"
    author = "Seu Nome"
    description = "Guia completo para criação, configuração e integração de plugins no aplicativo."

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # Cria um QTextBrowser para exibir o conteúdo da ajuda em HTML
        self.text_browser = QTextBrowser(self)
        self.text_browser.setReadOnly(True)
        self.text_browser.setHtml(self.get_help_text())

        layout.addWidget(self.text_browser)
        self.setLayout(layout)

    def get_help_text(self):
        # Conteúdo de ajuda em HTML atualizado, incluindo exemplo de configuração.
        help_text = """
        <h1>Guia para Criar, Configurar e Adicionar Plugins</h1>
        <p>Este aplicativo permite a criação de plugins para ampliar suas funcionalidades.
        Um plugin é um módulo Python que adiciona uma nova aba ao aplicativo.
        Siga os passos abaixo para criar, configurar e integrar seu plugin:</p>
        
        <h2>1. Estrutura do Plugin</h2>
        <ul>
            <li>O plugin deve ser um arquivo <code>.py</code> (exemplo: <code>meu_plugin.py</code>).</li>
            <li>Organize seus plugins em uma pasta dedicada, como <code>plugins/</code>.
                Você pode usar subpastas para manter a organização.</li>
            <li>Dentro do plugin, crie uma classe que <strong>herde de <code>PluginTab</code></strong>.
                Essa classe deve definir ao menos o atributo <code>name</code> (que aparecerá na aba)
                e implementar a interface desejada.</li>
        </ul>
        
        <h2>2. Exemplo de Código do Plugin</h2>
        <pre style="background-color: #f4f4f4; padding: 10px;">
from plugin_base import PluginTab
from PyQt5.QtWidgets import QLabel, QVBoxLayout

class MeuPlugin(PluginTab):
    name = "Meu Plugin"
    version = "1.0"
    author = "Seu Nome"
    description = "Exemplo simples de plugin."

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("Conteúdo do meu plugin.", self)
        layout.addWidget(label)
        self.setLayout(layout)
        </pre>
        
        <h2>3. Exemplo do Arquivo <code>main.py</code></h2>
        <p>O arquivo <code>main.py</code> é o ponto de entrada do plugin. Ele deve definir a variável <code>plugin_class</code> para indicar qual classe será carregada.
        Também pode incluir uma função <code>main()</code> para testar o plugin de forma independente.</p>
        <pre style="background-color: #f4f4f4; padding: 10px;">
import sys
import os

# Adiciona o diretório pai ao sys.path para facilitar a importação
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from plugin_help_tab import PluginHelpTab

plugin_class = PluginHelpTab

def main():
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = PluginHelpTab()
    window.setWindowTitle("Ajuda Plugins")
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
        </pre>
        
        <h2>4. Exemplo de Configuração em um Plugin</h2>
        <p>Plugins podem oferecer uma interface de configuração para que o usuário personalize as opções.
        Normalmente, utiliza-se um diálogo (por exemplo, usando <code>QDialog</code>) para coletar as configurações,
        que são salvas em um arquivo JSON. Veja um exemplo:</p>
        <pre style="background-color: #f4f4f4; padding: 10px;">
# pixel_art_config_dialog.py
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QSpinBox, QDialogButtonBox, QDialog

class PixelArtConfigDialog(QDialog):
    def __init__(self, current_config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações do Pixel Art")
        self.current_config = current_config.copy()  # Cópia da configuração atual
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Limite de Histórico de Undo
        layout.addWidget(QLabel("Limite de Histórico de Undo (snapshots):"))
        self.undo_history_spin = QSpinBox(self)
        self.undo_history_spin.setRange(10, 1000)
        self.undo_history_spin.setValue(self.current_config.get("max_undo_history", 100))
        layout.addWidget(self.undo_history_spin)
        
        # Resolução Padrão do Canvas
        layout.addWidget(QLabel("Resolução padrão do canvas (pixels):"))
        self.canvas_res_spin = QSpinBox(self)
        self.canvas_res_spin.setRange(16, 1024)
        self.canvas_res_spin.setValue(self.current_config.get("default_canvas_resolution", 32))
        layout.addWidget(self.canvas_res_spin)
        
        # Zoom Padrão do Canvas
        layout.addWidget(QLabel("Zoom padrão do canvas:"))
        self.canvas_zoom_spin = QSpinBox(self)
        self.canvas_zoom_spin.setRange(1, 50)
        self.canvas_zoom_spin.setValue(self.current_config.get("default_canvas_zoom", 10))
        layout.addWidget(self.canvas_zoom_spin)
        
        # Botões OK/Cancelar
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_config(self):
        return {
            "max_undo_history": self.undo_history_spin.value(),
            "default_canvas_resolution": self.canvas_res_spin.value(),
            "default_canvas_zoom": self.canvas_zoom_spin.value()
        }
        </pre>
        <p>No plugin, você pode abrir esse diálogo da seguinte forma:</p>
        <pre style="background-color: #f4f4f4; padding: 10px;">
def configure(self):
    # Carrega a configuração atual (por exemplo, de um arquivo JSON)
    current_config = load_pixel_art_config()
    dialog = PixelArtConfigDialog(current_config, self)
    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        new_config = dialog.get_config()
        # Atualiza e persiste as configurações:
        save_pixel_art_config(new_config)
        QMessageBox.information(self, "Configurações", "Configurações atualizadas com sucesso!")
</pre>
        
        <h2>5. Como Adicionar o Plugin ao Aplicativo</h2>
        <ol>
            <li>
                <strong>Usando o Gerenciador de Plugins:</strong>
                <p>No menu do aplicativo, acesse <em>Plugins → Gerenciar Plugins</em>.
                Nesta janela, você verá a lista de plugins disponíveis (pastas contendo um arquivo <code>main.py</code>).</p>
                <ul>
                    <li>Clique em <strong>"Adicionar Plugin"</strong> para selecionar uma pasta contendo seu plugin. 
                        O plugin será copiado para a pasta padrão (<code>plugins/</code>).</li>
                    <li>Após adicionar, clique em <strong>"Atualizar Lista"</strong> para atualizar a visualização.
                        Pode ser necessário reiniciar o aplicativo para carregar o novo plugin.</li>
                </ul>
            </li>
            <li>
                <strong>Carregamento Automático:</strong>
                <p>Os plugins registrados no arquivo <code>loaded_plugins.json</code> são carregados automaticamente na inicialização.
                Assim, uma vez registrado, seu plugin estará disponível sempre que o aplicativo iniciar.</p>
            </li>
        </ol>
        
        <h2>6. Dependências e Boas Práticas</h2>
        <p>Para facilitar o desenvolvimento, o aplicativo pode incluir um módulo de bibliotecas (<code>plugin_libs.py</code>)
        com diversas dependências. Documente seu código, teste seu plugin de forma independente e utilize as bibliotecas disponíveis para acelerar o desenvolvimento.</p>
        
        <p><strong>Dica:</strong> Este guia é um ponto de partida. Sinta-se à vontade para expandir a interface e adicionar novas funcionalidades conforme necessário.</p>
        """
        return help_text
