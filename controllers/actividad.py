"""CONTROLADOR de la bitácora de actividad del usuario (MongoDB): crear, consultar y eliminar eventos."""
from flask import Blueprint, g, jsonify, request

from controllers.utilidades import cuerpo_json
from models.actividad import Actividad
from services import actividad
from services.errores import ErrorServicio
from services.sesion import requiere_sesion

bp = Blueprint("actividad", __name__, url_prefix="/api/actividad")

# El navegador solo puede crear estos eventos; el resto los registra el servidor.
TIPOS_MANUALES = ("tema_visto",)


@bp.post("")
@requiere_sesion()
def crear():
    """CREATE. Cuerpo: {"tipo": "tema_visto", "detalle": {"tema": 3}}."""
    datos = cuerpo_json()
    tipo = datos.get("tipo")
    if tipo not in TIPOS_MANUALES:
        raise ErrorServicio(400, "Tipo de actividad no permitido. Permitidos: " + ", ".join(TIPOS_MANUALES) + ".")
    detalle = actividad.validar_detalle(datos.get("detalle", {}))
    return jsonify(Actividad.crear(g.usuario.id, tipo, detalle).a_dict()), 201


@bp.get("")
@requiere_sesion()
def listar():
    """READ. Mis últimos eventos. Parámetros: ?limite=10 (1 a 100) y ?tipo=login."""
    try:
        limite = int(request.args.get("limite", 10))
    except ValueError:
        raise ErrorServicio(400, "limite debe ser un número entero.")
    if not 1 <= limite <= 100:
        raise ErrorServicio(400, "limite debe estar entre 1 y 100.")
    tipo = request.args.get("tipo")
    if tipo and tipo not in actividad.TIPOS_ACTIVIDAD:
        raise ErrorServicio(400, "Ese tipo de actividad no existe.")
    eventos = Actividad.ultimas(g.usuario.id, limite, tipo)
    return jsonify({"idUsuario": g.usuario.id, "total": len(eventos), "actividades": [e.a_dict() for e in eventos]})


@bp.delete("/<id_actividad>")
@requiere_sesion()
def eliminar(id_actividad):
    """DELETE. Solo puedes borrar tus propios eventos."""
    evento = Actividad.por_id(id_actividad)
    if evento is None or evento.id_usuario != g.usuario.id:
        raise ErrorServicio(404, "No encontramos esa actividad.")
    evento.eliminar()
    return jsonify({"eliminado": True})
