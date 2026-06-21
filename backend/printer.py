#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Printer Connection Manager - Proyecto de Grado
Gestiona la conexión serial con impresora Ender 3 Pro (Marlin).
Auto-escaneo de puertos USB, reconexión automática y envío de G-Code.
"""

import glob
import time
import threading
from enum import Enum

import serial
from PySide6.QtCore import QObject, Signal, QTimer
from backend.config import PrinterConfig as PC


class PrinterState(Enum):
    DISCONNECTED = "disconnected"
    SCANNING = "scanning"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    BUSY = "busy"
    ERROR = "error"


class PrinterConnection(QObject):
    """
    Gestiona la conexión serial con la impresora 3D.
    - Auto-escaneo de /dev/ttyUSB* y /dev/ttyACM*
    - Reconexión automática
    - Envío de G-Code línea por línea
    - Señales Qt para actualizar la UI
    """

    # Señales
    state_changed = Signal(str)           # PrinterState.value
    connection_info = Signal(str)         # Puerto conectado o mensaje
    response_received = Signal(str)      # Respuesta de Marlin
    error_occurred = Signal(str)          # Errores
    gcode_progress = Signal(int, int)     # (línea_actual, total_líneas)
    gcode_finished = Signal()             # G-Code completado

    BAUDRATE = PC.SERIAL_BAUDRATE
    SCAN_PATTERNS = PC.SERIAL_SCAN_PATTERNS
    RECONNECT_INTERVAL_MS = PC.SERIAL_RECONNECT_MS
    SERIAL_TIMEOUT = PC.SERIAL_TIMEOUT_S

    def __init__(self, parent=None):
        super().__init__(parent)
        self._serial = None
        self._state = PrinterState.DISCONNECTED
        self._port = ""
        self._lock = threading.Lock()
        self._sending = False
        self._stop_send = False

        # Timer de reconexión (escanea si desconectado)
        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.timeout.connect(self._on_timer_tick)
        self._reconnect_timer.start(self.RECONNECT_INTERVAL_MS)

        # Timer de heartbeat (verifica conexión activa cada 3s)
        self._heartbeat_timer = QTimer(self)
        self._heartbeat_timer.timeout.connect(self._check_alive)
        self._heartbeat_timer.start(3000)

        # Intentar conexión inmediata
        QTimer.singleShot(500, self._try_connect)

    # === Propiedades ===

    @property
    def state(self):
        return self._state

    @property
    def is_connected(self):
        return self._state in (PrinterState.CONNECTED, PrinterState.BUSY)

    @property
    def port(self):
        return self._port

    # === Escaneo y Conexión ===

    def _scan_ports(self):
        """Escanea puertos seriales disponibles."""
        ports = []
        for pattern in self.SCAN_PATTERNS:
            ports.extend(glob.glob(pattern))
        return sorted(ports)

    def _on_timer_tick(self):
        """Llamado por el timer de reconexión."""
        if self._state == PrinterState.DISCONNECTED:
            self._try_connect()

    def _check_alive(self):
        """Heartbeat: verifica activamente que la impresora sigue conectada."""
        if self._state not in (PrinterState.CONNECTED, PrinterState.BUSY):
            return

        # 1. Verificar que el archivo del puerto aún existe
        import os
        if self._port and not os.path.exists(self._port):
            self._handle_disconnect("Puerto desconectado")
            return

        # 2. Si está ocupada enviando G-Code, no interrumpir
        if self._state == PrinterState.BUSY:
            return

        # 3. Intentar enviar M105 (consulta de temperatura, inofensivo)
        with self._lock:
            try:
                if not self._serial or not self._serial.is_open:
                    self._handle_disconnect("Puerto cerrado")
                    return

                self._serial.write(b"M105\n")
                self._serial.flush()

                # Esperar respuesta breve
                deadline = time.time() + 2.0
                while time.time() < deadline:
                    if self._serial.in_waiting:
                        self._serial.readline()  # Leer y descartar respuesta
                        return  # OK, sigue viva
                    time.sleep(0.05)

                # Sin respuesta = desconectada
                self._handle_disconnect("Sin respuesta")

            except (serial.SerialException, OSError):
                self._handle_disconnect("Error de comunicación")

    def _handle_disconnect(self, reason=""):
        """Maneja una desconexión detectada."""
        try:
            if self._serial:
                self._serial.close()
        except Exception:
            pass
        self._serial = None
        self._port = ""
        self._set_state(PrinterState.DISCONNECTED)
        msg = f"Impresora desconectada"
        if reason:
            msg += f": {reason}"
        self.connection_info.emit(msg)

    def _try_connect(self):
        """Intenta conectar a la impresora escaneando puertos."""
        if self._state in (PrinterState.CONNECTED, PrinterState.BUSY,
                           PrinterState.CONNECTING):
            return

        self._set_state(PrinterState.SCANNING)
        ports = self._scan_ports()

        if not ports:
            self._set_state(PrinterState.DISCONNECTED)
            self.connection_info.emit("Sin puertos detectados")
            return

        for port in ports:
            try:
                self._set_state(PrinterState.CONNECTING)
                self.connection_info.emit(f"Probando {port}...")

                ser = serial.Serial(
                    port=port,
                    baudrate=self.BAUDRATE,
                    timeout=self.SERIAL_TIMEOUT,
                    write_timeout=self.SERIAL_TIMEOUT,
                )

                # Esperar a que Marlin arranque
                time.sleep(0.5)

                # Leer banner de Marlin (si hay)
                ser.reset_input_buffer()

                # Enviar M115 (firmware info) para verificar Marlin
                ser.write(b"M115\n")
                time.sleep(0.8)

                response = ""
                while ser.in_waiting:
                    line = ser.readline().decode("utf-8", errors="ignore").strip()
                    response += line + " "

                if "ok" in response.lower() or "marlin" in response.lower() or response:
                    # ¡Conexión exitosa!
                    self._serial = ser
                    self._port = port
                    self._set_state(PrinterState.CONNECTED)
                    self.connection_info.emit(f"Conectado: {port}")
                    return
                else:
                    ser.close()

            except (serial.SerialException, OSError) as e:
                self.error_occurred.emit(f"{port}: {str(e)}")
                try:
                    if 'ser' in locals():
                        ser.close()
                except Exception:
                    pass

        self._set_state(PrinterState.DISCONNECTED)
        self.connection_info.emit("Impresora no encontrada")

    def disconnect_serial(self):
        """Desconecta la impresora."""
        self._stop_send = True
        with self._lock:
            if self._serial and self._serial.is_open:
                try:
                    self._serial.close()
                except Exception:
                    pass
            self._serial = None
            self._port = ""
            self._set_state(PrinterState.DISCONNECTED)
            self.connection_info.emit("Desconectado")

    def reconnect(self):
        """Fuerza un intento de reconexión."""
        self.disconnect_serial()
        QTimer.singleShot(500, self._try_connect)

    # === Envío de Comandos ===

    def send_command(self, cmd):
        """
        Envía un comando G-Code individual.
        Retorna la respuesta de Marlin o None si falla.
        """
        if not self.is_connected or not self._serial:
            return None

        with self._lock:
            try:
                cmd = cmd.strip()
                if not cmd or cmd.startswith(";"):
                    return "skip"

                # Interceptar comando M280 para controlar el servo localmente
                if cmd.startswith("M280 P0"):
                    try:
                        parts = cmd.split("S")
                        if len(parts) > 1:
                            angle = int(parts[1].split()[0])
                            print(f"[AlfajorOS SERVO] Interceptando M280: moviendo a {angle} grados.")
                            from backend.servo_controller import set_servo_angle
                            set_servo_angle(angle)
                    except Exception as e:
                        print(f"Error parseando M280: {e}")
                    return "ok\n" # Falsificar respuesta para Marlin

                self._serial.write((cmd + "\n").encode("utf-8"))
                self._serial.flush()

                # Esperar respuesta (ok / error)
                response = ""
                # M400, G28, G29 necesitan mucho más tiempo porque esperan a movimientos físicos
                timeout_s = 3600 if any(cmd.startswith(x) for x in ["M400", "G28", "G29"]) else 15
                deadline = time.time() + timeout_s
                
                while time.time() < deadline:
                    if self._serial.in_waiting:
                        line = self._serial.readline().decode("utf-8", errors="ignore").strip()
                        response += line + "\n"
                        self.response_received.emit(line)

                        if "ok" in line.lower():
                            return response
                        elif "error" in line.lower():
                            self.error_occurred.emit(f"Marlin error: {line}")
                            return response
                        elif "busy" in line.lower():
                            # Resetear el timeout si Marlin reporta estar ocupado
                            deadline = time.time() + timeout_s
                    else:
                        time.sleep(0.01)

                # Timeout
                self.error_occurred.emit(f"Timeout esperando respuesta a: {cmd}")
                # IMPORTANTE: Si hay timeout, devolver None para abortar y no seguir desfasando
                return None

            except (serial.SerialException, OSError) as e:
                self.error_occurred.emit(f"Error serial: {str(e)}")
                self._handle_disconnect("Conexión perdida")
                return None

    def send_gcode(self, gcode_text):
        """
        Envía un bloque de G-Code completo en un hilo separado.
        Emite gcode_progress y gcode_finished.
        """
        if not self.is_connected:
            self.error_occurred.emit("Impresora no conectada")
            return False

        self._stop_send = False
        self._set_state(PrinterState.BUSY)

        thread = threading.Thread(
            target=self._send_gcode_thread,
            args=(gcode_text,),
            daemon=True
        )
        thread.start()
        return True

    def _send_gcode_thread(self, gcode_text):
        """Hilo que envía G-Code línea por línea."""
        # Mantener los comentarios para loggearlos en consola
        lines = [l.strip() for l in gcode_text.split("\n") if l.strip()]
        
        # El total de líneas solo cuenta los comandos reales
        valid_lines = [l for l in lines if not l.startswith(";")]
        total = len(valid_lines)
        cmd_count = 0

        for i, line in enumerate(lines):
            if self._stop_send:
                break

            if line.startswith(";"):
                print(f"[AlfajorOS INFO] Ejecutando: {line}")
                continue

            result = self.send_command(line)
            if result is None:
                # Conexión perdida
                self.error_occurred.emit("Conexión perdida durante envío")
                break

            cmd_count += 1
            self.gcode_progress.emit(cmd_count, total)

        if not self._stop_send:
            self._set_state(PrinterState.CONNECTED)
            self.gcode_finished.emit()
        else:
            self._set_state(PrinterState.CONNECTED)

    def stop_sending(self):
        """Detiene el envío de G-Code."""
        self._stop_send = True

    # === Estado ===

    def _set_state(self, new_state):
        if self._state != new_state:
            self._state = new_state
            self.state_changed.emit(new_state.value)

    def cleanup(self):
        """Limpia recursos al cerrar la aplicación."""
        self._reconnect_timer.stop()
        self._heartbeat_timer.stop()
        self._stop_send = True
        self.disconnect_serial()
