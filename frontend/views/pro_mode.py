#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modo PRO - Proyecto de Grado
Ventana avanzada con controles profesionales para la extrusora de crema.
Parametros cargados y guardados desde printer_config.yaml.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QDoubleSpinBox, QSpinBox,
    QGroupBox, QProgressBar, QTextEdit, QTabWidget,
    QFrame, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from frontend.widgets.virtual_keyboard import VirtualKeyboard
from backend.config import PrinterConfig as PC


class ProModeWindow(QMainWindow):
    """Ventana de Modo PRO con controles del printer_config.yaml."""

    volver_basico = Signal()
    actividad_detectada = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Modo PRO - Extrusora de Crema")
        self.setMinimumSize(1024, 600)
        self.setMaximumSize(1024, 600)

        self._spinboxes = {}  # key -> widget mapping for save/load
        self._setup_ui()
        self._aplicar_estilo()
        self._cargar_valores()

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

        self.tabs.addTab(self._crear_tab_alfajor(), "Alfajor")
        self.tabs.addTab(self._crear_tab_impresion(), "Impresión")
        self.tabs.addTab(self._crear_tab_extrusor(), "Extrusor")
        self.tabs.addTab(self._crear_tab_viaje_linea(), "Viaje/Línea")
        self.tabs.addTab(self._crear_tab_monitor(), "Monitor")
        self.tabs.addTab(self._crear_tab_gcode(), "G-Code")

        layout.addWidget(self.tabs)

        # === Barra inferior: Guardar / Restaurar ===
        h_bottom = QHBoxLayout()

        btn_restaurar = QPushButton("↺ RESTAURAR VALORES")
        btn_restaurar.setMinimumHeight(45)
        btn_restaurar.setFont(QFont("Purisa", 11, QFont.Bold))
        btn_restaurar.setStyleSheet("background-color: #7E57C2; color: white;")
        btn_restaurar.clicked.connect(self._on_restaurar)
        h_bottom.addWidget(btn_restaurar)

        btn_guardar = QPushButton("💾 GUARDAR CONFIG")
        btn_guardar.setMinimumHeight(45)
        btn_guardar.setFont(QFont("Purisa", 11, QFont.Bold))
        btn_guardar.setStyleSheet("background-color: #4DB6AC; color: white;")
        btn_guardar.clicked.connect(self._on_guardar)
        h_bottom.addWidget(btn_guardar)

        layout.addLayout(h_bottom)

        # === Status Bar ===
        self.statusBar().showMessage("Modo PRO activado. Parámetros cargados de printer_config.yaml")

    # ================================================================
    # Helper para crear spinboxes registrados
    # ================================================================

    def _add_double_spin(self, grid, row, label, key, vmin, vmax, step, suffix, decimals=1):
        """Crea un QDoubleSpinBox registrado en self._spinboxes."""
        grid.addWidget(QLabel(label), row, 0)
        spin = QDoubleSpinBox()
        spin.setRange(vmin, vmax)
        spin.setSingleStep(step)
        spin.setSuffix(suffix)
        spin.setDecimals(decimals)
        grid.addWidget(spin, row, 1)
        self._spinboxes[key] = spin
        return spin

    def _add_int_spin(self, grid, row, label, key, vmin, vmax, step, suffix):
        """Crea un QSpinBox registrado en self._spinboxes."""
        grid.addWidget(QLabel(label), row, 0)
        spin = QSpinBox()
        spin.setRange(vmin, vmax)
        spin.setSingleStep(step)
        spin.setSuffix(suffix)
        grid.addWidget(spin, row, 1)
        self._spinboxes[key] = spin
        return spin

    # ================================================================
    # Tabs de configuración
    # ================================================================

    def _crear_tab_alfajor(self):
        """Tab: Parámetros del alfajor."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        grp = QGroupBox("Dimensiones del Alfajor")
        grp.setFont(QFont("Purisa", 10, QFont.Bold))
        grid = QGridLayout(grp)

        self._add_double_spin(grid, 0, "Diámetro (mm):", "alfajor_diametro",
                              20.0, 200.0, 1.0, " mm")
        self._add_double_spin(grid, 1, "Margen borde (mm):", "alfajor_margen",
                              0.0, 20.0, 0.5, " mm")
        self._add_double_spin(grid, 2, "Centro X (mm):", "alfajor_centro_x",
                              0.0, 300.0, 1.0, " mm")
        self._add_double_spin(grid, 3, "Centro Y (mm):", "alfajor_centro_y",
                              0.0, 300.0, 1.0, " mm")

        # Info calculada
        self.lbl_radio = QLabel("")
        self.lbl_radio.setStyleSheet("color: #4DB6AC; font-weight: bold;")
        grid.addWidget(QLabel("Radio útil:"), 4, 0)
        grid.addWidget(self.lbl_radio, 4, 1)

        # Conectar para actualizar radio en tiempo real
        self._spinboxes["alfajor_diametro"].valueChanged.connect(self._actualizar_radio_label)
        self._spinboxes["alfajor_margen"].valueChanged.connect(self._actualizar_radio_label)

        layout.addWidget(grp)
        layout.addStretch(1)
        return widget

    def _crear_tab_impresion(self):
        """Tab: Velocidades y altura de impresión."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        grp = QGroupBox("Parámetros de Impresión")
        grp.setFont(QFont("Purisa", 10, QFont.Bold))
        grid = QGridLayout(grp)

        self._add_double_spin(grid, 0, "Altura Z (mm):", "z_altura",
                              0.0, 20.0, 0.1, " mm")
        self._add_double_spin(grid, 1, "Offset Z (mm):", "z_offset",
                              -50.0, 50.0, 0.5, " mm")
        self._add_int_spin(grid, 2, "Vel. impresión (mm/min):", "vel_impresion",
                           100, 5000, 50, " mm/min")
        self._add_int_spin(grid, 3, "Vel. viaje (mm/min):", "vel_viaje",
                           500, 10000, 100, " mm/min")
        self._add_int_spin(grid, 4, "Vel. Z (mm/min):", "vel_z",
                           100, 3000, 50, " mm/min")
        self._add_int_spin(grid, 5, "Vel. primera capa (mm/min):", "vel_primera_capa",
                           100, 5000, 50, " mm/min")

        layout.addWidget(grp)
        layout.addStretch(1)
        return widget

    def _crear_tab_extrusor(self):
        """Tab: Extrusor, retracción y purga."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Extrusor
        grp1 = QGroupBox("Extrusor")
        grp1.setFont(QFont("Purisa", 10, QFont.Bold))
        grid1 = QGridLayout(grp1)

        self._add_double_spin(grid1, 0, "Boquilla (mm):", "boquilla",
                              0.5, 10.0, 0.1, " mm")
        self._add_double_spin(grid1, 1, "Flujo E/mm:", "flujo",
                              0.01, 5.0, 0.01, " mm/mm", decimals=2)

        layout.addWidget(grp1)

        # Retracción
        grp2 = QGroupBox("Retracción (Jeringa)")
        grp2.setFont(QFont("Purisa", 10, QFont.Bold))
        grid2 = QGridLayout(grp2)

        self._add_double_spin(grid2, 0, "Retracción (mm):", "retraccion",
                              0.0, 200.0, 1.0, " mm")
        self._add_double_spin(grid2, 1, "Desretracción (mm):", "desretraccion",
                              0.0, 200.0, 1.0, " mm")
        self._add_int_spin(grid2, 2, "Vel. retracción (mm/min):", "vel_retraccion",
                           100, 20000, 100, " mm/min")

        layout.addWidget(grp2)

        # Purga
        grp3 = QGroupBox("Purga Inicial")
        grp3.setFont(QFont("Purisa", 10, QFont.Bold))
        grid3 = QGridLayout(grp3)

        self._add_double_spin(grid3, 0, "Purga (mm):", "purga_inicial",
                              0.0, 500.0, 5.0, " mm")
        self._add_double_spin(grid3, 1, "Pos. purga X:", "purga_x",
                              0.0, 300.0, 1.0, " mm")
        self._add_double_spin(grid3, 2, "Pos. purga Y:", "purga_y",
                              0.0, 300.0, 1.0, " mm")
        self._add_double_spin(grid3, 3, "Pos. purga Z:", "purga_z",
                              0.0, 50.0, 0.5, " mm")

        layout.addWidget(grp3)
        return widget

    def _crear_tab_viaje_linea(self):
        """Tab: Viaje y grosor de línea."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        grp1 = QGroupBox("Viaje")
        grp1.setFont(QFont("Purisa", 10, QFont.Bold))
        grid1 = QGridLayout(grp1)

        self._add_double_spin(grid1, 0, "Z-Hop (mm):", "z_hop",
                              0.0, 20.0, 0.5, " mm")
        self._add_double_spin(grid1, 1, "Pos. final X:", "pos_final_x",
                              0.0, 300.0, 1.0, " mm")
        self._add_double_spin(grid1, 2, "Pos. final Y:", "pos_final_y",
                              0.0, 300.0, 1.0, " mm")
        self._add_double_spin(grid1, 3, "Pos. final Z:", "pos_final_z",
                              0.0, 50.0, 1.0, " mm")

        layout.addWidget(grp1)

        grp2 = QGroupBox("Grosor de Línea")
        grp2.setFont(QFont("Purisa", 10, QFont.Bold))
        grid2 = QGridLayout(grp2)

        self._add_double_spin(grid2, 0, "Grosor default (mm):", "grosor_default",
                              0.1, 10.0, 0.1, " mm")
        self._add_double_spin(grid2, 1, "Grosor mínimo (mm):", "grosor_min",
                              0.1, 10.0, 0.1, " mm")
        self._add_double_spin(grid2, 2, "Grosor máximo (mm):", "grosor_max",
                              0.1, 20.0, 0.5, " mm")

        layout.addWidget(grp2)
        layout.addStretch(1)
        return widget

    def _crear_tab_monitor(self):
        """Tab de monitoreo en tiempo real."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        grp_info = QGroupBox("📊 Estado del Sistema")
        grp_info.setFont(QFont("Purisa", 10, QFont.Bold))
        grid = QGridLayout(grp_info)

        labels_info = [
            ("Velocidad actual:", "0 mm/s"),
            ("Progreso:", "0%"),
            ("Tiempo transcurrido:", "00:00:00"),
            ("Tiempo estimado:", "--:--:--"),
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

        self.pb_general = QProgressBar()
        self.pb_general.setMinimumHeight(30)
        self.pb_general.setFormat("Progreso general: %p%")
        layout.addWidget(self.pb_general)

        grp_log = QGroupBox("📋 Log de Eventos")
        grp_log.setFont(QFont("Purisa", 10, QFont.Bold))
        v_log = QVBoxLayout(grp_log)
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumHeight(200)
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
        self.txt_gcode.setPlainText(
            "; === G-Code Extrusora de Crema ===\n"
            "; Proyecto de Grado - Alfajores\n"
            ";\n"
            "G28          ; Home todos los ejes\n"
            "G90          ; Modo absoluto\n"
            "M302 P1      ; Extrusion en frio\n"
            "G92 E0       ; Reset extrusor\n"
            ";\n"
            "; === Escriba su G-Code aqui ===\n"
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

        layout.addLayout(h_btn)

        self.keyboard_gcode = VirtualKeyboard()
        self.keyboard_gcode.set_target(self.txt_gcode)
        layout.addWidget(self.keyboard_gcode)

        return widget

    # ================================================================
    # Cargar / Guardar
    # ================================================================

    def _cargar_valores(self):
        """Carga valores actuales de PrinterConfig en los spinboxes."""
        PC.reload()
        mapping = {
            "alfajor_diametro": PC.ALFAJOR_DIAMETRO_MM,
            "alfajor_margen": PC.ALFAJOR_MARGEN_MM,
            "alfajor_centro_x": PC.ALFAJOR_CENTRO_X,
            "alfajor_centro_y": PC.ALFAJOR_CENTRO_Y,
            "z_altura": PC.Z_ALTURA_MM,
            "z_offset": PC.Z_OFFSET_MM,
            "vel_impresion": PC.VEL_IMPRESION,
            "vel_viaje": PC.VEL_VIAJE,
            "vel_z": PC.VEL_Z,
            "vel_primera_capa": PC.VEL_PRIMERA_CAPA,
            "boquilla": PC.BOQUILLA_MM,
            "flujo": PC.FLUJO_E_POR_MM,
            "retraccion": PC.RETRACCION_MM,
            "desretraccion": PC.DESRETRACCION_MM,
            "vel_retraccion": PC.VEL_RETRACCION,
            "purga_inicial": PC.PURGA_INICIAL_MM,
            "purga_x": PC.PURGA_POS_X,
            "purga_y": PC.PURGA_POS_Y,
            "purga_z": PC.PURGA_POS_Z,
            "z_hop": PC.Z_HOP_MM,
            "pos_final_x": PC.POS_FINAL_X,
            "pos_final_y": PC.POS_FINAL_Y,
            "pos_final_z": PC.POS_FINAL_Z,
            "grosor_default": PC.GROSOR_DEFAULT_MM,
            "grosor_min": PC.GROSOR_MIN_MM,
            "grosor_max": PC.GROSOR_MAX_MM,
        }
        for key, value in mapping.items():
            if key in self._spinboxes:
                self._spinboxes[key].blockSignals(True)
                self._spinboxes[key].setValue(value)
                self._spinboxes[key].blockSignals(False)

        self._actualizar_radio_label()

    def _aplicar_valores_a_config(self):
        """Transfiere valores de los spinboxes a PrinterConfig."""
        PC.ALFAJOR_DIAMETRO_MM = self._spinboxes["alfajor_diametro"].value()
        PC.ALFAJOR_MARGEN_MM = self._spinboxes["alfajor_margen"].value()
        PC.ALFAJOR_CENTRO_X = self._spinboxes["alfajor_centro_x"].value()
        PC.ALFAJOR_CENTRO_Y = self._spinboxes["alfajor_centro_y"].value()
        PC.ALFAJOR_RADIO_MM = (PC.ALFAJOR_DIAMETRO_MM / 2) - PC.ALFAJOR_MARGEN_MM
        PC.Z_ALTURA_MM = self._spinboxes["z_altura"].value()
        PC.Z_OFFSET_MM = self._spinboxes["z_offset"].value()
        PC.VEL_IMPRESION = self._spinboxes["vel_impresion"].value()
        PC.VEL_VIAJE = self._spinboxes["vel_viaje"].value()
        PC.VEL_Z = self._spinboxes["vel_z"].value()
        PC.VEL_PRIMERA_CAPA = self._spinboxes["vel_primera_capa"].value()
        PC.BOQUILLA_MM = self._spinboxes["boquilla"].value()
        PC.FLUJO_E_POR_MM = self._spinboxes["flujo"].value()
        PC.RETRACCION_MM = self._spinboxes["retraccion"].value()
        PC.DESRETRACCION_MM = self._spinboxes["desretraccion"].value()
        PC.VEL_RETRACCION = self._spinboxes["vel_retraccion"].value()
        PC.PURGA_INICIAL_MM = self._spinboxes["purga_inicial"].value()
        PC.PURGA_POS_X = self._spinboxes["purga_x"].value()
        PC.PURGA_POS_Y = self._spinboxes["purga_y"].value()
        PC.PURGA_POS_Z = self._spinboxes["purga_z"].value()
        PC.Z_HOP_MM = self._spinboxes["z_hop"].value()
        PC.POS_FINAL_X = self._spinboxes["pos_final_x"].value()
        PC.POS_FINAL_Y = self._spinboxes["pos_final_y"].value()
        PC.POS_FINAL_Z = self._spinboxes["pos_final_z"].value()
        PC.GROSOR_DEFAULT_MM = self._spinboxes["grosor_default"].value()
        PC.GROSOR_MIN_MM = self._spinboxes["grosor_min"].value()
        PC.GROSOR_MAX_MM = self._spinboxes["grosor_max"].value()

    def _actualizar_radio_label(self):
        """Actualiza el label de radio útil calculado."""
        d = self._spinboxes["alfajor_diametro"].value()
        m = self._spinboxes["alfajor_margen"].value()
        radio = (d / 2) - m
        self.lbl_radio.setText(f"{radio:.1f} mm")

    # ================================================================
    # Handlers
    # ================================================================

    def _on_guardar(self):
        """Guarda la configuración actual al YAML."""
        self.actividad_detectada.emit()
        self._aplicar_valores_a_config()
        try:
            PC.save()
            PC.reload()
            self._log("✅ Configuración guardada en printer_config.yaml")
            self.statusBar().showMessage("Configuración guardada correctamente.")
            QMessageBox.information(
                self, "Guardado",
                "La configuración se guardó exitosamente\n"
                "en printer_config.yaml"
            )
        except Exception as e:
            self._log(f"❌ Error al guardar: {e}")
            QMessageBox.critical(
                self, "Error",
                f"No se pudo guardar la configuración:\n{e}"
            )

    def _on_restaurar(self):
        """Recarga valores desde el YAML (descarta cambios no guardados)."""
        self.actividad_detectada.emit()
        self._cargar_valores()
        self._log("↺ Valores restaurados desde printer_config.yaml")
        self.statusBar().showMessage("Valores restaurados del archivo YAML.")

    def _on_volver(self):
        """Vuelve al modo básico."""
        self.actividad_detectada.emit()
        self.volver_basico.emit()
        self.hide()

    def _actualizar_monitor(self):
        """Actualiza los valores del monitor."""
        pass  # Placeholder para futura integración con datos reales

    def _log(self, mensaje):
        """Añade un mensaje al log."""
        from datetime import datetime
        hora = datetime.now().strftime("%H:%M:%S")
        self.txt_log.append(f"[{hora}] {mensaje}")

    # ================================================================
    # Estilo
    # ================================================================

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
            QSpinBox, QDoubleSpinBox {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 8px;
                color: #e0e0e0;
                min-height: 30px;
                font-size: 13px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #4DB6AC;
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
                padding: 8px 15px;
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
            QLabel {
                font-size: 13px;
            }
        """)

    # ================================================================
    # Eventos
    # ================================================================

    def showEvent(self, event):
        self.actividad_detectada.emit()
        self._cargar_valores()
        super().showEvent(event)

    def mousePressEvent(self, event):
        self.actividad_detectada.emit()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        self.actividad_detectada.emit()
        super().keyPressEvent(event)
