#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visualización 3D del Alfajor - Proyecto de Grado
Widget QPainter con perspectiva 3D pseudo-isométrica.
3 vistas: Planta (top-down), Isométrica, Libre (touch drag).
Compatible con EGLFS (sin QOpenGLWidget).
"""

import math
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer
from PySide6.QtGui import (
    QPainter, QColor, QBrush, QPen, QFont,
    QRadialGradient, QLinearGradient, QPainterPath,
    QTransform
)

# Modos de vista
VIEW_TOP = 0        # Planta (top-down)
VIEW_ISOMETRIC = 1  # Isométrica
VIEW_FREE = 2       # Libre (touch)

VIEW_NAMES = ["PLANTA", "ISOMÉTRICA", "LIBRE"]


class AlfajorCanvas(QWidget):
    """
    Widget 3D del alfajor con crema usando QPainter con perspectiva.
    Soporta 3 vistas y volumen en galleta, crema y texto.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._progreso = 0
        self._patron = ""
        self._texto = ""
        self._grosor = 50
        self._imagen_path = ""
        self._imagen_path_cache = {}   # {path: list[segments]} — cache del pipeline
        self._animacion_t = 0.0
        self._printing = False

        # Vista
        self._view_mode = VIEW_TOP
        self._tilt = 0.0          # Ángulo de inclinación (0=top, 60=lateral)
        self._rotation = 0.0      # Rotación horizontal
        # Para vista libre
        self._drag_last = None
        self._free_tilt = 35.0
        self._free_rotation = 30.0

        # Timer de animación
        self._timer_anim = QTimer(self)
        self._timer_anim.timeout.connect(self._tick_anim)
        self._timer_anim.start(50)

        # Rects de botones de vista (calculados en paintEvent)
        self._btn_rects = []  # [(QRectF, view_mode), ...]

        self.setMinimumSize(300, 300)
        self.setStyleSheet("background-color: #1e1e1e; border: 2px solid #4DB6AC; border-radius: 10px;")

    # === Propiedades ===

    @property
    def _render_progreso(self):
        if self._printing:
            return self._progreso
        elif self._patron or self._texto or self._imagen_path:
            return 100
        else:
            return 0

    @property
    def _current_tilt(self):
        if self._view_mode == VIEW_TOP:
            return 0.0
        elif self._view_mode == VIEW_ISOMETRIC:
            return 35.0
        else:
            return self._free_tilt

    @property
    def _current_rotation(self):
        if self._view_mode == VIEW_TOP:
            return 0.0
        elif self._view_mode == VIEW_ISOMETRIC:
            return 30.0
        else:
            return self._free_rotation

    # === API pública ===

    def set_progreso(self, valor):
        self._progreso = max(0, min(100, valor))
        self.update()

    def set_patron(self, patron):
        self._patron = patron
        self.update()

    def set_texto(self, texto):
        self._texto = texto
        self.update()

    def set_grosor(self, grosor):
        self._grosor = grosor
        self.update()

    def set_imagen(self, path):
        """Establece una imagen personalizada para preview.
        Procesa el pipeline UNA sola vez y cachea el resultado.
        """
        self._patron = ""  # Limpiar patrón al usar imagen
        self._imagen_path = path

        # Procesar inmediatamente y guardar en cache para que los frames
        # posteriores no vuelvan a ejecutar Zhang-Suen thinning
        if path and path not in self._imagen_path_cache:
            try:
                from backend.config import PrinterConfig as PC
                from backend.path_generator import PathGenerator
                pg = PathGenerator(PC.ALFAJOR_RADIO_MM, self._grosor)
                self._imagen_path_cache[path] = pg.generar_imagen(path)
            except Exception as e:
                print(f"[Canvas] Error procesando imagen: {e}")
                self._imagen_path_cache[path] = []

        self.update()

    def reset(self):
        """Reinicia todo: progreso, patrón, texto, vista."""
        self._progreso = 0
        self._patron = ""
        self._texto = ""
        self._grosor = 50
        self._imagen_path = ""
        self._printing = False
        self._view_mode = VIEW_TOP
        self._free_tilt = 35.0
        self._free_rotation = 30.0
        self.update()

    def start_animacion(self):
        self._printing = True
        self._progreso = 0
        self.update()

    def stop_animacion(self):
        self._printing = False
        self.update()

    def set_view(self, mode):
        self._view_mode = mode
        self.update()

    def cycle_view(self):
        self._view_mode = (self._view_mode + 1) % 3
        self.update()

    # === Proyección 3D → 2D ===

    def _project(self, x3d, y3d, z3d, cx, cy, scale):
        """Proyecta un punto 3D a coordenadas 2D con perspectiva."""
        tilt = math.radians(self._current_tilt)
        rot = math.radians(self._current_rotation)

        # Rotación alrededor de Y
        x1 = x3d * math.cos(rot) - y3d * math.sin(rot)
        y1 = x3d * math.sin(rot) + y3d * math.cos(rot)
        z1 = z3d

        # Inclinación (rotación alrededor de X)
        y2 = y1 * math.cos(tilt) - z1 * math.sin(tilt)
        z2 = y1 * math.sin(tilt) + z1 * math.cos(tilt)

        # Proyección ortográfica con escala
        px = cx + x1 * scale
        py = cy + y2 * scale

        return px, py, z2

    def _project_point(self, x3d, y3d, z3d, cx, cy, scale):
        px, py, _ = self._project(x3d, y3d, z3d, cx, cy, scale)
        return QPointF(px, py)

    # === Touch / Mouse ===

    def mousePressEvent(self, event):
        pos = event.position()
        # Verificar si se presionó un botón de vista
        for rect, mode in self._btn_rects:
            if rect.contains(pos):
                self._view_mode = mode
                self.update()
                return
        # Vista libre: iniciar drag
        if self._view_mode == VIEW_FREE:
            self._drag_last = pos
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._view_mode == VIEW_FREE and self._drag_last is not None:
            pos = event.position()
            dx = pos.x() - self._drag_last.x()
            dy = pos.y() - self._drag_last.y()
            # Horizontal = rotación alrededor del eje Z (alrededor del alfajor)
            self._free_rotation += dx * 0.8
            # Vertical = inclinación (tilt)
            self._free_tilt = max(0, min(70, self._free_tilt + dy * 0.5))
            self._drag_last = pos
            self.update()

    def mouseReleaseEvent(self, event):
        self._drag_last = None
        super().mouseReleaseEvent(event)

    # === Dibujo ===

    def _tick_anim(self):
        self._animacion_t += 0.05
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        size = min(w, h) - 30
        scale = size * 0.35 / 35

        # Fondo (sin transformar)
        self._dibujar_fondo(painter, w, h)

        tilt = self._current_tilt
        rot = self._current_rotation

        # Aplicar rotación global alrededor del centro
        painter.save()
        if abs(rot) > 0.1:
            t = QTransform()
            t.translate(cx, cy)
            rot_rad = math.radians(rot)
            # Shear para simular rotación en Z alrededor del alfajor
            t.rotate(rot)
            t.translate(-cx, -cy)
            painter.setTransform(t, True)

        # Dibujar en orden de profundidad
        self._dibujar_sombra(painter, cx, cy, scale, tilt)
        self._dibujar_alfajor_3d(painter, cx, cy, scale, tilt)

        rp = self._render_progreso
        if rp > 0 and (self._patron or self._imagen_path):
            self._dibujar_crema_3d(painter, cx, cy, scale, tilt, rp)

        if self._texto and rp > 60:
            self._dibujar_texto_3d(painter, cx, cy, scale, tilt, rp)

        painter.restore()  # Quitar rotación para UI

        # Indicador de progreso (sin rotación)
        if self._printing and self._progreso > 0 and self._progreso < 100:
            self._dibujar_indicador_progreso(painter, cx, cy, size)

        # UI (sin rotación)
        self._dibujar_ui(painter, w, h)

        painter.end()

    def _dibujar_fondo(self, painter, w, h):
        grad = QRadialGradient(w / 2, h / 2, max(w, h) / 2)
        grad.setColorAt(0.0, QColor(35, 35, 45))
        grad.setColorAt(1.0, QColor(20, 20, 28))
        painter.fillRect(0, 0, w, h, grad)

    def _dibujar_sombra(self, painter, cx, cy, scale, tilt):
        """Sombra debajo del alfajor."""
        painter.setPen(Qt.NoPen)
        r = 35 * scale
        # Proyectar la sombra
        sx, sy = cx, cy
        if tilt > 5:
            sy = cy + 15 * math.sin(math.radians(tilt))
        painter.setBrush(QBrush(QColor(0, 0, 0, 40)))
        ry = r * math.cos(math.radians(tilt)) * 0.95
        painter.drawEllipse(QPointF(sx + 3, sy + 5), r, max(ry, r * 0.3))

    def _dibujar_alfajor_3d(self, painter, cx, cy, scale, tilt):
        """Dibuja el alfajor como un cilindro 3D."""
        r = 35 * scale
        grosor_galleta = 12 * scale  # Grosor del alfajor (más alto = más 3D)
        tilt_rad = math.radians(tilt)
        cos_t = math.cos(tilt_rad)

        # Altura visual del cilindro
        h_visual = grosor_galleta * math.sin(tilt_rad)
        # Radio Y (elipse por perspectiva)
        ry = r * cos_t if tilt > 2 else r

        # Colores
        color_top = QColor(200, 160, 110)
        color_side = QColor(150, 115, 75)
        color_bottom = QColor(120, 90, 55)

        # === Cara inferior (solo si hay inclinación) ===
        if tilt > 5:
            grad_b = QRadialGradient(cx, cy + h_visual / 2, r)
            grad_b.setColorAt(0, color_bottom.lighter(110))
            grad_b.setColorAt(1, color_bottom)
            painter.setBrush(QBrush(grad_b))
            painter.setPen(QPen(color_bottom.darker(120), 1))
            painter.drawEllipse(QPointF(cx, cy + h_visual / 2), r, max(ry, r * 0.3))

        # === Lado del cilindro (solo si hay inclinación) ===
        if tilt > 5:
            side_path = QPainterPath()
            # Arco inferior
            rect_bot = QRectF(cx - r, cy + h_visual / 2 - ry, r * 2, ry * 2)
            side_path.arcMoveTo(rect_bot, 180)
            side_path.arcTo(rect_bot, 180, 180)
            # Línea al arco superior
            rect_top = QRectF(cx - r, cy - h_visual / 2 - ry, r * 2, ry * 2)
            side_path.arcTo(rect_top, 0, -180)
            side_path.closeSubpath()

            # Gradiente lateral
            grad_s = QLinearGradient(cx - r, cy, cx + r, cy)
            grad_s.setColorAt(0.0, color_side.darker(120))
            grad_s.setColorAt(0.3, color_side.lighter(110))
            grad_s.setColorAt(0.7, color_side)
            grad_s.setColorAt(1.0, color_side.darker(130))
            painter.setBrush(QBrush(grad_s))
            painter.setPen(QPen(color_side.darker(140), 0.5))
            painter.drawPath(side_path)

            # Línea de crema en el medio del lado
            crema_y = cy
            painter.setPen(QPen(QColor(255, 245, 220, 180), grosor_galleta * 0.3))
            painter.drawArc(
                QRectF(cx - r, crema_y - ry * 0.15, r * 2, ry * 0.3),
                180 * 16, 180 * 16
            )

        # === Cara superior (tapa) ===
        grad_t = QRadialGradient(cx - r * 0.2, cy - h_visual / 2 - ry * 0.2, r * 1.2)
        grad_t.setColorAt(0.0, QColor(220, 180, 130))
        grad_t.setColorAt(0.4, QColor(200, 160, 110))
        grad_t.setColorAt(0.7, QColor(175, 140, 95))
        grad_t.setColorAt(1.0, QColor(150, 115, 75))
        painter.setBrush(QBrush(grad_t))
        painter.setPen(QPen(QColor(130, 100, 65), 1.5))
        painter.drawEllipse(QPointF(cx, cy - h_visual / 2), r, max(ry, r * 0.3))

        # Textura puntos en la tapa
        painter.setPen(Qt.NoPen)
        top_cy = cy - h_visual / 2
        for i in range(30):
            angulo = (i * 137.5) * math.pi / 180
            fraction = 0.15 + (i * 0.8 / 30)
            px = cx + r * fraction * math.cos(angulo)
            py = top_cy + max(ry, r * 0.3) * fraction * math.sin(angulo)
            dot_size = 1.2 + (i % 3) * 0.6
            alpha = 25 + (i % 4) * 8
            painter.setBrush(QBrush(QColor(140, 110, 70, alpha)))
            painter.drawEllipse(QPointF(px, py), dot_size, dot_size)

        # Borde highlight
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(230, 195, 150, 50), 2))
        painter.drawEllipse(QPointF(cx, cy - h_visual / 2), r - 3, max(ry - 3, r * 0.27))

    def _dibujar_crema_3d(self, painter, cx, cy, scale, tilt, progreso):
        """Dibuja la crema con volumen ENCIMA del alfajor."""
        from backend.config import PrinterConfig as PC
        r = 35 * scale
        tilt_rad = math.radians(tilt)
        h_alfajor = 12 * scale * math.sin(tilt_rad)
        ry = r * math.cos(tilt_rad) if tilt > 2 else r
        radio_alfajor = PC.ALFAJOR_DIAMETRO_MM / 2
        ratio = PC.ALFAJOR_RADIO_MM / radio_alfajor if radio_alfajor > 0 else 0.82
        radio_crema = r * ratio

        grosor_linea = 3 + (self._grosor / 100) * 7
        crema_height = 5 * scale

        alfajor_top_cy = cy - h_alfajor / 2
        crema_surface_cy = alfajor_top_cy - crema_height * math.sin(tilt_rad)

        painter.save()
        if tilt > 2:
            t = QTransform()
            t.translate(cx, crema_surface_cy)
            t.scale(1.0, max(ry / r, 0.3))
            t.translate(-cx, -crema_surface_cy)
            painter.setTransform(t, True)

        # Capas 3D de sombra
        if tilt > 2:
            num_layers = 6
            for layer in range(num_layers, 0, -1):
                frac = layer / num_layers
                offset = crema_height * frac * 2
                alpha = int(40 + frac * 100)
                thickness = grosor_linea + 3 - layer * 0.3
                sombra_pen = QPen(QColor(220, 200, 160, alpha),
                                 max(1, thickness),
                                 Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                painter.setPen(sombra_pen)
                painter.setBrush(Qt.NoBrush)
                self._dibujar_path(painter, cx, crema_surface_cy + offset,
                                   radio_crema, progreso)

        # Capa principal de crema
        color_crema = QColor(255, 245, 220, 245)
        pen = QPen(color_crema, grosor_linea, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        self._dibujar_path(painter, cx, crema_surface_cy, radio_crema, progreso)

        # Highlight
        highlight_pen = QPen(QColor(255, 255, 252, 110), max(2, grosor_linea * 0.5),
                           Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(highlight_pen)
        self._dibujar_path(painter, cx, crema_surface_cy - 1.5, radio_crema, progreso)

        painter.restore()

    def _dibujar_texto_3d(self, painter, cx, cy, scale, tilt, progreso):
        """Dibuja texto con extrusión 3D usando STROKE_FONT (igual que G-Code)."""
        if not self._texto:
            return

        from backend.config import PrinterConfig as PC
        from backend.path_generator import PathGenerator

        r = 35 * scale
        tilt_rad = math.radians(tilt)
        h_alfajor = 12 * scale * math.sin(tilt_rad)
        ry = r * math.cos(tilt_rad) if tilt > 2 else r
        crema_height = 5 * scale

        alfajor_top_cy = cy - h_alfajor / 2
        texto_surface_cy = alfajor_top_cy - crema_height * math.sin(tilt_rad)

        progress_texto = min(100, max(0, (progreso - 60) * 100 / 40))

        painter.save()
        if tilt > 2:
            t = QTransform()
            t.translate(cx, texto_surface_cy)
            t.scale(1.0, max(ry / r, 0.3))
            t.translate(-cx, -texto_surface_cy)
            painter.setTransform(t, True)

        # Generar path de texto con PathGenerator
        pg = PathGenerator(PC.ALFAJOR_RADIO_MM, self._grosor)
        text_path = pg.generar_texto(self._texto)
        if not text_path:
            painter.restore()
            return

        # Escalar mm → pixels
        radio_alfajor = PC.ALFAJOR_DIAMETRO_MM / 2
        ratio = PC.ALFAJOR_RADIO_MM / radio_alfajor if radio_alfajor > 0 else 0.82
        radio_crema = r * ratio
        px_per_mm = radio_crema / PC.ALFAJOR_RADIO_MM if PC.ALFAJOR_RADIO_MM > 0 else 1.0

        # Clip por progreso
        clipped = PathGenerator.clipped_path(text_path, progress_texto / 100.0)

        grosor_texto = max(2, 3 + (self._grosor / 100) * 4)

        # Capas 3D
        text_extrusion = 6 * scale if tilt > 3 else 2 * scale
        num_layers = 8 if tilt > 3 else 3
        for d in range(num_layers, 0, -1):
            frac = d / num_layers
            alpha = int(30 + frac * 140)
            offset_y = text_extrusion * frac
            painter.setPen(QPen(QColor(90, 55, 20, alpha), grosor_texto,
                               Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            self._render_path_raw(painter, clipped, cx, texto_surface_cy + offset_y, px_per_mm)

        # Superficie
        painter.setPen(QPen(QColor(160, 100, 40, 240), grosor_texto,
                           Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        self._render_path_raw(painter, clipped, cx, texto_surface_cy, px_per_mm)

        # Highlight
        painter.setPen(QPen(QColor(240, 200, 140, 100), max(1, grosor_texto * 0.5),
                           Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        self._render_path_raw(painter, clipped, cx, texto_surface_cy - 1.5, px_per_mm)

        painter.restore()

    # === Path rendering unificado ===

    def _dibujar_path(self, painter, cx, cy, radio_max, progreso):
        """Dibuja el patrón o imagen actual usando PathGenerator.
        Para imágenes: usa cache — el pipeline pesado ya se ejecutó en set_imagen().
        """
        from backend.config import PrinterConfig as PC
        from backend.path_generator import PathGenerator

        if self._imagen_path:
            # Usar cache: O(1), sin procesamiento CV2
            path = self._imagen_path_cache.get(self._imagen_path, [])
        else:
            pg = PathGenerator(PC.ALFAJOR_RADIO_MM, self._grosor)
            patron = self._patron if self._patron else "espiral"
            path = pg.generar(patron)

        if not path:
            return

        # Escalar mm → pixels
        px_per_mm = radio_max / PC.ALFAJOR_RADIO_MM if PC.ALFAJOR_RADIO_MM > 0 else 1.0

        # Clip por progreso
        clipped = PathGenerator.clipped_path(path, progreso / 100.0)

        self._render_path_raw(painter, clipped, cx, cy, px_per_mm)

    def _render_path_raw(self, painter, path, cx, cy, px_per_mm):
        """Renderiza un path (lista de segmentos) con QPainter."""
        for segment in path:
            if len(segment) < 2:
                continue
            qpath = QPainterPath()
            x0 = cx + segment[0][0] * px_per_mm
            y0 = cy + segment[0][1] * px_per_mm
            qpath.moveTo(x0, y0)
            for pt in segment[1:]:
                px = cx + pt[0] * px_per_mm
                py = cy + pt[1] * px_per_mm
                qpath.lineTo(px, py)
            painter.drawPath(qpath)

    # === UI ===

    def _dibujar_indicador_progreso(self, painter, cx, cy, size):
        r = size * 0.48
        painter.setPen(QPen(QColor(60, 60, 60, 100), 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), r, r)
        painter.setPen(QPen(QColor(77, 182, 172, 180), 3, Qt.SolidLine, Qt.RoundCap))
        rect = QRectF(cx - r, cy - r, r * 2, r * 2)
        painter.drawArc(rect, 90 * 16, -int(self._progreso * 3.6 * 16))

    def _dibujar_ui(self, painter, w, h):
        """Dibuja botones de vista en el lateral derecho y estado inferior."""
        # === Botones de vista (lateral derecho) ===
        self._btn_rects = []
        btn_w, btn_h = 55, 55
        margin_r = 8
        spacing = 8
        start_y = 10
        icons = ["⬇", "◇", "↻"]
        modes = [VIEW_TOP, VIEW_ISOMETRIC, VIEW_FREE]

        for i, (icon, mode) in enumerate(zip(icons, modes)):
            bx = w - btn_w - margin_r
            by = start_y + i * (btn_h + spacing)
            rect = QRectF(bx, by, btn_w, btn_h)
            self._btn_rects.append((rect, mode))

            # Fondo del botón
            is_active = (self._view_mode == mode)
            if is_active:
                painter.setBrush(QBrush(QColor(77, 182, 172, 200)))
                painter.setPen(QPen(QColor(77, 182, 172), 1.5))
            else:
                painter.setBrush(QBrush(QColor(50, 50, 55, 180)))
                painter.setPen(QPen(QColor(80, 80, 85), 1))

            painter.drawRoundedRect(rect, 8, 8)

            # Icono
            text_color = QColor(255, 255, 255) if is_active else QColor(160, 160, 165)
            painter.setPen(QPen(text_color))
            painter.setFont(QFont("Purisa", 20, QFont.Bold))
            painter.drawText(rect, Qt.AlignCenter, icon)

        # === Estado inferior ===
        if self._printing and self._progreso >= 100:
            texto = "✓ COMPLETADO"
            color = QColor(77, 182, 172, 200)
        elif self._printing and self._progreso > 0:
            texto = f"EXTRUYENDO... {self._progreso}%"
            color = QColor(255, 171, 64, 200)
        elif self._patron:
            texto = f"Vista previa: {self._patron}"
            color = QColor(150, 150, 150, 150)
        elif self._imagen_path:
            import os
            nombre = os.path.basename(self._imagen_path)
            texto = f"Vista previa: {nombre}"
            color = QColor(150, 150, 150, 150)
        elif self._texto:
            texto = f"Vista previa: '{self._texto}'"
            color = QColor(150, 150, 150, 150)
        else:
            texto = "Listo para decorar"
            color = QColor(100, 100, 100, 120)

        painter.setPen(QPen(color))
        painter.setFont(QFont("Purisa", 9))
        painter.drawText(QRectF(0, h - 22, w, 18), Qt.AlignCenter, texto)
