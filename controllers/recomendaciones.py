"""Consulta de recomendaciones de estudio."""
from flask import Blueprint, g, jsonify

from models import usuario as modelo_usuario
from models.sqlite_db import get_sqlite
from services import recomendaciones
from services.errores import ErrorServicio
from services.sesion import requiere_sesion

bp = Blueprint("recomendaciones", __name__, url_prefix="/api/recomendaciones")


@bp.get("/<int:usuario_id>")
@requiere_sesion()
def obtener(usuario_id):
    """Módulos recomendados para un estudiante. Un estudiante solo ve los suyos; el profesor ve los de todos."""
    if g.usuario["rol"] == "estudiante" and g.usuario["id_usuario"] != usuario_id:
        raise ErrorServicio(403, "Solo puedes consultar tus propias recomendaciones.")
    if modelo_usuario.por_id(get_sqlite(), usuario_id) is None:
        raise ErrorServicio(404, "No encontramos ese usuario.")
    return jsonify(recomendaciones.obtener(get_sqlite(), usuario_id))
