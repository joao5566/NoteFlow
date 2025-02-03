# shop_module.py
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox,
    QGridLayout, QTabWidget, QHBoxLayout, QScrollArea, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QTimer, QSize,QPoint
from PyQt5.QtGui import QColor, QPixmap, QIcon, QFont,QPainter, QBrush, QFont,QPolygon,QPen

import os
import json
import logging



def load_shop_items():
    items = []
    main_items_path = "shop_items"
    hats_path = os.path.join(main_items_path, "hats")  # Caminho específico para chapéus
    body_colors_path = os.path.join(main_items_path, "body_colors")  # Novo caminho para as cores de corpo

    # Carrega itens gerais
    if os.path.exists(main_items_path):
        for file_name in os.listdir(main_items_path):
            if file_name.endswith(".json") and file_name != "hats" and file_name != "body_colors":  # Ignora chapéus e cores de corpo
                file_path = os.path.join(main_items_path, file_name)
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        item_data = json.load(file)
                        if 'type' in item_data and item_data['type'] != 'hat':  # Evita carregar chapéus do diretório principal
                            items.append(item_data)
                except json.JSONDecodeError as e:
                    QMessageBox.warning(None, "Erro de JSON", f"Erro ao carregar {file_name}: {str(e)}")

    # Carrega chapéus
    if os.path.exists(hats_path):
        for file_name in os.listdir(hats_path):
            if file_name.endswith(".json"):
                file_path = os.path.join(hats_path, file_name)
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        hat_data = json.load(file)
                        items.append(hat_data)  # Assume que todos os itens no diretório 'hats' são chapéus
                except json.JSONDecodeError as e:
                    QMessageBox.warning(None, "Erro de JSON", f"Erro ao carregar {file_name}: {str(e)}")

    # Carrega cores de corpo
    if os.path.exists(body_colors_path):
        for file_name in os.listdir(body_colors_path):
            if file_name.endswith(".json"):
                file_path = os.path.join(body_colors_path, file_name)
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        body_color_data = json.load(file)
                        body_color_data["type"] = "body_color"  # Certifique-se de definir o tipo como 'body_color'
                        items.append(body_color_data)
                except json.JSONDecodeError as e:
                    QMessageBox.warning(None, "Erro de JSON", f"Erro ao carregar {file_name}: {str(e)}")

    return items


