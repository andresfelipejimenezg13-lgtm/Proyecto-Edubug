"""Límite de intentos fallidos de inicio de sesión (protección contra fuerza bruta).

Cuenta los fallos por (IP, correo) dentro de una ventana de tiempo. Vive en memoria del proceso:
es suficiente para esta aplicación; con varios procesos habría que moverlo a Redis o a una base de datos.
"""
import time
from collections import defaultdict, deque

from flask import current_app

from services.errores import ErrorServicio


class LimitadorLogin:
    def __init__(self):
        self._fallos = defaultdict(deque)

    def _recortar(self, clave, ventana):
        fallos = self._fallos[clave]
        limite = time.monotonic() - ventana
        while fallos and fallos[0] < limite:
            fallos.popleft()
        return fallos

    def verificar(self, ip, email):
        """Lanza 429 si ya se superó el máximo de intentos fallidos."""
        maximo = current_app.config["LOGIN_MAX_INTENTOS"]
        ventana = current_app.config["LOGIN_VENTANA_SEG"]
        fallos = self._recortar((ip, email), ventana)
        if len(fallos) >= maximo:
            espera = int(fallos[0] + ventana - time.monotonic()) + 1
            raise ErrorServicio(429, f"Demasiados intentos fallidos. Intenta de nuevo en {max((espera + 59) // 60, 1)} minuto(s).")

    def fallo(self, ip, email):
        self._fallos[(ip, email)].append(time.monotonic())

    def exito(self, ip, email):
        self._fallos.pop((ip, email), None)


def obtener():
    app = current_app
    if "limitador_login" not in app.extensions:
        app.extensions["limitador_login"] = LimitadorLogin()
    return app.extensions["limitador_login"]
