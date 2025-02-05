# plugin_system.py
import os
import json
import importlib.util
import logging
import shutil
from logging.handlers import RotatingFileHandler

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFileDialog, QListWidget, QListWidgetItem,
    QDialog, QDialogButtonBox, QMessageBox, QHBoxLayout, QCheckBox, QPushButton
)
from PyQt5.QtCore import Qt
from plugin_base import PluginTab

# ----------------------
# Configuração do Logging
# ----------------------
LOG_FILE = "plugin_system.log"
# Cria o handler que rotaciona o log quando ele atingir 5 MB e mantém 5 arquivos de backup
handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

# ----------------------
# Configuração dos Plugins
# ----------------------
CONFIG_FILE = "loaded_plugins.json"

def load_plugin_config():
    """
    Retorna uma lista de dicionários no formato:
       [{"file": caminho_do_plugin, "name": nome, "enabled": True, ...}, ...]
    Caso o arquivo não exista, retorna lista vazia.
    Se o arquivo estiver em formato antigo (lista de strings), converte para o novo formato.
    """
    if not os.path.exists(CONFIG_FILE):
        return []
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            plugins = data.get("plugins", [])
            # Verifica se é uma lista de strings (formato antigo)
            if plugins and isinstance(plugins[0], str):
                new_plugins = []
                for file in plugins:
                    new_plugins.append({
                        "file": file,
                        "name": os.path.splitext(os.path.basename(file))[0],
                        "enabled": True
                    })
                return new_plugins
            # Garante que cada entrada possua a flag "enabled"
            for entry in plugins:
                if "enabled" not in entry:
                    entry["enabled"] = True
            return plugins
    except Exception as e:
        logging.error(f"Erro ao carregar config de plugins: {e}")
        return []

def save_plugin_config(plugin_entries):
    """
    Salva a lista de plugins no formato de dicionários.
    """
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"plugins": plugin_entries}, f, indent=4)
    except Exception as e:
        logging.error(f"Erro ao salvar config de plugins: {e}")

def get_plugin_info(plugin_file):
    """
    Tenta carregar o módulo do plugin e extrair informações básicas:
    - name, version, author e description.
    Se ocorrer erro, retorna informações padrão.
    """
    info = {
        "name": os.path.splitext(os.path.basename(plugin_file))[0],
        "version": "N/A",
        "author": "N/A",
        "description": "Sem descrição"
    }
    try:
        plugin_dir = os.path.dirname(plugin_file)
        if plugin_dir not in os.sys.path:
            os.sys.path.insert(0, plugin_dir)
        module_name = os.path.splitext(os.path.basename(plugin_file))[0]
        spec = importlib.util.spec_from_file_location(module_name, plugin_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if plugin_dir in os.sys.path:
            os.sys.path.remove(plugin_dir)
        # Procura a classe do plugin: variável "plugin_class" ou uma subclasse de PluginTab
        plugin_class = getattr(module, "plugin_class", None)
        if plugin_class is None:
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, PluginTab) and attr is not PluginTab:
                    plugin_class = attr
                    break
        if plugin_class:
            # Atualiza as informações se os atributos existirem
            info["name"] = getattr(plugin_class, "name", info["name"])
            info["version"] = getattr(plugin_class, "version", info["version"])
            info["author"] = getattr(plugin_class, "author", info["author"])
            info["description"] = getattr(plugin_class, "description", info["description"])
    except Exception as e:
        logging.error(f"Erro ao obter informações do plugin ({plugin_file}): {e}")
    return info

def load_plugin_instance(parent, plugin_file):
    """
    Importa o módulo do plugin e retorna a instância do plugin (classe derivada de PluginTab).
    """
    try:
        import sys
        plugin_dir = os.path.dirname(plugin_file)
        if plugin_dir not in sys.path:
            sys.path.insert(0, plugin_dir)
        module_name = os.path.splitext(os.path.basename(plugin_file))[0]
        spec = importlib.util.spec_from_file_location(module_name, plugin_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if plugin_dir in sys.path:
            sys.path.remove(plugin_dir)
        plugin_class = getattr(module, "plugin_class", None)
        if plugin_class is None:
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, PluginTab) and attr is not PluginTab:
                    plugin_class = attr
                    break
        if plugin_class is None:
            QMessageBox.warning(parent, "Erro", "Nenhuma classe de plugin válida encontrada no arquivo.")
            return None
        plugin_instance = plugin_class(parent)
        return plugin_instance
    except Exception as e:
        logging.exception("Erro ao carregar plugin")
        QMessageBox.critical(parent, "Erro ao carregar plugin", f"Ocorreu um erro:\n{e}")
        return None

