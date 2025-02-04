#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bootstrap para exibir a splash screen imediatamente e depois carregar o aplicativo.
"""
from PyQt5.QtWebEngineWidgets import QWebEngineView 
import sys
import os
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtCore import Qt

def main():
    app = QApplication(sys.argv)

    # Define o caminho da imagem da splash screen
    splash_image = "splash.png"  # Substitua pelo caminho correto, se necessário

    if os.path.exists(splash_image):
        pixmap = QPixmap(splash_image)
    else:
        # Se a imagem não existir, cria um pixmap simples de 400x300 com fundo branco
        pixmap = QPixmap(400, 300)
        pixmap.fill(QColor("white"))

    # Cria e exibe a splash screen
    splash = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
    splash.showMessage("Carregando o aplicativo...", Qt.AlignBottom | Qt.AlignCenter, Qt.black)
    splash.show()
    app.processEvents()  # Garante que a splash seja exibida imediatamente

    # Agora, importe e inicialize o aplicativo principal.
    # Essa importação só ocorrerá depois que a splash já estiver visível.
    from calendar_widget import CalendarApp  # Seu módulo principal

    window = CalendarApp()
    window.show()
    app.setStyle("Fusion")
    # Fecha a splash screen assim que o aplicativo estiver pronto
    splash.finish(window)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
