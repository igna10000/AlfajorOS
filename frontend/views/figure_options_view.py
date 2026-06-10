#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure Options View - Proyecto de Grado
Ventana para seleccionar patrón decorativo con previsualización.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QLabel,
    QSlider, QFrame, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QStringListModel
from PySide6.QtGui import QFont

from frontend.widgets.alfajor_canvas import AlfajorCanvas
from backend.config import SystemConfig


class FigureOptionsView(QMainWindow):
    """Ventana para seleccionar patrón decorativo con previsualización."""

    figura_configurada = Signal(str, int)
    abrir_imagen = Signal()
    ir_atras = Signal()
    actividad_detectada = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Patrón Decorativo")
        self.setFixedSize(SystemConfig.SCREEN_WIDTH, SystemConfig.SCREEN_HEIGHT)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self._patron_actual = ""
        self._build_ui()
        self._aplicar_estilo()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # === Panel izquierdo: lista de patrones + slider ===
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # Título
        lbl_titulo = QLabel("Seleccione un patrón:")
        lbl_titulo.setFont(QFont("Purisa", 14, QFont.Bold))
        lbl_titulo.setStyleSheet("color: #4DB6AC;")
        left_layout.addWidget(lbl_titulo)

        # Lista de patrones
        self.list_patrones = QListWidget()
        self.list_patrones.setFont(QFont("Purisa", 12))
        for patron in SystemConfig.PATRONES:
            item = QListWidgetItem(patron)
            self.list_patrones.addItem(item)
        self.list_patrones.currentRowChanged.connect(self._on_patron_seleccionado)
        left_layout.addWidget(self.list_patrones, stretch=1)

        # Slider de grosor eliminado (grosor determinado por la boquilla)

        # Botones
        h_btns = QHBoxLayout()
        h_btns.setSpacing(10)

        self.btn_atras = QPushButton("← ATRÁS")
        self.btn_atras.setMinimumHeight(50)
        self.btn_atras.setFont(QFont("Purisa", 12, QFont.Bold))
        self.btn_atras.clicked.connect(self._on_atras)
        h_btns.addWidget(self.btn_atras)

        self.btn_imagen = QPushButton("🖼 IMAGEN")
        self.btn_imagen.setMinimumHeight(50)
        self.btn_imagen.setFont(QFont("Purisa", 12, QFont.Bold))
        self.btn_imagen.clicked.connect(self._on_imagen)
        h_btns.addWidget(self.btn_imagen)

        self.btn_confirmar = QPushButton("✓ CONFIRMAR")
        self.btn_confirmar.setMinimumHeight(50)
        self.btn_confirmar.setFont(QFont("Purisa", 12, QFont.Bold))
        self.btn_confirmar.clicked.connect(self._on_confirmar)
        h_btns.addWidget(self.btn_confirmar)

        left_layout.addLayout(h_btns)

        left_panel.setMaximumWidth(380)
        main_layout.addWidget(left_panel)

        # === Separador ===
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color: #4DB6AC;")
        main_layout.addWidget(sep)

        # === Panel derecho: previsualización ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)

        lbl_preview = QLabel("Vista previa:")
        lbl_preview.setFont(QFont("Purisa", 12, QFont.Bold))
        lbl_preview.setStyleSheet("color: #FFAB40;")
        right_layout.addWidget(lbl_preview)

        # Canvas de previsualización
        self.preview_canvas = AlfajorCanvas()
        self.preview_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout.addWidget(self.preview_canvas, stretch=1)

        main_layout.addWidget(right_panel, stretch=1)

    def _aplicar_estilo(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #2b2b2b;
            }
            QListWidget {
                background-color: #3c3c3c;
                color: #e0e0e0;
                border: 2px solid #4DB6AC;
                border-radius: 8px;
                padding: 5px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #4DB6AC;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #3d6e68;
            }
            QPushButton {
                background-color: #4DB6AC;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #3d9e95;
            }
        """)

    # === Handlers ===

    def _on_patron_seleccionado(self, row):
        if row >= 0:
            self._patron_actual = SystemConfig.PATRONES[row]
            self.preview_canvas.set_patron(self._patron_actual)
            self.preview_canvas.set_grosor(50)

    def _on_atras(self):
        self.actividad_detectada.emit()
        self.ir_atras.emit()
        self.hide()

    def _on_imagen(self):
        self.actividad_detectada.emit()
        self.abrir_imagen.emit()
        self.hide()

    def _on_confirmar(self):
        self.actividad_detectada.emit()
        if not self._patron_actual:
            QMessageBox.warning(self, "Advertencia",
                                "Seleccione un patrón decorativo.")
            return
        grosor = 50
        self.figura_configurada.emit(self._patron_actual, grosor)
        self.hide()

    def reset(self):
        self.list_patrones.clearSelection()
        self._patron_actual = ""
        self.preview_canvas.reset()

    def showEvent(self, event):
        self.actividad_detectada.emit()
        super().showEvent(event)

    def mousePressEvent(self, event):
        self.actividad_detectada.emit()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        self.actividad_detectada.emit()
        super().keyPressEvent(event)
