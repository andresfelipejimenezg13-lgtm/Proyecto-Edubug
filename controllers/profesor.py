"""Panel de progreso del grupo (CU-05, solo profesores)."""
from flask import Blueprint, jsonify

from models import curso as modelo_curso
from models.sqlite_db import get_sqlite
from services import progreso
from services.errores import ErrorServicio
from services.sesion import requiere_sesion

bp = Blueprint("profesor", __name__, url_prefix="/api/profesor")


@bp.get("/progreso/<int:curso_id>")
@requiere_sesion(rol="profesor")
def progreso_grupo(curso_id):
    curso = modelo_curso.obtener(get_sqlite(), curso_id)
    if curso is None:
        raise ErrorServicio(404, "No encontramos ese curso.")
    return jsonify(progreso.panel_profesor(get_sqlite(), curso))
