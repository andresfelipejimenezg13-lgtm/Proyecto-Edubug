"""Inicio de sesión (CU-01) y consulta del usuario actual."""
from flask import Blueprint, g, jsonify
from werkzeug.security import check_password_hash

from controllers.utilidades import cuerpo_json
from models import usuario as modelo_usuario
from models.sqlite_db import get_sqlite
from services import actividad, progreso
from services.errores import ErrorServicio
from services.sesion import crear_token, requiere_sesion

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def respuesta_de_sesion(usuario, con_token=True):
    conexion = get_sqlite()
    datos = {
        "usuario": modelo_usuario.publico(usuario),
        "siguiente": progreso.pantalla_inicial(conexion, usuario),
        "progreso": progreso.progreso_estudiante(conexion, usuario["id_usuario"])
        if usuario["rol"] == "estudiante" else None,
    }
    if con_token:
        datos["token"] = crear_token(usuario["id_usuario"])
    return datos


@bp.post("/login")
def login():
    datos = cuerpo_json()
    email = str(datos.get("email", "")).strip().lower()
    password = str(datos.get("password", ""))

    usuario = modelo_usuario.por_email(get_sqlite(), email)
    # Mismo mensaje si falla el correo o la contraseña, para no revelar qué cuentas existen.
    if usuario is None or not check_password_hash(usuario["password_hash"], password):
        raise ErrorServicio(401, "Correo o contraseña incorrectos.")
    actividad.registrar("login", usuario["id_usuario"], {"rol": usuario["rol"]})
    return jsonify(respuesta_de_sesion(usuario))


@bp.get("/yo")
@requiere_sesion()
def yo():
    return jsonify(respuesta_de_sesion(g.usuario, con_token=False))
