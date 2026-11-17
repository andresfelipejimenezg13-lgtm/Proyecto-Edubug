"""CONTROLADOR de recomendaciones de estudio."""
from flask import Blueprint, g, jsonify

from models.usuario import Usuario
from services import recomendaciones
from services.errores import ErrorServicio
from services.sesion import requiere_sesion

bp = Blueprint("recomendaciones", __name__, url_prefix="/api/recomendaciones")


@bp.get("/<int:usuario_id>")
@requiere_sesion()
def obtener(usuario_id):
    """Módulos recomendados para un estudiante. Un estudiante solo ve los suyos; el profesor ve los de todos."""
    if g.usuario.es_estudiante and g.usuario.id != usuario_id:
        raise ErrorServicio(403, "Solo puedes consultar tus propias recomendaciones.")
    if Usuario.por_id(usuario_id) is None:
        raise ErrorServicio(404, "No encontramos ese usuario.")
    return jsonify(recomendaciones.obtener(usuario_id))
