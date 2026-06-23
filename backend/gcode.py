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

    def set_servo(self, angle):
        """Genera el comando custom para mover el servo, sincronizado con M400."""
        self.comment(f"Control de Servo a {angle} grados")
        self.raw("M400") # Vaciar buffer de Marlin para sincronizar con Python
        self.raw(f"M280 P0 S{angle}")

    def home(self, manual_z0=False):
        if manual_z0:
            self.comment("Homing omitido (preservando Z0 manual)")
            self.raw("G91")
            self.raw("G1 Z5 F600")
            self.raw("G90")
            # Se omite G28 X Y porque en Marlin G28 borra el offset G92 Z0
        else:
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

    def dwell(self, seconds):
        """Pausa la ejecucion por n segundos."""
        self.raw(f"G4 P{int(seconds * 1000)}")

    def travel(self, x, y, z=None):
        """Movimiento sin extruir — continuo, sin detener XY.
        Si retraccion habilitada: retrae E durante el movimiento XY.
        Si deshabilitada: solo mueve XY sin tocar E.
        Sin Z-hop en ningun caso.
        """
        if PC.RETRACCION_HABILITADA and not self.retracted:
            self.e_total -= PC.RETRACCION_MM
            self.retracted = True
        # Mover XY y opcionalmente Z (un solo comando, sin paradas)
        z_str = f" Z{z:.3f}" if z is not None else ""
        self.raw(f"G1 X{x:.3f} Y{y:.3f}{z_str} E{self.e_total:.4f} F{PC.VEL_VIAJE}")
        self.current_x = x
        self.current_y = y
        if z is not None:
            self.current_z = z

    def extrude_to(self, x, y, z=None, speed=None):
        """Movimiento con extrusion."""
        if speed is None:
            speed = PC.VEL_IMPRESION
        # Si esta retraido, absorber desretraccion en este movimiento
        if self.retracted:
            self.e_total += PC.DESRETRACCION_MM
            self.retracted = False
        dx = x - self.current_x
        dy = y - self.current_y
        dz = (z - self.current_z) if z is not None else 0
        dist = math.sqrt(dx * dx + dy * dy + dz * dz)
        if dist < 0.01:
            return
        self.e_total += dist * PC.FLUJO_E_POR_MM
        z_str = f" Z{z:.3f}" if z is not None else ""
        self.raw(f"G1 X{x:.3f} Y{y:.3f}{z_str} E{self.e_total:.4f} F{speed}")
        self.current_x = x
        self.current_y = y
        if z is not None:
            self.current_z = z

    def _retract(self):
        self.e_total -= PC.RETRACCION_MM
        self.raw(f"G1 E{self.e_total:.4f} F{PC.VEL_RETRACCION}")
        self.retracted = True

    def _unretract(self):
        self.e_total += PC.DESRETRACCION_MM
        self.raw(f"G1 E{self.e_total:.4f} F{PC.VEL_RETRACCION}")
        self.retracted = False

    def park(self, fin_retraccion_mm=None):
        """Secuencia de finalizacion segura:
        1. Movimiento simultaneo X+Y+Z en un solo G0 rapido al punto de reposo.
        2. Retraccion forzada en el punto de reposo, segun solicitud del usuario.
        """
        if fin_retraccion_mm is None:
            fin_retraccion_mm = PC.FIN_RETRACCION_MM

        # --- Paso 1: Subir Z seguro y luego mover XY ---
        safe_z = max(PC.POS_FINAL_Z, self.current_z + PC.Z_HOP_MM * 2)
        self.comment(
            f"Estacionamiento: Subir Z={safe_z:.1f} seguro, "
            f"XY={PC.POS_FINAL_X:.1f},{PC.POS_FINAL_Y:.1f}"
        )
        self.raw(f"G1 Z{safe_z:.1f} F{PC.VEL_Z}")
        self.raw(
            f"G0 X{PC.POS_FINAL_X:.1f} Y{PC.POS_FINAL_Y:.1f} F{PC.VEL_VIAJE}"
        )
        self.raw("M211 S1") # Reactivar limites de software tras estacionar
        self.current_x = PC.POS_FINAL_X
        self.current_y = PC.POS_FINAL_Y
        self.current_z = safe_z

        # --- Paso 2: Retraccion forzada al finalizar (en el punto de reposo) ---
        if fin_retraccion_mm > 0 and not self.retracted:
            self.comment(f"Retraccion final: {fin_retraccion_mm} mm (en reposo)")
            self.e_total -= fin_retraccion_mm
            self.raw(f"G1 E{self.e_total:.4f} F{PC.VEL_RETRACCION}")
            self.retracted = True

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
        self.radio = PC.ALFAJOR_RADIO_MM

    def generar_completo(self, configs_serie=None, manual_z0=False, manual_home=None, fin_retraccion_mm=None, purga_inicial_mm=None, modo_serie=False):
        """
        Genera G-Code completo para un patron y/o texto basado en configs_serie.
        Retorna (gcode_str, metadata) donde metadata contiene:
          - drawing_start: linea donde empieza el dibujo
          - drawing_end: linea donde termina el dibujo
          - total_lines: total de lineas de codigo
        """
        g = GCodeBuilder()

        if not configs_serie:
            configs_serie = [{"patron": "", "texto": "", "grosor": 50, "imagen_path": ""} for _ in range(9)]

        # Recargar config desde YAML para garantizar centros actualizados
        PC.reload()
        self.radio = PC.ALFAJOR_RADIO_MM  # Actualizar radio tras reload (incluye margen)

        # Configurar matriz de centros
        if modo_serie:
            centros = PC.ALFAJORES_CENTROS
            manual_z0 = False # En modo serie SIEMPRE se requiere G28 para respetar los Z absolutos
        else:
            if manual_z0 and manual_home is not None:
                centros = [list(manual_home)]
            else:
                centros = [[PC.ALFAJOR_CENTRO_X, PC.ALFAJOR_CENTRO_Y, PC.ALFAJOR_CENTRO_Z]]

        # Header
        g.comment("=" * 50)
        g.comment("AlfajorOS - G-Code de Crema")
        g.comment(f"Modo Serie: {modo_serie}")
        g.comment(f"Radio util: {self.radio:.1f} mm")
        g.comment("=" * 50)
        g.blank()

        # Inicializacion
        g.home(manual_z0)
        g.set_absolute()
        g.cold_extrusion()
        g.raw("M211 S0") # Deshabilitar limites de software para permitir Z negativo
        g.reset_extruder()
        g.blank()

        # Mover a posicion de purga
        g.comment("Posicionando para purga")
        if manual_z0:
            purga_z = centros[0][2] + 5.0
        else:
            purga_z = PC.PURGA_POS_Z
        g.move_z(purga_z + PC.Z_HOP_MM)
        g.raw(f"G0 X{PC.PURGA_POS_X:.1f} Y{PC.PURGA_POS_Y:.1f} F{PC.VEL_VIAJE}")
        g.move_z(purga_z)
        g.blank()

        # Purga
        if purga_inicial_mm is None:
            purga_inicial_mm = PC.PURGA_INICIAL_MM

        if purga_inicial_mm > 0:
            g.comment("Purga inicial")
            g.set_servo(PC.SERVO_ANGULO_ABIERTO)
            g.e_total += purga_inicial_mm
            g.raw(f"G1 E{g.e_total:.4f} F600")
            g.set_servo(PC.SERVO_ANGULO_CERRADO)
            g.reset_extruder()
            g.retracted = True  # Post-purga: considerar retraido
            g.blank()

        drawing_start = g.line_count

        # Iterar sobre los centros (1 o 9 alfajores)
        for i, (cx, cy, cz) in enumerate(centros):
            c = configs_serie[i]
            patron = c["patron"]
            texto = c["texto"]
            imagen_path = c["imagen_path"]
            grosor_pct = c["grosor"]

            # Omitir si no hay diseño para este alfajor
            if not patron and not texto and not imagen_path:
                continue

            self.cx = cx
            self.cy = cy
            self.z_print = cz + PC.Z_ALTURA_MM
            
            g.comment(f"--- Iniciando Alfajor {i+1} en X:{cx:.1f} Y:{cy:.1f} Z:{self.z_print:.2f} ---")
            
            # Viaje al centro del alfajor con Z-Hop
            safe_z = max(g.current_z + PC.Z_HOP_MM, self.z_print + PC.Z_HOP_MM)
            g.move_z(safe_z)
            g.raw(f"G0 X{self.cx:.1f} Y{self.cy:.1f} F{PC.VEL_VIAJE}")
            g.move_z(self.z_print)
            g.current_x = self.cx
            g.current_y = self.cy
            g.current_z = self.z_print
            
            # Abrir servo durante toda la galleta
            g.set_servo(PC.SERVO_ANGULO_ABIERTO)
            g.blank()
            
            # Patron
            if patron:
                g.comment(f"=== Patron: {patron} ===")
                pg = PathGenerator(self.radio, grosor_pct)
                p_lower = patron.lower()
                if "domo" in p_lower:
                    # Cilindro Domo 3D con Z acelerado
                    num_capas = PC.DOMO_NUM_CAPAS
                    z_por_capa = PC.DOMO_Z_POR_CAPA_MM
                    capas_base = PC.DOMO_CAPAS_BASE
                    z_aceleracion = PC.DOMO_Z_ACELERACION
                    z_acum = 0.0
                    capas_domo = max(1, num_capas - capas_base)
                    for capa in range(num_capas):
                        g.comment(f"--- Domo Capa {capa + 1}/{num_capas} ---")
                        if capa > 0:
                            if capa <= capas_base:
                                # Capas base: Z uniforme
                                z_acum += z_por_capa
                            else:
                                # Capas domo: Z acelerado
                                idx_domo = capa - capas_base
                                t = idx_domo / capas_domo
                                z_acum += z_por_capa * (1.0 + z_aceleracion * (t ** 2))
                            g.move_z(self.z_print + z_acum)
                        path_capa = pg.generar_domo_capa(capa, num_capas)
                        self._path_to_gcode(g, path_capa)
                        g.blank()
                        
                    if PC.DOMO_DEMO_ARCOS:
                        g.comment("--- Demostracion Arcos 3D Convexos ---")
                        path_arcos = pg.generar_arcos_3d_demo()
                        # El base_z es la altura final del domo
                        z_final_domo = self.z_print + z_acum
                        self._path_to_gcode(g, path_arcos, base_z=z_final_domo)
                        g.blank()
                elif "cono" in p_lower and "estrella" in p_lower:
                    # Conos Estrella 3D
                    num_capas = PC.CONOS_NUM_CAPAS
                    z_por_capa = PC.CONOS_Z_POR_CAPA_MM
                    for capa in range(num_capas):
                        g.comment(f"--- Conos Estrella Capa {capa + 1}/{num_capas} ---")
                        z_actual = self.z_print + (capa * z_por_capa)
                        if capa > 0:
                            g.move_z(z_actual)
                        path_capa = pg.generar_conos_capa(capa, num_capas)
                        self._path_to_gcode(g, path_capa)
                        g.blank()
                elif "escalonado" in p_lower:
                    # Cilindro Escalonado 3D
                    num_capas = PC.ESCALONADO_NUM_CAPAS
                    z_por_capa = PC.ESCALONADO_Z_POR_CAPA_MM
                    for capa in range(num_capas):
                        g.comment(f"--- Escalonado Capa {capa + 1}/{num_capas} ---")
                        z_actual = self.z_print + (capa * z_por_capa)
                        if capa > 0:
                            g.move_z(z_actual)
                        path_capa = pg.generar_escalonado_capa(capa, num_capas)
                        self._path_to_gcode(g, path_capa)
                        g.blank()
                elif "cilindro" in p_lower:
                    # Cilindro 3D original
                    num_capas = PC.CILINDRO_NUM_CAPAS
                    z_por_capa = PC.CILINDRO_Z_POR_CAPA_MM
                    path_capa = pg.generar_cilindro_capa()
                    for capa in range(num_capas):
                        g.comment(f"--- Capa {capa + 1}/{num_capas} ---")
                        z_actual = self.z_print + (capa * z_por_capa)
                        if capa > 0:
                             g.move_z(z_actual)
                        self._path_to_gcode(g, path_capa)
                        g.blank()
                else:
                    path = pg.generar(patron)
                    self._path_to_gcode(g, path)
                    g.blank()

            # Texto
            if texto:
                g.comment(f"=== Texto: {texto} ===")
                pg_txt = PathGenerator(self.radio, grosor_pct)
                path_texto = pg_txt.generar_texto(texto)
                self._path_to_gcode(g, path_texto)
                g.blank()

            # Imagen personalizada
            if imagen_path:
                g.comment(f"=== Imagen: {os.path.basename(imagen_path)} ===")
                pg_img = PathGenerator(self.radio, grosor_pct)
                path_img = pg_img.generar_imagen(imagen_path)
                self._path_to_gcode(g, path_img)
                g.blank()
                
            # Cerrar servo al finalizar la galleta
            g.set_servo(PC.SERVO_ANGULO_CERRADO)
            g.blank()
                
            # Al terminar el alfajor, si hay más, forzamos retracción para el viaje
            if i < len(centros) - 1:
                g.comment(f"Retracción para viaje al siguiente alfajor")
                if not g.retracted:
                    g._retract()
            
        drawing_end = g.line_count

        # Footer
        g.comment("=== Fin ===")
        g.park(fin_retraccion_mm)
        g.set_servo(PC.SERVO_ANGULO_CERRADO)
        g.blank()

        metadata = {
            "drawing_start": drawing_start,
            "drawing_end": drawing_end,
            "total_lines": g.line_count,
        }

        return g.build(), metadata

    def _path_to_gcode(self, g, path, base_z=None):
        """
        Convierte un path de segmentos a comandos G-Code.
        Cada segmento: primer punto = travel, resto = extrude.
        Coordenadas del path estan centradas en (0,0),
        se trasladan a (cx, cy) del alfajor en la cama.
        X se niega para corregir el espejo entre la vista previa
        (pantalla) y la orientacion fisica de la impresora.
        Si base_z se provee y el punto tiene un offset Z, genera 3D move.
        """
        for segment in path:
            if len(segment) < 2:
                continue
            
            def get_z(pt):
                return base_z + pt[2] if base_z is not None and len(pt) > 2 else None

            # Travel al primer punto del segmento
            pt0 = segment[0]
            x0 = self.cx - pt0[0]
            y0 = self.cy + pt0[1]
            z0 = get_z(pt0)
            g.travel(x0, y0, z=z0)
            
            # Extrude por el resto del segmento
            for pt in segment[1:]:
                px = self.cx - pt[0]
                py = self.cy + pt[1]
                pz = get_z(pt)
                g.extrude_to(px, py, z=pz)


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
