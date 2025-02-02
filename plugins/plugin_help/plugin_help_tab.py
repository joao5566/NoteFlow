from plugin_base import PluginTab
from PyQt5.QtWidgets import QVBoxLayout, QTextBrowser

class PluginHelpTab(PluginTab):
    """
    Plugin que adiciona uma aba de Ajuda para Plugins.
    Exibe um guia com instruções de como criar, adicionar e integrar plugins ao aplicativo.
    """
    name = "Ajuda Plugins"

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
        # Conteúdo de ajuda em HTML atualizado, incluindo exemplo do arquivo main.py
        help_text = """
        <h1>Guia para Criar e Adicionar Plugins</h1>
        <p>Este aplicativo permite a criação de plugins para ampliar suas funcionalidades. Um plugin é um módulo Python que adiciona uma nova aba ao aplicativo. Siga os passos abaixo para criar e integrar seu plugin:</p>
        
        <h2>1. Estrutura do Plugin</h2>
        <ul>
            <li>O plugin deve ser um arquivo <code>.py</code> (por exemplo, <code>meu_plugin.py</code>).</li>
            <li>Organize seus plugins em uma pasta dedicada (por exemplo, <code>plugins/</code>), podendo ser divididos em subpastas para manter a organização.</li>
            <li>Dentro do seu plugin, crie uma classe que <strong>herde de <code>PluginTab</code></strong>. Essa classe deve definir, pelo menos, o atributo <code>name</code> (que aparecerá como o título da aba) e implementar a interface desejada.</li>
        </ul>
        
        <h2>2. Exemplo de Código do Plugin</h2>
        <pre style="background-color: #f4f4f4; padding: 10px;">
from plugin_base import PluginTab
from PyQt5.QtWidgets import QLabel, QVBoxLayout

class MeuPlugin(PluginTab):
    name = "Meu Plugin"

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("Conteúdo do meu plugin.", self)
        layout.addWidget(label)
        self.setLayout(layout)
        </pre>
        
        <h2>3. Exemplo do Arquivo <code>main.py</code></h2>
        <p>O arquivo <code>main.py</code> é o ponto de entrada do plugin. Ele deve definir a variável <code>plugin_class</code> para indicar qual classe será carregada pelo aplicativo e pode incluir uma função <code>main()</code> para testar o plugin de forma independente.</p>
        <pre style="background-color: #f4f4f4; padding: 10px;">
import sys
import os

# Adiciona o diretório pai ao sys.path para facilitar a importação de módulos do app
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from plugin_help_tab import PluginHelpTab

# Define a variável global para o carregamento do plugin
plugin_class = PluginHelpTab

# Função main para testes independentes
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
        
        <h2>4. Como Adicionar o Plugin ao Aplicativo</h2>
        <ol>
            <li>
                <strong>Utilizando o Gerenciador de Plugins:</strong>
                <p>No menu do aplicativo, acesse <em>Plugins → Gerenciar Plugins</em>. Nesta janela, você verá a lista de plugins disponíveis (subpastas contendo um arquivo <code>main.py</code>).</p>
                <ul>
                    <li>Clique em <strong>"Adicionar Plugin"</strong> para selecionar uma pasta contendo seu plugin. O plugin será copiado para a pasta padrão (<code>plugins/</code>).</li>
                    <li>Após adicionar, clique em <strong>"Atualizar Lista de Plugs"</strong> para atualizar a visualização. Em alguns casos, o aplicativo precisará ser reiniciado para carregar o novo plugin.</li>
                </ul>
            </li>
            <li>
                <strong>Carregamento Automático:</strong>
                <p>Os plugins registrados no arquivo <code>loaded_plugins.json</code> são carregados automaticamente na inicialização do aplicativo. Assim, uma vez registrado, seu plugin estará disponível sempre que o app for iniciado.</p>
            </li>
        </ol>
        
        <h2>5. Dependências Disponíveis</h2>
        <p>Para facilitar o desenvolvimento de plugins, o aplicativo já inclui um módulo de bibliotecas (<code>plugin_libs.py</code>) com diversas dependências comuns. A lista completa (com versões) é a seguinte:</p>
        <pre style="background-color: #f4f4f4; padding: 10px;">
altgraph==0.17.4
asteval==1.0.6
beautifulsoup4==4.12.3
certifi==2025.1.31
cffi==1.17.1
charset-normalizer==3.4.1
comtypes==1.4.9
contourpy==1.3.1
cryptography==44.0.0
cycler==0.12.1
docstring-to-markdown==0.15
et_xmlfile==2.0.0
fonttools==4.55.8
fpdf==1.7.2
idna==3.10
jedi==0.19.2
kiwisolver==1.4.8
lupa==2.4
Markdown==3.7
matplotlib==3.10.0
numpy==2.2.2
openpyxl==3.1.5
packaging==24.2
pandas==2.2.3
parso==0.8.4
pefile==2023.2.7
pillow==11.1.0
pluggy==1.5.0
pycparser==2.22
pygame==2.6.1
pyinstaller==6.11.1
pyinstaller-hooks-contrib==2025.0
pyparsing==3.2.1
pypiwin32==223
PyQt5==5.15.11
PyQt5-Qt5==5.15.2
PyQt5_sip==12.16.1
python-dateutil==2.9.0.post0
python-lsp-jsonrpc==1.1.2
python-lsp-server==1.12.0
python-vlc==3.0.21203
pyttsx3==2.98
pytz==2025.1
pywin32==308
pywin32-ctypes==0.2.3
requests==2.32.3
setuptools==75.8.0
six==1.17.0
soupsieve==2.6
tzdata==2025.1
ujson==5.10.0
urllib3==2.3.0
        </pre>
        <p>Exemplo de uso no seu plugin:</p>
        <pre style="background-color: #f4f4f4; padding: 10px;">
from plugin_libs import QtWidgets, np, pd, plt, requests, logging, functools, itertools, math, calendar

class MeuPlugin(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel("Plugin Exemplo", self)
        layout.addWidget(label)
        # Exemplo com NumPy:
        print("Vetor de exemplo:", np.array([1, 2, 3]))
        self.setLayout(layout)
        </pre>
        
        <h2>6. Boas Práticas</h2>
        <ul>
            <li>Teste seu plugin de forma independente para garantir que a classe base e a interface estejam funcionando corretamente.</li>
            <li>Documente seu código para facilitar a manutenção e futuras melhorias.</li>
            <li>Aproveite as bibliotecas já importadas no <code>plugin_libs.py</code> para acelerar o desenvolvimento.</li>
        </ul>
        
        <p><strong>Dica:</strong> Este é um exemplo básico. Sinta-se à vontade para expandir a interface e adicionar novas funcionalidades conforme necessário.</p>
        """
        return help_text
