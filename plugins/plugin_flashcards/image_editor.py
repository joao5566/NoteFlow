#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QVBoxLayout, QDialog, QDialogButtonBox, QComboBox, QLabel, QFileDialog
from PyQt5.QtCore import QBuffer, QIODevice

# --- Classe para redimensionar imagens em uma QGraphicsScene ---
class ResizablePixmapItem(QtWidgets.QGraphicsPixmapItem):
    def __init__(self, pixmap):
        super().__init__(pixmap)
        self.original_pixmap = pixmap
        self.setFlags(QtWidgets.QGraphicsItem.ItemIsSelectable | 
                      QtWidgets.QGraphicsItem.ItemIsMovable |
                      QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)
        self.handle_size = 10
        self.resizing = False
        self.current_handle = None
        self.setAcceptHoverEvents(True)
        self.updateHandlesPos()

    def updateHandlesPos(self):
        rect = self.boundingRect()
        self.handles = {
            'top_left': QtCore.QRectF(rect.topLeft(), QtCore.QSizeF(self.handle_size, self.handle_size)),
            'top_right': QtCore.QRectF(rect.topRight() - QtCore.QPointF(self.handle_size, 0), QtCore.QSizeF(self.handle_size, self.handle_size)),
            'bottom_left': QtCore.QRectF(rect.bottomLeft() - QtCore.QPointF(0, self.handle_size), QtCore.QSizeF(self.handle_size, self.handle_size)),
            'bottom_right': QtCore.QRectF(rect.bottomRight() - QtCore.QPointF(self.handle_size, self.handle_size), QtCore.QSizeF(self.handle_size, self.handle_size))
        }

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        if self.isSelected():
            pen = QtGui.QPen(QtCore.Qt.black, 1, QtCore.Qt.DashLine)
            painter.setPen(pen)
            for handle in self.handles.values():
                painter.drawRect(handle)

    def hoverMoveEvent(self, event):
        for handle, rect in self.handles.items():
            if rect.contains(event.pos()):
                self.setCursor(QtCore.Qt.SizeFDiagCursor)
                return
        self.setCursor(QtCore.Qt.ArrowCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        for handle, rect in self.handles.items():
            if rect.contains(event.pos()):
                self.resizing = True
                self.current_handle = handle
                self.orig_rect = self.boundingRect()
                self.orig_pos = event.pos()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.resizing and self.current_handle:
            diff = event.pos() - self.orig_pos
            if self.current_handle == 'bottom_right':
                new_width = self.orig_rect.width() + diff.x()
                new_height = self.orig_rect.height() + diff.y()
            elif self.current_handle == 'top_left':
                new_width = self.orig_rect.width() - diff.x()
                new_height = self.orig_rect.height() - diff.y()
            elif self.current_handle == 'top_right':
                new_width = self.orig_rect.width() + diff.x()
                new_height = self.orig_rect.height() - diff.y()
            elif self.current_handle == 'bottom_left':
                new_width = self.orig_rect.width() - diff.x()
                new_height = self.orig_rect.height() + diff.y()
            new_width = max(new_width, 20)
            new_height = max(new_height, 20)
            new_pixmap = self.original_pixmap.scaled(
                int(new_width), int(new_height),
                QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
            )
            self.setPixmap(new_pixmap)
            self.updateHandlesPos()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.resizing = False
        self.current_handle = None
        super().mouseReleaseEvent(event)

# --- Diálogo para redimensionar imagem ---
class ImageResizeDialog(QDialog):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Redimensionar Imagem")
        self.setWindowState(QtCore.Qt.WindowMaximized)
        self.resize(600, 400)
        self.scene = QtWidgets.QGraphicsScene(self)
        self.view = QtWidgets.QGraphicsView(self.scene, self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.view)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.pixmap_item = ResizablePixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)
        self.scene.setSceneRect(self.pixmap_item.boundingRect())

    def getResizedPixmap(self):
        return self.pixmap_item.pixmap()

