"""CONTROLADOR del depurador de código HTML (CU-03, solo estudiantes)."""
from flask import Blueprint, current_app, g, jsonify

from controllers.utilidades import cuerpo_json
from services import depurador
from services.errores import ErrorServicio
from services.sesion import requiere_sesion

bp = Blueprint("depurador", __name__, url_prefix="/api/depurador")


@bp.post("/analizar")
@requiere_sesion(rol="estudiante")
def analizar():
    """Recibe {"codigoHtml": "..."}; guarda el envío y los errores y devuelve cada error explicado."""
    codigo = cuerpo_json().get("codigoHtml")
    if not isinstance(codigo, str) or not codigo.strip():
        raise ErrorServicio(400, "Escribe o pega tu código HTML antes de validarlo.")
    maximo = current_app.config["MAX_CODIGO_HTML"]
    if len(codigo) > maximo:
        raise ErrorServicio(400, f"El código no puede pasar de {maximo} caracteres.")
    return jsonify(depurador.procesar(g.usuario, codigo))
