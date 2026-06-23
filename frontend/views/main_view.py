#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main View - Proyecto de Grado
Ventana principal con visualización del alfajor y controles de extrusión.
Layout: barra superior (.ui) con Extruir/STOP/PRO +
        columna izquierda (Texto/Patrón/Limpiar) + canvas derecho.
"""

import os
from PySide6.QtWidgets import (
    QMainWindow, QMessageBox, QPushButton, QVBoxLayout,
    QHBoxLayout, QWidget, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from frontend.resources.ui_loader import load_ui
from frontend.widgets.animated_button import aplicar_animacion_pulso
from frontend.widgets.alfajor_canvas import AlfajorCanvas
from frontend.widgets.printer_indicator import PrinterIndicator
from frontend.widgets.jog_control import JogControlWidget
from backend.config import SystemConfig
from backend.extruder import ExtruderEngine
from backend.printer import PrinterConnection
from backend.gcode import GCodeGenerator


# Estilo celeste para botones laterales
BTN_LATERAL_STYLE = """
    QPushButton {
        background-color: #4DB6AC;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        font-family: Purisa;
    }
    QPushButton:pressed {
        background-color: #3d9e95;
    }
"""


class MainView(QMainWindow):
    """Ventana principal con visualización del alfajor."""

    abrir_texto = Signal()
    abrir_figura = Signal()
    abrir_pro = Signal()
    actividad_detectada = Signal()
    impresion_iniciada = Signal()
    impresion_terminada = Signal()

    def __init__(self, usuario="usuario", parent=None):
        super().__init__(parent)
        self.usuario = usuario

        # Motor de extrusión (backend)
        self.engine = ExtruderEngine(self)

        # Conexión serial con impresora
        self.printer = PrinterConnection(self)

        # Cargar UI
        load_ui("ventana_1_v2.ui", self)
        self.setWindowTitle(f"Extrusora de Crema — {self.usuario}")

        # Reemplazar el widget placeholder con AlfajorCanvas
        self._setup_alfajor_canvas()

        # Añadir columna izquierda con Texto/Patrón/Limpiar
        self._setup_columna_izquierda()

        # Añadir columna derecha con controles de movimiento
        self._setup_columna_derecha()

        # Ocultar botones de Texto y Figura del .ui (se reemplazan por la columna)
        self._ocultar_botones_ui()

        # Conectar
        self._conectar_botones()
        self._conectar_engine()
        self._conectar_printer()
        self._aplicar_animaciones()
        self._configurar_estado_inicial()
        self._manual_z0_set = False

    def _setup_alfajor_canvas(self):
        """Reemplaza el openGLWidget placeholder con AlfajorCanvas."""
        self.canvas = AlfajorCanvas(self)

        if hasattr(self, 'openGLWidget'):
            old_widget = self.openGLWidget
            parent_layout = old_widget.parentWidget()

            if parent_layout and parent_layout.layout():
                layout = parent_layout.layout()
                self._replace_in_layout(layout, old_widget, self.canvas)
            else:
                self.canvas.setParent(old_widget.parentWidget())
                self.canvas.setGeometry(old_widget.geometry())
                self.canvas.setMinimumSize(old_widget.minimumSize())
                old_widget.hide()

            self.canvas.setMinimumSize(old_widget.minimumSize())
            self.canvas.setSizePolicy(old_widget.sizePolicy())

    def _replace_in_layout(self, layout, old_widget, new_widget):
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget() == old_widget:
                layout.removeWidget(old_widget)
                old_widget.hide()
                old_widget.deleteLater()
                layout.insertWidget(i, new_widget)
                return True
            elif item.layout():
                if self._replace_in_layout(item.layout(), old_widget, new_widget):
                    return True
        return False

    def _setup_columna_izquierda(self):
        """Añade columna izquierda con Texto/Patrón/Limpiar al lado del canvas."""
        # Crear la columna
        self._left_col = QWidget()
        left_layout = QVBoxLayout(self._left_col)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # Indicador de impresora (LED + texto)
        self.printer_indicator = PrinterIndicator()
        left_layout.addWidget(self.printer_indicator)

        btn_font = QFont("Purisa", 11, QFont.Bold)

        # Botón TEXTO
        self.btn_texto = QPushButton("📝\nTEXTO")
        self.btn_texto.setMinimumSize(90, 65)
        self.btn_texto.setFont(btn_font)
        self.btn_texto.setStyleSheet(BTN_LATERAL_STYLE)
        self.btn_texto.clicked.connect(self._on_anadir_texto)
        left_layout.addWidget(self.btn_texto)

        # Botón PATRÓN
        self.btn_patron = QPushButton("🎨\nPATRÓN")
        self.btn_patron.setMinimumSize(90, 65)
        self.btn_patron.setFont(btn_font)
        self.btn_patron.setStyleSheet(BTN_LATERAL_STYLE)
        self.btn_patron.clicked.connect(self._on_anadir_figura)
        left_layout.addWidget(self.btn_patron)

        # Botón LIMPIAR
        self.btn_limpiar = QPushButton("🗑\nLIMPIAR")
        self.btn_limpiar.setMinimumSize(90, 65)
        self.btn_limpiar.setFont(btn_font)
        self.btn_limpiar.setStyleSheet(BTN_LATERAL_STYLE)
        self.btn_limpiar.clicked.connect(self._on_limpiar)
        left_layout.addWidget(self.btn_limpiar)

        left_layout.addStretch(1)

        # Botón MODO (Individual / Serie)
        self.btn_modo = QPushButton("MODO:\nINDIVIDUAL")
        self.btn_modo.setMinimumSize(90, 65)
        self.btn_modo.setFont(btn_font)
        self.btn_modo.setStyleSheet("""
            QPushButton {
                background-color: #5C6BC0;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-family: Purisa;
            }
            QPushButton:checked {
                background-color: #FF5722;
            }
        """)
        self.btn_modo.setCheckable(True)
        self.btn_modo.clicked.connect(self._on_toggle_modo)
        
        sp_modo = self.btn_modo.sizePolicy()
        sp_modo.setRetainSizeWhenHidden(True)
        self.btn_modo.setSizePolicy(sp_modo)
        self.btn_modo.hide()
        
        left_layout.addWidget(self.btn_modo)
        self.modo_serie = False

        # Botón MOTORES (liberar motores)
        self.btn_motores = QPushButton("MOTORES\nOFF")
        self.btn_motores.setMinimumSize(90, 55)
        self.btn_motores.setFont(btn_font)
        self.btn_motores.setStyleSheet("""
            QPushButton {
                background-color: #7E57C2;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-family: Purisa;
            }
            QPushButton:pressed {
                background-color: #6a48a8;
            }
        """)
        self.btn_motores.clicked.connect(self._on_release_motors)
        
        sp_mot = self.btn_motores.sizePolicy()
        sp_mot.setRetainSizeWhenHidden(True)
        self.btn_motores.setSizePolicy(sp_mot)
        self.btn_motores.hide()
        
        left_layout.addWidget(self.btn_motores)

        # Botón PRO (al final de la columna)
        self.btn_pro = QPushButton("PRO")
        self.btn_pro.setMinimumSize(90, 55)
        self.btn_pro.setFont(btn_font)
        self.btn_pro.setStyleSheet("""
            QPushButton {
                background-color: #FFAB40;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-family: Purisa;
            }
            QPushButton:pressed {
                background-color: #e09530;
            }
        """)
        self.btn_pro.clicked.connect(self._on_modo_pro)
        
        sp_pro = self.btn_pro.sizePolicy()
        sp_pro.setRetainSizeWhenHidden(True)
        self.btn_pro.setSizePolicy(sp_pro)
        self.btn_pro.hide()
        
        left_layout.addWidget(self.btn_pro)

        self._left_col.setFixedWidth(100)

        # Insertar la columna a la izquierda del canvas en su layout padre
        canvas_parent = self.canvas.parentWidget()
        if canvas_parent and canvas_parent.layout():
            layout = canvas_parent.layout()
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item.widget() == self.canvas:
                    layout.insertWidget(i, self._left_col)
                    break
            else:
                self._insert_before_recursive(layout, self.canvas, self._left_col)

    def _insert_before_recursive(self, layout, target, new_widget):
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget() == target:
                layout.insertWidget(i, new_widget)
                return True
            elif item.layout():
                if self._insert_before_recursive(item.layout(), target, new_widget):
                    return True
        return False

    def _setup_columna_derecha(self):
        """Añade columna derecha oculta. El botón Jog ahora es flotante."""
        self._right_col = QWidget()
        r_layout = QVBoxLayout(self._right_col)
        r_layout.setContentsMargins(0,0,0,0)
        
        self.jog_control = JogControlWidget(self.printer)
        self.jog_control.z0_set.connect(self._on_z0_set)
        self.jog_control.homed_all.connect(self._on_homed_all)
        self.jog_control.home_saved.connect(self._on_home_saved)
        self.jog_control.btn_close.clicked.connect(self._toggle_jog)
        self.jog_control.hide()
        r_layout.addWidget(self.jog_control)
        r_layout.addStretch()
        
        # Botón flotante para el Jog, sobre el Canvas, esquina inferior derecha
        self.btn_toggle_jog = QPushButton("⚙️", self.canvas)
        self.btn_toggle_jog.setFixedSize(45, 45)
        self.btn_toggle_jog.setStyleSheet("""
            QPushButton {
                background-color: rgba(60, 60, 60, 200);
                color: white;
                border-radius: 22px;
                font-size: 20px;
                border: 2px solid #4DB6AC;
            }
            QPushButton:hover { background-color: rgba(77, 182, 172, 220); }
        """)
        self.btn_toggle_jog.clicked.connect(self._toggle_jog)
        
        # Insertar la columna a la derecha del canvas en su layout padre
        canvas_parent = self.canvas.parentWidget()
        if canvas_parent and canvas_parent.layout():
            layout = canvas_parent.layout()
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item.widget() == self.canvas:
                    layout.insertWidget(i + 1, self._right_col)
                    break
            else:
                self._insert_after_recursive(layout, self.canvas, self._right_col)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Posicionar el botón flotante en la esquina inferior derecha del canvas
        if hasattr(self, 'btn_toggle_jog') and self.canvas:
            margin = 15
            self.btn_toggle_jog.move(
                self.canvas.width() - self.btn_toggle_jog.width() - margin,
                self.canvas.height() - self.btn_toggle_jog.height() - margin
            )

    def _toggle_jog(self):
        v = not self.jog_control.isVisible()
        self.jog_control.setVisible(v)
        self.btn_modo.setVisible(v)
        self.btn_motores.setVisible(v)
        self.btn_pro.setVisible(v)

    def _insert_after_recursive(self, layout, target, new_widget):
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget() == target:
                layout.insertWidget(i + 1, new_widget)
                return True
            elif item.layout():
                if self._insert_after_recursive(item.layout(), target, new_widget):
                    return True
        return False

    def _on_z0_set(self):
        self._manual_z0_set = True

    def _on_homed_all(self):
        self._manual_z0_set = False
        self._manual_home = None
        self._gcode_meta = None
        self.pushButton_4.setEnabled(True)
        self.pushButton_5.setEnabled(False)

    def _on_home_saved(self, x, y, z):
        self._manual_home = (x, y, z)
        self._manual_z0_set = True
        
        # Guardar en config.yaml (similar a calibracion de modo serie)
        from backend.config import PrinterConfig as PC
        PC.ALFAJOR_CENTRO_X = x
        PC.ALFAJOR_CENTRO_Y = y
        PC.ALFAJOR_CENTRO_Z = z
        PC.save()

    def _ocultar_botones_ui(self):
        """Elimina botones de Texto, Figura y PRO del .ui (reemplazados por columna)."""
        for attr in ['pushButton_3', 'pushButton_2', 'pushButton']:
            if hasattr(self, attr):
                btn = getattr(self, attr)
                parent = btn.parentWidget()
                if parent and parent.layout():
                    parent.layout().removeWidget(btn)
                btn.hide()
                btn.deleteLater()

    def _conectar_botones(self):
        """Conecta los botones de la UI (.ui)."""
        # Botones del .ui (barra superior)
        self.pushButton_4.clicked.connect(self._on_stop)      # STOP
        self.pushButton_5.clicked.connect(self._on_print)     # Extruir/Print
        # Agrandar botón Extruir
        self.pushButton_5.setMinimumHeight(75)
        self.pushButton_5.setFont(QFont("Purisa", 14, QFont.Bold))

    def _conectar_engine(self):
        self.engine.progress_updated.connect(self._on_progress)
        self.engine.extrusion_finished.connect(self._on_finished)
        self.engine.extrusion_stopped.connect(self._on_stopped)
        self.engine.status_message.connect(self._on_status)

    def _conectar_printer(self):
        """Conecta señales de la impresora al indicador visual."""
        self.printer.state_changed.connect(self.printer_indicator.set_state)
        self.printer.connection_info.connect(self.printer_indicator.set_port_info)
        self.printer.connection_info.connect(
            lambda info: self.statusbar.showMessage(f"Impresora: {info}")
        )
        self.printer.error_occurred.connect(
            lambda err: self.statusbar.showMessage(f"Error: {err}")
        )
        # Progreso real del G-Code
        self.printer.gcode_progress.connect(self._on_gcode_progress)
        self.printer.gcode_finished.connect(self._on_gcode_done)

    def _aplicar_animaciones(self):
        # Botones columna izquierda
        aplicar_animacion_pulso(self.btn_texto)
        aplicar_animacion_pulso(self.btn_patron)
        aplicar_animacion_pulso(self.btn_limpiar)
        aplicar_animacion_pulso(self.btn_motores)
        aplicar_animacion_pulso(self.btn_pro)
        
        # Botones Jog Control
        for btn in self.jog_control.get_animable_buttons():
            aplicar_animacion_pulso(btn)
            
        # Botones del .ui
        aplicar_animacion_pulso(self.pushButton_4)
        aplicar_animacion_pulso(self.pushButton_5)

    def _configurar_estado_inicial(self):
        self.progressBar.setValue(0)
        self.pushButton_4.setEnabled(False)
        self.statusbar.showMessage(f"Bienvenido, {self.usuario}. Listo para decorar.")

    # === Handlers ===

    def _on_anadir_texto(self):
        self.actividad_detectada.emit()
        self.abrir_texto.emit()
        self.statusbar.showMessage("Configurando texto para decorar...")

    def _on_anadir_figura(self):
        self.actividad_detectada.emit()
        self.abrir_figura.emit()
        self.statusbar.showMessage("Seleccionando patron decorativo...")

    def _on_modo_pro(self):
        self.actividad_detectada.emit()
        self.abrir_pro.emit()
        self.statusbar.showMessage("Abriendo Modo PRO...")

    def _on_toggle_modo(self):
        self.actividad_detectada.emit()
        self.modo_serie = self.btn_modo.isChecked()
        self.canvas.set_modo_serie(self.modo_serie)
        if self.modo_serie:
            self.btn_modo.setText("MODO:\nSERIE 3x3")
            self.statusbar.showMessage("Modo cambiado a: SERIE 3x3")
            self.btn_toggle_jog.show()
            
            # Preguntar si usar malla o recalibrar
            msg = QMessageBox(self)
            msg.setWindowTitle("Modo Serie 3x3")
            msg.setText("¿Desea usar la malla de calibración guardada (valores YAML) o recalibrar los 9 alfajores?")
            btn_usar = msg.addButton("Usar Guardada", QMessageBox.AcceptRole)
            btn_recal = msg.addButton("Recalibrar Malla", QMessageBox.ActionRole)
            msg.exec()
            if msg.clickedButton() == btn_recal:
                from frontend.widgets.calibration_wizard import CalibrationWizard
                wizard = CalibrationWizard(self.printer, self)
                wizard.exec()
        else:
            self.btn_modo.setText("MODO:\nINDIVIDUAL")
            self.statusbar.showMessage("Modo cambiado a: INDIVIDUAL")
            self.btn_toggle_jog.show()

    def _on_stop(self):
        self.actividad_detectada.emit()
        self.printer.stop_sending()
        if self.engine.is_extruding:
            self.engine.stop()
        self.canvas.stop_animacion()
        self.pushButton_4.setEnabled(False)
        self.pushButton_5.setEnabled(True)
        self.progressBar.setValue(0)
        self.canvas.set_progreso(0)
        self.impresion_terminada.emit()
        self.statusbar.showMessage("Impresion detenida.")

    def _on_release_motors(self):
        """Libera los motores (M84) para mover manualmente."""
        self.actividad_detectada.emit()
        if self.printer.is_connected:
            self.printer.send_command("M84")
            self.statusbar.showMessage("Motores liberados. Puede mover manualmente.")
        else:
            QMessageBox.warning(
                self, "Sin conexion",
                "La impresora no esta conectada."
            )

    def _on_limpiar(self):
        self.actividad_detectada.emit()
        self.printer.stop_sending()
        if self.engine.is_extruding:
            self.engine.stop()
            self.impresion_terminada.emit()
        self.engine.reset()
        self.canvas.reset()
        # Resetear modo serie
        self.modo_serie = False
        self.btn_modo.setChecked(False)
        self.btn_modo.setText("MODO:\nINDIVIDUAL")
        self.btn_toggle_jog.show()
        self.progressBar.setValue(0)
        self.pushButton_4.setEnabled(False)
        self.pushButton_5.setEnabled(True)
        self.statusbar.showMessage("Todo reiniciado. Listo para decorar.")

    def _on_print(self):
        self.actividad_detectada.emit()
        if self.engine.is_extruding:
            return

        # Validar conexion con impresora
        if not self.printer.is_connected:
            QMessageBox.warning(
                self, "Sin impresora",
                "La impresora no esta conectada.\nVerifique la conexion USB."
            )
            return

        # Validar que al menos un alfajor tenga diseño
        has_design = False
        if self.modo_serie:
            for c in self.canvas._configs:
                if c["patron"] or c["texto"] or c["imagen_path"]:
                    has_design = True
                    break
        else:
            c = self.canvas._configs[0]
            if c["patron"] or c["texto"] or c["imagen_path"]:
                has_design = True

        if not has_design:
            QMessageBox.warning(
                self, "Sin configuracion",
                "Debe seleccionar un patrón decorativo o\ningresar un texto antes de extruir."
            )
            return

        # --- Dialogo de Purga Inicial (Extrusion) ---
        from frontend.widgets.jog_control import RetractionDialog
        from backend.config import PrinterConfig as PC
        
        dialog_purga = RetractionDialog(
            self,
            default_val=PC.PURGA_INICIAL_MM,
            prompt_text="Ajuste la distancia de EXTRUSIÓN INICIAL (Purga):"
        )
        dialog_purga.setWindowTitle("Extrusión Inicial")
        if not dialog_purga.exec():
            return
            
        purga_inicial = dialog_purga.get_value()

        # --- Dialogo de Retraccion Final ---
        dialog_ret = RetractionDialog(
            self,
            default_val=PC.FIN_RETRACCION_MM,
            prompt_text="Ajuste la distancia a RETRAER al finalizar la impresión:"
        )
        dialog_ret.setWindowTitle("Retracción Final")
        if not dialog_ret.exec():
            return
            
        fin_retraccion = dialog_ret.get_value()

        # Generar G-Code
        gen = GCodeGenerator()
        gcode, meta = gen.generar_completo(
            configs_serie=self.canvas._configs,
            manual_z0=self._manual_z0_set,
            manual_home=getattr(self, '_manual_home', None),
            fin_retraccion_mm=fin_retraccion,
            purga_inicial_mm=purga_inicial,
            modo_serie=self.modo_serie
        )

        # Guardar metadata para mapeo de progreso
        self._gcode_meta = meta

        # Confirmar extrusion
        from backend.gcode import GCodeParser
        n_lineas = GCodeParser.contar_lineas(gcode)
        
        if self.modo_serie:
            resumen_str = "Matriz de 9 alfajores"
        else:
            c = self.canvas._configs[0]
            img_nombre = os.path.basename(c["imagen_path"]) if c["imagen_path"] else ''
            resumen_str = (
                f"Patrón: {c['patron'] or 'ninguno'}\n"
                f"Texto: {c['texto'] or 'ninguno'}\n"
                f"Imagen: {img_nombre or 'ninguna'}"
            )

        respuesta = QMessageBox.question(
            self, "Confirmar Extrusion",
            f"Se generaron {n_lineas} comandos G-Code.\n"
            f"{resumen_str}\n\n"
            "Iniciar extrusión de crema?",
            QMessageBox.Yes | QMessageBox.No
        )
        if respuesta == QMessageBox.Yes:
            # Activar animacion y UI
            self.canvas.start_animacion()
            self.pushButton_4.setEnabled(True)
            self.pushButton_5.setEnabled(False)
            self.impresion_iniciada.emit()

            # Enviar G-Code real a la impresora (progreso via _on_gcode_progress)
            self.printer.send_gcode(gcode)
            self.statusbar.showMessage("Enviando G-Code a la impresora...")

    def _on_progress(self, value):
        """Progreso de la simulacion del engine (no usado durante impresion real)."""
        self.progressBar.setValue(value)
        self.canvas.set_progreso(value)

    def _on_gcode_progress(self, current, total):
        """Progreso real del envio de G-Code — mapea a progreso visual."""
        if total <= 0:
            return

        meta = getattr(self, '_gcode_meta', None)
        if meta:
            ds = meta["drawing_start"]
            de = meta["drawing_end"]
            drawing_range = de - ds

            if drawing_range > 0:
                if current <= ds:
                    visual_pct = 0
                elif current >= de:
                    visual_pct = 100
                else:
                    visual_pct = int(((current - ds) / drawing_range) * 100)
            else:
                visual_pct = int((current / total) * 100)
        else:
            visual_pct = int((current / total) * 100)

        bar_pct = int((current / total) * 100)
        self.progressBar.setValue(bar_pct)
        self.canvas.set_progreso(visual_pct)
        self.statusbar.showMessage(
            f"Imprimiendo: {current}/{total} ({bar_pct}%)"
        )

    def _on_gcode_done(self):
        """G-Code enviado completamente — finalizar impresion."""
        self._on_finished()

    def _on_finished(self):
        self.pushButton_4.setEnabled(False)
        self.pushButton_5.setEnabled(True)
        self.canvas.stop_animacion()
        self.impresion_terminada.emit()
        QMessageBox.information(self, "Completado",
                                "La extrusion de crema ha finalizado!")

    def _on_stopped(self):
        self.pushButton_4.setEnabled(False)
        self.pushButton_5.setEnabled(True)
        self.progressBar.setValue(0)
        self.canvas.stop_animacion()
        self.canvas.set_progreso(0)
        QMessageBox.warning(self, "Detenido",
                            "La extrusión fue detenida.\nProgreso reiniciado.")

    def _on_status(self, msg):
        self.statusbar.showMessage(msg)

    # === API ===

    def set_texto(self, texto):
        self.engine.set_texto(texto)
        self.canvas.set_texto(texto)
        self.statusbar.showMessage(f"Texto configurado: '{texto}'")

    def set_figura(self, figura, tamano):
        self.engine.set_patron(figura)
        self.canvas.set_patron(figura)
        self.canvas.set_grosor(tamano)
        self.statusbar.showMessage(f"Patrón: {figura} (grosor: {tamano}%)")

    def set_imagen(self, path):
        """Configura una imagen personalizada para imprimir."""
        self.canvas.set_imagen(path)
        self.statusbar.showMessage(
            f"Imagen: {os.path.basename(path)}"
        )

    def mousePressEvent(self, event):
        self.actividad_detectada.emit()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        self.actividad_detectada.emit()
        super().keyPressEvent(event)
