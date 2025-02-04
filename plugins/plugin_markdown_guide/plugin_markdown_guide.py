from plugin_base import PluginTab
from PyQt5.QtWidgets import QVBoxLayout, QTextBrowser, QStackedWidget, QWidget, QPushButton, QHBoxLayout
from PyQt5.QtCore import QUrl

# Importa o QWebEngineView para renderizar sites
from PyQt5.QtWebEngineWidgets import QWebEngineView

class PluginMarkdownGuide(PluginTab):
    """
    Plugin que adiciona uma aba com um guia completo sobre Markdown.
    Esse guia apresenta exemplos de sintaxe básica, utilização de HTML e
    personalização via <style> para que os usuários possam aplicar Markdown
    tanto nas notas quanto no editor do aplicativo.
    
    Ao clicar no link para <code>https://www.markdownguide.org</code>, o plugin renderiza o site
    internamente utilizando o QWebEngineView.
    """
    name = "Guia Markdown"

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Layout principal do plugin
        main_layout = QVBoxLayout(self)
        
        # Cria um QStackedWidget para alternar entre o guia e o webview
        self.stacked_widget = QStackedWidget(self)
        
        # Página 0: Guia em Markdown (QTextBrowser)
        self.guide_widget = QWidget()
        guide_layout = QVBoxLayout(self.guide_widget)
        self.text_browser = QTextBrowser(self)
        self.text_browser.setReadOnly(True)
        self.text_browser.setOpenExternalLinks(False)  # Impede abertura automática do navegador
        self.text_browser.setHtml(self.get_markdown_guide())
        guide_layout.addWidget(self.text_browser)
        self.guide_widget.setLayout(guide_layout)
        self.stacked_widget.addWidget(self.guide_widget)
        
        # Página 1: WebView para renderizar o site
        self.web_widget = QWidget()
        web_layout = QVBoxLayout(self.web_widget)
        # Cria um botão de voltar para retornar à página do guia
        btn_layout = QHBoxLayout()
        self.back_button = QPushButton("Voltar", self)
        self.back_button.clicked.connect(self.go_back)
        btn_layout.addWidget(self.back_button)
        btn_layout.addStretch()
        web_layout.addLayout(btn_layout)
        # Cria o QWebEngineView para carregar o site
        self.web_view = QWebEngineView(self)
        web_layout.addWidget(self.web_view)
        self.web_widget.setLayout(web_layout)
        self.stacked_widget.addWidget(self.web_widget)
        
        main_layout.addWidget(self.stacked_widget)
        self.setLayout(main_layout)
        
        # Conecta o clique de links do QTextBrowser à função que renderiza o site
        self.text_browser.anchorClicked.connect(self.open_link_in_webview)

    def get_markdown_guide(self):
        guide_text = """
        <h1>Guia Completo sobre Markdown</h1>
        <p>O Markdown é uma linguagem de marcação simples que permite converter texto plano em HTML de forma rápida e intuitiva. A seguir, você encontrará exemplos e dicas para utilizar Markdown nas suas notas e no editor.</p>
        
        <h2>1. Sintaxe Básica</h2>
        <ul>
            <li>
                <strong>Títulos</strong>: Utilize o caractere <code>#</code> para criar títulos. Exemplos:
                <pre style="background-color: #f4f4f4; padding: 10px;">
# Título Nível 1
## Título Nível 2
### Título Nível 3
                </pre>
            </li>
            <li>
                <strong>Negrito e Itálico</strong>: Para destacar textos, use:
                <pre style="background-color: #f4f4f4; padding: 10px;">
**Negrito** ou __Negrito__
*Itálico* ou _Itálico_
                </pre>
            </li>
            <li>
                <strong>Listas</strong>: Crie listas não ordenadas ou ordenadas:
                <pre style="background-color: #f4f4f4; padding: 10px;">
- Item 1
- Item 2
- Item 3

1. Primeiro item
2. Segundo item
3. Terceiro item
                </pre>
            </li>
            <li>
                <strong>Links e Imagens</strong>: Insira links e imagens da seguinte forma:
                <pre style="background-color: #f4f4f4; padding: 10px;">
[Texto do Link](https://www.exemplo.com)

![Texto Alternativo](https://via.placeholder.com/150)
                </pre>
            </li>
            <li>
                <strong>Código</strong>: Destaque trechos de código com crases simples para inline:
                <pre style="background-color: #f4f4f4; padding: 10px;">
`código inline`
                </pre>
            </li>
        </ul>
        
        <h2>2. Markdown com HTML e <code>&lt;style&gt;</code></h2>
        <p>Você pode combinar Markdown com HTML para personalizar a formatação do seu conteúdo. Por exemplo, adicione estilos diretamente no documento:</p>
        <pre style="background-color: #f4f4f4; padding: 10px;">
&lt;style&gt;
  h1 { color: #2E86C1; }
  p { font-family: Arial, sans-serif; }
  code { background-color: #f4f4f4; padding: 2px 4px; }
&lt;/style&gt;

# Título com Estilo
<p style="color: green; font-size: 16px;">Este parágrafo está estilizado usando a tag &lt;style&gt;.</p>
        </pre>
        <p>Dessa forma, você pode definir estilos globais para títulos, parágrafos, blocos de código e outros elementos HTML que compõem a sua nota.</p>
        
        <h2>3. Exemplo Completo de Nota em Markdown</h2>
        <p>Confira um exemplo de nota estruturada em Markdown:</p>
        <pre style="background-color: #f4f4f4; padding: 10px;">
# Nota de Reunião

**Data:** 04/02/2025

## Participantes
- João
- Maria
- Carlos

## Pauta
1. Revisão do Projeto
2. Definição de Prazos
3. Alocação de Recursos

## Comentários
* A reunião foi produtiva e todas as questões foram debatidas.
* Próxima reunião agendada para 11/02/2025.

Para mais detalhes, acesse [Nosso Site](https://www.markdownguide.org).
        </pre>
        
        <h2>4. Dicas para Uso no Editor e Notas</h2>
        <ul>
            <li>Utilize a visualização de Markdown do editor para conferir a renderização do conteúdo em tempo real.</li>
            <li>Experimente combinar Markdown com HTML para criar layouts mais sofisticados.</li>
            <li>Defina estilos globais utilizando a tag <code>&lt;style&gt;</code> para padronizar a aparência de suas notas.</li>
        </ul>

        <h2>5. Recursos Adicionais</h2>
        <p>Para se aprofundar no uso de Markdown, confira os seguintes links:</p>
        <ul>
            <li><a href="https://www.markdownguide.org" target="_self">Markdown Guide</a></li>
            <li><a href="https://daringfireball.net/projects/markdown/" target="_blank">Daring Fireball - Markdown</a></li>
        </ul>
        
        <p>Esperamos que este guia ajude você a aproveitar ao máximo o poder do Markdown para criar notas e conteúdos ricos no seu editor. Boas anotações!</p>
        """
        return guide_text

    def open_link_in_webview(self, url):
        """
        Ao clicar no link, se for o endereço desejado, abre-o no QWebEngineView.
        """
        if url.toString() == "https://www.markdownguide.org":
            self.web_view.load(url)
            self.stacked_widget.setCurrentIndex(1)
        else:
            from PyQt5.QtGui import QDesktopServices
            QDesktopServices.openUrl(url)

    def go_back(self):
        """
        Retorna para a visualização do guia Markdown.
        Para evitar que o QTextBrowser fique em branco, recarregamos o conteúdo.
        """
        # Recarrega o conteúdo do guia (caso haja alterações ou perda de estado)
        self.text_browser.setHtml(self.get_markdown_guide())
        self.stacked_widget.setCurrentIndex(0)

# Permite testar o plugin de forma independente
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = PluginMarkdownGuide()
    window.setWindowTitle("Guia Markdown")
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
