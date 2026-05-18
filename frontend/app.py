#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
App Controller - Proyecto de Grado
Orquestador principal: gestiona navegación entre vistas y ciclo de vida.
"""

from PySide6.QtWidgets import QMessageBox

from backend.config import SystemConfig
from frontend.views.login_view import LoginWindow
from frontend.views.main_view import MainView
from frontend.views.text_options_view import TextOptionsView
from frontend.views.figure_options_view import FigureOptionsView
from frontend.views.image_selection_view import ImageSelectionView
from frontend.views.pro_mode import ProModeWindow
from frontend.views.example_window import ExampleWindow
from frontend.views.product_selection import ProductSelectionWindow
from frontend.views.screensaver import ScreensaverWindow
from frontend.widgets.password_dialog import PasswordDialog


class AppController:
    """
    Controlador principal de la aplicación.
    Gestiona la navegación entre ventanas y el ciclo de vida.
    """

    def __init__(self):
        self.usuario_actual = ""

        # === Crear vistas ===
        self.login = LoginWindow()
        self.screensaver = ScreensaverWindow(
            timeout_seconds=SystemConfig.SCREENSAVER_TIMEOUT_S
        )
        self.main_win = None
        self.text_opts = TextOptionsView()
        self.figure_opts = FigureOptionsView()
        self.image_selection = ImageSelectionView()
        self.pro_mode = ProModeWindow()
        self.example_win = ExampleWindow()

        # === Conectar señales ===
        self._conectar_login()
        self._conectar_text_opts()
        self._conectar_figure_opts()
        self._conectar_image_selection()
        self._conectar_pro_mode()
        self._conectar_example()
        self._conectar_actividad([
            self.text_opts, self.figure_opts, self.image_selection,
            self.pro_mode, self.example_win
        ])

    # === Conexiones ===

    def _conectar_login(self):
        self.login.login_exitoso.connect(self._on_login_exitoso)

    def _conectar_main(self):
        self.main_win.abrir_texto.connect(self._on_abrir_texto)
        self.main_win.abrir_figura.connect(self._on_abrir_figura)
        self.main_win.abrir_pro.connect(self._on_abrir_pro)
        self.main_win.actividad_detectada.connect(self._on_actividad)
        self.main_win.impresion_iniciada.connect(self.screensaver.bloquear)
        self.main_win.impresion_terminada.connect(self.screensaver.desbloquear)

    def _conectar_text_opts(self):
        self.text_opts.texto_configurado.connect(self._on_texto_configurado)
        self.text_opts.ir_siguiente.connect(self._on_texto_siguiente)
        self.text_opts.ir_atras.connect(self._on_texto_atras)

    def _conectar_figure_opts(self):
        self.figure_opts.figura_configurada.connect(self._on_figura_configurada)
        self.figure_opts.ir_atras.connect(self._on_figura_atras)
        self.figure_opts.abrir_imagen.connect(self._on_abrir_imagen)

    def _conectar_image_selection(self):
        self.image_selection.imagen_seleccionada.connect(self._on_imagen_configurada)
        self.image_selection.ir_atras.connect(self._on_imagen_atras)

    def _conectar_pro_mode(self):
        self.pro_mode.volver_basico.connect(self._on_volver_basico)

    def _conectar_example(self):
        self.example_win.confirmado.connect(self._on_confirmado)

    def _conectar_actividad(self, ventanas):
        for ventana in ventanas:
            ventana.actividad_detectada.connect(self._on_actividad)

    # === Handlers ===

    def _posicionar_ventana(self, ventana):
        ventana.move(0, 0)

    def _on_login_exitoso(self, usuario):
        self.usuario_actual = usuario
        self.login.hide()
        self.main_win = MainView(usuario=usuario)
        self._conectar_main()
        self._posicionar_ventana(self.main_win)
        self.main_win.show()
        self.screensaver.reiniciar_timer_inactividad()

    def _on_abrir_texto(self):
        self.text_opts.reset()
        self._posicionar_ventana(self.text_opts)
        self.text_opts.show()
        self.text_opts.raise_()

    def _on_abrir_figura(self):
        self.figure_opts.reset()
        self._posicionar_ventana(self.figure_opts)
        self.figure_opts.show()
        self.figure_opts.raise_()

    def _on_abrir_pro(self):
        dialog = PasswordDialog(
            titulo="Modo PRO",
            mensaje="Ingrese la contraseña para Modo PRO:",
            parent=self.main_win
        )
        password, ok = dialog.get_password()
        if ok and password == SystemConfig.PRO_PASSWORD:
            self._posicionar_ventana(self.pro_mode)
            self.pro_mode.show()
            self.pro_mode.raise_()
        elif ok:
            QMessageBox.warning(
                self.main_win, "Acceso Denegado",
                "Contraseña incorrecta.\nNo se puede acceder al Modo PRO."
            )

    def _on_texto_configurado(self, texto):
        if self.main_win:
            self.main_win.set_texto(texto)

    def _on_texto_siguiente(self):
        if self.main_win:
            self.main_win.show()
            self.main_win.raise_()

    def _on_texto_atras(self):
        if self.main_win:
            self.main_win.show()
            self.main_win.raise_()

    def _on_figura_configurada(self, figura, tamano):
        if self.main_win:
            self.main_win.set_figura(figura, tamano)
            self.main_win.show()
            self.main_win.raise_()

    def _on_figura_atras(self):
        if self.main_win:
            self.main_win.show()
            self.main_win.raise_()

    def _on_abrir_imagen(self):
        """Abre la ventana de selección de imágenes."""
        self.image_selection.reset()
        self._posicionar_ventana(self.image_selection)
        self.image_selection.show()
        self.image_selection.raise_()

    def _on_imagen_configurada(self, path):
        """Imagen seleccionada — configurar en MainView."""
        if self.main_win:
            self.main_win.set_imagen(path)
            self.main_win.show()
            self.main_win.raise_()

    def _on_imagen_atras(self):
        """Volver de selección de imagen a figure_opts."""
        self._posicionar_ventana(self.figure_opts)
        self.figure_opts.show()
        self.figure_opts.raise_()

    def _on_volver_basico(self):
        if self.main_win:
            self.main_win.show()
            self.main_win.raise_()

    def _on_confirmado(self, resultado):
        print(f"[INFO] Usuario confirmó: {'SÍ' if resultado else 'NO'}")

    def _on_actividad(self):
        self.screensaver.reiniciar_timer_inactividad()

    # === Inicio ===

    def iniciar(self):
        self.login.move(0, 0)
        self.login.show()