# --- Editor de Texto Rico ---
class RichTextEditor(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.toolbar = QtWidgets.QToolBar(self)
        layout.addWidget(self.toolbar)
        # Ações de formatação
        bold_action = QtWidgets.QAction("B", self)
        bold_action.setShortcut("Ctrl+B")
        bold_action.triggered.connect(self.toggle_bold)
        self.toolbar.addAction(bold_action)
        italic_action = QtWidgets.QAction("I", self)
        italic_action.setShortcut("Ctrl+I")
        italic_action.triggered.connect(self.toggle_italic)
        self.toolbar.addAction(italic_action)
        underline_action = QtWidgets.QAction("U", self)
        underline_action.setShortcut("Ctrl+U")
        underline_action.triggered.connect(self.toggle_underline)
        self.toolbar.addAction(underline_action)
        color_action = QtWidgets.QAction("Cor", self)
        color_action.triggered.connect(self.change_color)
        self.toolbar.addAction(color_action)
        self.font_combo = QtWidgets.QFontComboBox(self)
        self.font_combo.currentFontChanged.connect(self.change_font)
        self.toolbar.addWidget(self.font_combo)
        self.font_size_combo = QComboBox(self)
        for size in [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]:
            self.font_size_combo.addItem(str(size), size)
        self.font_size_combo.setCurrentText("12")
        self.font_size_combo.currentIndexChanged.connect(self.change_font_size)
        self.toolbar.addWidget(self.font_size_combo)
        image_action = QtWidgets.QAction("Inserir Imagem", self)
        image_action.triggered.connect(self.insert_image)
        self.toolbar.addAction(image_action)
        self.text_edit = ResizableImageTextEdit(self)
        layout.addWidget(self.text_edit)
        self.setLayout(layout)

    def toggle_bold(self):
        fmt = self.text_edit.currentCharFormat()
        weight = QtGui.QFont.Bold if fmt.fontWeight() != QtGui.QFont.Bold else QtGui.QFont.Normal
        fmt.setFontWeight(weight)
        self.text_edit.mergeCurrentCharFormat(fmt)

    def toggle_italic(self):
        fmt = self.text_edit.currentCharFormat()
        fmt.setFontItalic(not fmt.fontItalic())
        self.text_edit.mergeCurrentCharFormat(fmt)

    def toggle_underline(self):
        fmt = self.text_edit.currentCharFormat()
        fmt.setFontUnderline(not fmt.fontUnderline())
        self.text_edit.mergeCurrentCharFormat(fmt)

    def change_color(self):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            fmt = self.text_edit.currentCharFormat()
            fmt.setForeground(QtGui.QBrush(color))
            self.text_edit.mergeCurrentCharFormat(fmt)

    def change_font(self, font):
        fmt = self.text_edit.currentCharFormat()
        fmt.setFont(font)
        self.text_edit.mergeCurrentCharFormat(fmt)

    def change_font_size(self):
        size = int(self.font_size_combo.currentData())
        fmt = self.text_edit.currentCharFormat()
        fmt.setFontPointSize(size)
        self.text_edit.mergeCurrentCharFormat(fmt)

    def insert_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Imagem", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            with open(file_path, "rb") as image_file:
                image_data = image_file.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            if file_path.lower().endswith(".png"):
                mime = "image/png"
            elif file_path.lower().endswith((".jpg", ".jpeg")):
                mime = "image/jpeg"
            elif file_path.lower().endswith(".bmp"):
                mime = "image/bmp"
            elif file_path.lower().endswith(".gif"):
                mime = "image/gif"
            else:
                mime = "application/octet-stream"
            html_img = f'<img src="data:{mime};base64,{base64_data}" alt="Imagem" />'
            cursor = self.text_edit.textCursor()
            cursor.insertHtml(html_img)

    def toHtml(self):
        return self.text_edit.toHtml()

    def setHtml(self, html):
        self.text_edit.setHtml(html)

# --- QTextEdit com suporte a redimensionamento de imagens ---
class ResizableImageTextEdit(QtWidgets.QTextEdit):
    def mouseDoubleClickEvent(self, event):
        cursor = self.cursorForPosition(event.pos())
        fmt = cursor.charFormat()
        if fmt.isImageFormat():
            image_format = fmt.toImageFormat()
            image_src = image_format.name()
            if image_src.startswith("data:"):
                try:
                    header, base64_data = image_src.split(",", 1)
                except ValueError:
                    return super().mouseDoubleClickEvent(event)
                image_data = base64.b64decode(base64_data)
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(image_data)
                dialog = ImageResizeDialog(pixmap, self)
                if dialog.exec_() == QtWidgets.QDialog.Accepted:
                    new_pixmap = dialog.getResizedPixmap()
                    buffer = QBuffer()
                    buffer.open(QIODevice.WriteOnly)
                    new_pixmap.save(buffer, "PNG")
                    new_base64 = base64.b64encode(buffer.data()).decode('utf-8')
                    new_src = f"data:image/png;base64,{new_base64}"
                    new_format = QtGui.QTextImageFormat()
                    new_format.setName(new_src)
                    cursor.select(QtGui.QTextCursor.WordUnderCursor)
                    cursor.removeSelectedText()
                    cursor.insertImage(new_format)
        else:
            super().mouseDoubleClickEvent(event)
