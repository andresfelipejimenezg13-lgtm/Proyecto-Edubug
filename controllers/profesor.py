"""CONTROLADOR del panel de progreso del grupo (CU-05, solo profesores)."""
from flask import Blueprint, jsonify

from models.curso import Curso
from services import progreso
from services.errores import ErrorServicio
from services.sesion import DOCENTES, requiere_sesion

bp = Blueprint("profesor", __name__, url_prefix="/api/profesor")


@bp.get("/progreso/<int:curso_id>")
@requiere_sesion(rol=DOCENTES)
def progreso_grupo(curso_id):
    curso = Curso.obtener(curso_id)
    if curso is None:
        raise ErrorServicio(404, "No encontramos ese curso.")
    return jsonify(progreso.panel_profesor(curso))
