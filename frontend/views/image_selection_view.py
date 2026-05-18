#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image Selection View - Proyecto de Grado
Ventana para seleccionar una imagen personalizada de backend/assets/.
Muestra thumbnails y preview de la imagen seleccionada.
"""

import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QLabel,
    QFrame, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QIcon, QPixmap

from backend.config import SystemConfig
from backend.image_processor import ImageProcessor


class ImageSelectionView(QMainWindow):
    """Ventana para seleccionar imagen personalizada con previsualización."""

    imagen_seleccionada = Signal(str)   # path de la imagen
    ir_atras = Signal()
    actividad_detectada = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Imagen")
        self.setFixedSize(SystemConfig.SCREEN_WIDTH, SystemConfig.SCREEN_HEIGHT)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self._imagen_actual = ""
        self._imagenes = []
        self._build_ui()
        self._aplicar_estilo()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # === Panel izquierdo: galería de imágenes ===
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # Título
        lbl_titulo = QLabel("Seleccione una imagen:")
        lbl_titulo.setFont(QFont("Purisa", 14, QFont.Bold))
        lbl_titulo.setStyleSheet("color: #4DB6AC;")
        left_layout.addWidget(lbl_titulo)

        # Lista de imágenes con iconos
        self.list_imagenes = QListWidget()
        self.list_imagenes.setFont(QFont("Purisa", 11))
        self.list_imagenes.setIconSize(QSize(64, 64))
        self.list_imagenes.setSpacing(4)
        self.list_imagenes.currentRowChanged.connect(self._on_imagen_seleccionada)
        left_layout.addWidget(self.list_imagenes, stretch=1)

        # Botones
        h_btns = QHBoxLayout()
        h_btns.setSpacing(10)

        self.btn_atras = QPushButton("← ATRÁS")
        self.btn_atras.setMinimumHeight(50)
        self.btn_atras.setFont(QFont("Purisa", 12, QFont.Bold))
        self.btn_atras.clicked.connect(self._on_atras)
        h_btns.addWidget(self.btn_atras)

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

        # Preview de imagen
        self.lbl_imagen = QLabel()
        self.lbl_imagen.setAlignment(Qt.AlignCenter)
        self.lbl_imagen.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lbl_imagen.setStyleSheet(
            "background-color: #1e1e1e; "
            "border: 2px solid #4DB6AC; "
            "border-radius: 10px;"
        )
        self.lbl_imagen.setMinimumSize(300, 300)
        right_layout.addWidget(self.lbl_imagen, stretch=1)

        # Info de la imagen
        self.lbl_info = QLabel("")
        self.lbl_info.setFont(QFont("Purisa", 10))
        self.lbl_info.setStyleSheet("color: #aaa;")
        self.lbl_info.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.lbl_info)

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

    def _cargar_imagenes(self):
        """Escanea y carga las imágenes disponibles en la galería."""
        self.list_imagenes.clear()
        self._imagenes = ImageProcessor.listar_imagenes()

        for img_info in self._imagenes:
            item = QListWidgetItem()
            item.setText(img_info['nombre'])

            # Cargar thumbnail
            pixmap = QPixmap(img_info['path'])
            if not pixmap.isNull():
                thumb = pixmap.scaled(
                    64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                item.setIcon(QIcon(thumb))

            self.list_imagenes.addItem(item)

    # === Handlers ===

    def _on_imagen_seleccionada(self, row):
        if row >= 0 and row < len(self._imagenes):
            img_info = self._imagenes[row]
            self._imagen_actual = img_info['path']

            # Mostrar preview
            pixmap = QPixmap(img_info['path'])
            if not pixmap.isNull():
                # Escalar al tamaño del label manteniendo proporción
                preview = pixmap.scaled(
                    self.lbl_imagen.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.lbl_imagen.setPixmap(preview)

            # Info
            self.lbl_info.setText(
                f"{img_info['nombre']}{img_info['ext']}"
            )

    def _on_atras(self):
        self.actividad_detectada.emit()
        self.ir_atras.emit()
        self.hide()

    def _on_confirmar(self):
        self.actividad_detectada.emit()
        if not self._imagen_actual:
            QMessageBox.warning(self, "Advertencia",
                                "Seleccione una imagen.")
            return
        self.imagen_seleccionada.emit(self._imagen_actual)
        self.hide()

    def reset(self):
        """Reinicia la vista y recarga imágenes."""
        self.list_imagenes.clearSelection()
        self._imagen_actual = ""
        self.lbl_imagen.clear()
        self.lbl_info.setText("")
        self._cargar_imagenes()

    def showEvent(self, event):
        self.actividad_detectada.emit()
        self._cargar_imagenes()
        super().showEvent(event)

    def mousePressEvent(self, event):
        self.actividad_detectada.emit()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        self.actividad_detectada.emit()
        super().keyPressEvent(event)
