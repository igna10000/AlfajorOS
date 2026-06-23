# AlfajorOS - Project Context

Este archivo proporciona el contexto técnico completo del proyecto **AlfajorOS**. Sirve como guía de referencia para agentes de programación y desarrolladores que necesiten entender la arquitectura, las tecnologías y las reglas del sistema.

## 1. Descripción General
**AlfajorOS** es una aplicación de escritorio basada en **PySide6** (Qt for Python), diseñada para ejecutarse en una pantalla táctil (por lo que el cursor de la interfaz gráfica se oculta por defecto). Su propósito es servir de interfaz de control para una impresora 3D (ejecutando firmware Marlin) que ha sido modificada físicamente para extruir de forma fría crema o dulce de leche sobre alfajores.

## 2. Tecnologías y Dependencias
- **Python 3**
- **PySide6**: Para toda la interfaz gráfica de usuario (GUI).
- **pyserial**: Para la comunicación por puerto serie con la impresora 3D.
- **opencv-python-headless** & **numpy**: Para el procesamiento de imágenes (conversión de imagen a bandeja/G-Code).
- **PyYAML**: Para el manejo dinámico de la configuración de la máquina (`printer_config.yaml`).

## 3. Estructura del Proyecto

```
AlfajorOS/
├── main.py                     # Entry point de la app. Inicializa la UI global.
├── printer_config.yaml         # Archivo persistente con todos los parámetros de calibración.
├── requirements.txt            # Dependencias del sistema.
├── backend/                    # Lógica de negocio, conexión y algoritmos.
│   ├── config.py               # Clase `PrinterConfig` para exponer/escribir variables de `.yaml` y `SystemConfig`.
│   ├── extruder.py             # Lógica de generación de movimientos de extrusión.
│   ├── gcode.py                # Generador de código G-Code (trayectorias planas, 3D, retracciones).
│   ├── image_processor.py      # Transforma imágenes blanco y negro en secuencias G-Code.
│   ├── path_generator.py       # Crea patrones y trayectorias de decorado.
│   └── printer.py              # Administrador de la conexión Serial. Emite señales Qt asíncronas de progreso.
└── frontend/                   # Capa de presentación (UI).
    ├── app.py                  # Controlador global que maneja la navegación y recursos.
    ├── styles.py               # Hojas de estilo globales (QSS) para una UI oscura/moderna.
    ├── resources/              # Archivos .ui estáticos generados por QtDesigner.
    ├── views/                  # Pantallas principales de la interfaz.
    │   ├── main_view.py        # Menú principal.
    │   ├── pro_mode.py         # Opciones y debug avanzado.
    │   ├── product_selection.py# Flujo de trabajo para seleccionar decorado.
    │   └── ...                 # Screensaver, opciones de imagen/texto, etc.
    └── widgets/                # Componentes reutilizables personalizados.
        ├── alfajor_canvas.py   # Lienzo de previsualización de trayectorias.
        ├── jog_control.py      # Controles de movimiento manual para la impresora (XY/Z).
        ├── virtual_keyboard.py # Teclado en pantalla (para uso en entorno táctil).
        └── ...
```

## 4. Reglas y Convenciones del Proyecto
1. **Frontend Táctil**: Todos los botones y componentes deben tener un tamaño apto para pulsación táctil. Se emplean teclados virtuales y el cursor está desactivado.
2. **Asincronismo Qt**: Toda la comunicación con el puerto Serial se delega a hilos separados dentro de `printer.py` para no bloquear el Hilo Principal (GUI Thread). Se usan **Signals** y **Slots** rigurosamente para actualizar el frontend (`state_changed`, `gcode_progress`, etc).
3. **Configuración Centralizada**: Ningún script debe "hardcodear" parámetros de hardware (velocidades de viaje, diámetros de boquilla, medidas del alfajor, multiplicadores de extrusión). Todo debe consumirse y editarse a través de `backend/config.py`, que lee/escribe en `printer_config.yaml`.
4. **Seguridad en G-Code**: Todos los movimientos de fin de impresión incluyen lógicas de "Z-hop" y retracción (o movimientos anti-goteo combinados XY+Z) para no dañar el decorado recién impreso.

