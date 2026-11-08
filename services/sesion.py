"""Autenticación con JWT y control de acceso por rol (RBAC).

El token es un JWT firmado (HS256) con: sub (id del usuario), rol, iat, exp e iss.
En cada petición se verifica la firma, el vencimiento y el emisor, y se vuelve a leer al usuario en SQLite:
así un cambio de rol o una cuenta eliminada tienen efecto de inmediato, sin esperar a que el token venza.
"""
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import current_app, g, request

from models import usuario as modelo_usuario
from models.sqlite_db import get_sqlite
from services.errores import ErrorServicio

ROLES = ("estudiante", "profesor", "admin")
DOCENTES = ("profesor", "admin")  # quienes pueden gestionar cursos y ver el progreso del grupo
ALGORITMO = "HS256"


def crear_token(usuario):
    ahora = datetime.now(timezone.utc)
    carga = {
        "sub": str(usuario["id_usuario"]),
        "rol": usuario["rol"],
        "iat": ahora,
        "exp": ahora + timedelta(seconds=current_app.config["TOKEN_MAX_AGE"]),
        "iss": current_app.config["JWT_EMISOR"],
    }
    return jwt.encode(carga, current_app.config["SECRET_KEY"], algorithm=ALGORITMO)


def leer_token(token):
    """Devuelve el id de usuario del token o lanza 401."""
    try:
        carga = jwt.decode(
            token, current_app.config["SECRET_KEY"], algorithms=[ALGORITMO],
            issuer=current_app.config["JWT_EMISOR"], options={"require": ["exp", "iat", "sub", "iss"]},
        )
        return int(carga["sub"])
    except jwt.ExpiredSignatureError:
        raise ErrorServicio(401, "Tu sesión expiró. Inicia sesión de nuevo.")
    except (jwt.InvalidTokenError, ValueError):
        raise ErrorServicio(401, "Sesión no válida.")


def requiere_sesion(rol=None):
    """Exige `Authorization: Bearer <JWT>`.

    `rol` puede ser un texto ("admin") o varios (("profesor", "admin")). Sin sesión responde 401;
    con sesión pero sin el rol necesario, 403.
    """
    permitidos = (rol,) if isinstance(rol, str) else tuple(rol or ())

    def decorador(funcion):
        @wraps(funcion)
        def envoltura(*args, **kwargs):
            cabecera = request.headers.get("Authorization", "")
            if not cabecera.startswith("Bearer "):
                raise ErrorServicio(401, "Debes iniciar sesión.")
            id_usuario = leer_token(cabecera[7:])

            usuario = modelo_usuario.por_id(get_sqlite(), id_usuario)
            if usuario is None:
                raise ErrorServicio(401, "La cuenta ya no existe.")
            if permitidos and usuario["rol"] not in permitidos:
                raise ErrorServicio(403, "No tienes permiso para esta acción.")
            g.usuario = usuario
            return funcion(*args, **kwargs)

        return envoltura

    return decorador
