# plugins/plugin_help/plugin_help_tab.py

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
        # Conteúdo de ajuda em HTML atualizado
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
        
        <h2>3. Como Adicionar o Plugin ao Aplicativo</h2>
        <ol>
            <li>
                <strong>Utilizando o Gerenciador de Plugins:</strong>
                <p>No menu do aplicativo, acesse <em>Plugins → Gerenciar Plugins</em>. Nesta janela, você verá a lista de plugins disponíveis (subpastas contendo um arquivo <code>main.py</code>).</p>
                <ul>
                    <li>Clique em <strong>"Adicionar Plugin"</strong> para selecionar uma pasta contendo seu plugin. O plugin será copiado para a pasta padrão (<code>plugins/</code>).</li>
                    <li>Após adicionar, clique em <strong>"Atualizar Lista"</strong> para atualizar a visualização.</li>
                </ul>
            </li>
            <li>
                <strong>Atualizando e Reiniciando o App:</strong>
                <p>
                    O botão <strong>"Atualizar Lista de Plugs"</strong> não só atualiza a lista de plugins e registra os plugins válidos no arquivo <code>loaded_plugins.json</code>, como também reinicia o aplicativo automaticamente para carregar as novas configurações.
                </p>
            </li>
            <li>
                <strong>Carregamento Automático:</strong>
                <p>Os plugins registrados em <code>loaded_plugins.json</code> são carregados automaticamente na inicialização do aplicativo. Assim, uma vez registrado, seu plugin estará disponível sempre que o app for iniciado.</p>
            </li>
        </ol>
        
        <h2>4. Dependências Disponíveis</h2>
        <p>O instalador do aplicativo já inclui as seguintes bibliotecas, que você pode utilizar no seu plugin:</p>
        <pre style="background-color: #f4f4f4; padding: 10px;">
altgraph
asteval
beautifulsoup4
cffi
contourpy
cryptography
cycler
docstring-to-markdown
et_xmlfile
fonttools
fpdf
jedi
kiwisolver
lupa
Markdown
matplotlib
numpy
openpyxl
packaging
pandas
parso
pillow
pluggy
pycparser
pygame
pyinstaller
pyinstaller-hooks-contrib
pyparsing
PyQt5
PyQt5-Qt5
PyQt5_sip
python-dateutil
python-lsp-jsonrpc
python-lsp-server
python-vlc
pytz
setuptools
six
soupsieve
tzdata
ujson
        </pre>
        
        <h2>5. Boas Práticas</h2>
        <ul>
            <li>Teste seu plugin de forma independente para garantir que a classe base e a interface estejam funcionando corretamente.</li>
            <li>Documente o código do seu plugin para facilitar a manutenção e futuras melhorias.</li>
            <li>Aproveite as bibliotecas disponíveis para criar funcionalidades ricas e interativas.</li>
        </ul>
        
        <p><strong>Dica:</strong> Este é um exemplo básico. Sinta-se à vontade para expandir a interface e adicionar novas funcionalidades conforme necessário.</p>
        """
        return help_text
