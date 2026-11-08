"""Inicio de sesión (CU-01) y consulta del usuario actual."""
from flask import Blueprint, current_app, g, jsonify, request
from werkzeug.security import check_password_hash

from controllers.utilidades import cuerpo_json
from models import usuario as modelo_usuario
from models.sqlite_db import get_sqlite
from services import actividad, limitador, progreso
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
        datos["token"] = crear_token(usuario)
        datos["tipoToken"] = "Bearer"
        datos["expiraEnSegundos"] = current_app.config["TOKEN_MAX_AGE"]
    return datos


@bp.post("/login")
def login():
    datos = cuerpo_json()
    email = str(datos.get("email", "")).strip().lower()
    password = str(datos.get("password", ""))

    ip = request.remote_addr or "?"
    limite = limitador.obtener()
    limite.verificar(ip, email)

    usuario = modelo_usuario.por_email(get_sqlite(), email)
    # Mismo mensaje si falla el correo o la contraseña, para no revelar qué cuentas existen.
    if usuario is None or not check_password_hash(usuario["password_hash"], password):
        limite.fallo(ip, email)
        if usuario is not None:
            actividad.registrar("login_fallido", usuario["id_usuario"], {"ip": ip})
        raise ErrorServicio(401, "Correo o contraseña incorrectos.")
    limite.exito(ip, email)
    actividad.registrar("login", usuario["id_usuario"], {"rol": usuario["rol"]})
    return jsonify(respuesta_de_sesion(usuario))


@bp.get("/yo")
@requiere_sesion()
def yo():
    return jsonify(respuesta_de_sesion(g.usuario, con_token=False))