## 5. Historial Reciente de Características
- Homing Z0 manual directamente desde la pantalla.
- `jog_control` añadido para manipular físicamente la máquina desde la UI.
- Soporte de impresión de cilindros en 3D (múltiples capas configurables).
- Retracción de fin de impresión obligatoria.
- Modulo de traducción de Imágenes a G-Code incorporado al flujo de selección UI.
- **Matriz 3x3 Interactiva**: `AlfajorCanvas` soporta vista y renderizado de bandeja completa de 9 alfajores con diseños independientes en paralelo, renderizando el progreso de la extrusión sincronizado con la máquina real.
- **Asistente de Calibración Inteligente (`CalibrationWizard`)**: Módulo interactivo con UI táctil para viajar automáticamente a las coordenadas tentativas de la bandeja y establecer con precisión (mediante Jog) los centros XY y alturas Z independientes para cada posición, garantizando tolerancia a variaciones en la superficie.
- **Prevención de Colisiones Z-Hop (Safe Z)**: Algoritmo de viaje (travel) dinámico que calcula la altura Z segura `max(current_z, target_z)` en todo momento, evitando estrellar la boquilla contra construcciones 3D previas al viajar o estacionar.
- **Robustez Serial (M114)**: Sincronización estricta del buffer serial y vaciado antes de leer comandos síncronos de la impresora para evitar desfaces en las posiciones devueltas.
- **Recarga de Configuración en Caliente (`PC.reload()`)**: Sincronización en tiempo real de `printer_config.yaml` antes de iniciar el trabajo, posibilitando ajustes físicos sin reiniciar AlfajorOS.
- **Control Físico de Tapa (Servo SG90)**: Integración de la librería `gpiozero` (`lgpio`) en `backend/servo_controller.py` mediante el GPIO 19 de la Raspberry Pi. El servo opera a 20° (abierto) durante el tiempo total de extrusión de la galleta y 130° (cerrado) en estados de viaje o reposo.
- **Sincronización Física Estricta (M400 y Serial Timeouts)**: Solución al desfase entre la interfaz visual de Python y los motores físicos. El sistema intercepta el comando `M280` localmente e inyecta `M400` para obligar a Python a esperar la finalización de los movimientos de Marlin. Se rediseñó `printer.py` para utilizar *timeouts asíncronos adaptativos* (3600s para M400/G28) que se reinician de manera segura al recibir señales `echo: busy: processing` desde la placa base.

- **3 Nuevas Figuras 3D Decorativas**: Tres figuras 3D multicapa disponibles junto al Cilindro original:
  - **Cilindro Domo**: Cilindro con cúpula/domo. Las capas base son circulares de radio completo; las capas superiores reducen progresivamente su radio (`reduccion_radio`) simulando un iglú que se cierra.
  - **Conos Estrella**: 4 conos en los puntos cardinales (N, S, E, O) del alfajor. Cada cono es una pila de círculos cuyo radio decrece linealmente desde `radio_cono_base` hasta ~1mm, formando 4 montañitas en punta.
  - **Cilindro Escalonado**: Pirámide escalonada tipo "torta de casamiento". El radio decrece en escalones discretos (`reduccion_por_escalon^n`), cada escalón abarca N capas.
  - Todos los parámetros son configurables desde `printer_config.yaml` (secciones `cilindro_domo`, `conos_estrella`, `cilindro_escalonado`).
  - Previsualización 3D completa con capas apiladas con profundidad visual en `AlfajorCanvas`.

---
*NOTA AL AGENTE: Debes modificar y actualizar este archivo cada vez que el usuario agregue una nueva característica sustancial o modifique la arquitectura, para que este contexto se mantenga "vivo" y preciso.*
