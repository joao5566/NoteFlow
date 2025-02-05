#!/usr/bin/env python
# -*- coding: utf-8 -*-

import calendar
import datetime
import importlib
import base64
import numpy as np
import matplotlib.pyplot as plt
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QInputDialog, QMessageBox
from history import HistoryTableWidget

class StatisticsTab(QWidget):
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        self.db_connection = db_connection
        self.filtered_reviews = []  # Dados filtrados da tabela review_history
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QtWidgets.QTabWidget(self)
        layout.addWidget(self.tabs)
        self.dashboard_tab = QWidget(self)
        self.setup_dashboard_tab()
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.history_tab = QWidget(self)
        self.setup_history_tab()
        self.tabs.addTab(self.history_tab, "Histórico de Revisões")

    def setup_dashboard_tab(self):
        dash_layout = QVBoxLayout(self.dashboard_tab)
        # Seleção do tipo de gráfico
        graph_selection_layout = QHBoxLayout()
        graph_selection_layout.addWidget(QLabel("Tipo de Gráfico:", self))
        self.graph_type_combo = QComboBox(self)
        self.graph_type_combo.addItems([
            "Revisões por Dia (Barras)",
            "Revisões por Dia (Linhas)",
            "Heatmap por Ano",
            "Heatmap de Vários Anos",
            "Comparativo de Revisões por Dias da Semana - Barras",
            "Comparativo de Revisões por Dias da Semana - Linhas",
            "Comparativo de Revisões por Dias da Semana - Pizza",
            "Procrastinação (Pizza)"
        ])
        graph_selection_layout.addWidget(self.graph_type_combo)
        dash_layout.addLayout(graph_selection_layout)
        # Filtros: Anos, Meses e Semanas
        filter_layout = QHBoxLayout()
        self.year_list = QtWidgets.QListWidget(self)
        self.year_list.setSelectionMode(QtWidgets.QListWidget.MultiSelection)
        filter_layout.addWidget(QLabel("Anos:"))
        filter_layout.addWidget(self.year_list)
        self.year_list.itemSelectionChanged.connect(self.update_months)
        self.month_list = QtWidgets.QListWidget(self)
        self.month_list.setSelectionMode(QtWidgets.QListWidget.MultiSelection)
        filter_layout.addWidget(QLabel("Meses:"))
        filter_layout.addWidget(self.month_list)
        self.month_list.itemSelectionChanged.connect(self.update_weeks)
        self.week_list = QtWidgets.QListWidget(self)
        self.week_list.setSelectionMode(QtWidgets.QListWidget.MultiSelection)
        filter_layout.addWidget(QLabel("Semanas:"))
        filter_layout.addWidget(self.week_list)
        self.update_button = QPushButton("Atualizar Estatísticas", self)
        self.update_button.clicked.connect(self.plot_selected_graph)
        filter_layout.addWidget(self.update_button)
        dash_layout.addLayout(filter_layout)
        # Área para o gráfico
        matplotlib = importlib.import_module("matplotlib")
        matplotlib.use("Qt5Agg")
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.figure import Figure
        self.figure = Figure(figsize=(6, 4))
        self.canvas = FigureCanvas(self.figure)
        dash_layout.addWidget(self.canvas)
        self.update_years()

    def setup_history_tab(self):
        # Adiciona o HistoryTableWidget na aba de histórico
        history_layout = QVBoxLayout(self.history_tab)
        self.history_widget = HistoryTableWidget(self.db_connection, self.history_tab)
        history_layout.addWidget(self.history_widget)

    def update_years(self):
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT DISTINCT strftime('%Y', review_date) AS year FROM review_history ORDER BY year")
        years = [row["year"] for row in cursor.fetchall()]
        self.year_list.clear()
        for year in years:
            self.year_list.addItem(year)
        self.month_list.clear()
        self.week_list.clear()

    def update_months(self):
        selected_years = [item.text() for item in self.year_list.selectedItems()]
        if not selected_years:
            self.month_list.clear()
            self.week_list.clear()
            self.month_list.setEnabled(False)
            self.week_list.setEnabled(False)
            return
        placeholders = ", ".join(["?"] * len(selected_years))
        query = f"SELECT DISTINCT strftime('%m', review_date) AS month FROM review_history WHERE strftime('%Y', review_date) IN ({placeholders}) ORDER BY month"
        cursor = self.db_connection.cursor()
        cursor.execute(query, selected_years)
        months = [row["month"] for row in cursor.fetchall()]
        self.month_list.clear()
        for m in sorted(months):
            self.month_list.addItem(f"{int(m):02d}")
        self.month_list.setEnabled(True)
        self.week_list.clear()
        self.week_list.setEnabled(False)

    def update_weeks(self):
        selected_years = [item.text() for item in self.year_list.selectedItems()]
        selected_months = [item.text() for item in self.month_list.selectedItems()]
        if not selected_years or not selected_months:
            self.week_list.clear()
            self.week_list.setEnabled(False)
            return
        self.week_list.clear()
        for week in range(1, 6):
            self.week_list.addItem(str(week))
        self.week_list.setEnabled(True)

    def filter_reviews(self):
        selected_years = [item.text() for item in self.year_list.selectedItems()]
        selected_months = [item.text() for item in self.month_list.selectedItems()]
        selected_weeks = [int(item.text()) for item in self.week_list.selectedItems()]
        query = "SELECT * FROM review_history"
        conditions = []
        params = []
        if selected_years:
            placeholders = ", ".join(["?"] * len(selected_years))
            conditions.append(f"strftime('%Y', review_date) IN ({placeholders})")
            params.extend(selected_years)
        if selected_months:
            placeholders = ", ".join(["?"] * len(selected_months))
            conditions.append(f"strftime('%m', review_date) IN ({placeholders})")
            params.extend(selected_months)
        if selected_weeks:
            week_conditions = []
            for week in selected_weeks:
                week_conditions.append(f"((CAST(strftime('%d', review_date) AS INTEGER)-1)/7 + 1) = {week}")
            conditions.append("(" + " OR ".join(week_conditions) + ")")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY review_date"
        cursor = self.db_connection.cursor()
        cursor.execute(query, params)
        self.filtered_reviews = cursor.fetchall()

    def plot_selected_graph(self):
        self.filter_reviews()
        graph_type = self.graph_type_combo.currentText()
        self.figure.clear()
        plot_methods = {
            "Revisões por Dia (Barras)": self.plot_revisions_bar,
            "Revisões por Dia (Linhas)": self.plot_revisions_line,
            "Heatmap por Ano": self.plot_heatmap_for_year,
            "Heatmap de Vários Anos": self.plot_heatmap,
            "Comparativo de Revisões por Dias da Semana - Barras": self.plot_weekday_bar_chart,
            "Comparativo de Revisões por Dias da Semana - Linhas": self.plot_weekday_line_chart,
            "Comparativo de Revisões por Dias da Semana - Pizza": self.plot_weekday_pie_chart,
            "Procrastinação (Pizza)": self.plot_procrastination_chart
        }
        plot_method = plot_methods.get(graph_type, None)
        if plot_method:
            if graph_type == "Heatmap por Ano":
                text, ok = QInputDialog.getText(self, "Entrada", "Digite o ano desejado:")
                if ok and text.isdigit():
                    plot_method(int(text))
                else:
                    QMessageBox.warning(self, "Entrada Inválida", "Por favor, digite um ano válido.")
                    return
            else:
                plot_method()
        self.canvas.draw()

    def plot_revisions_bar(self):
        counts = {}
        for row in self.filtered_reviews:
            date = row["review_date"]
            counts[date] = counts.get(date, 0) + 1
        dates = sorted(counts.keys())
        rev_counts = [counts[date] for date in dates]
        ax = self.figure.add_subplot(111)
        ax.bar(dates, rev_counts, color='skyblue')
        ax.set_title("Revisões por Dia (Barras)")
        ax.set_xlabel("Data")
        ax.set_ylabel("Número de Revisões")
        ax.tick_params(axis='x', rotation=45)
        self.figure.tight_layout()

    def plot_revisions_line(self):
        counts = {}
        for row in self.filtered_reviews:
            date = row["review_date"]
            counts[date] = counts.get(date, 0) + 1
        dates = sorted(counts.keys())
        rev_counts = [counts[date] for date in dates]
        ax = self.figure.add_subplot(111)
        ax.plot(dates, rev_counts, marker='o', linestyle='-', color='purple')
        ax.set_title("Revisões por Dia (Linhas)")
        ax.set_xlabel("Data")
        ax.set_ylabel("Número de Revisões")
        ax.tick_params(axis='x', rotation=45)
        self.figure.tight_layout()

    def plot_heatmap_for_year(self, year):
        from PyQt5.QtCore import QDate
        dates = [
            QDate.fromString(row["review_date"], "yyyy-MM-dd") for row in self.filtered_reviews
            if QDate.fromString(row["review_date"], "yyyy-MM-dd").year() == year
        ]
        if not dates:
            QMessageBox.warning(self, "Sem dados", f"Não há revisões para exibir no ano {year}.")
            return
        heatmap_data = np.zeros((12, 31), dtype=int)
        for date in dates:
            month_index = date.month() - 1
            day_index = date.day() - 1
            heatmap_data[month_index, day_index] += 1
        ax = self.figure.add_subplot(111)
        cax = ax.imshow(heatmap_data, cmap='YlGn', aspect='auto', vmin=0, vmax=heatmap_data.max())
        ax.set_xticks(np.arange(31))
        ax.set_xticklabels([str(i + 1) for i in range(31)])
        ax.set_yticks(np.arange(12))
        ax.set_yticklabels([QtCore.QDate.longMonthName(i + 1) for i in range(12)])
        ax.set_title(f"Heatmap de Revisões - {year}")
        ax.set_xlabel("Dias do Mês")
        ax.set_ylabel("Meses")
        self.figure.colorbar(cax, orientation='vertical', label='Número de Revisões')

    def plot_heatmap(self):
        from PyQt5.QtCore import QDate
        dates = [QDate.fromString(row["review_date"], "yyyy-MM-dd") for row in self.filtered_reviews]
        if not dates:
            QMessageBox.warning(self, "Sem dados", "Não há revisões para exibir no período selecionado.")
            return
        selected_years = sorted(set(date.year() for date in dates))
        months = list(range(1, 13))
        heatmap_data = np.zeros((len(selected_years), len(months)), dtype=int)
        for date in dates:
            year_index = selected_years.index(date.year())
            month_index = date.month() - 1
            heatmap_data[year_index, month_index] += 1
        ax = self.figure.add_subplot(111)
        cax = ax.imshow(heatmap_data, cmap='YlGn', aspect='auto')
        ax.set_xticks(np.arange(len(months)))
        ax.set_xticklabels([QtCore.QDate.shortMonthName(m) for m in months])
        ax.set_yticks(np.arange(len(selected_years)))
        ax.set_yticklabels([str(year) for year in selected_years])
        ax.set_title("Heatmap de Revisões por Mês e Ano")
        ax.set_xlabel("Meses")
        ax.set_ylabel("Anos")
        self.figure.colorbar(cax, orientation='vertical', label='Número de Revisões')

    def plot_weekday_bar_chart(self):
        weekday_counts = {day: 0 for day in calendar.day_name}
        from PyQt5.QtCore import QDate
        for row in self.filtered_reviews:
            date = QDate.fromString(row["review_date"], "yyyy-MM-dd")
            weekday = calendar.day_name[date.dayOfWeek() - 1]
            weekday_counts[weekday] += 1
        days = list(weekday_counts.keys())
        counts = list(weekday_counts.values())
        ax = self.figure.add_subplot(111)
        bars = ax.bar(days, counts, color='skyblue')
        ax.set_title("Revisões por Dia da Semana (Barras)")
        ax.set_xlabel("Dias da Semana")
        ax.set_ylabel("Número de Revisões")
        ax.set_ylim(0, max(counts) + 5)
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height}', xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom')

    def plot_weekday_line_chart(self):
        from collections import defaultdict
        week_day_counts = defaultdict(lambda: defaultdict(int))
        from PyQt5.QtCore import QDate
        for row in self.filtered_reviews:
            date = QDate.fromString(row["review_date"], "yyyy-MM-dd")
            week_number = date.weekNumber()[0]
            weekday = calendar.day_name[date.dayOfWeek() - 1]
            week_day_counts[week_number][weekday] += 1
        if not week_day_counts:
            QMessageBox.warning(self, "Sem dados", "Não há revisões para exibir no gráfico de linhas.")
            return
        weeks = sorted(week_day_counts.keys())
        days = list(calendar.day_name)
        day_trends = {day: [] for day in days}
        for week in weeks:
            for day in days:
                day_trends[day].append(week_day_counts[week].get(day, 0))
        ax = self.figure.add_subplot(111)
        for day, counts in day_trends.items():
            ax.plot(weeks, counts, marker='o', label=day)
        ax.set_title("Tendência de Revisões por Dia da Semana (Linhas)")
        ax.set_xlabel("Número da Semana")
        ax.set_ylabel("Número de Revisões")
        ax.legend(title="Dias")
        ax.grid(True)

    def plot_weekday_pie_chart(self):
        weekday_counts = {day: 0 for day in calendar.day_name}
        from PyQt5.QtCore import QDate
        for row in self.filtered_reviews:
            date = QDate.fromString(row["review_date"], "yyyy-MM-dd")
            weekday = calendar.day_name[date.dayOfWeek() - 1]
            weekday_counts[weekday] += 1
        labels = list(weekday_counts.keys())
        sizes = list(weekday_counts.values())
        if sum(sizes) == 0:
            QMessageBox.warning(self, "Sem dados", "Não há revisões para exibir no gráfico de pizza.")
            return
        ax = self.figure.add_subplot(111)
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired.colors)
        ax.set_title("Revisões por Dia da Semana (Pizza)")
        ax.axis('equal')

    def plot_procrastination_chart(self):
        from PyQt5.QtCore import QDate
        dates = [QDate.fromString(row["review_date"], "yyyy-MM-dd") for row in self.filtered_reviews]
        if not dates:
            QMessageBox.information(self, "Sem dados", "Não há revisões para exibir.")
            return
        current_date = QDate.currentDate()
        total_days = current_date.daysInMonth()
        reviewed_days = { (date.year(), date.month(), date.day()) for date in dates }
        num_reviewed = len(reviewed_days)
        num_not_reviewed = total_days - num_reviewed
        ax = self.figure.add_subplot(111)
        ax.pie([num_reviewed, num_not_reviewed], labels=["Revisados", "Não Revisados"],
               autopct='%1.1f%%', colors=["#66b3ff", "#ff9999"])
        ax.set_title("Procrastinação (Mês Atual)")
        ax.axis('equal')
