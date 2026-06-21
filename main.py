#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================
  AlfajorOS — Extrusora de Crema para Alfajores
  Proyecto de Grado v2.0
=============================================================

  Arquitectura:
  ┌──────────────────────────────────────────┐
  │              main.py (entry point)       │
  ├──────────────────────────────────────────┤
  │  frontend/                               │
  │  ├── app.py          (controlador)       │
  │  ├── styles.py       (estilos globales)  │
  │  ├── views/          (vistas/pantallas)  │
  │  ├── widgets/        (componentes)       │
  │  └── resources/      (.ui, ui_loader)    │
  ├──────────────────────────────────────────┤
  │  backend/                                │
  │  ├── config.py       (configuración)     │
  │  ├── extruder.py     (motor extrusión)   │
  │  └── gcode.py        (generador G-Code)  │
  └──────────────────────────────────────────┘

  Ejecutar:
    python3 main.py

  Requisitos:
    pip install PySide6
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor

from frontend.app import AppController
from frontend.styles import get_global_stylesheet
from backend.servo_controller import set_servo_angle


def main():
    """Punto de entrada principal de AlfajorOS."""
    # Inicializar el servo en 130 grados cuando no está dibujando (cerrado)
    set_servo_angle(130)

    app = QApplication(sys.argv)
    app.setApplicationName("AlfajorOS — Extrusora de Crema")
    app.setOrganizationName("Proyecto de Grado")

    # Ocultar cursor (proyecto táctil)
    app.setOverrideCursor(QCursor(Qt.BlankCursor))

    # Estilo global
    app.setStyleSheet(get_global_stylesheet())

    # Iniciar controlador
    controller = AppController()
    controller.iniciar()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
