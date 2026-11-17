"""CONTROLADOR de usuarios: registro público de estudiantes y perfil."""
from flask import Blueprint, g, jsonify

from controllers.utilidades import cuerpo_json, texto
from services import autenticacion, cuentas
from services.sesion import requiere_sesion

bp = Blueprint("usuarios", __name__, url_prefix="/api/usuarios")


@bp.post("/registro")
def registro():
    datos = cuerpo_json()
    usuario = cuentas.registrar_estudiante(
        texto(datos, "nombre", "El nombre", 80),
        texto(datos, "email", "El correo", 120).lower(),
        str(datos.get("password", "")),
        datos.get("rol", "estudiante"),
    )
    return jsonify(autenticacion.respuesta_de_sesion(usuario)), 201


@bp.get("/<int:id_usuario>/perfil-completo")
@requiere_sesion()
def perfil_completo(id_usuario):
    """Endpoint combinado (persistencia políglota): datos de SQLite y de MongoDB en una sola respuesta."""
    return jsonify(cuentas.perfil_completo(g.usuario, id_usuario))
