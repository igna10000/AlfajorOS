#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image Processor - Proyecto de Grado
Procesa imágenes (jpeg, png, etc.) para convertir a paths imprimibles.

Pipeline:
  1. Cargar imagen en escala de grises
  2. Redimensionar a tamaño máximo (para limitar costo computacional)
  3. Binarizar (Otsu o umbral fijo desde YAML)
  4. Invertir (fondo negro, trazos blancos)
  5. Esqueletizar (Zhang-Suen thinning) → trazo de 1px
  6. Trazar paths conectados desde el esqueleto
  7. Simplificar con approxPolyDP (epsilon configurable)
  8. Escalar y centrar en (0,0) dentro del radio del alfajor

Retorna paths en el mismo formato que PathGenerator:
  list[list[tuple[float, float]]]
  Cada sub-lista es un segmento continuo.
  Primer punto = travel, siguientes = extrusión.

OPTIMIZACIÓN: Cache a nivel de módulo — el pipeline se ejecuta UNA sola
vez por imagen. Llamadas sucesivas (canvas preview + gcode generation)
usan el resultado cacheado.
"""

import os
import numpy as np
import cv2

from backend.config import PrinterConfig as PC, SystemConfig

# ================================================================
# Cache global: {(image_path, radio_mm) -> list[segments]}
# Evita reprocesar la misma imagen en múltiples llamadas
# ================================================================
_PATH_CACHE: dict = {}

# Tamaño máximo de la imagen para procesar (en píxeles en el lado mayor)
# Imágenes más grandes se redimensionan para limitar el costo de Zhang-Suen
MAX_IMAGE_SIZE = 400


class ImageProcessor:
    """Procesa imágenes para convertir a paths imprimibles (un solo trazo)."""

    SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')

    # ================================================================
    # API pública
    # ================================================================

    @staticmethod
    def listar_imagenes():
        """
        Retorna lista de imágenes disponibles en ASSETS_DIR.
        Cada elemento: {'nombre': str, 'path': str, 'ext': str}
        """
        assets_dir = SystemConfig.ASSETS_DIR
        if not os.path.isdir(assets_dir):
            return []

        imagenes = []
        for fname in sorted(os.listdir(assets_dir)):
            ext = os.path.splitext(fname)[1].lower()
            if ext in ImageProcessor.SUPPORTED_EXTENSIONS:
                imagenes.append({
                    'nombre': os.path.splitext(fname)[0],
                    'path': os.path.join(assets_dir, fname),
                    'ext': ext,
                })
        return imagenes

    @staticmethod
    def limpiar_cache():
        """Limpia el cache global (útil si cambian parámetros en YAML)."""
        global _PATH_CACHE
        _PATH_CACHE.clear()

    @staticmethod
    def imagen_a_path(image_path, radio_mm):
        """
        Convierte una imagen a path de segmentos imprimibles.
        Usa cache global: el pipeline pesado solo se ejecuta una vez.

        Parámetros:
          image_path: ruta absoluta a la imagen
          radio_mm:   radio útil del alfajor en mm

        Retorna:
          list[list[tuple[float, float]]] — formato PathGenerator
          Coordenadas centradas en (0, 0) en mm.
        """
        global _PATH_CACHE

        # Clave de cache: path + radio (redondear a 2 decimales)
        cache_key = (image_path, round(radio_mm, 2))
        if cache_key in _PATH_CACHE:
            return _PATH_CACHE[cache_key]

        # --- Pipeline ---
        result = ImageProcessor._procesar(image_path, radio_mm)
        _PATH_CACHE[cache_key] = result
        return result

    @staticmethod
    def _procesar(image_path, radio_mm):
        """Ejecuta el pipeline completo de procesamiento."""

        # 1. Cargar en escala de grises
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"No se pudo cargar la imagen: {image_path}")

        # 2. Redimensionar si es mayor que MAX_IMAGE_SIZE (mejora velocidad ~10x)
        h, w = img.shape
        max_dim = max(h, w)
        if max_dim > MAX_IMAGE_SIZE:
            escala = MAX_IMAGE_SIZE / max_dim
            new_w = max(1, int(w * escala))
            new_h = max(1, int(h * escala))
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # 3. Binarizar
        umbral = PC.IMG_UMBRAL_BINARIO
        if umbral <= 0:
            # Otsu automático
            _, binario = cv2.threshold(
                img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
        else:
            _, binario = cv2.threshold(img, umbral, 255, cv2.THRESH_BINARY)

        # 4. Invertir: fondo (blanco) → negro(0), trazos (negro) → blanco(255)
        #    Las imágenes son fondo blanco con bordes negros
        binario_inv = cv2.bitwise_not(binario)

        # 5. Esqueletizar (Zhang-Suen thinning)
        esqueleto = ImageProcessor._esqueletizar(binario_inv)

        # 6. Trazar paths conectados desde el esqueleto
        paths_px = ImageProcessor._trazar_paths(esqueleto)

        # 7. Filtrar segmentos cortos (ruido)
        area_min = PC.IMG_AREA_MINIMA_PX
        paths_px = [
            p for p in paths_px
            if len(p) >= 2 and ImageProcessor._longitud_path(p) >= area_min
        ]

        if not paths_px:
            return []

        # 8. Simplificar con approxPolyDP
        epsilon_pct = PC.IMG_EPSILON_PCT
        paths_simplificados = []
        for path in paths_px:
            pts = np.array(path, dtype=np.float32).reshape(-1, 1, 2)
            perimetro = cv2.arcLength(pts, closed=False)
            if perimetro > 0:
                epsilon = epsilon_pct * perimetro
                aprox = cv2.approxPolyDP(pts, epsilon, closed=False)
                puntos = [(float(p[0][0]), float(p[0][1])) for p in aprox]
            else:
                puntos = path
            if len(puntos) >= 2:
                paths_simplificados.append(puntos)

        if not paths_simplificados:
            return []

        # 9. Normalizar: centrar en (0,0) y escalar a radio_mm
        margen = PC.IMG_MARGEN_MM
        radio_util = max(radio_mm - margen, radio_mm * 0.5)

        return ImageProcessor._normalizar_paths(
            paths_simplificados, img.shape[1], img.shape[0], radio_util
        )

    # ================================================================
    # Zhang-Suen Thinning (esqueletización) — NumPy vectorizado
    # ================================================================

    @staticmethod
    def _esqueletizar(binario):
        """
        Aplica Zhang-Suen thinning para reducir a esqueleto de 1px.
        Entrada: imagen binaria (0 y 255), trazos en 255.
        Retorna: imagen binaria con esqueleto de 1px.
        Implementación 100% vectorizada con NumPy (sin bucles Python).
        """
        img = (binario > 0).astype(np.uint8)
        prev = np.zeros_like(img)

        while True:
            marcados = ImageProcessor._zhang_suen_paso(img, paso=1)
            img[marcados] = 0
            marcados = ImageProcessor._zhang_suen_paso(img, paso=2)
            img[marcados] = 0

            if np.array_equal(img, prev):
                break
            prev = img.copy()

        return img * 255

    @staticmethod
    def _zhang_suen_paso(img, paso):
        """
        Un paso del algoritmo Zhang-Suen, completamente vectorizado.
        paso=1: sub-iteración 1, paso=2: sub-iteración 2.
        Retorna máscara booleana de píxeles a eliminar.
        """
        P2 = img[0:-2, 1:-1]   # arriba
        P3 = img[0:-2, 2:]     # arriba-derecha
        P4 = img[1:-1, 2:]     # derecha
        P5 = img[2:,   2:]     # abajo-derecha
        P6 = img[2:,   1:-1]   # abajo
        P7 = img[2:,   0:-2]   # abajo-izquierda
        P8 = img[1:-1, 0:-2]   # izquierda
        P9 = img[0:-2, 0:-2]   # arriba-izquierda
        P1 = img[1:-1, 1:-1]   # centro

        # Número de transiciones 0→1 en el anillo P2..P9..P2
        transiciones = (
            ((P2 == 0) & (P3 == 1)).astype(np.uint8) +
            ((P3 == 0) & (P4 == 1)).astype(np.uint8) +
            ((P4 == 0) & (P5 == 1)).astype(np.uint8) +
            ((P5 == 0) & (P6 == 1)).astype(np.uint8) +
            ((P6 == 0) & (P7 == 1)).astype(np.uint8) +
            ((P7 == 0) & (P8 == 1)).astype(np.uint8) +
            ((P8 == 0) & (P9 == 1)).astype(np.uint8) +
            ((P9 == 0) & (P2 == 1)).astype(np.uint8)
        )

        # Número de vecinos foreground (2 ≤ B ≤ 6)
        B = (P2 + P3 + P4 + P5 + P6 + P7 + P8 + P9).astype(np.uint8)

        cond_comun = (P1 == 1) & (transiciones == 1) & (B >= 2) & (B <= 6)

        if paso == 1:
            cond = cond_comun & ((P2 * P4 * P6) == 0) & ((P4 * P6 * P8) == 0)
        else:
            cond = cond_comun & ((P2 * P4 * P8) == 0) & ((P2 * P6 * P8) == 0)

        marcados = np.zeros_like(img, dtype=bool)
        marcados[1:-1, 1:-1] = cond
        return marcados

    # ================================================================
    # Trazado de paths desde esqueleto — optimizado con np.where
    # ================================================================

    @staticmethod
    def _trazar_paths(esqueleto):
        """
        Traza paths ordenados desde una imagen de esqueleto.
        Usa np.where para encontrar píxeles en O(1) en lugar de iterar toda
        la imagen píxel a píxel.

        Retorna: list[list[tuple[float, float]]] — coordenadas (x, y) en px
        """
        skel = (esqueleto > 0).astype(np.uint8)
        h, w = skel.shape
        visitado = np.zeros_like(skel, dtype=bool)

        # Vecindad 8-conectada (dy, dx)
        vecinos_8 = [(-1, -1), (-1, 0), (-1, 1),
                     (0,  -1),           (0,  1),
                     (1,  -1),  (1, 0), (1,  1)]

        def get_vecinos_no_visitados(y, x):
            result = []
            for dy, dx in vecinos_8:
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and skel[ny, nx] == 1 and not visitado[ny, nx]:
                    result.append((ny, nx))
            return result

        def contar_vecinos_skel(y, x):
            count = 0
            for dy, dx in vecinos_8:
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and skel[ny, nx] == 1:
                    count += 1
            return count

        # Obtener todos los píxeles del esqueleto eficientemente con np.where
        ys, xs = np.where(skel == 1)
        todos_pixeles = list(zip(ys.tolist(), xs.tolist()))

        if not todos_pixeles:
            return []

        # Detectar endpoints (1 vecino) — puntos de inicio naturales
        endpoints = [(y, x) for y, x in todos_pixeles
                     if contar_vecinos_skel(y, x) == 1]

        # Si no hay endpoints (figura cerrada), comenzar desde cualquier px
        if not endpoints:
            endpoints = [todos_pixeles[0]]

        paths = []

        def trazar_desde(start_y, start_x):
            """Traza un path lineal desde un punto de inicio."""
            path = []
            cy, cx = start_y, start_x
            while True:
                visitado[cy, cx] = True
                path.append((float(cx), float(cy)))
                siguientes = get_vecinos_no_visitados(cy, cx)
                if not siguientes:
                    break
                cy, cx = siguientes[0]
            return path

        # Trazar desde endpoints
        for sy, sx in endpoints:
            if not visitado[sy, sx]:
                path = trazar_desde(sy, sx)
                if len(path) >= 2:
                    paths.append(path)

        # Trazar ciclos cerrados que quedaron sin visitar
        for y, x in todos_pixeles:
            if not visitado[y, x]:
                path = trazar_desde(y, x)
                if len(path) >= 2:
                    paths.append(path)

        return paths

    # ================================================================
    # Normalización y escalado
    # ================================================================

    @staticmethod
    def _normalizar_paths(paths_px, img_w, img_h, radio_mm):
        """
        Normaliza paths de píxeles a coordenadas mm centradas en (0, 0).
        Escala proporcionalmente para que la imagen quepa dentro del radio.
        """
        # Bounding box usando numpy para velocidad
        all_pts = np.array(
            [(x, y) for path in paths_px for x, y in path],
            dtype=np.float32
        )
        if len(all_pts) == 0:
            return []

        min_x, min_y = all_pts.min(axis=0)
        max_x, max_y = all_pts.max(axis=0)

        cx_bb = (min_x + max_x) / 2.0
        cy_bb = (min_y + max_y) / 2.0
        ancho = max_x - min_x
        alto  = max_y - min_y
        dimension_max = max(ancho, alto)

        if dimension_max == 0:
            return []

        # Escalar al diámetro útil del alfajor
        escala = (2.0 * radio_mm) / dimension_max

        paths_mm = []
        for path in paths_px:
            segment = [
                ((x - cx_bb) * escala, (y - cy_bb) * escala)
                for x, y in path
            ]
            if len(segment) >= 2:
                paths_mm.append(segment)

        return paths_mm

    # ================================================================
    # Utilidades
    # ================================================================

    @staticmethod
    def _longitud_path(path):
        """Calcula la longitud total de un path en píxeles."""
        if len(path) < 2:
            return 0.0
        pts = np.array(path, dtype=np.float32)
        diffs = np.diff(pts, axis=0)
        return float(np.sum(np.hypot(diffs[:, 0], diffs[:, 1])))
