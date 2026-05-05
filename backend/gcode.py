#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de G-Code - Proyecto de Grado
Genera G-Code a escala 1:1 para patrones de crema sobre alfajores.
Coordenadas centradas en (centro_x, centro_y) de la cama de impresion.
"""

import math
from backend.config import PrinterConfig as PC


# ============================================================
# Stroke Font - Coordenadas de trazos para cada caracter
# Cada caracter es una lista de polylines (segmentos continuos)
# Coordenadas normalizadas en un grid de 0-1 (ancho) x 0-1 (alto)
# ============================================================

STROKE_FONT = {
    'A': [[(0,1),(0.5,0),(1,1)], [(0.2,0.6),(0.8,0.6)]],
    'B': [[(0,1),(0,0),(0.7,0),(1,0.15),(1,0.35),(0.7,0.5),(0,0.5)],
          [(0.7,0.5),(1,0.65),(1,0.85),(0.7,1),(0,1)]],
    'C': [[(1,0.15),(0.7,0),(0.3,0),(0,0.15),(0,0.85),(0.3,1),(0.7,1),(1,0.85)]],
    'D': [[(0,0),(0,1),(0.6,1),(1,0.75),(1,0.25),(0.6,0),(0,0)]],
    'E': [[(1,0),(0,0),(0,0.5),(0.7,0.5),(0,0.5),(0,1),(1,1)]],
    'F': [[(1,0),(0,0),(0,0.5),(0.7,0.5),(0,0.5),(0,1)]],
    'G': [[(1,0.15),(0.7,0),(0.3,0),(0,0.15),(0,0.85),(0.3,1),(0.7,1),(1,0.85),(1,0.5),(0.5,0.5)]],
    'H': [[(0,0),(0,1)], [(1,0),(1,1)], [(0,0.5),(1,0.5)]],
    'I': [[(0.3,0),(0.7,0)], [(0.5,0),(0.5,1)], [(0.3,1),(0.7,1)]],
    'J': [[(0.3,0),(0.7,0)], [(0.5,0),(0.5,0.85),(0.3,1),(0.1,0.85)]],
    'K': [[(0,0),(0,1)], [(1,0),(0,0.5),(1,1)]],
    'L': [[(0,0),(0,1),(1,1)]],
    'M': [[(0,1),(0,0),(0.5,0.4),(1,0),(1,1)]],
    'N': [[(0,1),(0,0),(1,1),(1,0)]],
    'O': [[(0.3,0),(0,0.2),(0,0.8),(0.3,1),(0.7,1),(1,0.8),(1,0.2),(0.7,0),(0.3,0)]],
    'P': [[(0,1),(0,0),(0.7,0),(1,0.15),(1,0.35),(0.7,0.5),(0,0.5)]],
    'Q': [[(0.3,0),(0,0.2),(0,0.8),(0.3,1),(0.7,1),(1,0.8),(1,0.2),(0.7,0),(0.3,0)],
          [(0.6,0.7),(1,1)]],
    'R': [[(0,1),(0,0),(0.7,0),(1,0.15),(1,0.35),(0.7,0.5),(0,0.5)],
          [(0.5,0.5),(1,1)]],
    'S': [[(1,0.15),(0.7,0),(0.3,0),(0,0.15),(0,0.35),(0.3,0.5),
           (0.7,0.5),(1,0.65),(1,0.85),(0.7,1),(0.3,1),(0,0.85)]],
    'T': [[(0,0),(1,0)], [(0.5,0),(0.5,1)]],
    'U': [[(0,0),(0,0.85),(0.3,1),(0.7,1),(1,0.85),(1,0)]],
    'V': [[(0,0),(0.5,1),(1,0)]],
    'W': [[(0,0),(0.25,1),(0.5,0.5),(0.75,1),(1,0)]],
    'X': [[(0,0),(1,1)], [(1,0),(0,1)]],
    'Y': [[(0,0),(0.5,0.5),(1,0)], [(0.5,0.5),(0.5,1)]],
    'Z': [[(0,0),(1,0),(0,1),(1,1)]],
    '0': [[(0.3,0),(0,0.2),(0,0.8),(0.3,1),(0.7,1),(1,0.8),(1,0.2),(0.7,0),(0.3,0)]],
    '1': [[(0.2,0.2),(0.5,0)], [(0.5,0),(0.5,1)], [(0.2,1),(0.8,1)]],
    '2': [[(0,0.2),(0.3,0),(0.7,0),(1,0.2),(1,0.4),(0,1),(1,1)]],
    '3': [[(0,0.15),(0.3,0),(0.7,0),(1,0.2),(1,0.35),(0.7,0.5),(1,0.65),(1,0.8),(0.7,1),(0.3,1),(0,0.85)]],
    '4': [[(0,0),(0,0.5),(1,0.5)], [(0.7,0),(0.7,1)]],
    '5': [[(1,0),(0,0),(0,0.45),(0.7,0.45),(1,0.6),(1,0.85),(0.7,1),(0.3,1),(0,0.85)]],
    '6': [[(0.7,0),(0.3,0),(0,0.2),(0,0.85),(0.3,1),(0.7,1),(1,0.85),(1,0.65),(0.7,0.5),(0,0.5)]],
    '7': [[(0,0),(1,0),(0.3,1)]],
    '8': [[(0.3,0),(0,0.15),(0,0.35),(0.3,0.5),(0.7,0.5),(1,0.65),(1,0.85),(0.7,1),(0.3,1),(0,0.85),(0,0.65),(0.3,0.5),(0.7,0.5),(1,0.35),(1,0.15),(0.7,0),(0.3,0)]],
    '9': [[(1,0.5),(0.7,0.5),(0.3,0.5),(0,0.35),(0,0.15),(0.3,0),(0.7,0),(1,0.15),(1,0.8),(0.7,1),(0.3,1)]],
    ' ': [],
    '.': [[(0.4,0.9),(0.6,0.9),(0.6,1),(0.4,1),(0.4,0.9)]],
    ',': [[(0.5,0.85),(0.5,1),(0.3,1.15)]],
    '-': [[(0.2,0.5),(0.8,0.5)]],
    '!': [[(0.5,0),(0.5,0.7)], [(0.45,0.9),(0.55,0.9),(0.55,1),(0.45,1),(0.45,0.9)]],
    '?': [[(0.1,0.15),(0.3,0),(0.7,0),(0.9,0.15),(0.9,0.35),(0.5,0.55),(0.5,0.7)],
          [(0.45,0.9),(0.55,0.9),(0.55,1),(0.45,1),(0.45,0.9)]],
}


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
        """Movimiento rapido sin extruir (con retraccion + Z-hop)."""
        if not self.retracted:
            self._retract()
        # Z-hop
        hop_z = self.current_z + PC.Z_HOP_MM
        self.raw(f"G1 Z{hop_z:.2f} F{PC.VEL_Z}")
        # Mover XY
        self.raw(f"G0 X{x:.3f} Y{y:.3f} F{PC.VEL_VIAJE}")
        # Bajar Z
        self.raw(f"G1 Z{self.current_z:.2f} F{PC.VEL_Z}")
        # Desretraer
        self._unretract()
        self.current_x = x
        self.current_y = y

    def extrude_to(self, x, y, speed=None):
        """Movimiento con extrusion."""
        if speed is None:
            speed = PC.VEL_IMPRESION
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
        """Posicion de estacionamiento al finalizar."""
        if not self.retracted:
            self._retract()
        self.raw(f"G1 Z{PC.POS_FINAL_Z:.1f} F{PC.VEL_Z}")
        self.raw(f"G0 X{PC.POS_FINAL_X:.1f} Y{PC.POS_FINAL_Y:.1f} F{PC.VEL_VIAJE}")

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

    def generar_completo(self, patron="", texto="", grosor_pct=50):
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

        # Mover al centro del alfajor para empezar
        g.comment("Posicionando en centro del alfajor")
        g.move_z(self.z_print + PC.Z_HOP_MM)
        g.raw(f"G0 X{self.cx:.1f} Y{self.cy:.1f} F{PC.VEL_VIAJE}")
        g.move_z(self.z_print)
        g.blank()

        # === Marca inicio de dibujo ===
        drawing_start = g.line_count

        # Patron
        if patron:
            g.comment(f"=== Patron: {patron} ===")
            self._generar_patron(g, patron, grosor_pct)
            g.blank()

        # Texto
        if texto:
            g.comment(f"=== Texto: {texto} ===")
            self._generar_texto(g, texto)
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

    # ========================================================
    # Patrones
    # ========================================================

    def _generar_patron(self, g, patron, grosor_pct):
        """Despacha al generador correcto segun el patron."""
        p = patron.lower()
        if "espiral" in p:
            self._p_espiral(g, grosor_pct)
        elif "zigzag" in p:
            self._p_zigzag(g, grosor_pct)
        elif "circulo" in p:
            self._p_circulos(g, grosor_pct)
        elif "rejilla" in p:
            self._p_rejilla(g, grosor_pct)
        elif "estrella" in p:
            self._p_estrella(g, grosor_pct)
        elif "corazon" in p:
            self._p_corazon(g, grosor_pct)
        elif "onda" in p:
            self._p_ondas(g, grosor_pct)
        elif "relleno" in p or "completo" in p:
            self._p_relleno(g, grosor_pct)
        elif "borde" in p:
            self._p_borde(g, grosor_pct)
        else:
            self._p_espiral(g, grosor_pct)

    def _grosor_mm(self, grosor_pct):
        """Convierte porcentaje de grosor a mm de separacion entre lineas."""
        return PC.GROSOR_MIN_MM + (grosor_pct / 100) * (PC.GROSOR_MAX_MM - PC.GROSOR_MIN_MM)

    # --- Espiral ---
    def _p_espiral(self, g, grosor_pct, vueltas=None):
        r = self.radio
        grosor = self._grosor_mm(grosor_pct)
        if vueltas is None:
            vueltas = max(2, int(r / grosor))

        pasos = vueltas * 36
        g.travel(self.cx, self.cy)

        for i in range(1, pasos + 1):
            angulo = math.radians(i * 10)
            radio_i = (i / pasos) * r
            x = self.cx + radio_i * math.cos(angulo)
            y = self.cy + radio_i * math.sin(angulo)
            g.extrude_to(x, y)

    # --- Zigzag ---
    def _p_zigzag(self, g, grosor_pct):
        r = self.radio
        grosor = self._grosor_mm(grosor_pct)
        lineas = max(3, int((r * 2) / grosor))
        paso = (r * 2) / lineas

        first = True
        for i in range(lineas + 1):
            y_off = -r + i * paso
            # Calcular ancho del cordon a esta altura (circulo)
            if abs(y_off) > r:
                continue
            half_w = math.sqrt(r * r - y_off * y_off)

            if i % 2 == 0:
                x_start = self.cx - half_w
                x_end = self.cx + half_w
            else:
                x_start = self.cx + half_w
                x_end = self.cx - half_w

            y = self.cy + y_off
            if first:
                g.travel(x_start, y)
                first = False
            else:
                g.travel(x_start, y)
            g.extrude_to(x_end, y)

    # --- Circulos concentricos ---
    def _p_circulos(self, g, grosor_pct):
        r = self.radio
        grosor = self._grosor_mm(grosor_pct)
        num_circulos = max(2, int(r / grosor))

        for c in range(num_circulos, 0, -1):
            rc = r * (c / num_circulos)
            puntos = max(24, int(rc * 2))
            x0 = self.cx + rc
            y0 = self.cy
            g.travel(x0, y0)
            for i in range(1, puntos + 1):
                ang = math.radians(i * (360 / puntos))
                x = self.cx + rc * math.cos(ang)
                y = self.cy + rc * math.sin(ang)
                g.extrude_to(x, y)

    # --- Rejilla ---
    def _p_rejilla(self, g, grosor_pct):
        r = self.radio
        grosor = self._grosor_mm(grosor_pct)
        lineas = max(3, int((r * 2) / grosor))
        paso = (r * 2) / lineas

        # Lineas horizontales
        for i in range(lineas + 1):
            y_off = -r + i * paso
            if abs(y_off) > r:
                continue
            half_w = math.sqrt(r * r - y_off * y_off)
            y = self.cy + y_off
            x1 = self.cx - half_w
            x2 = self.cx + half_w
            if i % 2 == 0:
                g.travel(x1, y)
                g.extrude_to(x2, y)
            else:
                g.travel(x2, y)
                g.extrude_to(x1, y)

        # Lineas verticales
        for i in range(lineas + 1):
            x_off = -r + i * paso
            if abs(x_off) > r:
                continue
            half_h = math.sqrt(r * r - x_off * x_off)
            x = self.cx + x_off
            y1 = self.cy - half_h
            y2 = self.cy + half_h
            if i % 2 == 0:
                g.travel(x, y1)
                g.extrude_to(x, y2)
            else:
                g.travel(x, y2)
                g.extrude_to(x, y1)

    # --- Estrella ---
    def _p_estrella(self, g, grosor_pct, puntas=5):
        r = self.radio
        r_inner = r * 0.4
        total = puntas * 2
        vertices = []
        for i in range(total):
            ang = math.radians(i * (360 / total) - 90)
            ri = r if (i % 2 == 0) else r_inner
            vertices.append((
                self.cx + ri * math.cos(ang),
                self.cy + ri * math.sin(ang)
            ))

        g.travel(vertices[0][0], vertices[0][1])
        for vx, vy in vertices[1:]:
            g.extrude_to(vx, vy)
        g.extrude_to(vertices[0][0], vertices[0][1])

    # --- Corazon ---
    def _p_corazon(self, g, grosor_pct):
        r = self.radio
        puntos = 120
        # La ecuacion parametrica del corazon tiene extension maxima ~17 unidades
        # Normalizamos dividiendo por 17 para que el corazon llene el radio util
        scale = r / 17.0
        coords = []
        for i in range(puntos + 1):
            t = math.radians(i * (360 / puntos))
            # Ecuacion parametrica del corazon
            x = scale * 16 * (math.sin(t) ** 3)
            y = -scale * (13 * math.cos(t) - 5 * math.cos(2*t) -
                          2 * math.cos(3*t) - math.cos(4*t))
            coords.append((self.cx + x, self.cy + y))

        g.travel(coords[0][0], coords[0][1])
        for x, y in coords[1:]:
            g.extrude_to(x, y)

    # --- Ondas ---
    def _p_ondas(self, g, grosor_pct):
        r = self.radio
        grosor = self._grosor_mm(grosor_pct)
        lineas = max(3, int((r * 2) / grosor))
        paso = (r * 2) / lineas
        amplitud = paso * 0.4

        first = True
        for i in range(lineas + 1):
            y_off = -r + i * paso
            if abs(y_off) > r:
                continue
            half_w = math.sqrt(r * r - y_off * y_off)
            y_base = self.cy + y_off

            num_seg = max(10, int(half_w * 2 / 2))
            seg_w = (half_w * 2) / num_seg
            direction = 1 if i % 2 == 0 else -1

            start_x = self.cx - half_w if direction == 1 else self.cx + half_w
            if first:
                g.travel(start_x, y_base)
                first = False
            else:
                g.travel(start_x, y_base)

            for s in range(1, num_seg + 1):
                frac = s / num_seg
                x = self.cx - half_w + frac * half_w * 2
                if direction == -1:
                    x = self.cx + half_w - frac * half_w * 2
                y = y_base + amplitud * math.sin(frac * math.pi * 4)
                g.extrude_to(x, y)

    # --- Relleno completo ---
    def _p_relleno(self, g, grosor_pct):
        """Relleno en zigzag denso."""
        r = self.radio
        grosor = self._grosor_mm(grosor_pct)
        paso = max(0.8, grosor * 0.5)
        lineas = int((r * 2) / paso)

        first = True
        for i in range(lineas + 1):
            y_off = -r + i * paso
            if abs(y_off) >= r:
                continue
            half_w = math.sqrt(r * r - y_off * y_off)
            y = self.cy + y_off

            if i % 2 == 0:
                x_s, x_e = self.cx - half_w, self.cx + half_w
            else:
                x_s, x_e = self.cx + half_w, self.cx - half_w

            if first:
                g.travel(x_s, y)
                first = False
            else:
                g.travel(x_s, y)
            g.extrude_to(x_e, y)

    # --- Borde decorativo ---
    def _p_borde(self, g, grosor_pct):
        """Circulo exterior con ondulacion."""
        r = self.radio
        puntos = 72
        amplitud = 2.0

        g.travel(self.cx + r, self.cy)
        for i in range(1, puntos + 1):
            ang = math.radians(i * (360 / puntos))
            ri = r - amplitud + amplitud * math.sin(ang * 6)
            ri = min(ri, r)  # Nunca exceder el radio del alfajor
            x = self.cx + ri * math.cos(ang)
            y = self.cy + ri * math.sin(ang)
            g.extrude_to(x, y)

    # ========================================================
    # Texto
    # ========================================================

    def _generar_texto(self, g, texto):
        """Genera G-Code para texto usando stroke font."""
        if not texto:
            return

        texto = texto.upper()
        # Calcular dimensiones
        char_h = self.radio * 0.5
        char_w = char_h * 0.65
        spacing = char_w * 0.15
        total_w = len(texto) * char_w + (len(texto) - 1) * spacing
        # Limitar al diametro
        if total_w > self.radio * 1.6:
            scale = (self.radio * 1.6) / total_w
            char_w *= scale
            char_h *= scale
            spacing *= scale
            total_w = len(texto) * char_w + (len(texto) - 1) * spacing

        start_x = self.cx - total_w / 2
        start_y = self.cy - char_h / 2

        for ci, ch in enumerate(texto):
            ox = start_x + ci * (char_w + spacing)
            oy = start_y

            polylines = STROKE_FONT.get(ch, [])
            for polyline in polylines:
                if len(polyline) < 2:
                    continue
                # Primer punto = travel
                px = ox + polyline[0][0] * char_w
                py = oy + polyline[0][1] * char_h
                g.travel(px, py)
                # Resto = extrude
                for pt in polyline[1:]:
                    px = ox + pt[0] * char_w
                    py = oy + pt[1] * char_h
                    g.extrude_to(px, py)


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
