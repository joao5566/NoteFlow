# Importações Padrão
import sys
import calendar
import sqlite3
import numpy as np

# Importações de Terceiros
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QListWidget, QPushButton, QComboBox, QMessageBox, QLineEdit, QFileDialog,
    QTabWidget
)
from PyQt5.QtCore import QDate, pyqtSignal, Qt
from PyQt5.QtGui import QTextDocument
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt


# Constantes
DB_PATH = "data.db"

# --------------------------------------------------
# Definição da Classe StatsWidget
# --------------------------------------------------

class StatsWidget(QWidget):
    """Widget para exibir estatísticas com gráficos interativos."""

    # Sinal para notificação de deleção de nota
    note_deleted = pyqtSignal(str)

    # Constante para paginação (não utilizada atualmente, mas mantida para futuras implementações)
    NOTES_PER_PAGE = 10

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Estatísticas")
        self.layout = QVBoxLayout(self)

        # Configuração das abas
        self.tabs = QTabWidget(self)
        self.layout.addWidget(self.tabs)

        # Inicializa as abas
        self.init_graph_tab()
        self.init_task_tab()

        # Atualiza anos nas listas de filtros
        self.update_years()
        self.update_task_years()

    # ------------------------------
    # Métodos de Inicialização das Abas
    # ------------------------------

    def init_graph_tab(self):
        """Inicializa a aba de gráficos."""
        self.graph_tab_layout = QVBoxLayout()

        # Resumo numérico no topo
        self.summary_label = QLabel(self)
        self.graph_tab_layout.addWidget(self.summary_label)

        # Filtros de anos, meses, categorias, tags e semanas
        self.filter_layout = QHBoxLayout()

        # Lista de anos
        self.year_list = QListWidget(self)
        self.year_list.setSelectionMode(QListWidget.MultiSelection)
        self.year_label = QLabel("Anos:")
        self.filter_layout.addWidget(self.year_label)
        self.filter_layout.addWidget(self.year_list)
        self.year_list.itemSelectionChanged.connect(self.update_months)

        # Lista de meses
        self.month_list = QListWidget(self)
        self.month_list.setSelectionMode(QListWidget.MultiSelection)
        self.month_label = QLabel("Meses:")
        self.filter_layout.addWidget(self.month_label)
        self.filter_layout.addWidget(self.month_list)
        self.month_list.itemSelectionChanged.connect(self.update_weeks)

        # Lista de semanas
        self.week_list = QListWidget(self)
        self.week_list.setSelectionMode(QListWidget.MultiSelection)
        self.week_label = QLabel("Semanas:")
        self.filter_layout.addWidget(self.week_label)
        self.filter_layout.addWidget(self.week_list)

        # Campo de categorias
        self.category_input = QLineEdit(self)
        self.category_input.setPlaceholderText("Categorias (separadas por vírgula)")
        self.filter_layout.addWidget(QLabel("Categorias:"))
        self.filter_layout.addWidget(self.category_input)

        # Campo de tags
        self.tag_input = QLineEdit(self)
        self.tag_input.setPlaceholderText("Tags (separadas por vírgula)")
        self.filter_layout.addWidget(QLabel("Tags:"))
        self.filter_layout.addWidget(self.tag_input)

        # Botões de ação
        self.update_button = QPushButton("Atualizar Estatísticas", self)
        self.update_button.clicked.connect(self.update_all)
        self.filter_layout.addWidget(self.update_button)

        self.export_button = QPushButton("Exportar Gráfico", self)
        self.export_button.clicked.connect(self.export_chart)
        self.export_button.setEnabled(False)  # Desativado inicialmente
        self.filter_layout.addWidget(self.export_button)

        # Botões de seleção rápida
        self.select_all_button = QPushButton("Selecionar Todo o Ano", self)
        self.select_all_button.clicked.connect(self.select_all_years)
        self.filter_layout.addWidget(self.select_all_button)

        self.clear_selection_button = QPushButton("Limpar Seleção", self)
        self.clear_selection_button.clicked.connect(self.clear_selection)
        self.filter_layout.addWidget(self.clear_selection_button)

        self.graph_tab_layout.addLayout(self.filter_layout)

        # Seleção de tipo de gráfico
        self.graph_type_combo = QComboBox(self)
        self.graph_type_combo.addItems([
            "Procrastinação (Dias Estudados vs Não Estudados)",
            "Heatmap por Ano",
            "Heatmap de Vários anos",
            "Notas ao Longo do Tempo",
            "Notas por Categoria",
            "Notas por Tags",
            "Progresso (Feito vs Pendentes)",
            "Gráfico Comparativo",
            # Novas opções adicionadas abaixo
            "Comparativo de Notas por Dias da Semana - Barras",
            "Comparativo de Notas por Dias da Semana - Linhas",
            "Comparativo de Notas por Dias da Semana - Pizza"
        ])
        self.graph_type_combo.currentIndexChanged.connect(self.handle_graph_type_change)
        self.graph_tab_layout.addWidget(QLabel("Tipo de Gráfico:"))
        self.graph_tab_layout.addWidget(self.graph_type_combo)

        # Campo de entrada para ano (aparece somente para alguns gráficos)
        self.year_input = QLineEdit(self)
        self.year_input.setPlaceholderText("Digite o ano (ex: 2025)")
        self.year_input.setVisible(False)
        self.graph_tab_layout.addWidget(self.year_input)

        # Feedback para o usuário
        self.year_feedback = QLabel("Digite o ano e clique em 'Atualizar Estatísticas' para gerar o gráfico.", self)
        self.year_feedback.setStyleSheet("color: blue; font-size: 15px; font-weight: bold;")
        self.year_feedback.setVisible(False)
        self.graph_tab_layout.addWidget(self.year_feedback)

        # Área para exibir gráficos
        self.figure = plt.figure(figsize=(12, 6))
        self.canvas = FigureCanvas(self.figure)
        self.graph_tab_layout.addWidget(self.canvas)

        # Adiciona a aba de gráficos ao QTabWidget
        graph_widget = QWidget(self)
        graph_widget.setLayout(self.graph_tab_layout)
        self.tabs.addTab(graph_widget, "Gráficos")

    def init_task_tab(self):
        """Inicializa a aba de estatísticas de tarefas."""
        self.task_tab_layout = QVBoxLayout()

        # Resumo numérico
        self.task_summary_label = QLabel(self)
        self.task_tab_layout.addWidget(self.task_summary_label)

        # Filtros de meses e anos para tarefas
        self.task_filter_layout = QHBoxLayout()

        # Lista de meses para tarefas
        self.task_month_list = QListWidget(self)
        self.task_month_list.setSelectionMode(QListWidget.MultiSelection)
        for i in range(1, 13):
            self.task_month_list.addItem(f"{i:02d}")
        self.task_filter_layout.addWidget(QLabel("Meses:"))
        self.task_filter_layout.addWidget(self.task_month_list)

        # Lista de anos para tarefas
        self.task_year_list = QListWidget(self)
        self.task_year_list.setSelectionMode(QListWidget.MultiSelection)
        self.task_filter_layout.addWidget(QLabel("Anos:"))
        self.task_filter_layout.addWidget(self.task_year_list)

        self.task_tab_layout.addLayout(self.task_filter_layout)

        # Botão para atualizar estatísticas de tarefas
        self.update_task_button = QPushButton("Atualizar Estatísticas de Tarefas", self)
        self.update_task_button.clicked.connect(self.update_task_stats)
        self.task_tab_layout.addWidget(self.update_task_button)

        # Área para exibir gráficos de tarefas
        self.task_figure = plt.figure(figsize=(12, 6))
        self.task_canvas = FigureCanvas(self.task_figure)
        self.task_tab_layout.addWidget(self.task_canvas)

        # Adiciona a aba de tarefas ao QTabWidget
        task_widget = QWidget(self)
        task_widget.setLayout(self.task_tab_layout)
        self.tabs.addTab(task_widget, "Estatísticas de Tarefas")

    # ------------------------------
    # Métodos de Atualização de Filtros
    # ------------------------------

    def update_years(self):
        """Atualiza a lista de anos com base nas notas existentes no banco de dados."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT strftime('%Y', date) AS year FROM notes ORDER BY year")
            years = [row[0] for row in cursor.fetchall()]
            self.year_list.clear()
            for year in years:
                self.year_list.addItem(year)

    def update_task_years(self):
        """Atualiza a lista de anos com base nas tarefas existentes no banco de dados."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT strftime('%Y', creation_date) AS year FROM tasks ORDER BY year")
            years = [row[0] for row in cursor.fetchall()]
            self.task_year_list.clear()
            for year in years:
                self.task_year_list.addItem(year)

    # ------------------------------
    # Métodos de Atualização Dinâmica de Meses e Semanas
    # ------------------------------

    def update_months(self):
        """Atualiza a lista de meses com base nos anos selecionados."""
        selected_years = [item.text() for item in self.year_list.selectedItems()]
        if not selected_years:
            # Se nenhum ano estiver selecionado, desabilita os meses e semanas
            self.month_list.clear()
            self.week_list.clear()
            self.month_list.setEnabled(False)
            self.week_list.setEnabled(False)
            return

        # Consulta os meses disponíveis nos anos selecionados
        placeholders = ", ".join(["?"] * len(selected_years))
        query = f"SELECT DISTINCT strftime('%m', date) FROM notes WHERE strftime('%Y', date) IN ({placeholders}) ORDER BY strftime('%m', date)"
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(query, selected_years)
            months = [row[0] for row in cursor.fetchall()]

        # Atualiza a lista de meses
        self.month_list.clear()
        for month in sorted(months):
            self.month_list.addItem(f"{int(month):02d}")  # Exibir como '01', '02', etc.
        self.month_list.setEnabled(True)

        # Limpa e desabilita a lista de semanas até que os meses sejam selecionados
        self.week_list.clear()
        self.week_list.setEnabled(False)

    def update_weeks(self):
        """Atualiza a lista de semanas com base nos meses selecionados."""
        selected_years = [item.text() for item in self.year_list.selectedItems()]
        selected_months = [item.text() for item in self.month_list.selectedItems()]
        if not selected_years or not selected_months:
            # Se não houver seleção de anos ou meses, desabilita as semanas
            self.week_list.clear()
            self.week_list.setEnabled(False)
            return

        # Para simplificar, consideraremos até 5 semanas por mês
        self.week_list.clear()
        for week in range(1, 6):
            self.week_list.addItem(str(week))
        self.week_list.setEnabled(True)

    # ------------------------------
    # Métodos de Filtragem e Atualização
    # ------------------------------

    def update_all(self):
        """Atualiza a filtragem, a tabela e o gráfico."""
        self.filter_notes()
        self.plot_dynamic_chart()

    def filter_notes(self):
        """Filtra as notas com base nos filtros selecionados."""
        selected_years = [item.text() for item in self.year_list.selectedItems()]
        selected_months = [item.text() for item in self.month_list.selectedItems()]
        selected_weeks = [int(item.text()) for item in self.week_list.selectedItems()]
        categories = [cat.strip() for cat in self.category_input.text().split(",") if cat.strip()]
        tags = [tag.strip() for tag in self.tag_input.text().split(",") if tag.strip()]

        query = "SELECT date, text, categories, tags FROM notes"
        conditions = []
        params = []

        # Filtrar por ano(s)
        if selected_years:
            placeholders = ", ".join(["?"] * len(selected_years))
            conditions.append(f"strftime('%Y', date) IN ({placeholders})")
            params.extend(selected_years)

        # Filtrar por mês(es)
        if selected_months:
            placeholders = ", ".join(["?"] * len(selected_months))
            conditions.append(f"strftime('%m', date) IN ({placeholders})")
            params.extend(selected_months)

        # Filtrar por semana(s) do mês
        if selected_weeks:
            # Calcular a semana do mês: ((dia - 1) / 7) + 1
            week_conditions = []
            for week in selected_weeks:
                week_conditions.append(f"((CAST(strftime('%d', date) AS INTEGER) - 1) / 7 + 1) = {week}")
            conditions.append("(" + " OR ".join(week_conditions) + ")")

        # Filtrar por categorias
        if categories:
            category_conditions = " OR ".join(["categories LIKE ?"] * len(categories))
            conditions.append(f"({category_conditions})")
            params.extend([f"%{cat}%" for cat in categories])

        # Filtrar por tags
        if tags:
            tag_conditions = " OR ".join(["tags LIKE ?"] * len(tags))
            conditions.append(f"({tag_conditions})")
            params.extend([f"%{tag}%" for tag in tags])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            self.filtered_notes = cursor.fetchall()

        self.update_summary()

    def update_summary(self):
        """Atualiza o resumo numérico no topo."""
        total_notes = len(self.filtered_notes)
        total_categories = len(set(cat for _, _, cats, _ in self.filtered_notes for cat in cats.split(",") if cats))
        total_tags = len(set(tag for _, _, _, tags in self.filtered_notes for tag in tags.split(",") if tags))
        total_done = sum(1 for _, _, _, tags in self.filtered_notes if "feito" in tags.split(","))

        self.summary_label.setText(
            f"Total de Notas: {total_notes} | Categorias Únicas: {total_categories} | "
            f"Tags Únicas: {total_tags} | Feito: {total_done}"
        )

    # ------------------------------
    # Métodos de Plotagem de Gráficos
    # ------------------------------

    def handle_graph_type_change(self):
        """Lida com a mudança no tipo de gráfico selecionado."""
        chart_type = self.graph_type_combo.currentText()

        # Mostrar ou esconder campos com base no tipo de gráfico
        if chart_type == "Heatmap por Ano":
            self.year_input.setVisible(True)
            self.year_feedback.setVisible(True)
        else:
            self.year_input.setVisible(False)
            self.year_feedback.setVisible(False)

    def plot_dynamic_chart(self):
        """Desenha o gráfico com base no tipo selecionado."""
        if not self.filtered_notes:
            QMessageBox.information(self, "Sem dados", "Não há notas suficientes para exibir o gráfico.")
            self.export_button.setEnabled(False)
            self.figure.clear()
            self.canvas.draw()
            return

        chart_type = self.graph_type_combo.currentText()

        self.export_button.setEnabled(True)  # Habilita o botão de exportação somente se houver dados

        # Definir visibilidade do campo de ano e feedback
        if chart_type == "Heatmap por Ano":
            self.year_input.setVisible(True)
            self.year_feedback.setVisible(True)
        else:
            self.year_input.setVisible(False)
            self.year_feedback.setVisible(False)

        # Limpa a figura atual
        self.figure.clear()

        # Seleciona o método de plotagem com base no tipo de gráfico
        plot_methods = {
            "Heatmap por Ano": self.plot_heatmap_for_year,
            "Heatmap de Vários anos": self.plot_heatmap,
            "Notas ao Longo do Tempo": self.plot_notes_over_time,
            "Notas por Categoria": self.plot_notes_by_category,
            "Notas por Tags": self.plot_notes_by_tags,
            "Progresso (Feito vs Pendentes)": self.plot_progress_chart,
            "Procrastinação (Dias Estudados vs Não Estudados)": self.plot_procrastination_chart,
            "Gráfico Comparativo": self.plot_comparative_chart,
            # Novos métodos adicionados abaixo
            "Comparativo de Notas por Dias da Semana - Barras": self.plot_weekday_bar_chart,
            "Comparativo de Notas por Dias da Semana - Linhas": self.plot_weekday_line_chart,
            "Comparativo de Notas por Dias da Semana - Pizza": self.plot_weekday_pie_chart
        }

        plot_method = plot_methods.get(chart_type, None)
        if plot_method:
            if chart_type == "Heatmap por Ano":
                year_text = self.year_input.text().strip()
                if not year_text:
                    QMessageBox.warning(self, "Entrada Inválida", "Por favor, digite um ano antes de atualizar.")
                    return
                elif year_text.isdigit():
                    year = int(year_text)
                    plot_method(year)
                else:
                    QMessageBox.warning(self, "Entrada Inválida", "Por favor, digite um ano válido.")
                    return
            else:
                plot_method()

        # Atualiza o canvas
        self.canvas.draw()

    # ------------------------------
    # Métodos de Plotagem dos Novos Gráficos
    # ------------------------------

    def plot_weekday_bar_chart(self):
        """Plota um gráfico de barras mostrando o número de notas por dia da semana."""
        # Contar notas por dia da semana
        weekday_counts = {day:0 for day in calendar.day_name}  # Monday, Tuesday, etc.

        for date_str, _, _, _ in self.filtered_notes:
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            weekday = calendar.day_name[date.dayOfWeek() - 1]  # QDate.dayOfWeek() retorna 1 (Monday) to 7 (Sunday)
            weekday_counts[weekday] += 1

        days = list(weekday_counts.keys())
        counts = list(weekday_counts.values())

        ax = self.figure.add_subplot(111)
        bars = ax.bar(days, counts, color='skyblue')
        ax.set_title("Número de Notas por Dia da Semana")
        ax.set_xlabel("Dias da Semana")
        ax.set_ylabel("Quantidade de Notas")
        ax.set_ylim(0, max(counts) + 5)

        # Adicionar rótulos acima das barras
        for bar in bars:
            height = bar.get_height()
            ax.annotate('{}'.format(height),
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 pontos verticalmente
                        textcoords="offset points",
                        ha='center', va='bottom')

    def plot_weekday_line_chart(self):
        """Plota um gráfico de linhas mostrando a tendência de notas por dia da semana ao longo das semanas."""
        # Agrupar notas por semana e dia da semana
        from collections import defaultdict

        # Estrutura: {week_number: {day_name: count}}
        week_day_counts = defaultdict(lambda: defaultdict(int))

        for date_str, _, _, _ in self.filtered_notes:
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            week_number = date.weekNumber()[0]  # (week_number, is_last_week)
            weekday = calendar.day_name[date.dayOfWeek() - 1]
            week_day_counts[week_number][weekday] += 1

        if not week_day_counts:
            QMessageBox.warning(self, "Sem dados", "Não há notas para exibir no gráfico de linhas.")
            return

        weeks = sorted(week_day_counts.keys())
        days = list(calendar.day_name)

        # Preparar dados para cada dia
        day_trends = {day: [] for day in days}
        for week in weeks:
            for day in days:
                day_trends[day].append(week_day_counts[week].get(day, 0))

        # Plotar as linhas
        ax = self.figure.add_subplot(111)
        for day, counts in day_trends.items():
            ax.plot(weeks, counts, marker='o', label=day)

        ax.set_title("Tendência de Notas por Dia da Semana ao Longo das Semanas")
        ax.set_xlabel("Número da Semana")
        ax.set_ylabel("Quantidade de Notas")
        ax.legend(title="Dias da Semana")
        ax.grid(True)

    def plot_weekday_pie_chart(self):
        """Plota um gráfico de pizza mostrando a proporção de notas por dia da semana."""
        # Contar notas por dia da semana
        weekday_counts = {day:0 for day in calendar.day_name}  # Monday, Tuesday, etc.

        for date_str, _, _, _ in self.filtered_notes:
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            weekday = calendar.day_name[date.dayOfWeek() - 1]
            weekday_counts[weekday] += 1

        labels = list(weekday_counts.keys())
        sizes = list(weekday_counts.values())

        if sum(sizes) == 0:
            QMessageBox.warning(self, "Sem dados", "Não há notas para exibir no gráfico de pizza.")
            return

        ax = self.figure.add_subplot(111)
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired.colors)
        ax.set_title("Proporção de Notas por Dia da Semana")
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    def plot_heatmap_for_year(self, year):
        """Plota um heatmap de notas para um único ano, com cada linha representando um mês."""
        # Coletar as datas das notas filtradas
        dates = [
            QDate.fromString(date, "yyyy-MM-dd") for date, _, _, _ in self.filtered_notes
            if QDate.fromString(date, "yyyy-MM-dd").year() == year
        ]

        if not dates:
            QMessageBox.warning(self, "Sem dados", f"Não há notas para exibir no ano {year}.")
            return

        # Criar uma matriz 12x31 (12 meses, até 31 dias por mês)
        heatmap_data = np.zeros((12, 31), dtype=int)

        for date in dates:
            month_index = date.month() - 1
            day_index = date.day() - 1
            heatmap_data[month_index, day_index] += 1  # Incrementa a contagem de notas no dia correspondente

        # Plotar o heatmap
        ax = self.figure.add_subplot(111)
        cax = ax.imshow(heatmap_data, cmap='YlGn', aspect='auto', vmin=0, vmax=heatmap_data.max())

        # Configurar rótulos dos eixos
        ax.set_xticks(np.arange(31))
        ax.set_xticklabels([str(i + 1) for i in range(31)])
        ax.set_yticks(np.arange(12))
        ax.set_yticklabels([calendar.month_name[i + 1] for i in range(12)])
        ax.set_title(f"Heatmap de Notas - {year}")
        ax.set_xlabel("Dias do Mês")
        ax.set_ylabel("Meses")

        # Adicionar a barra de cores
        self.figure.colorbar(cax, orientation='vertical', ticks=range(0, heatmap_data.max()+1), label='Quantidade de Notas')

    def plot_heatmap(self):
        """Plota um heatmap com a contagem de notas por mês ao longo de vários anos."""
        # Coletar as datas filtradas
        dates = [QDate.fromString(date, "yyyy-MM-dd") for date, _, _, _ in self.filtered_notes]
        if not dates:
            QMessageBox.warning(self, "Sem dados", "Não há notas para exibir no período selecionado.")
            return

        # Coletar os anos únicos presentes nas datas
        selected_years = sorted(set(date.year() for date in dates))
        months = list(range(1, 13))  # Meses de 1 a 12

        # Criar uma matriz de contagem de notas (linhas: anos, colunas: meses)
        heatmap_data = np.zeros((len(selected_years), len(months)), dtype=int)

        for date in dates:
            year_index = selected_years.index(date.year())
            month_index = date.month() - 1
            heatmap_data[year_index, month_index] += 1  # Incrementa a contagem de notas no mês correspondente

        # Plotar o heatmap
        ax = self.figure.add_subplot(111)
        cax = ax.imshow(heatmap_data, cmap='YlGn', aspect='auto')

        # Configurar rótulos dos eixos
        ax.set_xticks(np.arange(len(months)))
        ax.set_xticklabels([calendar.month_abbr[m] for m in months])  # Abreviações dos meses
        ax.set_yticks(np.arange(len(selected_years)))
        ax.set_yticklabels([str(year) for year in selected_years])
        ax.set_title("Heatmap de Notas por Mês e Ano")
        ax.set_xlabel("Meses")
        ax.set_ylabel("Anos")

        # Adicionar a barra de cores
        self.figure.colorbar(cax, orientation='vertical', label='Quantidade de Notas')

    def plot_notes_over_time(self):
        """Plota um gráfico de linha: Notas ao longo do tempo."""
        dates = sorted([QDate.fromString(date, "yyyy-MM-dd") for date, _, _, _ in self.filtered_notes])
        counts = list(range(1, len(dates) + 1))

        date_strings = [date.toString("yyyy-MM-dd") for date in dates]

        ax = self.figure.add_subplot(111)
        ax.plot(date_strings, counts, marker='o', linestyle='-', color='purple')
        ax.set_title("Notas ao Longo do Tempo")
        ax.set_xlabel("Data")
        ax.set_ylabel("Quantidade de Notas")
        ax.tick_params(axis='x', rotation=45)

    def plot_notes_by_category(self):
        """Plota um gráfico de barras horizontal: Notas por categoria."""
        categories = {}
        for _, _, cats, _ in self.filtered_notes:
            for category in cats.split(","):
                if category.strip():
                    categories[category.strip()] = categories.get(category.strip(), 0) + 1

        if not categories:
            QMessageBox.information(self, "Sem dados", "Não há categorias para exibir.")
            return

        ax = self.figure.add_subplot(111)
        ax.barh(list(categories.keys()), list(categories.values()), color='skyblue')
        ax.set_title("Notas por Categoria")
        ax.set_xlabel("Quantidade")
        ax.set_ylabel("Categoria")

    def plot_notes_by_tags(self):
        """Plota um gráfico de barras horizontal: Notas por tags."""
        tags = {}
        for _, _, _, tags_str in self.filtered_notes:
            for tag in tags_str.split(","):
                if tag.strip():
                    tags[tag.strip()] = tags.get(tag.strip(), 0) + 1

        if not tags:
            QMessageBox.information(self, "Sem dados", "Não há tags para exibir.")
            return

        ax = self.figure.add_subplot(111)
        ax.barh(list(tags.keys()), list(tags.values()), color='lightgreen')
        ax.set_title("Notas por Tags")
        ax.set_xlabel("Quantidade")
        ax.set_ylabel("Tags")

    def plot_progress_chart(self):
        """Plota um gráfico de pizza: Progresso (feito vs pendentes)."""
        total_done = sum(1 for _, _, _, tags in self.filtered_notes if "feito" in tags.split(","))
        total_pending = len(self.filtered_notes) - total_done

        if total_done == 0 and total_pending == 0:
            QMessageBox.information(self, "Sem dados", "Não há progresso para exibir.")
            return

        ax = self.figure.add_subplot(111)
        ax.pie([total_done, total_pending], labels=["Feito", "Pendente"], autopct="%1.1f%%",
               colors=["#66b3ff", "#ff9999"])
        ax.set_title("Progresso (Feito vs Pendentes)")

    def plot_procrastination_chart(self):
        """Plota um gráfico de pizza: Procrastinação (dias estudados vs não estudados)."""
        dates = [QDate.fromString(date, "yyyy-MM-dd") for date, _, _, _ in self.filtered_notes]
        studied_days = set((date.year(), date.month(), date.day()) for date in dates)
        if not dates:
            QMessageBox.information(self, "Sem dados", "Não há dias estudados para exibir.")
            return

        current_date = QDate.currentDate()
        # Considerando o mês atual para cálculo de dias
        total_days = current_date.daysInMonth()
        procrastinated_days = total_days - len({day for (_, _, day) in studied_days if day <= total_days})

        if procrastinated_days < 0:
            procrastinated_days = 0

        ax = self.figure.add_subplot(111)
        ax.pie([len(studied_days), procrastinated_days], labels=["Estudados", "Não Estudados"],
               autopct="%1.1f%%", colors=["#66b3ff", "#ff9999"])
        ax.set_title("Procrastinação (Dias Estudados vs Não Estudados)")

    def plot_comparative_chart(self):
        """Plota um gráfico comparativo de categorias e tags."""
        categories = {}
        tags = {}

        for _, _, cats, tags_str in self.filtered_notes:
            for category in cats.split(","):
                if category.strip():
                    categories[category.strip()] = categories.get(category.strip(), 0) + 1
            for tag in tags_str.split(","):
                if tag.strip():
                    tags[tag.strip()] = tags.get(tag.strip(), 0) + 1

        if not categories and not tags:
            QMessageBox.information(self, "Sem dados", "Não há categorias ou tags para exibir.")
            return

        labels = list(categories.keys()) + list(tags.keys())
        values = list(categories.values()) + list(tags.values())

        ax = self.figure.add_subplot(111)
        ax.bar(labels, values, color=['skyblue'] * len(categories) + ['lightgreen'] * len(tags))
        ax.set_title("Gráfico Comparativo (Categorias vs Tags)")
        ax.set_xlabel("Categorias e Tags")
        ax.set_ylabel("Quantidade")
        ax.tick_params(axis='x', rotation=45)

    # ------------------------------
    # Métodos de Plotagem dos Novos Gráficos por Dia da Semana
    # ------------------------------

    def plot_weekday_bar_chart(self):
        """Plota um gráfico de barras mostrando o número de notas por dia da semana."""
        # Contar notas por dia da semana
        weekday_counts = {day:0 for day in calendar.day_name}  # Monday, Tuesday, etc.

        for date_str, _, _, _ in self.filtered_notes:
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            weekday = calendar.day_name[date.dayOfWeek() - 1]  # QDate.dayOfWeek() retorna 1 (Monday) to 7 (Sunday)
            weekday_counts[weekday] += 1

        days = list(weekday_counts.keys())
        counts = list(weekday_counts.values())

        ax = self.figure.add_subplot(111)
        bars = ax.bar(days, counts, color='skyblue')
        ax.set_title("Número de Notas por Dia da Semana")
        ax.set_xlabel("Dias da Semana")
        ax.set_ylabel("Quantidade de Notas")
        ax.set_ylim(0, max(counts) + 5)

        # Adicionar rótulos acima das barras
        for bar in bars:
            height = bar.get_height()
            ax.annotate('{}'.format(height),
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 pontos verticalmente
                        textcoords="offset points",
                        ha='center', va='bottom')

    def plot_weekday_line_chart(self):
        """Plota um gráfico de linhas mostrando a tendência de notas por dia da semana ao longo das semanas."""
        # Agrupar notas por semana e dia da semana
        from collections import defaultdict

        # Estrutura: {week_number: {day_name: count}}
        week_day_counts = defaultdict(lambda: defaultdict(int))

        for date_str, _, _, _ in self.filtered_notes:
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            week_number = date.weekNumber()[0]  # (week_number, is_last_week)
            weekday = calendar.day_name[date.dayOfWeek() - 1]
            week_day_counts[week_number][weekday] += 1

        if not week_day_counts:
            QMessageBox.warning(self, "Sem dados", "Não há notas para exibir no gráfico de linhas.")
            return

        weeks = sorted(week_day_counts.keys())
        days = list(calendar.day_name)

        # Preparar dados para cada dia
        day_trends = {day: [] for day in days}
        for week in weeks:
            for day in days:
                day_trends[day].append(week_day_counts[week].get(day, 0))

        # Plotar as linhas
        ax = self.figure.add_subplot(111)
        for day, counts in day_trends.items():
            ax.plot(weeks, counts, marker='o', label=day)

        ax.set_title("Tendência de Notas por Dia da Semana ao Longo das Semanas")
        ax.set_xlabel("Número da Semana")
        ax.set_ylabel("Quantidade de Notas")
        ax.legend(title="Dias da Semana")
        ax.grid(True)

    def plot_weekday_pie_chart(self):
        """Plota um gráfico de pizza mostrando a proporção de notas por dia da semana."""
        # Contar notas por dia da semana
        weekday_counts = {day:0 for day in calendar.day_name}  # Monday, Tuesday, etc.

        for date_str, _, _, _ in self.filtered_notes:
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            weekday = calendar.day_name[date.dayOfWeek() - 1]
            weekday_counts[weekday] += 1

        labels = list(weekday_counts.keys())
        sizes = list(weekday_counts.values())

        if sum(sizes) == 0:
            QMessageBox.warning(self, "Sem dados", "Não há notas para exibir no gráfico de pizza.")
            return

        ax = self.figure.add_subplot(111)
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired.colors)
        ax.set_title("Proporção de Notas por Dia da Semana")
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    def plot_heatmap_for_year(self, year):
        """Plota um heatmap de notas para um único ano, com cada linha representando um mês."""
        # Coletar as datas das notas filtradas
        dates = [
            QDate.fromString(date, "yyyy-MM-dd") for date, _, _, _ in self.filtered_notes
            if QDate.fromString(date, "yyyy-MM-dd").year() == year
        ]

        if not dates:
            QMessageBox.warning(self, "Sem dados", f"Não há notas para exibir no ano {year}.")
            return

        # Criar uma matriz 12x31 (12 meses, até 31 dias por mês)
        heatmap_data = np.zeros((12, 31), dtype=int)

        for date in dates:
            month_index = date.month() - 1
            day_index = date.day() - 1
            heatmap_data[month_index, day_index] += 1  # Incrementa a contagem de notas no dia correspondente

        # Plotar o heatmap
        ax = self.figure.add_subplot(111)
        cax = ax.imshow(heatmap_data, cmap='YlGn', aspect='auto', vmin=0, vmax=heatmap_data.max())

        # Configurar rótulos dos eixos
        ax.set_xticks(np.arange(31))
        ax.set_xticklabels([str(i + 1) for i in range(31)])
        ax.set_yticks(np.arange(12))
        ax.set_yticklabels([calendar.month_name[i + 1] for i in range(12)])
        ax.set_title(f"Heatmap de Notas - {year}")
        ax.set_xlabel("Dias do Mês")
        ax.set_ylabel("Meses")

        # Adicionar a barra de cores
        self.figure.colorbar(cax, orientation='vertical', ticks=range(0, heatmap_data.max()+1), label='Quantidade de Notas')

    def plot_heatmap(self):
        """Plota um heatmap com a contagem de notas por mês ao longo de vários anos."""
        # Coletar as datas filtradas
        dates = [QDate.fromString(date, "yyyy-MM-dd") for date, _, _, _ in self.filtered_notes]
        if not dates:
            QMessageBox.warning(self, "Sem dados", "Não há notas para exibir no período selecionado.")
            return

        # Coletar os anos únicos presentes nas datas
        selected_years = sorted(set(date.year() for date in dates))
        months = list(range(1, 13))  # Meses de 1 a 12

        # Criar uma matriz de contagem de notas (linhas: anos, colunas: meses)
        heatmap_data = np.zeros((len(selected_years), len(months)), dtype=int)

        for date in dates:
            year_index = selected_years.index(date.year())
            month_index = date.month() - 1
            heatmap_data[year_index, month_index] += 1  # Incrementa a contagem de notas no mês correspondente

        # Plotar o heatmap
        ax = self.figure.add_subplot(111)
        cax = ax.imshow(heatmap_data, cmap='YlGn', aspect='auto')

        # Configurar rótulos dos eixos
        ax.set_xticks(np.arange(len(months)))
        ax.set_xticklabels([calendar.month_abbr[m] for m in months])  # Abreviações dos meses
        ax.set_yticks(np.arange(len(selected_years)))
        ax.set_yticklabels([str(year) for year in selected_years])
        ax.set_title("Heatmap de Notas por Mês e Ano")
        ax.set_xlabel("Meses")
        ax.set_ylabel("Anos")

        # Adicionar a barra de cores
        self.figure.colorbar(cax, orientation='vertical', label='Quantidade de Notas')

    def plot_notes_over_time(self):
        """Plota um gráfico de linha: Notas ao longo do tempo."""
        dates = sorted([QDate.fromString(date, "yyyy-MM-dd") for date, _, _, _ in self.filtered_notes])
        counts = list(range(1, len(dates) + 1))

        date_strings = [date.toString("yyyy-MM-dd") for date in dates]

        ax = self.figure.add_subplot(111)
        ax.plot(date_strings, counts, marker='o', linestyle='-', color='purple')
        ax.set_title("Notas ao Longo do Tempo")
        ax.set_xlabel("Data")
        ax.set_ylabel("Quantidade de Notas")
        ax.tick_params(axis='x', rotation=45)

    def plot_notes_by_category(self):
        """Plota um gráfico de barras horizontal: Notas por categoria."""
        categories = {}
        for _, _, cats, _ in self.filtered_notes:
            for category in cats.split(","):
                if category.strip():
                    categories[category.strip()] = categories.get(category.strip(), 0) + 1

        if not categories:
            QMessageBox.information(self, "Sem dados", "Não há categorias para exibir.")
            return

        ax = self.figure.add_subplot(111)
        ax.barh(list(categories.keys()), list(categories.values()), color='skyblue')
        ax.set_title("Notas por Categoria")
        ax.set_xlabel("Quantidade")
        ax.set_ylabel("Categoria")

    def plot_notes_by_tags(self):
        """Plota um gráfico de barras horizontal: Notas por tags."""
        tags = {}
        for _, _, _, tags_str in self.filtered_notes:
            for tag in tags_str.split(","):
                if tag.strip():
                    tags[tag.strip()] = tags.get(tag.strip(), 0) + 1

        if not tags:
            QMessageBox.information(self, "Sem dados", "Não há tags para exibir.")
            return

        ax = self.figure.add_subplot(111)
        ax.barh(list(tags.keys()), list(tags.values()), color='lightgreen')
        ax.set_title("Notas por Tags")
        ax.set_xlabel("Quantidade")
        ax.set_ylabel("Tags")

    def plot_progress_chart(self):
        """Plota um gráfico de pizza: Progresso (feito vs pendentes)."""
        total_done = sum(1 for _, _, _, tags in self.filtered_notes if "feito" in tags.split(","))
        total_pending = len(self.filtered_notes) - total_done

        if total_done == 0 and total_pending == 0:
            QMessageBox.information(self, "Sem dados", "Não há progresso para exibir.")
            return

        ax = self.figure.add_subplot(111)
        ax.pie([total_done, total_pending], labels=["Feito", "Pendente"], autopct="%1.1f%%",
               colors=["#66b3ff", "#ff9999"])
        ax.set_title("Progresso (Feito vs Pendentes)")

    def plot_procrastination_chart(self):
        """Plota um gráfico de pizza: Procrastinação (dias estudados vs não estudados)."""
        dates = [QDate.fromString(date, "yyyy-MM-dd") for date, _, _, _ in self.filtered_notes]
        studied_days = set((date.year(), date.month(), date.day()) for date in dates)
        if not dates:
            QMessageBox.information(self, "Sem dados", "Não há dias estudados para exibir.")
            return

        current_date = QDate.currentDate()
        # Considerando o mês atual para cálculo de dias
        total_days = current_date.daysInMonth()
        procrastinated_days = total_days - len({day for (_, _, day) in studied_days if day <= total_days})

        if procrastinated_days < 0:
            procrastinated_days = 0

        ax = self.figure.add_subplot(111)
        ax.pie([len(studied_days), procrastinated_days], labels=["Estudados", "Não Estudados"],
               autopct="%1.1f%%", colors=["#66b3ff", "#ff9999"])
        ax.set_title("Procrastinação (Dias Estudados vs Não Estudados)")

    def plot_comparative_chart(self):
        """Plota um gráfico comparativo de categorias e tags."""
        categories = {}
        tags = {}

        for _, _, cats, tags_str in self.filtered_notes:
            for category in cats.split(","):
                if category.strip():
                    categories[category.strip()] = categories.get(category.strip(), 0) + 1
            for tag in tags_str.split(","):
                if tag.strip():
                    tags[tag.strip()] = tags.get(tag.strip(), 0) + 1

        if not categories and not tags:
            QMessageBox.information(self, "Sem dados", "Não há categorias ou tags para exibir.")
            return

        labels = list(categories.keys()) + list(tags.keys())
        values = list(categories.values()) + list(tags.values())

        ax = self.figure.add_subplot(111)
        ax.bar(labels, values, color=['skyblue'] * len(categories) + ['lightgreen'] * len(tags))
        ax.set_title("Gráfico Comparativo (Categorias vs Tags)")
        ax.set_xlabel("Categorias e Tags")
        ax.set_ylabel("Quantidade")
        ax.tick_params(axis='x', rotation=45)

    # ------------------------------
    # Métodos de Plotagem dos Novos Gráficos por Dia da Semana
    # ------------------------------

    def plot_weekday_bar_chart(self):
        """Plota um gráfico de barras mostrando o número de notas por dia da semana."""
        # Contar notas por dia da semana
        weekday_counts = {day:0 for day in calendar.day_name}  # Monday, Tuesday, etc.

        for date_str, _, _, _ in self.filtered_notes:
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            weekday = calendar.day_name[date.dayOfWeek() - 1]  # QDate.dayOfWeek() retorna 1 (Monday) to 7 (Sunday)
            weekday_counts[weekday] += 1

        days = list(weekday_counts.keys())
        counts = list(weekday_counts.values())

        ax = self.figure.add_subplot(111)
        bars = ax.bar(days, counts, color='skyblue')
        ax.set_title("Número de Notas por Dia da Semana")
        ax.set_xlabel("Dias da Semana")
        ax.set_ylabel("Quantidade de Notas")
        ax.set_ylim(0, max(counts) + 5)

        # Adicionar rótulos acima das barras
        for bar in bars:
            height = bar.get_height()
            ax.annotate('{}'.format(height),
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 pontos verticalmente
                        textcoords="offset points",
                        ha='center', va='bottom')

    def plot_weekday_line_chart(self):
        """Plota um gráfico de linhas mostrando a tendência de notas por dia da semana ao longo das semanas."""
        # Agrupar notas por semana e dia da semana
        from collections import defaultdict

        # Estrutura: {week_number: {day_name: count}}
        week_day_counts = defaultdict(lambda: defaultdict(int))

        for date_str, _, _, _ in self.filtered_notes:
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            week_number = date.weekNumber()[0]  # (week_number, is_last_week)
            weekday = calendar.day_name[date.dayOfWeek() - 1]
            week_day_counts[week_number][weekday] += 1

        if not week_day_counts:
            QMessageBox.warning(self, "Sem dados", "Não há notas para exibir no gráfico de linhas.")
            return

        weeks = sorted(week_day_counts.keys())
        days = list(calendar.day_name)

        # Preparar dados para cada dia
        day_trends = {day: [] for day in days}
        for week in weeks:
            for day in days:
                day_trends[day].append(week_day_counts[week].get(day, 0))

        # Plotar as linhas
        ax = self.figure.add_subplot(111)
        for day, counts in day_trends.items():
            ax.plot(weeks, counts, marker='o', label=day)

        ax.set_title("Tendência de Notas por Dia da Semana ao Longo das Semanas")
        ax.set_xlabel("Número da Semana")
        ax.set_ylabel("Quantidade de Notas")
        ax.legend(title="Dias da Semana")
        ax.grid(True)

    def plot_weekday_pie_chart(self):
        """Plota um gráfico de pizza mostrando a proporção de notas por dia da semana."""
        # Contar notas por dia da semana
        weekday_counts = {day:0 for day in calendar.day_name}  # Monday, Tuesday, etc.

        for date_str, _, _, _ in self.filtered_notes:
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            weekday = calendar.day_name[date.dayOfWeek() - 1]
            weekday_counts[weekday] += 1

        labels = list(weekday_counts.keys())
        sizes = list(weekday_counts.values())

        if sum(sizes) == 0:
            QMessageBox.warning(self, "Sem dados", "Não há notas para exibir no gráfico de pizza.")
            return

        ax = self.figure.add_subplot(111)
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired.colors)
        ax.set_title("Proporção de Notas por Dia da Semana")
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    # ------------------------------
    # Métodos de Seleção e Limpeza
    # ------------------------------

    def select_all_years(self):
        """Seleciona todos os anos na lista de filtros."""
        for i in range(self.year_list.count()):
            self.year_list.item(i).setSelected(True)

    def clear_selection(self):
        """Limpa a seleção de anos, meses e semanas nas listas de filtros."""
        self.year_list.clearSelection()
        self.month_list.clear()
        self.week_list.clear()
        self.month_list.setEnabled(False)
        self.week_list.setEnabled(False)

    # ------------------------------
    # Métodos de Exportação
    # ------------------------------

    def export_chart(self):
        """Exporta o gráfico atual como imagem PNG."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Gráfico como PNG", "grafico.png", "Imagens PNG (*.png)"
        )
        if path:
            self.figure.savefig(path)
            QMessageBox.information(self, "Exportação Concluída", f"Gráfico exportado como '{path}'")

    # ------------------------------
    # Métodos de Interação com Tarefas
    # ------------------------------

    def update_task_stats(self):
        """Atualiza as estatísticas de tarefas com base nos filtros selecionados."""
        selected_months = [item.text() for item in self.task_month_list.selectedItems()]
        selected_years = [item.text() for item in self.task_year_list.selectedItems()]

        query = "SELECT completed, COUNT(*) FROM tasks"
        conditions = []
        params = []

        if selected_months:
            placeholders = ", ".join(["?"] * len(selected_months))
            conditions.append(f"strftime('%m', creation_date) IN ({placeholders})")
            params.extend(selected_months)

        if selected_years:
            placeholders = ", ".join(["?"] * len(selected_years))
            conditions.append(f"strftime('%Y', creation_date) IN ({placeholders})")
            params.extend(selected_years)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " GROUP BY completed"

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            task_data = cursor.fetchall()

        total_tasks = sum(count for _, count in task_data)
        total_done = sum(count for completed, count in task_data if completed == 1)
        total_pending = total_tasks - total_done

        if total_tasks == 0:
            QMessageBox.information(self, "Sem dados", "Não há tarefas suficientes para exibir as estatísticas.")
            self.task_summary_label.setText("Total de Tarefas: 0 | Concluídas: 0 | Pendentes: 0")
            self.task_figure.clear()
            self.task_canvas.draw()
            return

        # Atualiza o resumo numérico
        self.task_summary_label.setText(
            f"Total de Tarefas: {total_tasks} | Concluídas: {total_done} | Pendentes: {total_pending}"
        )

        # Plotar o gráfico de progresso de tarefas
        self.task_figure.clear()
        ax = self.task_figure.add_subplot(111)
        ax.pie([total_done, total_pending], labels=["Concluídas", "Pendentes"],
               autopct="%1.1f%%", colors=["#66b3ff", "#ff9999"])
        ax.set_title("Progresso de Tarefas")
        self.task_canvas.draw()

    # ------------------------------
    # Métodos Adicionais
    # ------------------------------

    def strip_html(self, html):
        """Remove tags HTML e retorna o texto puro."""
        doc = QTextDocument()
        doc.setHtml(html)
        return doc.toPlainText()

    # ------------------------------
    # Métodos de Deleção de Notas
    # ------------------------------

    def delete_selected_note(self):
        """Deleta a nota selecionada na tabela de notas."""
        selected_row = self.notes_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Seleção Inválida", "Por favor, selecione uma nota para apagar.")
            return

        date_item = self.notes_table.item(selected_row, 0)
        if not date_item:
            QMessageBox.warning(self, "Erro", "Não foi possível encontrar a data da nota selecionada.")
            return

        note_date = date_item.text()
        reply = QMessageBox.question(
            self, "Confirmação", f"Tem certeza de que deseja apagar a nota de {note_date}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM notes WHERE date = ?", (note_date,))
                conn.commit()

            self.update_all()  # Atualiza a tabela e os gráficos
            QMessageBox.information(self, "Nota Apagada", "A nota foi apagada com sucesso.")
            self.note_deleted.emit(note_date)  # Emite o sinal com a data da nota apagada

# --------------------------------------------------
# Ponto de Entrada do Aplicativo
# --------------------------------------------------

def main():
    """Função principal para iniciar o widget de estatísticas."""
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = StatsWidget()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

