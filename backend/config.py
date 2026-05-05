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

    @classmethod
    def reload(cls):
        """Recarga la configuracion desde el YAML."""
        global _cfg
        _cfg = _load_yaml()
        # Re-asignar todos los atributos
        cls.ALFAJOR_DIAMETRO_MM = _get(_cfg, "alfajor", "diametro_mm", default=70.0)
        cls.ALFAJOR_MARGEN_MM = _get(_cfg, "alfajor", "margen_mm", default=3.0)
        cls.ALFAJOR_CENTRO_X = _get(_cfg, "alfajor", "centro_x", default=110.0)
        cls.ALFAJOR_CENTRO_Y = _get(_cfg, "alfajor", "centro_y", default=110.0)
        cls.ALFAJOR_RADIO_MM = (cls.ALFAJOR_DIAMETRO_MM / 2) - cls.ALFAJOR_MARGEN_MM
        cls.Z_ALTURA_MM = _get(_cfg, "impresion", "z_altura_mm", default=1.0)
        cls.VEL_IMPRESION = _get(_cfg, "impresion", "velocidad_impresion", default=1200)
        cls.VEL_VIAJE = _get(_cfg, "impresion", "velocidad_viaje", default=3000)
        cls.VEL_Z = _get(_cfg, "impresion", "velocidad_z", default=600)
        cls.FLUJO_E_POR_MM = _get(_cfg, "extrusor", "flujo_e_por_mm", default=0.05)
        cls.RETRACCION_MM = _get(_cfg, "extrusor", "retraccion_mm", default=2.0)
        cls.VEL_RETRACCION = _get(_cfg, "extrusor", "velocidad_retraccion", default=1800)
        cls.DESRETRACCION_MM = _get(_cfg, "extrusor", "desretraccion_mm", default=2.0)
        cls.PURGA_INICIAL_MM = _get(_cfg, "extrusor", "purga_inicial_mm", default=5.0)
        cls.PURGA_POS_X = _get(_cfg, "extrusor", "purga_pos_x", default=5.0)
        cls.PURGA_POS_Y = _get(_cfg, "extrusor", "purga_pos_y", default=5.0)
        cls.PURGA_POS_Z = _get(_cfg, "extrusor", "purga_pos_z", default=0.5)
        cls.Z_HOP_MM = _get(_cfg, "viaje", "z_hop_mm", default=3.0)
        cls.POS_FINAL_X = _get(_cfg, "viaje", "pos_final_x", default=10.0)
        cls.POS_FINAL_Y = _get(_cfg, "viaje", "pos_final_y", default=10.0)
        cls.POS_FINAL_Z = _get(_cfg, "viaje", "pos_final_z", default=10.0)


class SystemConfig:
    """Configuracion de la aplicacion (UI, patrones, etc)."""

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