def load_plugin_file_lazy(parent, plugin_file):
    """
    Cria e retorna um widget placeholder para o plugin, que só será carregado
    quando o usuário selecionar a aba.
    """
    plugin_entries = load_plugin_config()
    # Procura se já existe entrada para o plugin
    entry = next((p for p in plugin_entries if p["file"] == plugin_file), None)
    if not entry:
        info = get_plugin_info(plugin_file)
        entry = {"file": plugin_file, "name": info["name"], "enabled": True}
        plugin_entries.append(entry)
        save_plugin_config(plugin_entries)
    placeholder = QWidget()
    placeholder.loaded = False
    placeholder.plugin_file = plugin_file
    placeholder.is_plugin = True  # Identifica que este widget é de plugin
    layout = QVBoxLayout(placeholder)
    msg = QLabel("Clique nesta aba para carregar o plugin", placeholder)
    layout.addWidget(msg)
    placeholder.setWindowTitle(entry["name"])
    return placeholder

class PluginManagerDialog(QDialog):
    """
    Diálogo para gerenciar plugins, permitindo:
    - Visualizar informações do plugin (nome, versão, autor, descrição);
    - Habilitar/desabilitar plugins;
    - Adicionar e remover plugins;
    - Chamar a interface de configuração (se disponível).
    """
    def __init__(self, parent=None, plugin_folder="plugins"):
        super().__init__(parent)
        self.setWindowTitle("Gerenciar Plugins")
        # Define tamanho inicial, mas maximiza a janela ao ser exibida
        self.resize(600, 400)
        self.setWindowState(Qt.WindowMaximized)
        self.plugin_folder = plugin_folder
        self.parent_app = parent

        self.layout = QVBoxLayout(self)

        # Lista customizada para exibir informações e ações para cada plugin
        self.list_widget = QListWidget(self)
        self.layout.addWidget(self.list_widget)

        # Botões gerais de gerenciamento
        self.button_box = QDialogButtonBox(self)
        self.add_button = self.button_box.addButton("Adicionar Plugin", QDialogButtonBox.ActionRole)
        self.refresh_button = self.button_box.addButton("Atualizar Lista", QDialogButtonBox.ActionRole)
        self.close_button = self.button_box.addButton(QDialogButtonBox.Close)
        self.layout.addWidget(self.button_box)

        self.add_button.clicked.connect(self.add_plugin)
        self.refresh_button.clicked.connect(self.atualizar_lista_plugins)
        self.close_button.clicked.connect(self.accept)

        self.populate_list()

    def populate_list(self):
        """Popula a lista com os plugins encontrados na pasta padrão e na configuração."""
        self.list_widget.clear()
        plugin_entries = load_plugin_config()

        # Atualiza informações a partir do diretório de plugins
        if not os.path.exists(self.plugin_folder):
            os.makedirs(self.plugin_folder)
        for item in os.listdir(self.plugin_folder):
            item_path = os.path.join(self.plugin_folder, item)
            if os.path.isdir(item_path):
                main_file = os.path.join(item_path, "main.py")
                if os.path.exists(main_file):
                    abs_path = os.path.abspath(main_file)
                    # Verifica se já está na configuração; se não, adiciona
                    entry = next((p for p in plugin_entries if p["file"] == abs_path), None)
                    if not entry:
                        info = get_plugin_info(abs_path)
                        entry = {"file": abs_path, "name": info["name"], "enabled": True}
                        plugin_entries.append(entry)
                        save_plugin_config(plugin_entries)
                    # Cria o widget de item para a lista
                    item_widget = self.create_plugin_item_widget(entry)
                    list_item = QListWidgetItem()
                    list_item.setSizeHint(item_widget.sizeHint())
                    # Armazena o caminho do plugin para referência
                    list_item.setData(Qt.UserRole, entry["file"])
                    self.list_widget.addItem(list_item)
                    self.list_widget.setItemWidget(list_item, item_widget)

    def create_plugin_item_widget(self, entry):
        """
        Cria um widget com as informações do plugin e botões para ações.
        """
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Informações do plugin
        info = get_plugin_info(entry["file"])
        info_text = (f"<b>{info['name']}</b> "
                     f"(v{info['version']})<br>"
                     f"<i>{info['author']}</i><br>"
                     f"{info['description']}")
        label = QLabel(info_text)
        label.setTextFormat(Qt.RichText)
        layout.addWidget(label)

        # Checkbox para habilitar/desabilitar
        checkbox = QCheckBox("Habilitado")
        checkbox.setChecked(entry.get("enabled", True))
        checkbox.stateChanged.connect(lambda state, e=entry: self.toggle_plugin(e, state))
        layout.addWidget(checkbox)

        # Botão de configuração (se o plugin oferecer interface de configuração)
        config_button = QPushButton("Configurar")
        config_button.clicked.connect(lambda _, file=entry["file"]: self.configure_plugin(file))
        layout.addWidget(config_button)

        # Botão para remover o plugin
        remove_button = QPushButton("Remover")
        remove_button.clicked.connect(lambda _, e=entry: self.remove_plugin(e))
        layout.addWidget(remove_button)

        return widget

    def toggle_plugin(self, entry, state):
        """Atualiza a flag 'enabled' do plugin e salva a configuração."""
        plugin_entries = load_plugin_config()
        for p in plugin_entries:
            if p["file"] == entry["file"]:
                p["enabled"] = (state == Qt.Checked)
                break
        save_plugin_config(plugin_entries)
        logging.info(f"Plugin '{entry['name']}' habilitado: {state == Qt.Checked}")

    def configure_plugin(self, plugin_file):
        """
        Tenta instanciar o plugin e chamar seu método de configuração.
        Caso o plugin não tenha interface, exibe uma mensagem.
        """
        plugin_instance = load_plugin_instance(self, plugin_file)
        if plugin_instance:
            if hasattr(plugin_instance, "configure"):
                try:
                    plugin_instance.configure()
                except Exception as e:
                    logging.exception("Erro ao configurar plugin")
                    QMessageBox.critical(self, "Erro", f"Erro ao configurar plugin:\n{e}")
            else:
                QMessageBox.information(self, "Configurar", "Este plugin não possui opções de configuração.")
        else:
            QMessageBox.warning(self, "Erro", "Não foi possível carregar o plugin para configuração.")

    def remove_plugin(self, entry):
        """Remove o plugin da configuração e da pasta padrão (se desejar)."""
        reply = QMessageBox.question(
            self,
            "Remover Plugin",
            f"Tem certeza que deseja remover o plugin '{entry['name']}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            plugin_entries = load_plugin_config()
            plugin_entries = [p for p in plugin_entries if p["file"] != entry["file"]]
            save_plugin_config(plugin_entries)
            # Opcional: remover os arquivos do plugin da pasta padrão
            plugin_folder = os.path.dirname(entry["file"])
            if os.path.exists(plugin_folder):
                try:
                    shutil.rmtree(plugin_folder)
                except Exception as e:
                    logging.error(f"Erro ao remover diretório do plugin: {e}")
            self.populate_list()

    def add_plugin(self):
        """Adiciona um plugin copiando a pasta selecionada para a pasta padrão."""
        plugin_folder_selected = QFileDialog.getExistingDirectory(self, "Selecione a pasta do plugin")
        if plugin_folder_selected:
            try:
                if not os.path.exists(self.plugin_folder):
                    os.makedirs(self.plugin_folder)
                base_name = os.path.basename(plugin_folder_selected)
                dest_path = os.path.join(self.plugin_folder, base_name)
                shutil.copytree(plugin_folder_selected, dest_path)
                QMessageBox.information(self, "Sucesso", f"Plugin '{base_name}' adicionado com sucesso!")
                self.populate_list()
            except Exception as e:
                logging.exception("Erro ao adicionar plugin")
                QMessageBox.critical(self, "Erro", f"Erro ao adicionar plugin:\n{e}")

    def atualizar_lista_plugins(self):
        """
        Atualiza a lista de plugins a partir da pasta padrão. Após a atualização,
        exibe uma mensagem solicitando o reinício do aplicativo para que as mudanças tenham efeito.
        """
        novos_plugins = []
        if not os.path.exists(self.plugin_folder):
            os.makedirs(self.plugin_folder)
        for item in os.listdir(self.plugin_folder):
            item_path = os.path.join(self.plugin_folder, item)
            if os.path.isdir(item_path):
                main_file = os.path.join(item_path, "main.py")
                if os.path.exists(main_file):
                    abs_path = os.path.abspath(main_file)
                    info = get_plugin_info(abs_path)
                    novos_plugins.append({"file": abs_path, "name": info["name"], "enabled": True})
        save_plugin_config(novos_plugins)
        self.populate_list()
        QMessageBox.information(
            self,
            "Atualizado",
            "A lista de plugins foi atualizada. Por favor, reinicie o aplicativo para aplicar as alterações."
        )
        if self.parent_app:
            self.parent_app.close()
