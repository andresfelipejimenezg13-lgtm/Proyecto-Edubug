"""Tokens de sesión firmados y decorador para proteger endpoints."""
from functools import wraps

from flask import current_app, g, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from models import usuario as modelo_usuario
from models.sqlite_db import get_sqlite
from services.errores import ErrorServicio


def _serializador():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="edudebug-sesion")


def crear_token(id_usuario):
    return _serializador().dumps({"uid": id_usuario})


def requiere_sesion(rol=None):
    """Exige `Authorization: Bearer <token>`. Si se indica `rol`, también lo valida."""

    def decorador(funcion):
        @wraps(funcion)
        def envoltura(*args, **kwargs):
            cabecera = request.headers.get("Authorization", "")
            if not cabecera.startswith("Bearer "):
                raise ErrorServicio(401, "Debes iniciar sesión.")
            try:
                datos = _serializador().loads(
                    cabecera[7:], max_age=current_app.config["TOKEN_MAX_AGE"]
                )
            except SignatureExpired:
                raise ErrorServicio(401, "Tu sesión expiró. Inicia sesión de nuevo.")
            except BadSignature:
                raise ErrorServicio(401, "Sesión no válida.")

            usuario = modelo_usuario.por_id(get_sqlite(), datos["uid"])
            if usuario is None:
                raise ErrorServicio(401, "La cuenta ya no existe.")
            if rol and usuario["rol"] != rol:
                raise ErrorServicio(403, "No tienes permiso para esta acción.")
            g.usuario = usuario
            return funcion(*args, **kwargs)

        return envoltura

    return decorador
