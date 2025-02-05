#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QSpinBox, QCheckBox, QDialogButtonBox, QDialog

class FlashCardsConfigDialog(QDialog):
    def __init__(self, current_config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações do Flash Cards")
        self.current_config = current_config.copy()  # Cópia da configuração atual
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        # Fator de Facilidade Inicial
        layout.addWidget(QLabel("Fator de Facilidade Inicial (EF):"))
        self.ef_spin = QSpinBox(self)
        self.ef_spin.setRange(10, 100)  # Ex: 10 representa 1.0 e 100 representa 10.0
        self.ef_spin.setValue(self.current_config.get("initial_ef", 25))
        layout.addWidget(self.ef_spin)
        # Número de Cards por Sessão
        layout.addWidget(QLabel("Número de cards por sessão:"))
        self.cards_spin = QSpinBox(self)
        self.cards_spin.setRange(1, 100)
        self.cards_spin.setValue(self.current_config.get("cards_per_session", 10))
        layout.addWidget(self.cards_spin)
        # Áudio Automático
        self.audio_checkbox = QCheckBox("Reproduzir áudio automaticamente", self)
        self.audio_checkbox.setChecked(self.current_config.get("auto_audio", True))
        layout.addWidget(self.audio_checkbox)
        # Botões OK/Cancelar
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_config(self):
        return {
            "initial_ef": self.ef_spin.value(),
            "cards_per_session": self.cards_spin.value(),
            "auto_audio": self.audio_checkbox.isChecked()
        }
