"""Autenticación: reglas de contraseña, inicio de sesión y respuesta de sesión (CU-01)."""
import re

from flask import current_app
from werkzeug.security import check_password_hash

from models.usuario import Usuario
from services import actividad, limitador, progreso
from services.errores import ErrorServicio
from services.sesion import crear_token

CORREO_VALIDO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validar_correo(email):
    if not CORREO_VALIDO.match(email):
        raise ErrorServicio(400, "El correo no es válido.")


def validar_password(password):
    """Política de contraseñas: mínimo 8 caracteres, con al menos una letra y un número."""
    if len(password) < 8 or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise ErrorServicio(400, "La contraseña debe tener mínimo 8 caracteres, con letras y números.")


def respuesta_de_sesion(usuario, con_token=True):
    """Lo que recibe el navegador al entrar: usuario, a qué pantalla ir, progreso y (opcional) el token JWT."""
    datos = {
        "usuario": usuario.a_dict(),
        "siguiente": progreso.pantalla_inicial(usuario),
        "progreso": progreso.progreso_estudiante(usuario.id) if usuario.es_estudiante else None,
    }
    if con_token:
        datos["token"] = crear_token(usuario)
        datos["tipoToken"] = "Bearer"
        datos["expiraEnSegundos"] = current_app.config["TOKEN_MAX_AGE"]
    return datos


def iniciar_sesion(email, password, ip):
    limite = limitador.obtener()
    limite.verificar(ip, email)

    usuario = Usuario.por_email(email)
    # Mismo mensaje si falla el correo o la contraseña, para no revelar qué cuentas existen.
    if usuario is None or not check_password_hash(usuario.password_hash, password):
        limite.fallo(ip, email)
        if usuario is not None:
            actividad.registrar("login_fallido", usuario.id, {"ip": ip})
        raise ErrorServicio(401, "Correo o contraseña incorrectos.")
    limite.exito(ip, email)
    actividad.registrar("login", usuario.id, {"rol": usuario.rol})
    return respuesta_de_sesion(usuario)
