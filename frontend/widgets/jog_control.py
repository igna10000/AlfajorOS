#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jog Control Widget - Proyecto de Grado
Panel lateral para mover manualmente los ejes XYZ y establecer Z0 (cima del material).
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QPushButton, 
    QComboBox, QLabel, QMessageBox, QHBoxLayout, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

BTN_JOG_STYLE = """
    QPushButton {
        background-color: #5C6BC0;
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: bold;
        font-family: Purisa;
        font-size: 16px;
    }
    QPushButton:pressed {
        background-color: #3f51b5;
    }
    QPushButton:disabled {
        background-color: #9E9E9E;
    }
"""

BTN_Z0_STYLE = """
    QPushButton {
        background-color: #E91E63;
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: bold;
        font-family: Purisa;
        font-size: 13px;
    }
    QPushButton:pressed {
        background-color: #C2185B;
    }
    QPushButton:disabled {
        background-color: #9E9E9E;
    }
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QGridLayout
from PySide6.QtCore import Qt

class RetractionDialog(QDialog):
    """Diálogo amigable para pantallas táctiles para ajustar la retracción."""
    def __init__(self, parent=None, default_val=150.0, prompt_text="Ajuste la distancia a retraer antes de ir al centro:"):
        super().__init__(parent)
        self.setWindowTitle("Distancia de Retracción")
        self.val = default_val
        self.setModal(True)
        self.setFixedSize(450, 250)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        lbl_info = QLabel(prompt_text)
        lbl_info.setFont(QFont("Purisa", 12))
        lbl_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_info)
        
        self.lbl_val = QLabel(f"{self.val:.1f} mm")
        self.lbl_val.setFont(QFont("Purisa", 30, QFont.Bold))
        self.lbl_val.setAlignment(Qt.AlignCenter)
        self.lbl_val.setStyleSheet("background-color: #333; color: white; border-radius: 8px; padding: 5px;")
        layout.addWidget(self.lbl_val)
        
        grid = QGridLayout()
        grid.setSpacing(10)
        
        btn_style = "QPushButton { background-color: #5C6BC0; color: white; font-weight: bold; font-size: 20px; border-radius: 8px; min-height: 50px; } QPushButton:pressed { background-color: #3f51b5; }"
        
        btn_minus_50 = QPushButton("-50")
        btn_minus_10 = QPushButton("-10")
        btn_plus_10 = QPushButton("+10")
        btn_plus_50 = QPushButton("+50")
        
        for btn in [btn_minus_50, btn_minus_10, btn_plus_10, btn_plus_50]:
            btn.setStyleSheet(btn_style)
            
        btn_minus_50.clicked.connect(lambda: self.adjust(-50))
        btn_minus_10.clicked.connect(lambda: self.adjust(-10))
        btn_plus_10.clicked.connect(lambda: self.adjust(10))
        btn_plus_50.clicked.connect(lambda: self.adjust(50))
        
        grid.addWidget(btn_minus_50, 0, 0)
        grid.addWidget(btn_minus_10, 0, 1)
        grid.addWidget(btn_plus_10, 0, 2)
        grid.addWidget(btn_plus_50, 0, 3)
        layout.addLayout(grid)
        
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("✔ ACEPTAR")
        btn_cancel = QPushButton("✖ CANCELAR")
        btn_ok.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; font-size: 18px; min-height: 50px; border-radius: 8px;} QPushButton:pressed { background-color: #388E3C; }")
        btn_cancel.setStyleSheet("QPushButton { background-color: #F44336; color: white; font-weight: bold; font-size: 18px; min-height: 50px; border-radius: 8px;} QPushButton:pressed { background-color: #D32F2F; }")
        
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)
        
    def adjust(self, amount):
        self.val = max(0.0, self.val + amount)
        self.lbl_val.setText(f"{self.val:.1f} mm")

    def get_value(self):
        return self.val


class JogControlWidget(QWidget):
    """Panel para control manual de XYZ y configuración de Z0."""
    
    z0_set = Signal()
    homed_all = Signal()

    def __init__(self, printer, parent=None):
        super().__init__(parent)
        self.printer = printer
        self.setFixedWidth(130)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # Título
        lbl_titulo = QLabel("MOVIMIENTO")
        lbl_titulo.setFont(QFont("Purisa", 11, QFont.Bold))
        lbl_titulo.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(lbl_titulo)

        # Paso (Step size)
        self.combo_paso = QComboBox()
        self.combo_paso.addItems(["0.1 mm", "1.0 mm", "10.0 mm"])
        self.combo_paso.setCurrentIndex(1) # Default 1.0 mm
        self.combo_paso.setFont(QFont("Purisa", 10))
        self.combo_paso.setStyleSheet("""
            QComboBox { 
                padding: 4px; 
                border-radius: 4px; 
                background-color: #3c3c3c; 
                color: white; 
                border: 1px solid #555;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3c3c;
                color: white;
                selection-background-color: #5C6BC0;
            }
        """)
        main_layout.addWidget(self.combo_paso)

        # Grilla para XY
        grid_xy = QGridLayout()
        grid_xy.setSpacing(5)
        
        self.btn_y_plus = QPushButton("Y+")
        self.btn_y_plus.setFixedSize(40, 40)
        self.btn_y_plus.setStyleSheet(BTN_JOG_STYLE)
        self.btn_y_plus.clicked.connect(lambda: self._jog("Y", 1))

        self.btn_y_minus = QPushButton("Y-")
        self.btn_y_minus.setFixedSize(40, 40)
        self.btn_y_minus.setStyleSheet(BTN_JOG_STYLE)
        self.btn_y_minus.clicked.connect(lambda: self._jog("Y", -1))

        self.btn_x_plus = QPushButton("X+")
        self.btn_x_plus.setFixedSize(40, 40)
        self.btn_x_plus.setStyleSheet(BTN_JOG_STYLE)
        self.btn_x_plus.clicked.connect(lambda: self._jog("X", 1))

        self.btn_x_minus = QPushButton("X-")
        self.btn_x_minus.setFixedSize(40, 40)
        self.btn_x_minus.setStyleSheet(BTN_JOG_STYLE)
        self.btn_x_minus.clicked.connect(lambda: self._jog("X", -1))

        self.btn_home = QPushButton("🏠")
        self.btn_home.setFixedSize(40, 40)
        self.btn_home.setStyleSheet(BTN_JOG_STYLE)
        self.btn_home.clicked.connect(self._home_all)

        grid_xy.addWidget(self.btn_y_plus, 0, 1)
        grid_xy.addWidget(self.btn_x_minus, 1, 0)
        grid_xy.addWidget(self.btn_home, 1, 1)
        grid_xy.addWidget(self.btn_x_plus, 1, 2)
        grid_xy.addWidget(self.btn_y_minus, 2, 1)
        main_layout.addLayout(grid_xy)

        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        # Grilla para Z
        layout_z = QVBoxLayout()
        layout_z.setSpacing(5)
        
        lbl_z = QLabel("EJE Z")
        lbl_z.setFont(QFont("Purisa", 10, QFont.Bold))
        lbl_z.setAlignment(Qt.AlignCenter)
        layout_z.addWidget(lbl_z)

        self.btn_z_plus = QPushButton("Z+ (Subir)")
        self.btn_z_plus.setFixedHeight(35)
        self.btn_z_plus.setStyleSheet(BTN_JOG_STYLE)
        self.btn_z_plus.clicked.connect(lambda: self._jog("Z", 1))
        layout_z.addWidget(self.btn_z_plus)

        self.btn_z_minus = QPushButton("Z- (Bajar)")
        self.btn_z_minus.setFixedHeight(35)
        self.btn_z_minus.setStyleSheet(BTN_JOG_STYLE)
        self.btn_z_minus.clicked.connect(lambda: self._jog("Z", -1))
        layout_z.addWidget(self.btn_z_minus)

        main_layout.addLayout(layout_z)

        # Separador
        line_e = QFrame()
        line_e.setFrameShape(QFrame.HLine)
        line_e.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line_e)

        # Grilla para E
        layout_e = QVBoxLayout()
        layout_e.setSpacing(5)
        
        lbl_e = QLabel("EXTRUSOR")
        lbl_e.setFont(QFont("Purisa", 10, QFont.Bold))
        lbl_e.setAlignment(Qt.AlignCenter)
        layout_e.addWidget(lbl_e)

        self.btn_e_plus = QPushButton("E+ (Extruir)")
        self.btn_e_plus.setFixedHeight(35)
        self.btn_e_plus.setStyleSheet(BTN_JOG_STYLE)
        self.btn_e_plus.clicked.connect(lambda: self._jog_e(1))
        layout_e.addWidget(self.btn_e_plus)

        self.btn_e_minus = QPushButton("E- (Retraer)")
        self.btn_e_minus.setFixedHeight(35)
        self.btn_e_minus.setStyleSheet(BTN_JOG_STYLE)
        self.btn_e_minus.clicked.connect(lambda: self._jog_e(-1))
        layout_e.addWidget(self.btn_e_minus)

        main_layout.addLayout(layout_e)

        main_layout.addStretch()

        # Botón Set Z0
        self.btn_set_z0 = QPushButton("📍\nSETEAR CIMA\n(Z=0)")
        self.btn_set_z0.setFixedHeight(70)
        self.btn_set_z0.setStyleSheet(BTN_Z0_STYLE)
        self.btn_set_z0.clicked.connect(self._set_z0)
        main_layout.addWidget(self.btn_set_z0)

    def _get_step(self):
        txt = self.combo_paso.currentText()
        return float(txt.split()[0])

    def _jog(self, axis, direction):
        """Mueve el eje indicado usando posicionamiento relativo."""
        if not self.printer.is_connected:
            QMessageBox.warning(self, "Sin conexión", "La impresora no está conectada.")
            return

        step = self._get_step() * direction
        feedrate = 3000 if axis in ["X", "Y"] else 300

        # G91 = relativo, G0 X/Y/Z = mover, G90 = absoluto
        cmds = [
            "G91",
            f"G0 {axis}{step:.1f} F{feedrate}",
            "G90"
        ]
        
        for cmd in cmds:
            self.printer.send_command(cmd)

    def _jog_e(self, direction):
        """Mueve el extrusor (E) permitiendo la extrusión en frío."""
        if not self.printer.is_connected:
            QMessageBox.warning(self, "Sin conexión", "La impresora no está conectada.")
            return

        step = self._get_step() * direction
        feedrate = 600

        cmds = [
            "M302 P1", # Permitir extrusión en frío
            "G91",
            f"G1 E{step:.1f} F{feedrate}",
            "G90"
        ]
        
        for cmd in cmds:
            self.printer.send_command(cmd)

    def _home_all(self):
        """Secuencia: Home -> Retracción -> Ir al Centro."""
        if not self.printer.is_connected:
            QMessageBox.warning(self, "Sin conexión", "La impresora no está conectada.")
            return
            
        from backend.config import PrinterConfig as PC
        
        # Mostrar el diálogo táctil en lugar de QInputDialog
        dialog = RetractionDialog(self, default_val=PC.RETRACCION_MM)
        if dialog.exec():
            distancia = dialog.get_value()
            lineas_gcode = ["G28"]
            
            if distancia > 0:
                lineas_gcode.append("M302 P1 ; Permitir extrusión en frío")
                lineas_gcode.append("G91")
                
                # Segmentar en bloques de 10mm
                restante = distancia
                while restante > 0:
                    paso = min(10.0, restante)
                    lineas_gcode.append(f"G1 E-{paso:.4f} F{PC.VEL_RETRACCION}")
                    restante -= paso
                    
                lineas_gcode.append("G90")
                
            lineas_gcode.append(f"G0 X{PC.ALFAJOR_CENTRO_X:.1f} Y{PC.ALFAJOR_CENTRO_Y:.1f} F3000")
            
            self.printer.send_gcode("\n".join(lineas_gcode))
            self.homed_all.emit()

    def _set_z0(self):
        """Establece la posición Z actual como Z=0."""
        if not self.printer.is_connected:
            QMessageBox.warning(self, "Sin conexión", "La impresora no está conectada.")
            return
            
        respuesta = QMessageBox.question(
            self, "Setear Cima", 
            "¿Establecer la altura actual como la cima del material (Z=0)?\nLa impresora considerará este punto como el inicio del eje Z.",
            QMessageBox.Yes | QMessageBox.No
        )
        if respuesta == QMessageBox.Yes:
            self.printer.send_command("G92 Z0")
            self.z0_set.emit()
            QMessageBox.information(self, "Cima Establecida", "El punto actual se ha fijado como Z=0.")

    def get_animable_buttons(self):
        """Retorna la lista de botones a los que se les puede aplicar animación de pulso."""
        return [
            self.btn_y_plus, self.btn_y_minus, 
            self.btn_x_plus, self.btn_x_minus,
            self.btn_home, self.btn_z_plus, self.btn_z_minus,
            self.btn_e_plus, self.btn_e_minus,
            self.btn_set_z0
        ]
