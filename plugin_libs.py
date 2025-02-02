"""
plugin_libs.py

Este módulo reúne diversas bibliotecas e funções utilitárias para auxiliar
o desenvolvimento de plugins para o seu aplicativo.

Exemplo de uso:
    from plugin_libs import QtWidgets, np, pd, plt, requests, logging, functools, itertools, math, Path
"""

# Importações padrão e utilitárias
import sys
import os
import json
import re
import random
import datetime
import base64
import sqlite3
import tempfile
from pathlib import Path
import logging

# Bibliotecas para processamento de dados
import numpy as np
try:
    import pandas as pd
except ImportError:
    pd = None  # Caso o pandas não esteja instalado

# Bibliotecas para gráficos
import matplotlib.pyplot as plt

# Biblioteca para requisições HTTP
try:
    import requests
except ImportError:
    requests = None

# Outras bibliotecas utilitárias
import math
import itertools
import functools
import calendar

# ------------------------------
# Bibliotecas adicionais
# ------------------------------
try:
    import altgraph
except ImportError:
    altgraph = None

try:
    import asteval
except ImportError:
    asteval = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    import certifi
except ImportError:
    certifi = None

try:
    import cffi
except ImportError:
    cffi = None

try:
    import charset_normalizer
except ImportError:
    charset_normalizer = None

try:
    import comtypes
except ImportError:
    comtypes = None

try:
    import contourpy
except ImportError:
    contourpy = None

try:
    import cryptography
except ImportError:
    cryptography = None

try:
    import cycler
except ImportError:
    cycler = None

try:
    import docstring_to_markdown
except ImportError:
    docstring_to_markdown = None

try:
    import et_xmlfile
except ImportError:
    et_xmlfile = None

# Removido: importação do fonttools

try:
    import fpdf
except ImportError:
    fpdf = None

try:
    import idna
except ImportError:
    idna = None

try:
    import jedi
except ImportError:
    jedi = None

try:
    import kiwisolver
except ImportError:
    kiwisolver = None

try:
    import lupa
except ImportError:
    lupa = None

try:
    import markdown
except ImportError:
    markdown = None

try:
    import openpyxl
except ImportError:
    openpyxl = None

try:
    import packaging
except ImportError:
    packaging = None

try:
    import parso
except ImportError:
    parso = None

try:
    import pefile
except ImportError:
    pefile = None

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import pluggy
except ImportError:
    pluggy = None

try:
    import pycparser
except ImportError:
    pycparser = None

try:
    import pygame
except ImportError:
    pygame = None

# Removido: importação do pyinstaller
# Removido: importação do pyinstaller_hooks_contrib

try:
    import pyparsing
except ImportError:
    pyparsing = None

try:
    import win32api  # Proveniente do pypiwin32
except ImportError:
    win32api = None

try:
    import dateutil
except ImportError:
    dateutil = None

try:
    import jsonrpc  # Possível módulo da python-lsp-jsonrpc
except ImportError:
    jsonrpc = None

# Removido: importação do vlc

try:
    import pytz
except ImportError:
    pytz = None

try:
    import setuptools
except ImportError:
    setuptools = None

try:
    import six
except ImportError:
    six = None

try:
    import soupsieve
except ImportError:
    soupsieve = None

try:
    import tzdata
except ImportError:
    tzdata = None

try:
    import ujson
except ImportError:
    ujson = None

try:
    import urllib3
except ImportError:
    urllib3 = None

# Importações do PyQt5 (já incluídas anteriormente, mas vamos repassar para facilitar o acesso)
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QInputDialog, QMessageBox, QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import QUrl, QDate, Qt
from PyQt5.QtGui import QIcon, QPixmap

# Lista de objetos exportados para facilitar a importação
__all__ = [
    # Utilitários
    "sys", "os", "json", "re", "random", "datetime", "base64", "sqlite3", "tempfile", "Path",
    "logging",
    # Processamento de dados
    "np", "pd",
    # Gráficos
    "plt",
    # Requisições HTTP
    "requests",
    # Outras bibliotecas utilitárias
    "math", "itertools", "functools", "calendar",
    # Bibliotecas adicionais
    "altgraph", "asteval", "BeautifulSoup", "certifi", "cffi", "charset_normalizer", "comtypes",
    "contourpy", "cryptography", "cycler", "docstring_to_markdown", "et_xmlfile", "fpdf",
    "idna", "jedi", "kiwisolver", "lupa", "markdown", "openpyxl", "packaging", "parso", "pefile", "Image",
    "pluggy", "pycparser", "pygame", "pyparsing", "win32api",
    "dateutil", "jsonrpc", "pytz", "setuptools", "six", "soupsieve", "tzdata", "ujson", "urllib3",
    # PyQt5 e componentes
    "QtWidgets", "QtCore", "QtGui",
    "QWidget", "QVBoxLayout", "QHBoxLayout", "QLabel", "QPushButton", "QLineEdit",
    "QComboBox", "QInputDialog", "QMessageBox", "QTableWidget", "QTableWidgetItem",
    "QUrl", "QDate", "Qt", "QIcon", "QPixmap"
]

if __name__ == "__main__":
    print("Este módulo fornece diversas bibliotecas úteis para o desenvolvimento de plugins.")
    print("Bibliotecas disponíveis:")
    for lib in __all__:
        print(f" - {lib}")
