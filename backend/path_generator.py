#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Path Generator - Proyecto de Grado
Genera paths de coordenadas normalizadas para patrones de crema.
Estos paths son consumidos tanto por el generador de G-Code como
por el previsualizador del canvas, garantizando que ambos muestren
exactamente la misma figura.

Coordenadas centradas en (0, 0) en mm reales.
Un "path" es una lista de "segmentos".
Cada "segmento" es una lista de puntos (x_mm, y_mm).
  - El primer punto = posición de travel (sin extrusión)
  - Los puntos siguientes = extrusión continua
"""

import math
from backend.config import PrinterConfig as PC


# ============================================================
# Stroke Font - Coordenadas de trazos para cada caracter
# Cada caracter es una lista de polylines (segmentos continuos)
# Coordenadas normalizadas en un grid de 0-1 (ancho) x 0-1 (alto)
# ============================================================

STROKE_FONT = {
    'A': [[(0, 1), (0.5, 0), (1, 1)], [(0.2, 0.6), (0.8, 0.6)]],
    'B': [[(0, 1), (0, 0), (0.7, 0), (1, 0.15), (1, 0.35), (0.7, 0.5), (0, 0.5)],
          [(0.7, 0.5), (1, 0.65), (1, 0.85), (0.7, 1), (0, 1)]],
    'C': [[(1, 0.15), (0.7, 0), (0.3, 0), (0, 0.15), (0, 0.85), (0.3, 1), (0.7, 1), (1, 0.85)]],
    'D': [[(0, 0), (0, 1), (0.6, 1), (1, 0.75), (1, 0.25), (0.6, 0), (0, 0)]],
    'E': [[(1, 0), (0, 0), (0, 0.5), (0.7, 0.5), (0, 0.5), (0, 1), (1, 1)]],
    'F': [[(1, 0), (0, 0), (0, 0.5), (0.7, 0.5), (0, 0.5), (0, 1)]],
    'G': [[(1, 0.15), (0.7, 0), (0.3, 0), (0, 0.15), (0, 0.85), (0.3, 1),
           (0.7, 1), (1, 0.85), (1, 0.5), (0.5, 0.5)]],
    'H': [[(0, 0), (0, 1)], [(1, 0), (1, 1)], [(0, 0.5), (1, 0.5)]],
    'I': [[(0.3, 0), (0.7, 0)], [(0.5, 0), (0.5, 1)], [(0.3, 1), (0.7, 1)]],
    'J': [[(0.3, 0), (0.7, 0)], [(0.5, 0), (0.5, 0.85), (0.3, 1), (0.1, 0.85)]],
    'K': [[(0, 0), (0, 1)], [(1, 0), (0, 0.5), (1, 1)]],
    'L': [[(0, 0), (0, 1), (1, 1)]],
    'M': [[(0, 1), (0, 0), (0.5, 0.4), (1, 0), (1, 1)]],
    'N': [[(0, 1), (0, 0), (1, 1), (1, 0)]],
    'O': [[(0.3, 0), (0, 0.2), (0, 0.8), (0.3, 1), (0.7, 1),
           (1, 0.8), (1, 0.2), (0.7, 0), (0.3, 0)]],
    'P': [[(0, 1), (0, 0), (0.7, 0), (1, 0.15), (1, 0.35), (0.7, 0.5), (0, 0.5)]],
    'Q': [[(0.3, 0), (0, 0.2), (0, 0.8), (0.3, 1), (0.7, 1),
           (1, 0.8), (1, 0.2), (0.7, 0), (0.3, 0)],
          [(0.6, 0.7), (1, 1)]],
    'R': [[(0, 1), (0, 0), (0.7, 0), (1, 0.15), (1, 0.35), (0.7, 0.5), (0, 0.5)],
          [(0.5, 0.5), (1, 1)]],
    'S': [[(1, 0.15), (0.7, 0), (0.3, 0), (0, 0.15), (0, 0.35), (0.3, 0.5),
           (0.7, 0.5), (1, 0.65), (1, 0.85), (0.7, 1), (0.3, 1), (0, 0.85)]],
    'T': [[(0, 0), (1, 0)], [(0.5, 0), (0.5, 1)]],
    'U': [[(0, 0), (0, 0.85), (0.3, 1), (0.7, 1), (1, 0.85), (1, 0)]],
    'V': [[(0, 0), (0.5, 1), (1, 0)]],
    'W': [[(0, 0), (0.25, 1), (0.5, 0.5), (0.75, 1), (1, 0)]],
    'X': [[(0, 0), (1, 1)], [(1, 0), (0, 1)]],
    'Y': [[(0, 0), (0.5, 0.5), (1, 0)], [(0.5, 0.5), (0.5, 1)]],
    'Z': [[(0, 0), (1, 0), (0, 1), (1, 1)]],
    '0': [[(0.3, 0), (0, 0.2), (0, 0.8), (0.3, 1), (0.7, 1),
           (1, 0.8), (1, 0.2), (0.7, 0), (0.3, 0)]],
    '1': [[(0.2, 0.2), (0.5, 0)], [(0.5, 0), (0.5, 1)], [(0.2, 1), (0.8, 1)]],
    '2': [[(0, 0.2), (0.3, 0), (0.7, 0), (1, 0.2), (1, 0.4), (0, 1), (1, 1)]],
    '3': [[(0, 0.15), (0.3, 0), (0.7, 0), (1, 0.2), (1, 0.35), (0.7, 0.5),
           (1, 0.65), (1, 0.8), (0.7, 1), (0.3, 1), (0, 0.85)]],
    '4': [[(0, 0), (0, 0.5), (1, 0.5)], [(0.7, 0), (0.7, 1)]],
    '5': [[(1, 0), (0, 0), (0, 0.45), (0.7, 0.45), (1, 0.6),
           (1, 0.85), (0.7, 1), (0.3, 1), (0, 0.85)]],
    '6': [[(0.7, 0), (0.3, 0), (0, 0.2), (0, 0.85), (0.3, 1),
           (0.7, 1), (1, 0.85), (1, 0.65), (0.7, 0.5), (0, 0.5)]],
    '7': [[(0, 0), (1, 0), (0.3, 1)]],
    '8': [[(0.3, 0), (0, 0.15), (0, 0.35), (0.3, 0.5), (0.7, 0.5),
           (1, 0.65), (1, 0.85), (0.7, 1), (0.3, 1), (0, 0.85),
           (0, 0.65), (0.3, 0.5), (0.7, 0.5), (1, 0.35), (1, 0.15),
           (0.7, 0), (0.3, 0)]],
    '9': [[(1, 0.5), (0.7, 0.5), (0.3, 0.5), (0, 0.35), (0, 0.15),
           (0.3, 0), (0.7, 0), (1, 0.15), (1, 0.8), (0.7, 1), (0.3, 1)]],
    ' ': [],
    '.': [[(0.4, 0.9), (0.6, 0.9), (0.6, 1), (0.4, 1), (0.4, 0.9)]],
    ',': [[(0.5, 0.85), (0.5, 1), (0.3, 1.15)]],
    '-': [[(0.2, 0.5), (0.8, 0.5)]],
    '!': [[(0.5, 0), (0.5, 0.7)],
          [(0.45, 0.9), (0.55, 0.9), (0.55, 1), (0.45, 1), (0.45, 0.9)]],
    '?': [[(0.1, 0.15), (0.3, 0), (0.7, 0), (0.9, 0.15), (0.9, 0.35),
           (0.5, 0.55), (0.5, 0.7)],
          [(0.45, 0.9), (0.55, 0.9), (0.55, 1), (0.45, 1), (0.45, 0.9)]],
}


# ============================================================
# Path Generator
# ============================================================

class PathGenerator:
    """
    Genera paths de coordenadas para patrones de crema.
    Coordenadas centradas en (0, 0) en mm reales.
    Retorna: list[list[tuple[float, float]]]
      - Cada sub-lista es un segmento continuo
      - Primer punto = travel (mover sin extruir)
      - Puntos siguientes = extrusión continua
    """

    def __init__(self, radio_mm, grosor_pct=50):
        self.radio = radio_mm
        self.grosor_pct = grosor_pct

    def _grosor_mm(self):
        """Convierte porcentaje de grosor a mm de separación entre líneas."""
        return PC.GROSOR_MIN_MM + (self.grosor_pct / 100) * (
            PC.GROSOR_MAX_MM - PC.GROSOR_MIN_MM
        )

    # ========================================================
    # Dispatcher
    # ========================================================

    def generar(self, patron):
        """Genera path para el patrón dado. Retorna lista de segmentos."""
        p = patron.lower() if patron else "espiral"

        if "espiral" in p:
            return self._p_espiral()
        elif "zigzag" in p:
            return self._p_zigzag()
        elif "circulo" in p:
            return self._p_circulos()
        elif "rejilla" in p:
            return self._p_rejilla()
        elif "estrella" in p:
            return self._p_estrella()
        elif "corazon" in p:
            return self._p_corazon()
        elif "onda" in p:
            return self._p_ondas()
        elif "relleno" in p or "completo" in p:
            return self._p_relleno()
        elif "borde" in p:
            return self._p_borde()
        else:
            return self._p_espiral()

    def generar_texto(self, texto):
        """Genera path para texto usando STROKE_FONT."""
        return self._texto(texto)

    def generar_imagen(self, image_path):
        """Genera path a partir de una imagen procesada (esqueletizada).
        Usa ImageProcessor para: binarizar → esqueletizar → trazar → escalar.
        Retorna path en el mismo formato que generar() y generar_texto().
        """
        from backend.image_processor import ImageProcessor
        return ImageProcessor.imagen_a_path(image_path, self.radio)

    # ========================================================
    # Patrones
    # ========================================================

    def _p_espiral(self):
        """Espiral desde el centro hacia afuera."""
        r = self.radio
        grosor = self._grosor_mm()
        vueltas = max(2, int(r / grosor))
        pasos = vueltas * 36

        segment = [(0.0, 0.0)]  # Start at center
        for i in range(1, pasos + 1):
            angulo = math.radians(i * 10)
            radio_i = (i / pasos) * r
            x = radio_i * math.cos(angulo)
            y = radio_i * math.sin(angulo)
            segment.append((x, y))

        return [segment]

    def _p_zigzag(self):
        """Líneas horizontales zigzag dentro del círculo."""
        r = self.radio
        grosor = self._grosor_mm()
        lineas = max(3, int((r * 2) / grosor))
        paso = (r * 2) / lineas

        segments = []
        for i in range(lineas + 1):
            y_off = -r + i * paso
            if abs(y_off) > r:
                continue
            half_w = math.sqrt(r * r - y_off * y_off)

            if i % 2 == 0:
                x_start, x_end = -half_w, half_w
            else:
                x_start, x_end = half_w, -half_w

            segments.append([(x_start, y_off), (x_end, y_off)])

        return segments

    def _p_circulos(self):
        """Círculos concéntricos."""
        r = self.radio
        grosor = self._grosor_mm()
        num_circulos = max(2, int(r / grosor))

        segments = []
        for c in range(num_circulos, 0, -1):
            rc = r * (c / num_circulos)
            puntos = max(24, int(rc * 2))
            segment = []
            for i in range(puntos + 1):
                ang = math.radians(i * (360 / puntos))
                x = rc * math.cos(ang)
                y = rc * math.sin(ang)
                segment.append((x, y))
            segments.append(segment)

        return segments

    def _p_rejilla(self):
        """Rejilla cruzada (horizontal + vertical)."""
        r = self.radio
        grosor = self._grosor_mm()
        lineas = max(3, int((r * 2) / grosor))
        paso = (r * 2) / lineas

        segments = []

        # Líneas horizontales
        for i in range(lineas + 1):
            y_off = -r + i * paso
            if abs(y_off) > r:
                continue
            half_w = math.sqrt(r * r - y_off * y_off)
            if i % 2 == 0:
                segments.append([(-half_w, y_off), (half_w, y_off)])
            else:
                segments.append([(half_w, y_off), (-half_w, y_off)])

        # Líneas verticales
        for i in range(lineas + 1):
            x_off = -r + i * paso
            if abs(x_off) > r:
                continue
            half_h = math.sqrt(r * r - x_off * x_off)
            if i % 2 == 0:
                segments.append([(x_off, -half_h), (x_off, half_h)])
            else:
                segments.append([(x_off, half_h), (x_off, -half_h)])

        return segments

    def _p_estrella(self, puntas=5):
        """Estrella de 5 puntas."""
        r = self.radio
        r_inner = r * 0.4
        total = puntas * 2
        segment = []
        for i in range(total):
            ang = math.radians(i * (360 / total) - 90)
            ri = r if (i % 2 == 0) else r_inner
            segment.append((ri * math.cos(ang), ri * math.sin(ang)))

        # Cerrar la estrella
        segment.append(segment[0])
        return [segment]

    def _p_corazon(self):
        """Corazón paramétrico escalado al radio."""
        r = self.radio
        puntos = 120
        scale = r / 17.0

        segment = []
        for i in range(puntos + 1):
            t = math.radians(i * (360 / puntos))
            x = scale * 16 * (math.sin(t) ** 3)
            y = -scale * (13 * math.cos(t) - 5 * math.cos(2 * t) -
                          2 * math.cos(3 * t) - math.cos(4 * t))
            segment.append((x, y))

        return [segment]

    def _p_ondas(self):
        """Líneas onduladas horizontales."""
        r = self.radio
        grosor = self._grosor_mm()
        lineas = max(3, int((r * 2) / grosor))
        paso = (r * 2) / lineas
        amplitud = paso * 0.4

        segments = []
        for i in range(lineas + 1):
            y_off = -r + i * paso
            if abs(y_off) > r:
                continue
            half_w = math.sqrt(r * r - y_off * y_off)

            num_seg = max(10, int(half_w * 2 / 2))
            direction = 1 if i % 2 == 0 else -1

            segment = []
            for s in range(num_seg + 1):
                frac = s / num_seg
                if direction == 1:
                    x = -half_w + frac * half_w * 2
                else:
                    x = half_w - frac * half_w * 2
                y = y_off + amplitud * math.sin(frac * math.pi * 4)
                segment.append((x, y))
            segments.append(segment)

        return segments

    def _p_relleno(self):
        """Relleno denso en zigzag."""
        r = self.radio
        grosor = self._grosor_mm()
        paso = max(0.8, grosor * 0.5)
        lineas = int((r * 2) / paso)

        segments = []
        for i in range(lineas + 1):
            y_off = -r + i * paso
            if abs(y_off) >= r:
                continue
            half_w = math.sqrt(r * r - y_off * y_off)

            if i % 2 == 0:
                segments.append([(-half_w, y_off), (half_w, y_off)])
            else:
                segments.append([(half_w, y_off), (-half_w, y_off)])

        return segments

    def _p_borde(self):
        """Borde decorativo con ondulación sinusoidal."""
        r = self.radio
        puntos = 72
        amplitud = 2.0

        segment = []
        for i in range(puntos + 1):
            ang = math.radians(i * (360 / puntos))
            ri = r - amplitud + amplitud * math.sin(ang * 6)
            ri = min(ri, r)  # Nunca exceder el radio
            x = ri * math.cos(ang)
            y = ri * math.sin(ang)
            segment.append((x, y))

        return [segment]

    # ========================================================
    # Texto
    # ========================================================

    def _texto(self, texto):
        """Genera path para texto usando STROKE_FONT."""
        if not texto:
            return []

        r = self.radio
        texto = texto.upper()

        # Calcular dimensiones
        char_h = r * 0.7
        char_w = char_h * 0.65
        spacing = char_w * 0.43
        total_w = len(texto) * char_w + (len(texto) - 1) * spacing

        # Limitar al diámetro
        if total_w > r * 1.6:
            scale_factor = (r * 1.6) / total_w
            char_w *= scale_factor
            char_h *= scale_factor
            spacing *= scale_factor
            total_w = len(texto) * char_w + (len(texto) - 1) * spacing

        start_x = -total_w / 2
        start_y = -char_h / 2

        segments = []
        for ci, ch in enumerate(texto):
            ox = start_x + ci * (char_w + spacing)
            oy = start_y

            polylines = STROKE_FONT.get(ch, [])
            for polyline in polylines:
                if len(polyline) < 2:
                    continue
                segment = []
                for pt in polyline:
                    px = ox + pt[0] * char_w
                    py = oy + pt[1] * char_h
                    segment.append((px, py))
                segments.append(segment)

        return segments

    # ========================================================
    # Utilidades
    # ========================================================

    @staticmethod
    def total_points(path):
        """Cuenta el total de puntos en un path."""
        return sum(len(seg) for seg in path)

    @staticmethod
    def clipped_path(path, fraction):
        """
        Retorna un path recortado al porcentaje dado (0.0 - 1.0).
        Útil para animación de progreso.
        """
        if fraction >= 1.0:
            return path
        if fraction <= 0.0:
            return []

        total = PathGenerator.total_points(path)
        visible = int(total * fraction)
        if visible <= 0:
            return []

        result = []
        count = 0
        for seg in path:
            if count >= visible:
                break
            remaining = visible - count
            if remaining >= len(seg):
                result.append(seg)
                count += len(seg)
            else:
                result.append(seg[:remaining])
                count += remaining
                break

        return result
