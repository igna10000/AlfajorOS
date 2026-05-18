#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de G-Code - Proyecto de Grado
Genera G-Code a escala 1:1 para patrones de crema sobre alfajores.
Coordenadas centradas en (centro_x, centro_y) de la cama de impresion.

Usa PathGenerator para obtener las coordenadas de los patrones,
garantizando que el G-Code generado coincida con la previsualizacion.
"""

import math
import os
from backend.config import PrinterConfig as PC
from backend.path_generator import PathGenerator


class GCodeBuilder:
    """Construye un programa G-Code con manejo de estado del extrusor."""

    def __init__(self):
        self.lines = []
        self.e_total = 0.0
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_z = 0.0
        self.retracted = False

    def comment(self, text):
        self.lines.append(f"; {text}")

    def blank(self):
        self.lines.append("")

    def raw(self, cmd):
        self.lines.append(cmd)

    def home(self):
        self.raw("G28")

    def set_absolute(self):
        self.raw("G90")

    def reset_extruder(self):
        self.raw("G92 E0")
        self.e_total = 0.0

    def cold_extrusion(self):
        """Desbloquea extrusion en frio (M302 P1)."""
        self.raw("M302 P1")

    def disable_motors(self):
        self.raw("M84")

    def move_z(self, z):
        self.raw(f"G1 Z{z:.2f} F{PC.VEL_Z}")
        self.current_z = z

    def travel(self, x, y):
        """Movimiento sin extruir — continuo, sin detener XY.
        Si retraccion habilitada: retrae E durante el movimiento XY.
        Si deshabilitada: solo mueve XY sin tocar E.
        Sin Z-hop en ningun caso.
        """
        if PC.RETRACCION_HABILITADA and not self.retracted:
            self.e_total -= PC.RETRACCION_MM
            self.retracted = True
        # Mover XY (un solo comando, sin paradas)
        self.raw(f"G1 X{x:.3f} Y{y:.3f} E{self.e_total:.4f} F{PC.VEL_VIAJE}")
        self.current_x = x
        self.current_y = y

    def extrude_to(self, x, y, speed=None):
        """Movimiento con extrusion."""
        if speed is None:
            speed = PC.VEL_IMPRESION
        # Si esta retraido, absorber desretraccion en este movimiento
        if self.retracted:
            self.e_total += PC.DESRETRACCION_MM
            self.retracted = False
        dx = x - self.current_x
        dy = y - self.current_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 0.01:
            return
        self.e_total += dist * PC.FLUJO_E_POR_MM
        self.raw(f"G1 X{x:.3f} Y{y:.3f} E{self.e_total:.4f} F{speed}")
        self.current_x = x
        self.current_y = y

    def _retract(self):
        self.e_total -= PC.RETRACCION_MM
        self.raw(f"G1 E{self.e_total:.4f} F{PC.VEL_RETRACCION}")
        self.retracted = True

    def _unretract(self):
        self.e_total += PC.DESRETRACCION_MM
        self.raw(f"G1 E{self.e_total:.4f} F{PC.VEL_RETRACCION}")
        self.retracted = False

    def park(self):
        """Secuencia de finalizacion segura:
        1. Retraccion forzada (siempre, independiente de RETRACCION_HABILITADA)
           Evita que la crema gotee al levantar la boquilla.
        2. Movimiento simultaneo X+Y+Z en un solo G0 rapido:
           la boquilla sube mientras se desplaza lateralmente.
        """
        # --- Paso 1: Retraccion forzada al finalizar ---
        if PC.FIN_RETRACCION_MM > 0 and not self.retracted:
            self.comment("Retraccion final (evita goteo al levantar)")
            self.e_total -= PC.FIN_RETRACCION_MM
            self.raw(f"G1 E{self.e_total:.4f} F{PC.VEL_RETRACCION}")
            self.retracted = True

        # --- Paso 2: Subir Z + desplazar XY simultaneamente (un solo comando) ---
        self.comment(
            f"Estacionamiento: X={PC.POS_FINAL_X:.1f} "
            f"Y={PC.POS_FINAL_Y:.1f} "
            f"Z={PC.POS_FINAL_Z:.1f} (simultaneo)"
        )
        self.raw(
            f"G0 X{PC.POS_FINAL_X:.1f} Y{PC.POS_FINAL_Y:.1f} "
            f"Z{PC.POS_FINAL_Z:.1f} F{PC.VEL_VIAJE}"
        )
        self.current_x = PC.POS_FINAL_X
        self.current_y = PC.POS_FINAL_Y
        self.current_z = PC.POS_FINAL_Z

    def build(self):
        return "\n".join(self.lines) + "\n"

    @property
    def line_count(self):
        """Numero de lineas de codigo (no comentarios ni vacias)."""
        return sum(1 for l in self.lines if l.strip() and not l.startswith(";"))


# ============================================================
# Generador principal
# ============================================================

class GCodeGenerator:
    """Genera G-Code a escala 1:1 para patrones de crema."""

    def __init__(self):
        self.cx = PC.ALFAJOR_CENTRO_X
        self.cy = PC.ALFAJOR_CENTRO_Y
        self.radio = PC.ALFAJOR_RADIO_MM
        self.z_print = PC.Z_ALTURA_MM + PC.Z_OFFSET_MM

    def generar_completo(self, patron="", texto="", grosor_pct=50, imagen_path=""):
        """
        Genera G-Code completo para un patron y/o texto.
        Retorna (gcode_str, metadata) donde metadata contiene:
          - drawing_start: linea donde empieza el dibujo
          - drawing_end: linea donde termina el dibujo
          - total_lines: total de lineas de codigo
        """
        g = GCodeBuilder()

        # Header
        g.comment("=" * 50)
        g.comment("AlfajorOS - G-Code de Crema")
        g.comment(f"Patron: {patron or 'ninguno'}")
        g.comment(f"Texto: {texto or 'ninguno'}")
        g.comment(f"Imagen: {os.path.basename(imagen_path) if imagen_path else 'ninguna'}")
        g.comment(f"Centro: ({self.cx}, {self.cy})")
        g.comment(f"Radio util: {self.radio:.1f} mm")
        g.comment("=" * 50)
        g.blank()

        # Inicializacion
        g.home()
        g.set_absolute()
        g.cold_extrusion()
        g.reset_extruder()
        g.blank()

        # Mover a posicion de purga
        g.comment("Posicionando para purga")
        g.move_z(PC.PURGA_POS_Z + PC.Z_HOP_MM)
        g.raw(f"G0 X{PC.PURGA_POS_X:.1f} Y{PC.PURGA_POS_Y:.1f} F{PC.VEL_VIAJE}")
        g.move_z(PC.PURGA_POS_Z)
        g.blank()

        # Purga
        if PC.PURGA_INICIAL_MM > 0:
            g.comment("Purga inicial")
            g.e_total += PC.PURGA_INICIAL_MM
            g.raw(f"G1 E{g.e_total:.4f} F300")
            g.reset_extruder()
            g.retracted = True  # Post-purga: considerar retraido para evitar E negativo
            g.blank()

        # Posicionar en altura de impresion y centro del alfajor (un solo movimiento)
        g.comment("Posicionando en centro del alfajor")
        g.raw(f"G1 X{self.cx:.1f} Y{self.cy:.1f} Z{self.z_print:.2f} F{PC.VEL_VIAJE}")
        g.current_x = self.cx
        g.current_y = self.cy
        g.current_z = self.z_print
        g.retracted = False
        g.blank()

        # === Marca inicio de dibujo ===
        drawing_start = g.line_count

        # Patron — usa PathGenerator
        if patron:
            g.comment(f"=== Patron: {patron} ===")
            pg = PathGenerator(self.radio, grosor_pct)
            path = pg.generar(patron)
            self._path_to_gcode(g, path)
            g.blank()

        # Texto — usa PathGenerator
        if texto:
            g.comment(f"=== Texto: {texto} ===")
            pg_txt = PathGenerator(self.radio, grosor_pct)
            path_texto = pg_txt.generar_texto(texto)
            self._path_to_gcode(g, path_texto)
            g.blank()

        # Imagen personalizada — usa PathGenerator + ImageProcessor
        if imagen_path:
            g.comment(f"=== Imagen: {os.path.basename(imagen_path)} ===")
            pg_img = PathGenerator(self.radio, grosor_pct)
            path_img = pg_img.generar_imagen(imagen_path)
            self._path_to_gcode(g, path_img)
            g.blank()

        # === Marca fin de dibujo ===
        drawing_end = g.line_count

        # Footer
        g.comment("=== Fin ===")
        g.park()
        g.blank()

        metadata = {
            "drawing_start": drawing_start,
            "drawing_end": drawing_end,
            "total_lines": g.line_count,
        }

        return g.build(), metadata

    def _path_to_gcode(self, g, path):
        """
        Convierte un path de segmentos a comandos G-Code.
        Cada segmento: primer punto = travel, resto = extrude.
        Coordenadas del path estan centradas en (0,0),
        se trasladan a (cx, cy) del alfajor en la cama.
        X se niega para corregir el espejo entre la vista previa
        (pantalla) y la orientacion fisica de la impresora.
        """
        for segment in path:
            if len(segment) < 2:
                continue
            # Travel al primer punto del segmento
            x0 = self.cx - segment[0][0]
            y0 = self.cy + segment[0][1]
            g.travel(x0, y0)
            # Extrude por el resto del segmento
            for px, py in segment[1:]:
                g.extrude_to(self.cx - px, self.cy + py)


# ============================================================
# Parser / Validador
# ============================================================

class GCodeParser:
    """Parser basico de G-Code."""

    @staticmethod
    def validar(gcode_text):
        errores = []
        for i, linea in enumerate(gcode_text.split("\n"), 1):
            linea = linea.strip()
            if not linea or linea.startswith(";"):
                continue
            cmd = linea.split()[0].upper()
            if not any(cmd.startswith(p) for p in ("G", "M", "T", ";")):
                errores.append(f"Linea {i}: comando no reconocido '{cmd}'")
        return len(errores) == 0, errores

    @staticmethod
    def contar_lineas(gcode_text):
        count = 0
        for linea in gcode_text.split("\n"):
            linea = linea.strip()
            if linea and not linea.startswith(";"):
                count += 1
        return count

    @staticmethod
    def extraer_coordenadas(gcode_text):
        """Extrae coordenadas XY para visualizacion."""
        coords = []
        for linea in gcode_text.split("\n"):
            linea = linea.strip()
            if not linea or linea.startswith(";"):
                continue
            x, y = None, None
            for token in linea.split():
                if token.startswith("X"):
                    try:
                        x = float(token[1:])
                    except ValueError:
                        pass
                elif token.startswith("Y"):
                    try:
                        y = float(token[1:])
                    except ValueError:
                        pass
            if x is not None and y is not None:
                has_e = any(t.startswith("E") for t in linea.split() if t != "E")
                coords.append((x, y, has_e))
        return coords
