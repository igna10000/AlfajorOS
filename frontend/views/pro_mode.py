#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modo PRO - Proyecto de Grado
Ventana avanzada con controles profesionales para la extrusora de crema.
Incluye control de temperatura, presion, velocidad, patrones y G-code.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QSlider, QSpinBox, QDoubleSpinBox,
    QComboBox, QGroupBox, QProgressBar, QTextEdit, QTabWidget,
    QCheckBox, QFrame, QMessageBox, QStatusBar, QDial
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor
from frontend.widgets.virtual_keyboard import VirtualKeyboard


class ProModeWindow(QMainWindow):
    """Ventana de Modo PRO con controles avanzados."""

    volver_basico = Signal()
    actividad_detectada = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Modo PRO - Extrusora de Crema")
        self.setMinimumSize(1024, 600)
        self.setMaximumSize(1024, 600)

        self._setup_ui()
        self._aplicar_estilo()

        # Timer para actualización en tiempo real
        self.timer_monitor = QTimer(self)
        self.timer_monitor.timeout.connect(self._actualizar_monitor)

    def _setup_ui(self):
        """Configura la interfaz del modo PRO."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # === Barra superior ===
        barra_sup = QHBoxLayout()

        btn_volver = QPushButton("← Volver a Modo Básico")
        btn_volver.setMinimumHeight(40)
        btn_volver.setFont(QFont("Purisa", 10, QFont.Bold))
        btn_volver.clicked.connect(self._on_volver)
        barra_sup.addWidget(btn_volver)

        lbl_titulo = QLabel("⚡ MODO PRO")
        lbl_titulo.setAlignment(Qt.AlignCenter)
        lbl_titulo.setFont(QFont("Purisa", 16, QFont.Bold))
        lbl_titulo.setStyleSheet("color: #FFAB40;")
        barra_sup.addWidget(lbl_titulo)

        self.lbl_estado = QLabel("● LISTO")
        self.lbl_estado.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_estado.setFont(QFont("", 11, QFont.Bold))
        self.lbl_estado.setStyleSheet("color: #4DB6AC;")
        barra_sup.addWidget(self.lbl_estado)

        layout.addLayout(barra_sup)

        # === Tabs ===
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Purisa", 10))

        # Tab 1: Control de Extrusion
        self.tabs.addTab(self._crear_tab_impresion(), "Extrusion")
        # Tab 2: Configuracion de Crema
        self.tabs.addTab(self._crear_tab_configuracion(), "Crema")
        # Tab 3: Monitor
        self.tabs.addTab(self._crear_tab_monitor(), "Monitor")
        # Tab 4: G-Code
        self.tabs.addTab(self._crear_tab_gcode(), "G-Code")

        layout.addWidget(self.tabs)

        # === Status Bar ===
        self.statusBar().showMessage("Modo PRO activado. Todos los controles habilitados.")

    def _crear_tab_impresion(self):
        """Tab de control de extrusion de crema."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # -- Temperatura de crema --
        grp_temp = QGroupBox("Temperatura de Crema")
        grp_temp.setFont(QFont("Purisa", 10, QFont.Bold))
        grid_temp = QGridLayout(grp_temp)

        grid_temp.addWidget(QLabel("Temp. crema (C):"), 0, 0)
        self.spin_temp_extrusor = QSpinBox()
        self.spin_temp_extrusor.setRange(5, 45)
        self.spin_temp_extrusor.setValue(18)
        self.spin_temp_extrusor.setSuffix(" C")
        grid_temp.addWidget(self.spin_temp_extrusor, 0, 1)

        self.pb_temp_extrusor = QProgressBar()
        self.pb_temp_extrusor.setRange(5, 45)
        self.pb_temp_extrusor.setValue(5)
        self.pb_temp_extrusor.setFormat("%v C")
        grid_temp.addWidget(self.pb_temp_extrusor, 0, 2)

        grid_temp.addWidget(QLabel("Temp. base (C):"), 1, 0)
        self.spin_temp_cama = QSpinBox()
        self.spin_temp_cama.setRange(5, 30)
        self.spin_temp_cama.setValue(15)
        self.spin_temp_cama.setSuffix(" C")
        grid_temp.addWidget(self.spin_temp_cama, 1, 1)

        self.pb_temp_cama = QProgressBar()
        self.pb_temp_cama.setRange(5, 30)
        self.pb_temp_cama.setValue(5)
        self.pb_temp_cama.setFormat("%v C")
        grid_temp.addWidget(self.pb_temp_cama, 1, 2)

        btn_calentar = QPushButton("Estabilizar Temperatura")
        btn_calentar.clicked.connect(self._on_calentar)
        grid_temp.addWidget(btn_calentar, 2, 0, 1, 3)

        layout.addWidget(grp_temp)

        # -- Velocidad y Presion --
        grp_vel = QGroupBox("Velocidad y Presion de Extrusion")
        grp_vel.setFont(QFont("Purisa", 10, QFont.Bold))
        grid_vel = QGridLayout(grp_vel)

        grid_vel.addWidget(QLabel("Velocidad (mm/s):"), 0, 0)
        self.slider_velocidad = QSlider(Qt.Horizontal)
        self.slider_velocidad.setRange(5, 80)
        self.slider_velocidad.setValue(25)
        self.lbl_velocidad = QLabel("25 mm/s")
        self.slider_velocidad.valueChanged.connect(
            lambda v: self.lbl_velocidad.setText(f"{v} mm/s"))
        grid_vel.addWidget(self.slider_velocidad, 0, 1)
        grid_vel.addWidget(self.lbl_velocidad, 0, 2)

        grid_vel.addWidget(QLabel("Grosor de linea (mm):"), 1, 0)
        self.spin_capa = QDoubleSpinBox()
        self.spin_capa.setRange(0.5, 5.0)
        self.spin_capa.setValue(2.0)
        self.spin_capa.setSingleStep(0.5)
        self.spin_capa.setSuffix(" mm")
        grid_vel.addWidget(self.spin_capa, 1, 1)

        grid_vel.addWidget(QLabel("Presion (%):"), 2, 0)
        self.dial_relleno = QDial()
        self.dial_relleno.setRange(10, 100)
        self.dial_relleno.setValue(60)
        self.dial_relleno.setNotchesVisible(True)
        self.dial_relleno.setMaximumSize(80, 80)
        self.lbl_relleno = QLabel("60%")
        self.dial_relleno.valueChanged.connect(
            lambda v: self.lbl_relleno.setText(f"{v}%"))
        grid_vel.addWidget(self.dial_relleno, 2, 1)
        grid_vel.addWidget(self.lbl_relleno, 2, 2)

        layout.addWidget(grp_vel)

        # -- Botones de acción --
        h_botones = QHBoxLayout()

        btn_inicio = QPushButton("▶️ INICIAR PRO")
        btn_inicio.setMinimumHeight(45)
        btn_inicio.setFont(QFont("Purisa", 11, QFont.Bold))
        btn_inicio.setStyleSheet("background-color: #4DB6AC; color: white;")
        btn_inicio.clicked.connect(self._on_iniciar_pro)
        h_botones.addWidget(btn_inicio)

        btn_pausa = QPushButton("⏸️ PAUSAR")
        btn_pausa.setMinimumHeight(45)
        btn_pausa.setFont(QFont("Purisa", 11, QFont.Bold))
        btn_pausa.setStyleSheet("background-color: #FFAB40; color: white;")
        h_botones.addWidget(btn_pausa)

        btn_cancelar = QPushButton("⏹️ CANCELAR")
        btn_cancelar.setMinimumHeight(45)
        btn_cancelar.setFont(QFont("Purisa", 11, QFont.Bold))
        btn_cancelar.setStyleSheet("background-color: #F66151; color: white;")
        h_botones.addWidget(btn_cancelar)

        layout.addLayout(h_botones)

        return widget

    def _crear_tab_configuracion(self):
        """Tab de configuracion de crema."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Tipo de crema
        grp_material = QGroupBox("Tipo de Crema")
        grp_material.setFont(QFont("Purisa", 10, QFont.Bold))
        grid_mat = QGridLayout(grp_material)

        grid_mat.addWidget(QLabel("Crema:"), 0, 0)
        self.combo_material = QComboBox()
        self.combo_material.addItems([
            "Dulce de Leche", "Chocolate", "Vainilla",
            "Crema Chantilly", "Merengue", "Ganache"
        ])
        grid_mat.addWidget(self.combo_material, 0, 1)

        grid_mat.addWidget(QLabel("Boquilla (mm):"), 1, 0)
        spin_diam = QDoubleSpinBox()
        spin_diam.setRange(1.0, 10.0)
        spin_diam.setValue(3.0)
        spin_diam.setSingleStep(0.5)
        spin_diam.setSuffix(" mm")
        grid_mat.addWidget(spin_diam, 1, 1)

        grid_mat.addWidget(QLabel("Consistencia:"), 2, 0)
        combo_consistencia = QComboBox()
        combo_consistencia.addItems([
            "Firme", "Media", "Suave", "Muy suave"
        ])
        combo_consistencia.setCurrentIndex(1)
        grid_mat.addWidget(combo_consistencia, 2, 1)

        layout.addWidget(grp_material)

        # Opciones de extrusion
        grp_avanzado = QGroupBox("Opciones de Extrusion")
        grp_avanzado.setFont(QFont("Purisa", 10, QFont.Bold))
        grid_av = QGridLayout(grp_avanzado)

        self.chk_soportes = QCheckBox("Retraccion al mover")
        self.chk_soportes.setChecked(True)
        grid_av.addWidget(self.chk_soportes, 0, 0)

        self.chk_balsa = QCheckBox("Purga inicial")
        self.chk_balsa.setChecked(True)
        grid_av.addWidget(self.chk_balsa, 0, 1)

        self.chk_brim = QCheckBox("Repetir patron")
        grid_av.addWidget(self.chk_brim, 1, 0)

        self.chk_retraccion = QCheckBox("Limpieza auto al final")
        self.chk_retraccion.setChecked(True)
        grid_av.addWidget(self.chk_retraccion, 1, 1)

        self.chk_ventilador = QCheckBox("Centrar en alfajor")
        self.chk_ventilador.setChecked(True)
        grid_av.addWidget(self.chk_ventilador, 2, 0)

        self.chk_ironing = QCheckBox("Doble pasada")
        grid_av.addWidget(self.chk_ironing, 2, 1)

        grid_av.addWidget(QLabel("Patron de decorado:"), 3, 0)
        combo_patron = QComboBox()
        combo_patron.addItems([
            "Espiral", "Zigzag", "Circulos", "Lineas",
            "Rejilla", "Libre"
        ])
        combo_patron.setCurrentIndex(0)
        grid_av.addWidget(combo_patron, 3, 1)

        layout.addWidget(grp_avanzado)

        # Dimensiones del alfajor
        grp_dim = QGroupBox("Dimensiones del Alfajor")
        grp_dim.setFont(QFont("Purisa", 10, QFont.Bold))
        grid_dim = QGridLayout(grp_dim)

        grid_dim.addWidget(QLabel("Diametro (cm):"), 0, 0)
        spin_diam_alf = QDoubleSpinBox()
        spin_diam_alf.setRange(3.0, 15.0)
        spin_diam_alf.setValue(7.0)
        spin_diam_alf.setSingleStep(0.5)
        spin_diam_alf.setSuffix(" cm")
        grid_dim.addWidget(spin_diam_alf, 0, 1)

        grid_dim.addWidget(QLabel("Altura crema (mm):"), 1, 0)
        spin_alt = QDoubleSpinBox()
        spin_alt.setRange(1.0, 15.0)
        spin_alt.setValue(5.0)
        spin_alt.setSingleStep(0.5)
        spin_alt.setSuffix(" mm")
        grid_dim.addWidget(spin_alt, 1, 1)

        grid_dim.addWidget(QLabel("Margen borde (mm):"), 2, 0)
        spin_margen = QDoubleSpinBox()
        spin_margen.setRange(0.0, 10.0)
        spin_margen.setValue(3.0)
        spin_margen.setSingleStep(0.5)
        spin_margen.setSuffix(" mm")
        grid_dim.addWidget(spin_margen, 2, 1)

        layout.addWidget(grp_dim)

        return widget

    def _crear_tab_monitor(self):
        """Tab de monitoreo en tiempo real."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info del sistema
        grp_info = QGroupBox("📊 Estado del Sistema")
        grp_info.setFont(QFont("Purisa", 10, QFont.Bold))
        grid = QGridLayout(grp_info)

        labels_info = [
            ("Temp. Crema:", "-- C"),
            ("Temp. Base:", "-- C"),
            ("Velocidad actual:", "0 mm/s"),
            ("Presion extrusor:", "0%"),
            ("Tiempo transcurrido:", "00:00:00"),
            ("Tiempo estimado:", "--:--:--"),
            ("Progreso:", "0%"),
        ]

        self.monitor_labels = {}
        for i, (nombre, valor) in enumerate(labels_info):
            lbl_nombre = QLabel(nombre)
            lbl_nombre.setFont(QFont("", 10, QFont.Bold))
            grid.addWidget(lbl_nombre, i, 0)

            lbl_valor = QLabel(valor)
            lbl_valor.setFont(QFont("", 10))
            lbl_valor.setStyleSheet("color: #4DB6AC;")
            grid.addWidget(lbl_valor, i, 1)
            self.monitor_labels[nombre] = lbl_valor

        layout.addWidget(grp_info)

        # Barra de progreso general
        self.pb_general = QProgressBar()
        self.pb_general.setMinimumHeight(30)
        self.pb_general.setFormat("Progreso general: %p%")
        layout.addWidget(self.pb_general)

        # Log
        grp_log = QGroupBox("📋 Log de Eventos")
        grp_log.setFont(QFont("Purisa", 10, QFont.Bold))
        v_log = QVBoxLayout(grp_log)
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumHeight(150)
        self.txt_log.setFont(QFont("Monospace", 9))
        self.txt_log.setStyleSheet(
            "background-color: #1e1e1e; color: #4DB6AC; border: 1px solid #555;")
        self.txt_log.append("[SISTEMA] Modo PRO inicializado")
        self.txt_log.append("[SISTEMA] Esperando configuración...")
        v_log.addWidget(self.txt_log)
        layout.addWidget(grp_log)

        return widget

    def _crear_tab_gcode(self):
        """Tab para editar/ver G-Code."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        lbl = QLabel("📝 Editor de G-Code Manual")
        lbl.setFont(QFont("Purisa", 12, QFont.Bold))
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)

        self.txt_gcode = QTextEdit()
        self.txt_gcode.setFont(QFont("Monospace", 10))
        self.txt_gcode.setStyleSheet(
            "background-color: #1e1e1e; color: #00ff00; border: 1px solid #555;")
        from backend.config import PrinterConfig as PC
        self.txt_gcode.setPlainText(
            "; === G-Code Extrusora de Crema ===\n"
            "; Proyecto de Grado - Alfajores\n"
            ";\n"
            "G28          ; Home todos los ejes\n"
            "G1 Z10 F1000 ; Subir boquilla\n"
            "M104 S18     ; Temp crema 18C\n"
            "M109 S18     ; Esperar temp crema\n"
            "G92 E0       ; Reset extrusor\n"
            ";\n"
            "; === Purga inicial ===\n"
            f"G1 X{PC.PURGA_POS_X} Y{PC.PURGA_POS_Y} Z{PC.PURGA_POS_Z} F1500\n"
            "G1 E5 F300   ; Purgar crema\n"
            "G92 E0       ; Reset extrusor\n"
            ";\n"
            "; === Patron espiral sobre alfajor ===\n"
            "G1 Z2 F500   ; Bajar a altura de crema\n"
            f"G1 X{PC.ALFAJOR_CENTRO_X} Y{PC.ALFAJOR_CENTRO_Y} F1000 ; Centro del alfajor\n"
            "G2 X45 Y35 I5 J0 E3 F600 ; Espiral 1\n"
            "G2 X55 Y35 I5 J0 E6 F600 ; Espiral 2\n"
            "G2 X25 Y35 I-15 J0 E12 F600 ; Espiral 3\n"
            ";\n"
            "; === Fin ===\n"
            "G1 E-2 F500  ; Retraccion crema\n"
            "G1 Z20 F1000 ; Subir boquilla\n"
            "G28 X Y      ; Home XY\n"
        )
        layout.addWidget(self.txt_gcode)

        h_btn = QHBoxLayout()

        btn_enviar = QPushButton("📤 Enviar G-Code")
        btn_enviar.setMinimumHeight(40)
        btn_enviar.setFont(QFont("Purisa", 10, QFont.Bold))
        btn_enviar.clicked.connect(lambda: self._log("G-Code enviado a la impresora"))
        h_btn.addWidget(btn_enviar)

        btn_limpiar = QPushButton("🗑️ Limpiar")
        btn_limpiar.setMinimumHeight(40)
        btn_limpiar.clicked.connect(self.txt_gcode.clear)
        h_btn.addWidget(btn_limpiar)

        btn_ejemplo = QPushButton("📄 Cargar Ejemplo")
        btn_ejemplo.setMinimumHeight(40)
        h_btn.addWidget(btn_ejemplo)

        layout.addLayout(h_btn)

        # Teclado virtual para G-Code
        self.keyboard_gcode = VirtualKeyboard()
        self.keyboard_gcode.set_target(self.txt_gcode)
        layout.addWidget(self.keyboard_gcode)

        return widget

    def _aplicar_estilo(self):
        """Aplica estilos al modo PRO."""
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            QGroupBox {
                border: 2px solid #4DB6AC;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                color: #FFAB40;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 8px 15px;
                color: #e0e0e0;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #4DB6AC;
            }
            QPushButton:pressed {
                background-color: #4DB6AC;
            }
            QComboBox {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 8px;
                color: #e0e0e0;
                min-height: 30px;
                font-size: 13px;
            }
            QSpinBox, QDoubleSpinBox {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 8px;
                color: #e0e0e0;
                min-height: 30px;
                font-size: 13px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border-color: #4DB6AC;
            }
            QSlider::groove:horizontal {
                height: 12px;
                background: #3c3c3c;
                border-radius: 6px;
            }
            QSlider::handle:horizontal {
                background: #4DB6AC;
                width: 28px;
                margin: -8px 0;
                border-radius: 14px;
            }
            QSlider::sub-page:horizontal {
                background: #4DB6AC;
                border-radius: 6px;
            }
            QProgressBar {
                border: 1px solid #555;
                border-radius: 5px;
                text-align: center;
                background-color: #3c3c3c;
                color: #e0e0e0;
            }
            QProgressBar::chunk {
                background-color: #4DB6AC;
                border-radius: 4px;
            }
            QTabWidget::pane {
                border: 1px solid #555;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #e0e0e0;
                padding: 8px 20px;
                border: 1px solid #555;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #4DB6AC;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #4a4a4a;
            }
            QCheckBox {
                spacing: 10px;
                color: #e0e0e0;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 24px;
                height: 24px;
            }
        """)

    def _on_volver(self):
        """Vuelve al modo básico."""
        self.actividad_detectada.emit()
        self.volver_basico.emit()
        self.hide()

    def _on_calentar(self):
        """Simula la estabilizacion de temperatura."""
        self.actividad_detectada.emit()
        self._log(f"Estabilizando crema a {self.spin_temp_extrusor.value()}C...")
        self._log(f"Estabilizando base a {self.spin_temp_cama.value()}C...")
        self.timer_monitor.start(500)

    def _on_iniciar_pro(self):
        """Inicia extrusion en modo pro."""
        self.actividad_detectada.emit()
        vel = self.slider_velocidad.value()
        grosor = self.spin_capa.value()
        crema = self.combo_material.currentText()
        presion = self.dial_relleno.value()

        self._log(f"=== INICIO EXTRUSION PRO ===")
        self._log(f"Crema: {crema}")
        self._log(f"Velocidad: {vel} mm/s")
        self._log(f"Grosor de linea: {grosor} mm")
        self._log(f"Presion: {presion}%")

        QMessageBox.information(
            self, "Extrusion PRO",
            f"Configuracion:\n"
            f"  Crema: {crema}\n"
            f"  Velocidad: {vel} mm/s\n"
            f"  Grosor de linea: {grosor} mm\n"
            f"  Presion: {presion}%\n\n"
            f"Extrusion PRO iniciada!"
        )

    def _actualizar_monitor(self):
        """Actualiza los valores del monitor (simulación)."""
        import random
        temp_ext = min(self.spin_temp_extrusor.value(),
                       self.pb_temp_extrusor.value() + random.randint(1, 5))
        temp_cama = min(self.spin_temp_cama.value(),
                        self.pb_temp_cama.value() + random.randint(1, 3))

        self.pb_temp_extrusor.setValue(temp_ext)
        self.pb_temp_cama.setValue(temp_cama)

        self.monitor_labels["Temp. Crema:"].setText(f"{temp_ext} C")
        self.monitor_labels["Temp. Base:"].setText(f"{temp_cama} C")

        if (temp_ext >= self.spin_temp_extrusor.value() and
                temp_cama >= self.spin_temp_cama.value()):
            self.timer_monitor.stop()
            self._log("Temperaturas estabilizadas. Listo para extruir.")
            self.lbl_estado.setText("LISTO")
            self.lbl_estado.setStyleSheet("color: #4DB6AC;")

    def _log(self, mensaje):
        """Añade un mensaje al log."""
        from datetime import datetime
        hora = datetime.now().strftime("%H:%M:%S")
        self.txt_log.append(f"[{hora}] {mensaje}")

    def showEvent(self, event):
        self.actividad_detectada.emit()
        super().showEvent(event)

    def mousePressEvent(self, event):
        self.actividad_detectada.emit()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        self.actividad_detectada.emit()
        super().keyPressEvent(event)
