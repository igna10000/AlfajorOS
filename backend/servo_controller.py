#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Controlador del Servomotor - Proyecto de Grado
Maneja un servo SG90 conectado al GPIO 13 de la Raspberry Pi 5.
Se utiliza para controlar el flujo de crema (función de purgado).
"""

import threading
import time
import warnings

try:
    # Suprimir la advertencia de PWMSoftwareFallback
    from gpiozero.output_devices import PWMSoftwareFallback
    warnings.filterwarnings("ignore", category=PWMSoftwareFallback)
except ImportError:
    pass

try:
    from gpiozero import AngularServo, Device
    from gpiozero.pins.lgpio import LGPIOFactory
    
    # RPi 5 usa lgpio de forma predeterminada
    Device.pin_factory = LGPIOFactory()
    
    # Inicializar el servo en GPIO 19
    # SG90 típicamente usa pulsos entre 0.5ms (500us) y 2.4ms (2400us)
    servo = AngularServo(19, min_angle=0, max_angle=180, min_pulse_width=0.0005, max_pulse_width=0.0024)
except Exception as e:
    servo = None
    print(f"Advertencia: No se pudo inicializar el servo en GPIO 19. Detalles: {e}")

def _set_angle_thread(angle):
    if servo is not None:
        try:
            angle = max(0, min(180, angle))
            servo.angle = angle
        except Exception as e:
            print(f"Error moviendo servo: {e}")
    else:
        print(f"[Simulación] Servo movido a {angle} grados.")

def set_servo_angle(angle):
    """
    Mueve el servo SG90 al ángulo especificado de forma asíncrona.
    - 20 grados: Tapa abierta (solo al extruir).
    - 130 grados: Tapa cerrada (resto del tiempo).
    """
    thread = threading.Thread(target=_set_angle_thread, args=(angle,), daemon=True)
    thread.start()
