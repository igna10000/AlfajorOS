#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calibration Wizard - Proyecto de Grado
Asistente interactivo para la calibración de la matriz 3x3 de alfajores.
Permite seleccionar un alfajor, viajar automáticamente a la posición tentativa,
y utilizar el JogControlWidget para guardar el punto exacto.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QPushButton, QLabel, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from frontend.widgets.jog_control import JogControlWidget
from backend.config import PrinterConfig as PC

class CalibrationWizard(QDialog):
    def __init__(self, printer, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calibración de Malla 3x3")
        self.printer = printer
        self.setFixedSize(850, 550)
        self.setModal(True)
        
        # Copia PROFUNDA de la matriz para no alterar el config si se cancela
        self.centros_tmp = [[*c] for c in PC.ALFAJORES_CENTROS]
        self.current_idx = -1
        
        # === UI ===
        self.setStyleSheet("""
            QDialog { background-color: #2b2b2b; color: white; }
            QLabel { color: white; }
        """)
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(20)
        
        # --- Panel Izquierdo: Matriz Visual ---
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        
        lbl_matriz = QLabel("Seleccione Alfajor a Calibrar:")
        lbl_matriz.setFont(QFont("Purisa", 14, QFont.Bold))
        lbl_matriz.setStyleSheet("color: #4DB6AC;")
        left_layout.addWidget(lbl_matriz)
        
        lbl_desc = QLabel("La impresora viajará al centro tentativo.\nAjuste la boquilla hasta tocar la superficie\ny presione 'GUARDAR HOME'.")
        lbl_desc.setFont(QFont("Purisa", 10))
        lbl_desc.setStyleSheet("color: #ccc;")
        left_layout.addWidget(lbl_desc)
        
        grid = QGridLayout()
        grid.setSpacing(15)
        self.btn_alfajores = {}  # {idx: QPushButton}
        for row in range(3):
            for col in range(3):
                idx = (2 - row) * 3 + col
                btn = QPushButton(f"{idx+1}")
                btn.setFixedSize(90, 90)
                btn.setFont(QFont("Purisa", 24, QFont.Bold))
                btn.setStyleSheet("""
                    QPushButton { background-color: #555; color: white; border-radius: 8px;} 
                    QPushButton:checked { background-color: #FFAB40; border: 3px solid white; }
                """)
                btn.setCheckable(True)
                btn.clicked.connect(lambda checked, i=idx: self._select_alfajor(i))
                grid.addWidget(btn, row, col)
                self.btn_alfajores[idx] = btn
                
        left_layout.addLayout(grid)
        left_layout.addStretch()
        
        # Botones inferiores (Cancelar / Guardar todo)
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("✖ CANCELAR")
        btn_ok = QPushButton("✔ GUARDAR MALLA")
        
        btn_cancel.setStyleSheet("QPushButton { background-color: #F44336; color: white; font-weight: bold; font-size: 14px; min-height: 45px; border-radius: 8px;} QPushButton:pressed { background-color: #D32F2F; }")
        btn_ok.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; font-size: 14px; min-height: 45px; border-radius: 8px;} QPushButton:pressed { background-color: #388E3C; }")
        
        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self._save_and_accept)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        left_layout.addLayout(btn_layout)
        
        main_layout.addWidget(left_panel, stretch=1)
        
        # --- Separador ---
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color: #4DB6AC;")
        main_layout.addWidget(sep)
        
        # --- Panel Derecho: Jog Control ---
        self.jog = JogControlWidget(self.printer, self)
        self.jog.home_saved.connect(self._on_home_saved)
        main_layout.addWidget(self.jog)
        
    def _select_alfajor(self, idx):
        """Selecciona el alfajor y mueve la boquilla a su posicion tentativa."""
        if not self.printer.is_connected:
            QMessageBox.warning(self, "Sin conexión", "Conecte la impresora antes de calibrar.")
            self.btn_alfajores.get(idx, QPushButton()).setChecked(False)
            return

        # Actualizar visualmente la selección
        for i, btn in self.btn_alfajores.items():
            btn.setChecked(i == idx)
            
        self.current_idx = idx
        
        # Viajar a la coordenada tentativa
        x, y, z = self.centros_tmp[idx]
        
        # Secuencia de viaje seguro
        self.printer.send_command("M302 P1") # Permitir movimiento
        self.printer.send_command("G90") # Modo absoluto
        self.printer.send_command(f"G0 Z{z + PC.Z_HOP_MM:.2f} F{PC.VEL_VIAJE}")
        self.printer.send_command(f"G0 X{x:.1f} Y{y:.1f} F{PC.VEL_VIAJE}")
        self.printer.send_command(f"G0 Z{z:.2f} F{PC.VEL_Z}")
            
    def _on_home_saved(self, x, y, z):
        """Callback cuando el usuario presiona Guardar Home en el Jog Control."""
        if self.current_idx >= 0:
            self.centros_tmp[self.current_idx] = [x, y, z]
            # Cambiar color del boton a verde indicando "Calibrado"
            if self.current_idx in self.btn_alfajores:
                self.btn_alfajores[self.current_idx].setStyleSheet("""
                    QPushButton { background-color: #4CAF50; color: white; border-radius: 8px;} 
                    QPushButton:checked { background-color: #388E3C; border: 3px solid white; }
                """)
            
            # Auto avanzar al siguiente
            next_idx = self.current_idx + 1
            if next_idx < 9:
                self._select_alfajor(next_idx)
            else:
                QMessageBox.information(self, "Calibración Completa", "Has guardado los 9 alfajores.\nPresiona 'Guardar Malla' para finalizar.")
        else:
            QMessageBox.warning(self, "Atención", "Selecciona un número de la matriz primero para asignarle el Home.")
            
    def _save_and_accept(self):
        """Guarda la malla en el config y cierra."""
        PC.ALFAJORES_CENTROS = self.centros_tmp
        try:
            PC.save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar config:\n{e}")