class ShapeWidget(QWidget):
    def __init__(self, shape, color, size=30, parent=None):
        super().__init__(parent)
        self.shape = shape
        self.color = color
        self.size = size  # Definir o tamanho da forma
        self.setFixedSize(self.size, self.size)  # Ajusta o tamanho do widget para o tamanho definido
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()

        # Centraliza o ponto de origem
        painter.translate(width // 2, height // 2)

        # Definindo a cor
        painter.setBrush(QBrush(QColor(self.color), Qt.SolidPattern))
        painter.setPen(QPen(Qt.black, 1))  # Adiciona uma borda preta, caso necessário

        # Ajuste do tamanho das formas com base no parâmetro 'size'
        if self.shape == "glove":
            painter.drawEllipse(-self.size // 2, -self.size // 2, self.size, self.size)  # Ajusta o tamanho da luva
        elif self.shape == "glasses":
            lens_width = self.size // 2
            lens_height = self.size // 4
            # Desenhando as lentes dos óculos com o tamanho ajustado
            painter.drawRect(-lens_width - 2, -lens_height // 2, lens_width, lens_height)
            painter.drawRect(2, -lens_height // 2, lens_width, lens_height)
            painter.drawLine(-2, 0, 2, 0)  # Ponte dos óculos
        elif self.shape == "hat":
            painter.drawRect(-self.size // 2, -self.size // 4, self.size, self.size // 2)  # Ajusta o tamanho do chapéu
        elif self.shape == "circle":
            painter.drawEllipse(-self.size // 2, -self.size // 2, self.size, self.size)  # Ajusta o tamanho do círculo
        elif self.shape == "square":
            painter.drawRect(-self.size // 2, -self.size // 2, self.size, self.size)  # Ajusta o tamanho do quadrado
        elif self.shape == "triangle":
            # Ajuste para o triângulo, centralizado com base no tamanho
            points = [QPoint(0, -self.size // 2),  # Topo do triângulo
                      QPoint(self.size // 2, self.size // 2),  # Ponto inferior direito
                      QPoint(-self.size // 2, self.size // 2)]  # Ponto inferior esquerdo
            painter.drawPolygon(QPolygon(points))  # Triângulo centralizado
        elif self.shape == "star":
            # Desenho de uma estrela
            points = [
                QPoint(0, -self.size // 2), 
                QPoint(self.size // 3, -self.size // 3), 
                QPoint(self.size // 2, 0),
                QPoint(self.size // 3, self.size // 3), 
                QPoint(0, self.size // 2),
                QPoint(-self.size // 3, self.size // 3),
                QPoint(-self.size // 2, 0),
                QPoint(-self.size // 3, -self.size // 3),
            ]
            painter.drawPolygon(QPolygon(points))
        else:
            # Forma padrão (caso não definido)
            painter.setBrush(QBrush(Qt.gray, Qt.SolidPattern))
            painter.drawRect(-self.size // 2, -self.size // 2, self.size, self.size)  # Forma padrão centralizada

   
    

class ShopModule(QWidget):
    def __init__(self, pet_game, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Loja do Mascote")
        self.resize(800, 600)  # Ajuste o tamanho conforme necessário
        self.pet_game = pet_game  # Referência ao módulo principal para acessar status e moedas
        

        # Carregar itens da loja
        self.items = load_shop_items()  # Inicializa a lista de itens

        self.init_ui()

    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)  # Espaçamento vertical entre widgets no layout principal
        layout.setContentsMargins(20, 20, 20, 20)  # Margens externas

        self.setLayout(layout)

        self.setStyleSheet("QLabel, QPushButton { font-size: 14px; }")

        # Exibir moedas atuais
        self.coins_label = QLabel(f"Moedas: {self.pet_game.coins}")
        self.coins_label.setAlignment(Qt.AlignCenter)
        self.coins_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(self.coins_label)

        # Criar abas para itens disponíveis, comprados, consumíveis e bloqueados
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Definir as grades para itens
        self.available_grid = QGridLayout()  # Definir a grade de itens disponíveis
        self.purchased_grid = QGridLayout()  # Definir a grade de itens comprados
        self.consumables_grid = QGridLayout()  # Definir a grade de consumíveis
        self.locked_grid = QGridLayout()  # Definir a grade de itens bloqueados

        self.init_available_items_tab()
        self.init_purchased_items_tab()
        self.init_consumables_tab()
        self.init_purchased_consumables_tab()  # Nova aba para consumíveis comprados
        self.init_locked_items_tab()  # Adiciona a nova aba


    def init_available_items_tab(self):
        self.available_tab = QWidget()
        available_layout = QVBoxLayout(self.available_tab)
        available_layout.setSpacing(10)
        available_layout.setContentsMargins(10, 10, 10, 10)

        # Criar abas internas para separar os tipos de itens
        self.sub_tabs = QTabWidget()
        available_layout.addWidget(self.sub_tabs)

        # Abas para cada tipo de item
        self.hats_tab = QWidget()
        self.accessories_tab = QTabWidget()  # Subdivisão de Acessórios
        self.body_tab = QTabWidget()  # Alterado para QTabWidget para suportar addTab

        self.sub_tabs.addTab(self.hats_tab, "Chapéus")
        self.sub_tabs.addTab(self.accessories_tab, "Acessórios")
        self.sub_tabs.addTab(self.body_tab, "Corpo")

        # Sub-abas para os acessórios (óculos e luvas)
        self.glasses_tab = QWidget()
        self.gloves_tab = QWidget()

        self.accessories_tab.addTab(self.glasses_tab, "Óculos")
        self.accessories_tab.addTab(self.gloves_tab, "Luvas")

        # Sub-abas para a Cor do Corpo
        self.body_color_tab = QWidget()  # Sub-aba para as cores do corpo
        self.body_shape_tab = QWidget()  # Sub-aba para a forma do corpo

        self.body_tab.addTab(self.body_color_tab, "Cor Corpo")
        self.body_tab.addTab(self.body_shape_tab, "Forma Corpo")

        # Preencher abas com itens
        self.init_items_for_sub_tab(self.hats_tab, "hat")
        self.init_items_for_accessory_sub_tab(self.glasses_tab, "glasses")
        self.init_items_for_accessory_sub_tab(self.gloves_tab, "glove")
        self.init_items_for_sub_tab(self.body_shape_tab, "body_shape")
        self.init_items_for_sub_tab(self.body_color_tab, "body_color")  # Para as cores do corpo

        self.tabs.addTab(self.available_tab, "Comprar Itens")

    

    def init_items_for_sub_tab(self, tab_widget, item_type):
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setSpacing(10)
        tab_layout.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        tab_layout.addWidget(scroll)

        scroll_content = QWidget()
        scroll.setWidget(scroll_content)

        grid_layout = QGridLayout(scroll_content)
        grid_layout.setSpacing(10)
        grid_layout.setContentsMargins(10, 10, 10, 10)

        row, col = 0, 0
        max_columns = 3

        for item in self.items:
            if item.get("type") == item_type and self.pet_game.level >= item.get("level", 1) and not self.is_item_purchased(item):
                item_widget = self.create_item_widget(item, purchase=True)
                grid_layout.addWidget(item_widget, row, col)
                col += 1
                if col == max_columns:
                    col = 0
                    row += 1


    def init_items_for_accessory_sub_tab(self, tab_widget, shape_type):
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setSpacing(10)
        tab_layout.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        tab_layout.addWidget(scroll)

        scroll_content = QWidget()
        scroll.setWidget(scroll_content)

        grid_layout = QGridLayout(scroll_content)
        grid_layout.setSpacing(10)
        grid_layout.setContentsMargins(10, 10, 10, 10)

        row, col = 0, 0
        max_columns = 3

        for item in self.items:
            if item.get("type") == "accessory" and item.get("shape") == shape_type and self.pet_game.level >= item.get("level", 1) and not self.is_item_purchased(item):
                item_widget = self.create_item_widget(item, purchase=True)
                grid_layout.addWidget(item_widget, row, col)
                col += 1
                if col == max_columns:
                    col = 0
                    row += 1

    def init_purchased_items_tab(self):
        self.purchased_tab = QWidget()
        purchased_layout = QVBoxLayout(self.purchased_tab)
        purchased_layout.setSpacing(10)
        purchased_layout.setContentsMargins(10, 10, 10, 10)

        # Cria um QTabWidget para agrupar os itens comprados por categoria
        self.purchased_tabs = QTabWidget()
        purchased_layout.addWidget(self.purchased_tabs)

        # Define as categorias desejadas e cria um dicionário para armazenar os itens
        categories = {
            "Chapéus": [],
            "Óculos": [],
            "Luvas": [],
            "Corpo": []
        }

        # Agrupa os itens comprados por categoria
        for item in self.items:
            if item.get("type") != "consumable" and self.is_item_purchased(item):
                t = item.get("type")
                if t == "hat":
                    categories["Chapéus"].append(item)
                elif t == "accessory":
                    shape = item.get("shape")
                    if shape == "glasses":
                        categories["Óculos"].append(item)
                    elif shape == "glove":
                        categories["Luvas"].append(item)
                    else:
                        # Se houver outros tipos de acessórios, você pode criar uma nova categoria ou adicioná-los a uma categoria genérica
                        categories.setdefault("Acessórios", []).append(item)
                elif t in ["body_color", "body_shape"]:
                    categories["Corpo"].append(item)

        # Para cada categoria, cria uma aba interna com um QScrollArea e um layout em grade
        for cat, items in categories.items():
            if items:
                cat_widget = QWidget()
                cat_layout = QVBoxLayout(cat_widget)
                cat_layout.setSpacing(10)
                cat_layout.setContentsMargins(10, 10, 10, 10)

                scroll_area = QScrollArea()
                scroll_area.setWidgetResizable(True)
                cat_layout.addWidget(scroll_area)

                scroll_content = QWidget()
                scroll_area.setWidget(scroll_content)

                grid_layout = QGridLayout(scroll_content)
                grid_layout.setSpacing(10)
                grid_layout.setContentsMargins(10, 10, 10, 10)

                row, col = 0, 0
                max_columns = 3  # Você pode ajustar esse valor conforme o espaço desejado

                # Opcional: ordenar os itens alfabeticamente pelo nome
                items = sorted(items, key=lambda x: x.get("name", ""))
                for item in items:
                    item_widget = self.create_item_widget(item, purchase=False)
                    grid_layout.addWidget(item_widget, row, col)
                    col += 1
                    if col >= max_columns:
                        col = 0
                        row += 1

                self.purchased_tabs.addTab(cat_widget, cat)

        # Adiciona a aba "Itens Comprados" ao QTabWidget principal da loja
        self.tabs.addTab(self.purchased_tab, "Itens Comprados")


    def init_consumables_tab(self):
        self.consumables_tab = QWidget()
        consumables_layout = QVBoxLayout(self.consumables_tab)
        consumables_layout.setSpacing(10)
        consumables_layout.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        consumables_layout.addWidget(scroll)

        scroll_content = QWidget()
        scroll.setWidget(scroll_content)

        self.consumables_grid = QGridLayout(scroll_content)
        self.consumables_grid.setSpacing(10)
        self.consumables_grid.setContentsMargins(10, 10, 10, 10)

        row, col = 0, 0
        max_columns = 3  # Número máximo de colunas por linha

        for item in self.items:
            if item.get("type") == "consumable":
                if self.pet_game.level >= item.get("level", 1):
                    item_widget = self.create_consumable_widget(item)
                    self.consumables_grid.addWidget(item_widget, row, col)
                    col += 1
                    if col == max_columns:
                        col = 0
                        row += 1

        self.tabs.addTab(self.consumables_tab, "Consumíveis")

    def init_purchased_consumables_tab(self):
        self.purchased_consumables_tab = QWidget()
        purchased_consumables_layout = QVBoxLayout(self.purchased_consumables_tab)
        purchased_consumables_layout.setSpacing(10)
        purchased_consumables_layout.setContentsMargins(10, 10, 10, 10)

        # Exibir status do pet
        status_layout = QHBoxLayout()
        self.status_hunger = QLabel(f"Fome: {self.pet_game.hunger}")
        self.status_energy = QLabel(f"Energia: {self.pet_game.energy}")
        self.status_happiness = QLabel(f"Felicidade: {self.pet_game.happiness}")
        status_font = QFont("Arial", 14, QFont.Bold)
        self.status_hunger.setFont(status_font)
        self.status_energy.setFont(status_font)
        self.status_happiness.setFont(status_font)
        status_layout.addWidget(self.status_hunger)
        status_layout.addWidget(self.status_energy)
        status_layout.addWidget(self.status_happiness)
        purchased_consumables_layout.addLayout(status_layout)

        # Adicionar uma linha divisória
        divider = QLabel()
        divider.setFixedHeight(2)
        divider.setStyleSheet("background-color: gray;")
        purchased_consumables_layout.addWidget(divider)

        # Lista de consumíveis comprados
        self.consumables_list_widget = QListWidget()
        self.consumables_list_widget.setIconSize(QSize(64, 64))
        self.consumables_list_widget.setSpacing(10)
        purchased_consumables_layout.addWidget(self.consumables_list_widget)

        self.refresh_purchased_consumables()

        self.tabs.addTab(self.purchased_consumables_tab, "Consumíveis Comprados")

    def init_locked_items_tab(self):
        self.locked_tab = QWidget()
        locked_layout = QVBoxLayout(self.locked_tab)
        locked_layout.setSpacing(10)
        locked_layout.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        locked_layout.addWidget(scroll)

        scroll_content = QWidget()
        scroll.setWidget(scroll_content)

        self.locked_grid = QGridLayout(scroll_content)
        self.locked_grid.setSpacing(10)
        self.locked_grid.setContentsMargins(10, 10, 10, 10)

        row, col = 0, 0
        max_columns = 3  # Número máximo de colunas por linha

        for item in self.items:
            required_level = item.get("level", 1)
            if self.pet_game.level < required_level:
                item_widget = self.create_locked_item_widget(item)
                self.locked_grid.addWidget(item_widget, row, col)
                col += 1
                if col == max_columns:
                    col = 0
                    row += 1

        self.tabs.addTab(self.locked_tab, "Itens Bloqueados")

    def is_item_purchased(self, item):
        item_type = item.get("type")
        item_id = item.get("id")
        if item_type == "hat":
            return item_id in self.pet_game.unlocked_hats
        elif item_type == "accessory":
            return item_id in self.pet_game.unlocked_accessories
        elif item_type == "body_color":
            return item.get("color") in self.pet_game.unlocked_colors
        elif item_type == "body_shape":
            return item.get("shape") in self.pet_game.unlocked_bodies
        elif item_type == "consumable":
            return item_id in self.pet_game.unlocked_consumables
        return False

    def is_item_equipped(self, item):
        item_type = item.get("type")
        item_id = item.get("id")
        if item_type == "hat":
            return self.pet_game.equipped_hat == item_id
        elif item_type == "accessory":
            return item_id in self.pet_game.equipped_accessories
        elif item_type == "body_color":
            return self.pet_game.body_color == item.get("color")
        elif item_type == "body_shape":
            return self.pet_game.body_style == item.get("shape")
        return False

    
    def create_item_widget(self, item, purchase=True):
        widget = QWidget()
        layout = QHBoxLayout(widget)  # Layout horizontal
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)  # Espaçamento entre widgets
        layout.setContentsMargins(10, 10, 10, 10)  # Margens internas

        # Desenhando a forma do acessório (baseado no shape)
        shape = item.get("shape")
        color = item.get("color", "#000000")  # Pega a cor do item, se não definida, usa preto como padrão

        
        # Verifica se o item é do tipo 'body_color' e aplica a cor no widget correto
        if item.get("type") == "body_color":
            #print(f"Aplicando a cor para body_color: {color}")
            # Aqui você pode garantir que a cor seja aplicada corretamente, caso seja um corpo
            shape_widget = ShapeWidget("square", color, size=50) 
        else:
            # Se não for um item de corpo, trata a cor normalmente
            #shape_widget = ShapeWidget(shape, color, size=50)
            shape = item.get("shape")
            shape_widget = ShapeWidget(shape, color, size=50)

        icon_size = 50  # Ajuste o tamanho aqui para o tamanho desejado
        #shape_widget = ShapeWidget(shape, color, size=icon_size)
        layout.addWidget(shape_widget)  # A forma ficará à esquerda
        

        # Criando o layout vertical para as informações do item
        info_layout = QVBoxLayout()
        info_layout.setAlignment(Qt.AlignCenter)

        # Nome do item
        name_label = QLabel(item.get("name", "Item"))
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setFont(QFont("Arial", 12, QFont.Bold))
        info_layout.addWidget(name_label)

        # Preço do item
        price_label = QLabel(f"Preço: {item.get('price', 0)} moedas")
        price_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(price_label)

        # Descrição do item
        description = item.get("description", "Sem descrição")
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("font-size: 12px;")
        info_layout.addWidget(desc_label)

        # Botão de ação
        if purchase:
            button = QPushButton("Comprar")
            button.clicked.connect(lambda checked, i=item: self.buy_item(i))
        else:
            button_text = "Equipar" if not self.is_item_equipped(item) else "Equipado"
            button = QPushButton(button_text)
            button.setEnabled(not self.is_item_equipped(item))
            if not self.is_item_equipped(item):
                button.clicked.connect(lambda checked, i=item: self.equip_item(i))

        info_layout.addWidget(button)

        # Adiciona o layout de informações ao layout principal
        layout.addLayout(info_layout)

        return widget



    def create_consumable_widget(self, item):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)  # Espaçamento entre widgets
        layout.setContentsMargins(10, 10, 10, 10)  # Margens internas

        # Adicionar imagem ao consumível
        image_label = QLabel()
        image_path = item.get("image_path", "")  # Assegure-se de que 'image_path' está no JSON
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(pixmap)
        else:
            # Usar uma imagem padrão ou deixar vazio
            pixmap = QPixmap(64, 64)
            pixmap.fill(QColor("gray"))
            image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(image_label)

        # Detalhes do consumível
        details_layout = QVBoxLayout()
        name_label = QLabel(item.get("name", "Consumível"))
        name_label.setAlignment(Qt.AlignLeft)
        name_label.setFont(QFont("Arial", 12, QFont.Bold))
        details_layout.addWidget(name_label)

        price_label = QLabel(f"Preço: {item.get("price", 0)} moedas")
        price_label.setAlignment(Qt.AlignLeft)
        details_layout.addWidget(price_label)

        description = item.get("description", "Sem descrição")
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignLeft)
        desc_label.setStyleSheet("font-size: 12px;")  # Fonte menor para descrições
        details_layout.addWidget(desc_label)

        layout.addLayout(details_layout)

        # Botão de compra
        button = QPushButton("Comprar")
        button.clicked.connect(lambda checked, i=item: self.buy_consumable(i))
        layout.addWidget(button)

        return widget

    def create_purchased_consumable_widget(self, item, quantity):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Ícone do consumível
        icon_label = QLabel()
        image_path = item.get("image_path", "")
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            pixmap = pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            pixmap = QPixmap(48, 48)
            pixmap.fill(QColor("gray"))
            icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        # Nome e quantidade
        name_quantity_layout = QVBoxLayout()
        name_label = QLabel(item.get("name", "Consumível"))
        name_label.setFont(QFont("Arial", 12, QFont.Bold))
        name_label.setAlignment(Qt.AlignLeft)
        name_quantity_layout.addWidget(name_label)

        quantity_label = QLabel(f"Quantidade: {quantity}")
        quantity_label.setAlignment(Qt.AlignLeft)
        name_quantity_layout.addWidget(quantity_label)

        layout.addLayout(name_quantity_layout)

        # Botão para usar o consumível
        use_button = QPushButton("Usar")
        use_button.clicked.connect(lambda checked, i=item: self.use_consumable(i))
        layout.addWidget(use_button)

        return widget

    def create_locked_item_widget(self, item):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)  # Espaçamento entre widgets
        layout.setContentsMargins(10, 10, 10, 10)  # Margens internas

        # Adicionar imagem ao item bloqueado
        image_label = QLabel()
        image_path = item.get("image_path", "")  # Assegure-se de que 'image_path' está no JSON
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(pixmap)
        else:
            # Usar uma imagem padrão ou deixar vazio
            pixmap = QPixmap(64, 64)
            pixmap.fill(QColor("gray"))
            image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(image_label)

        # Nome do item
        name_label = QLabel(item.get("name", "Item"))
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(name_label)

        # Nível requerido
        required_level = item.get("level", 1)
        level_label = QLabel(f"Nível Requerido: {required_level}")
        level_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(level_label)

        # Descrição do item
        description = item.get("description", "Sem descrição")
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("font-size: 12px;")  # Fonte menor para descrições
        layout.addWidget(desc_label)

        return widget

    def buy_item(self, item):
        price = item.get("price", 0)
        if self.pet_game.coins >= price:
            item_type = item.get("type")
            item_id = item.get("id")

            # Desconta as moedas
            self.pet_game.coins -= price

            # Atualiza o estado do pet_game de acordo com o tipo do item
            if item_type == "hat":
                if item_id not in self.pet_game.unlocked_hats:
                    self.pet_game.unlocked_hats.append(item_id)
                self.pet_game.equipped_hat = item_id
            elif item_type == "accessory":
                if item_id not in self.pet_game.unlocked_accessories:
                    self.pet_game.unlocked_accessories.append(item_id)
                self.add_accessory(item)  # Usar a função auxiliar
            elif item_type == "body_color":
                color = item.get("color")
                if color and color not in self.pet_game.unlocked_colors:
                    self.pet_game.unlocked_colors.append(color)
                self.pet_game.body_color = color
            elif item_type == "body_shape":
                shape = item.get("shape")
                if shape and shape not in self.pet_game.unlocked_bodies:
                    self.pet_game.unlocked_bodies.append(shape)
                self.pet_game.body_style = shape
            elif item_type == "consumable":
                # Não é tratado aqui
                pass
            else:
                QMessageBox.warning(self, "Tipo de Item Desconhecido", f"O tipo de item '{item_type}' não é reconhecido.")
                return

            QMessageBox.information(self, "Compra Realizada", f"Você comprou '{item.get('name')}' com sucesso!")
            self.pet_game.save_pet_status()

            # Atualiza a loja
            self.refresh_shop()
        else:
            QMessageBox.warning(self, "Moedas Insuficientes", "Você não tem moedas suficientes para comprar este item.")

    def buy_consumable(self, item):
        price = item.get("price", 0)
        if self.pet_game.coins >= price:
            item_id = item.get("id")
            # Desconta as moedas
            self.pet_game.coins -= price
            # Incrementa a quantidade do consumível adquirido
            if item_id in self.pet_game.unlocked_consumables:
                self.pet_game.unlocked_consumables[item_id] += 1
            else:
                self.pet_game.unlocked_consumables[item_id] = 1
            #QMessageBox.information(self, "Compra Realizada", f"Você comprou '{item.get('name')}' com sucesso!")
            self.pet_game.save_pet_status()
            self.refresh_shop()
        else:
            QMessageBox.warning(self, "Moedas Insuficientes", "Você não tem moedas suficientes para comprar este consumível.")

    def equip_item(self, item):
        item_type = item.get("type")
        item_id = item.get("id")

        if item_type == "hat":
            if self.pet_game.equipped_hat == item_id:
                QMessageBox.information(self, "Já Equipado", f"O chapéu '{item.get('name')}' já está equipado.")
                return
            self.pet_game.equipped_hat = item_id
            QMessageBox.information(self, "Equipado", f"Você equipou o chapéu '{item.get('name')}'!")
        elif item_type == "accessory":
            accessory_shape = item.get("shape")
            if not accessory_shape:
                QMessageBox.warning(self, "Formato do Acessório Desconhecido", "O acessório não possui um formato definido.")
                return

            # Remover acessórios do mesmo tipo (shape) antes de equipar o novo
            accessories_to_remove = []
            for equipped_id in self.pet_game.equipped_accessories:
                equipped_item = next((i for i in self.items if i["id"] == equipped_id), None)
                if equipped_item and equipped_item.get("shape") == accessory_shape:
                    accessories_to_remove.append(equipped_id)

            for equipped_id in accessories_to_remove:
                self.pet_game.equipped_accessories.remove(equipped_id)
                equipped_item = next((i for i in self.items if i["id"] == equipped_id), None)
                if equipped_item:
                    QMessageBox.information(self, "Desquipado", f"Você desquipou o acessório '{equipped_item.get('name')}'.")

            # Adicionar o novo acessório
            if item_id not in self.pet_game.equipped_accessories:
                self.pet_game.equipped_accessories.append(item_id)
                QMessageBox.information(self, "Equipado", f"Você equipou o acessório '{item.get('name')}'!")
        elif item_type == "glove":
            glove_shape = item.get("shape")
            
            # Remover luvas equipadas
            if glove_shape == "glove":
                # Verificar se já há uma luva equipada e removê-la
                for equipped_id in self.pet_game.equipped_accessories:
                    equipped_item = next((i for i in self.items if i["id"] == equipped_id), None)
                    if equipped_item and equipped_item.get("shape") == "glove":
                        self.pet_game.equipped_accessories.remove(equipped_id)
                        equipped_item_name = equipped_item.get("name")
                        QMessageBox.information(self, "Desquipado", f"Você desquipou a luva '{equipped_item_name}'.")

                # Equipar a nova luva
                self.pet_game.equipped_accessories.append(item_id)
                QMessageBox.information(self, "Equipado", f"Você equipou a luva '{item.get('name')}'!")
        elif item_type == "body_color":
            if self.pet_game.body_color == item.get("color"):
                QMessageBox.information(self, "Já Equipado", f"A cor '{item.get('name')}' já está equipada.")
                return
            self.pet_game.body_color = item.get("color")
            QMessageBox.information(self, "Equipado", f"Você equipou a cor '{item.get('name')}'!")
        elif item_type == "body_shape":
            if self.pet_game.body_style == item.get("shape"):
                QMessageBox.information(self, "Já Equipado", f"O shape '{item.get('name')}' já está equipado.")
                return
            self.pet_game.body_style = item.get("shape")
            QMessageBox.information(self, "Equipado", f"Você equipou o shape '{item.get('name')}'!")
        else:
            QMessageBox.warning(self, "Tipo de Item Desconhecido", f"O tipo de item '{item_type}' não é reconhecido.")
            return

        self.pet_game.save_pet_status()
        self.refresh_shop()

        

    def use_consumable(self, item):
        consumable_type = item.get("consumable_type")
        effect = item.get("effect", {})

        # Aplica o efeito baseado no tipo de consumível
        if consumable_type == "happiness_boost":
            boost_amount = effect.get("amount", 0)
            self.pet_game.happiness = min(100, self.pet_game.happiness + boost_amount)
        elif consumable_type == "energy_boost":
            boost_amount = effect.get("amount", 0)
            self.pet_game.energy = min(100, self.pet_game.energy + boost_amount)
        elif consumable_type == "food":
            hunger_restore = effect.get("hunger_restore", 0)
            self.pet_game.hunger = min(100, self.pet_game.hunger + hunger_restore)
        elif consumable_type == "exp_boost":
            duration = effect.get("duration", 0)  # duração em segundos
            self.pet_game.exp_boost_active = True
            QTimer.singleShot(duration * 1000, self.deactivate_exp_boost)
        else:
            QMessageBox.warning(self, "Consumível Desconhecido", f"O consumível '{item.get('name')}' possui um tipo desconhecido.")
            return

        # Remover o consumível após o uso (se consumível único)
        if item.get("consumable_usage", "single") == "single":
            try:
                self.pet_game.unlocked_consumables[item.get("id")] -= 1
                if self.pet_game.unlocked_consumables[item.get("id")] <= 0:
                    del self.pet_game.unlocked_consumables[item.get("id")]
            except KeyError:
                QMessageBox.warning(self, "Erro", f"O consumível '{item.get('name')}' não está no seu inventário.")
                return

        # Atualizar os status na aba de consumíveis comprados
        self.pet_game.update_status_bars()

        self.pet_game.save_pet_status()
        self.refresh_purchased_consumables()

    def deactivate_exp_boost(self):
        self.pet_game.exp_boost_active = False

    def refresh_shop(self):
        # Atualizar o label de moedas
        self.coins_label.setText(f"Moedas: {self.pet_game.coins}")

        # Limpar todas as abas
        self.clear_layout(self.available_grid)
        self.clear_layout(self.purchased_grid)
        self.clear_layout(self.consumables_grid)
        self.clear_layout(self.locked_grid)

        # Repopular as abas
        self.populate_available_items()
        self.populate_purchased_items()
        self.populate_consumables()
        self.populate_locked_items()

        # Atualizar consumíveis comprados
        self.refresh_purchased_consumables()

    def refresh_purchased_consumables(self):
        # Limpar a lista atual
        self.consumables_list_widget.clear()

        # Adicionar consumíveis comprados
        for item_id, quantity in self.pet_game.unlocked_consumables.items():
            item = next((i for i in self.items if i["id"] == item_id), None)
            if item and quantity > 0:
                list_item = QListWidgetItem()
                widget = self.create_purchased_consumable_widget(item, quantity)
                list_item.setSizeHint(widget.sizeHint())
                self.consumables_list_widget.addItem(list_item)
                self.consumables_list_widget.setItemWidget(list_item, widget)

        # Atualizar status do pet
        self.status_hunger.setText(f"Fome: {self.pet_game.hunger}")
        self.status_energy.setText(f"Energia: {self.pet_game.energy}")
        self.status_happiness.setText(f"Felicidade: {self.pet_game.happiness}")

    def populate_available_items(self):
        row, col = 0, 0
        max_columns = 3

        for item in self.items:
            if item.get("type") != "consumable":
                if self.pet_game.level >= item.get("level", 1) and not self.is_item_purchased(item):
                    item_widget = self.create_item_widget(item, purchase=True)
                    self.available_grid.addWidget(item_widget, row, col)
                    col += 1
                    if col == max_columns:
                        col = 0
                        row += 1

    def populate_purchased_items(self):
        row, col = 0, 0
        max_columns = 3

        for item in self.items:
            if item.get("type") != "consumable":
                if self.is_item_purchased(item):
                    item_widget = self.create_item_widget(item, purchase=False)
                    self.purchased_grid.addWidget(item_widget, row, col)
                    col += 1
                    if col == max_columns:
                        col = 0
                        row += 1

    def populate_consumables(self):
        row, col = 0, 0
        max_columns = 3

        for item in self.items:
            if item.get("type") == "consumable":
                if self.pet_game.level >= item.get("level", 1):
                    item_widget = self.create_consumable_widget(item)
                    self.consumables_grid.addWidget(item_widget, row, col)
                    col += 1
                    if col == max_columns:
                        col = 0
                        row += 1

    def populate_locked_items(self):
        row, col = 0, 0
        max_columns = 3

        for item in self.items:
            required_level = item.get("level", 1)
            if self.pet_game.level < required_level:
                item_widget = self.create_locked_item_widget(item)
                self.locked_grid.addWidget(item_widget, row, col)
                col += 1
                if col == max_columns:
                    col = 0
                    row += 1

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def add_accessory(self, item):
        """
        Função auxiliar para adicionar um acessório garantindo exclusividade por `shape`.
        """
        accessory_shape = item.get("shape")
        if not accessory_shape:
            QMessageBox.warning(self, "Formato Desconhecido", "O acessório não possui um formato definido.")
            return

        # Remover acessórios do mesmo shape
        original_count = len(self.pet_game.equipped_accessories)
        self.pet_game.equipped_accessories = [
            acc_id for acc_id in self.pet_game.equipped_accessories
            if next((i for i in self.items if i["id"] == acc_id), {}).get("shape") != accessory_shape
        ]

        removed_count = original_count - len(self.pet_game.equipped_accessories)
        if removed_count > 0:
            QMessageBox.information(self, "Desquipado", f"Você desquipou {removed_count} acessório(s) do tipo '{accessory_shape}'.")

        # Adicionar o novo acessório
        if item.get("id") not in self.pet_game.equipped_accessories:
            self.pet_game.equipped_accessories.append(item.get("id"))
            QMessageBox.information(self, "Equipado", f"Você equipou o acessório '{item.get('name')}'!")

        # Salvar e atualizar a loja
        self.pet_game.save_pet_status()
        self.refresh_shop()

        

