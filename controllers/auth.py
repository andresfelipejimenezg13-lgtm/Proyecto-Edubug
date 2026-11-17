"""CONTROLADOR de sesión: inicio de sesión (CU-01) y consulta del usuario actual."""
from flask import Blueprint, g, jsonify, request

from controllers.utilidades import cuerpo_json
from services import autenticacion
from services.sesion import requiere_sesion

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/login")
def login():
    datos = cuerpo_json()
    email = str(datos.get("email", "")).strip().lower()
    password = str(datos.get("password", ""))
    return jsonify(autenticacion.iniciar_sesion(email, password, request.remote_addr or "?"))


@bp.get("/yo")
@requiere_sesion()
def yo():
    return jsonify(autenticacion.respuesta_de_sesion(g.usuario, con_token=False))
