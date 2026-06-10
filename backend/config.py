#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuracion del sistema - Proyecto de Grado
Carga parametros desde printer_config.yaml y expone constantes del sistema.
"""

import os
import yaml


# Ruta al archivo de configuracion
_CONFIG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_YAML_PATH = os.path.join(_CONFIG_DIR, "printer_config.yaml")


def _load_yaml():
    """Carga el YAML de configuracion. Retorna dict vacio si no existe."""
    if os.path.exists(_YAML_PATH):
        with open(_YAML_PATH, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


def _get(data, *keys, default=None):
    """Accede a una clave anidada en un dict."""
    d = data
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k, None)
        else:
            return default
    return d if d is not None else default


# Cargar config al importar
_cfg = _load_yaml()


class PrinterConfig:
    """Parametros de impresion cargados desde printer_config.yaml."""

    # === Alfajor ===
    ALFAJOR_DIAMETRO_MM = _get(_cfg, "alfajor", "diametro_mm", default=70.0)
    ALFAJOR_MARGEN_MM = _get(_cfg, "alfajor", "margen_mm", default=3.0)
    ALFAJOR_CENTRO_X = _get(_cfg, "alfajor", "centro_x", default=110.0)
    ALFAJOR_CENTRO_Y = _get(_cfg, "alfajor", "centro_y", default=110.0)
    ALFAJOR_CENTRO_Z = _get(_cfg, "alfajor", "centro_z", default=11.0)
    ALFAJORES_CENTROS = _get(_cfg, "alfajor", "matriz_centros", default=[
        [35.0, 35.0, 11.0], [105.0, 35.0, 11.0], [175.0, 35.0, 11.0],
        [35.0, 105.0, 11.0], [105.0, 105.0, 11.0], [175.0, 105.0, 11.0],
        [35.0, 175.0, 11.0], [105.0, 175.0, 11.0], [175.0, 175.0, 11.0]
    ])
    ALFAJOR_RADIO_MM = (ALFAJOR_DIAMETRO_MM / 2) - ALFAJOR_MARGEN_MM

    # === Impresion ===
    Z_ALTURA_MM = _get(_cfg, "impresion", "z_altura_mm", default=1.0)
    VEL_IMPRESION = _get(_cfg, "impresion", "velocidad_impresion", default=1200)
    VEL_VIAJE = _get(_cfg, "impresion", "velocidad_viaje", default=3000)
    VEL_Z = _get(_cfg, "impresion", "velocidad_z", default=600)
    VEL_PRIMERA_CAPA = _get(_cfg, "impresion", "velocidad_primera_capa", default=800)

    # === Extrusor ===
    BOQUILLA_MM = _get(_cfg, "extrusor", "diametro_boquilla_mm", default=3.0)
    FLUJO_E_POR_MM = _get(_cfg, "extrusor", "flujo_e_por_mm", default=0.05)
    RETRACCION_HABILITADA = _get(_cfg, "extrusor", "retraccion_habilitada", default=True)
    RETRACCION_MM = _get(_cfg, "extrusor", "retraccion_mm", default=2.0)
    VEL_RETRACCION = _get(_cfg, "extrusor", "velocidad_retraccion", default=1800)
    DESRETRACCION_MM = _get(_cfg, "extrusor", "desretraccion_mm", default=2.0)
    PURGA_INICIAL_MM = _get(_cfg, "extrusor", "purga_inicial_mm", default=5.0)
    PURGA_POS_X = _get(_cfg, "extrusor", "purga_pos_x", default=5.0)
    PURGA_POS_Y = _get(_cfg, "extrusor", "purga_pos_y", default=5.0)
    PURGA_POS_Z = _get(_cfg, "extrusor", "purga_pos_z", default=0.5)

    # === Viaje ===
    Z_HOP_MM = _get(_cfg, "viaje", "z_hop_mm", default=3.0)
    POS_FINAL_X = _get(_cfg, "viaje", "pos_final_x", default=10.0)
    POS_FINAL_Y = _get(_cfg, "viaje", "pos_final_y", default=10.0)
    POS_FINAL_Z = _get(_cfg, "viaje", "pos_final_z", default=10.0)
    FIN_RETRACCION_MM = _get(_cfg, "viaje", "fin_retraccion_mm", default=30.0)

    # === Linea ===
    GROSOR_DEFAULT_MM = _get(_cfg, "linea", "grosor_default_mm", default=2.0)
    GROSOR_MIN_MM = _get(_cfg, "linea", "grosor_min_mm", default=0.5)
    GROSOR_MAX_MM = _get(_cfg, "linea", "grosor_max_mm", default=5.0)

    # === Serial ===
    SERIAL_BAUDRATE = _get(_cfg, "serial", "baudrate", default=115200)
    SERIAL_SCAN_PATTERNS = _get(_cfg, "serial", "scan_patterns",
                                default=["/dev/ttyUSB*", "/dev/ttyACM*"])
    SERIAL_RECONNECT_MS = _get(_cfg, "serial", "reconnect_ms", default=5000)
    SERIAL_TIMEOUT_S = _get(_cfg, "serial", "timeout_s", default=2.0)

    # === Imagen ===
    IMG_EPSILON_PCT = _get(_cfg, "imagen", "epsilon_pct", default=0.005)
    IMG_UMBRAL_BINARIO = _get(_cfg, "imagen", "umbral_binario", default=0)
    IMG_AREA_MINIMA_PX = _get(_cfg, "imagen", "area_minima_px", default=50)
    IMG_MARGEN_MM = _get(_cfg, "imagen", "margen_imagen_mm", default=2.0)

    # === Cilindro 3D ===
    CILINDRO_NUM_CAPAS = _get(_cfg, "cilindro", "num_capas", default=5)
    CILINDRO_Z_POR_CAPA_MM = _get(_cfg, "cilindro", "z_por_capa_mm", default=2.0)

    @classmethod
    def reload(cls):
        """Recarga la configuracion desde el YAML."""
        global _cfg
        _cfg = _load_yaml()
        # === Alfajor ===
        cls.ALFAJOR_DIAMETRO_MM = _get(_cfg, "alfajor", "diametro_mm", default=70.0)
        cls.ALFAJOR_MARGEN_MM = _get(_cfg, "alfajor", "margen_mm", default=3.0)
        cls.ALFAJOR_CENTRO_X = _get(_cfg, "alfajor", "centro_x", default=110.0)
        cls.ALFAJOR_CENTRO_Y = _get(_cfg, "alfajor", "centro_y", default=110.0)
        cls.ALFAJOR_CENTRO_Z = _get(_cfg, "alfajor", "centro_z", default=11.0)
        cls.ALFAJORES_CENTROS = _get(_cfg, "alfajor", "matriz_centros", default=[
            [35.0, 35.0, 11.0], [105.0, 35.0, 11.0], [175.0, 35.0, 11.0],
            [35.0, 105.0, 11.0], [105.0, 105.0, 11.0], [175.0, 105.0, 11.0],
            [35.0, 175.0, 11.0], [105.0, 175.0, 11.0], [175.0, 175.0, 11.0]
        ])
        cls.ALFAJOR_RADIO_MM = (cls.ALFAJOR_DIAMETRO_MM / 2) - cls.ALFAJOR_MARGEN_MM
        # === Impresion ===
        cls.Z_ALTURA_MM = _get(_cfg, "impresion", "z_altura_mm", default=1.0)
        cls.VEL_IMPRESION = _get(_cfg, "impresion", "velocidad_impresion", default=1200)
        cls.VEL_VIAJE = _get(_cfg, "impresion", "velocidad_viaje", default=3000)
        cls.VEL_Z = _get(_cfg, "impresion", "velocidad_z", default=600)
        cls.VEL_PRIMERA_CAPA = _get(_cfg, "impresion", "velocidad_primera_capa", default=800)
        # === Extrusor ===
        cls.BOQUILLA_MM = _get(_cfg, "extrusor", "diametro_boquilla_mm", default=3.0)
        cls.FLUJO_E_POR_MM = _get(_cfg, "extrusor", "flujo_e_por_mm", default=0.05)
        cls.RETRACCION_HABILITADA = _get(_cfg, "extrusor", "retraccion_habilitada", default=True)
        cls.RETRACCION_MM = _get(_cfg, "extrusor", "retraccion_mm", default=2.0)
        cls.VEL_RETRACCION = _get(_cfg, "extrusor", "velocidad_retraccion", default=1800)
        cls.DESRETRACCION_MM = _get(_cfg, "extrusor", "desretraccion_mm", default=2.0)
        cls.PURGA_INICIAL_MM = _get(_cfg, "extrusor", "purga_inicial_mm", default=5.0)
        cls.PURGA_POS_X = _get(_cfg, "extrusor", "purga_pos_x", default=5.0)
        cls.PURGA_POS_Y = _get(_cfg, "extrusor", "purga_pos_y", default=5.0)
        cls.PURGA_POS_Z = _get(_cfg, "extrusor", "purga_pos_z", default=0.5)
        # === Viaje ===
        cls.Z_HOP_MM = _get(_cfg, "viaje", "z_hop_mm", default=3.0)
        cls.POS_FINAL_X = _get(_cfg, "viaje", "pos_final_x", default=10.0)
        cls.POS_FINAL_Y = _get(_cfg, "viaje", "pos_final_y", default=10.0)
        cls.POS_FINAL_Z = _get(_cfg, "viaje", "pos_final_z", default=10.0)
        cls.FIN_RETRACCION_MM = _get(_cfg, "viaje", "fin_retraccion_mm", default=30.0)
        # === Linea ===
        cls.GROSOR_DEFAULT_MM = _get(_cfg, "linea", "grosor_default_mm", default=2.0)
        cls.GROSOR_MIN_MM = _get(_cfg, "linea", "grosor_min_mm", default=0.5)
        cls.GROSOR_MAX_MM = _get(_cfg, "linea", "grosor_max_mm", default=5.0)
        # === Serial ===
        cls.SERIAL_BAUDRATE = _get(_cfg, "serial", "baudrate", default=115200)
        cls.SERIAL_SCAN_PATTERNS = _get(_cfg, "serial", "scan_patterns",
                                        default=["/dev/ttyUSB*", "/dev/ttyACM*"])
        cls.SERIAL_RECONNECT_MS = _get(_cfg, "serial", "reconnect_ms", default=5000)
        cls.SERIAL_TIMEOUT_S = _get(_cfg, "serial", "timeout_s", default=2.0)
        # === Imagen ===
        cls.IMG_EPSILON_PCT = _get(_cfg, "imagen", "epsilon_pct", default=0.005)
        cls.IMG_UMBRAL_BINARIO = _get(_cfg, "imagen", "umbral_binario", default=0)
        cls.IMG_AREA_MINIMA_PX = _get(_cfg, "imagen", "area_minima_px", default=50)
        cls.IMG_MARGEN_MM = _get(_cfg, "imagen", "margen_imagen_mm", default=2.0)
        # === Cilindro 3D ===
        cls.CILINDRO_NUM_CAPAS = _get(_cfg, "cilindro", "num_capas", default=5)
        cls.CILINDRO_Z_POR_CAPA_MM = _get(_cfg, "cilindro", "z_por_capa_mm", default=2.0)

    @classmethod
    def save(cls):
        """Guarda la configuracion actual al archivo YAML."""
        data = {
            'alfajor': {
                'diametro_mm': float(cls.ALFAJOR_DIAMETRO_MM),
                'margen_mm': float(cls.ALFAJOR_MARGEN_MM),
                'centro_x': float(cls.ALFAJOR_CENTRO_X),
                'centro_y': float(cls.ALFAJOR_CENTRO_Y),
                'centro_z': float(cls.ALFAJOR_CENTRO_Z),
                'matriz_centros': [ [float(x), float(y), float(z)] for x, y, z in cls.ALFAJORES_CENTROS ],
            },
            'impresion': {
                'z_altura_mm': float(cls.Z_ALTURA_MM),
                'velocidad_impresion': int(cls.VEL_IMPRESION),
                'velocidad_viaje': int(cls.VEL_VIAJE),
                'velocidad_z': int(cls.VEL_Z),
                'velocidad_primera_capa': int(cls.VEL_PRIMERA_CAPA),
            },
            'extrusor': {
                'diametro_boquilla_mm': float(cls.BOQUILLA_MM),
                'flujo_e_por_mm': float(cls.FLUJO_E_POR_MM),
                'retraccion_habilitada': bool(cls.RETRACCION_HABILITADA),
                'retraccion_mm': float(cls.RETRACCION_MM),
                'velocidad_retraccion': int(cls.VEL_RETRACCION),
                'desretraccion_mm': float(cls.DESRETRACCION_MM),
                'purga_inicial_mm': float(cls.PURGA_INICIAL_MM),
                'purga_pos_x': float(cls.PURGA_POS_X),
                'purga_pos_y': float(cls.PURGA_POS_Y),
                'purga_pos_z': float(cls.PURGA_POS_Z),
            },
            'viaje': {
                'z_hop_mm': float(cls.Z_HOP_MM),
                'pos_final_x': float(cls.POS_FINAL_X),
                'pos_final_y': float(cls.POS_FINAL_Y),
                'pos_final_z': float(cls.POS_FINAL_Z),
                'fin_retraccion_mm': float(cls.FIN_RETRACCION_MM),
            },
            'linea': {
                'grosor_default_mm': float(cls.GROSOR_DEFAULT_MM),
                'grosor_min_mm': float(cls.GROSOR_MIN_MM),
                'grosor_max_mm': float(cls.GROSOR_MAX_MM),
            },
            'serial': {
                'baudrate': int(cls.SERIAL_BAUDRATE),
                'scan_patterns': list(cls.SERIAL_SCAN_PATTERNS),
                'reconnect_ms': int(cls.SERIAL_RECONNECT_MS),
                'timeout_s': float(cls.SERIAL_TIMEOUT_S),
            },
            'imagen': {
                'epsilon_pct': float(cls.IMG_EPSILON_PCT),
                'umbral_binario': int(cls.IMG_UMBRAL_BINARIO),
                'area_minima_px': int(cls.IMG_AREA_MINIMA_PX),
                'margen_imagen_mm': float(cls.IMG_MARGEN_MM),
            },
            'cilindro': {
                'num_capas': int(cls.CILINDRO_NUM_CAPAS),
                'z_por_capa_mm': float(cls.CILINDRO_Z_POR_CAPA_MM),
            },
        }
        # Escribir con comentarios de cabecera
        header = (
            "# ============================================================\n"
            "# AlfajorOS - Configuracion de Impresora\n"
            "# Ender 3 Pro + Marlin - Extrusion de Crema en Frio\n"
            "# ============================================================\n\n"
        )
        with open(_YAML_PATH, 'w') as f:
            f.write(header)
            # Escribir cada seccion con comentario
            section_comments = {
                'alfajor': '# === Alfajor ===',
                'impresion': '# === Impresion ===',
                'extrusor': '# === Extrusor ===',
                'viaje': '# === Viaje ===',
                'linea': '# === Linea de crema ===',
                'serial': '# === Serial ===',
                'imagen': '# === Imagen ===',
                'cilindro': '# === Cilindro 3D ===',
            }
            for key in ['alfajor', 'impresion', 'extrusor', 'viaje', 'linea', 'serial', 'imagen', 'cilindro']:
                f.write(f"{section_comments[key]}\n")
                yaml.dump({key: data[key]}, f, default_flow_style=False,
                          allow_unicode=True, sort_keys=False)
                f.write("\n")


class SystemConfig:
    """Configuracion de la aplicacion (UI, patrones, etc)."""

    # === Ruta de assets ===
    ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')

    # === Dimensiones de pantalla ===
    SCREEN_WIDTH = 1024
    SCREEN_HEIGHT = 600

    # === Alfajor (delegado a PrinterConfig) ===
    ALFAJOR_DIAMETRO_CM = PrinterConfig.ALFAJOR_DIAMETRO_MM / 10
    ALFAJOR_MARGEN_MM = PrinterConfig.ALFAJOR_MARGEN_MM
    ALFAJOR_ALTURA_CREMA_MM = PrinterConfig.Z_ALTURA_MM

    # === Temperaturas (C) ===
    TEMP_CREMA_DEFAULT = 18
    TEMP_CREMA_MIN = 5
    TEMP_CREMA_MAX = 45
    TEMP_BASE_DEFAULT = 15
    TEMP_BASE_MIN = 5
    TEMP_BASE_MAX = 30

    # === Extrusion ===
    VELOCIDAD_DEFAULT = 25
    VELOCIDAD_MIN = 5
    VELOCIDAD_MAX = 80
    GROSOR_LINEA_DEFAULT = PrinterConfig.GROSOR_DEFAULT_MM
    GROSOR_LINEA_MIN = PrinterConfig.GROSOR_MIN_MM
    GROSOR_LINEA_MAX = PrinterConfig.GROSOR_MAX_MM
    PRESION_DEFAULT = 60
    PRESION_MIN = 10
    PRESION_MAX = 100
    BOQUILLA_DEFAULT = PrinterConfig.BOQUILLA_MM

    # === Tipos de crema ===
    TIPOS_CREMA = [
        "Dulce de Leche", "Chocolate", "Vainilla",
        "Crema Chantilly", "Merengue", "Ganache",
    ]

    # === Consistencias ===
    CONSISTENCIAS = ["Firme", "Media", "Suave", "Muy suave"]

    # === Patrones decorativos ===
    PATRONES = [
        "Espiral clasica", "Zigzag horizontal", "Circulos concentricos",
        "Rejilla cruzada", "Estrella", "Corazon",
        "Ondas paralelas", "Relleno completo", "Borde decorativo",
        "Cilindro 3D",
    ]

    PATRONES_PRO = [
        "Espiral", "Zigzag", "Circulos", "Lineas",
        "Rejilla", "Libre",
    ]

    # === Tiempos ===
    SCREENSAVER_TIMEOUT_S = 60
    EXTRUSION_TICK_MS = 100
    ANIMACION_FPS = 30

    # === Seguridad ===
    PRO_PASSWORD = "pro2026"
    MAX_TEXTO_CHARS = 10

    # === Colores del tema ===
    COLOR_PRIMARIO = "#4DB6AC"
    COLOR_FONDO = "#2b2b2b"
    COLOR_FONDO_OSCURO = "#1e1e1e"
    COLOR_SUPERFICIE = "#3c3c3c"
    COLOR_TEXTO = "#e0e0e0"
    COLOR_ACENTO = "#FFAB40"
    COLOR_ERROR = "#F66151"
    COLOR_BORDE = "#555"
