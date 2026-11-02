"""Endpoints del test diagnóstico adaptativo (CU-02, solo estudiantes)."""
from flask import Blueprint, g, jsonify

from controllers.utilidades import cuerpo_json, entero
from models.sqlite_db import get_sqlite
from services import actividad, diagnostico
from services.sesion import requiere_sesion

bp = Blueprint("diagnostico", __name__, url_prefix="/api/diagnostico")


@bp.post("/iniciar")
@requiere_sesion(rol="estudiante")
def iniciar():
    """Crea el test (o retoma el que quedó abierto) y entrega la pregunta actual."""
    estado = diagnostico.iniciar(get_sqlite(), g.usuario)
    actividad.registrar("diagnostico_iniciado", g.usuario["id_usuario"], {"idTest": estado["idTest"]})
    return jsonify(estado)


@bp.post("/responder")
@requiere_sesion(rol="estudiante")
def responder():
    """Recibe {"idTest", "idPregunta", "idOpcion"}; devuelve la siguiente pregunta o el nivel final."""
    datos = cuerpo_json()
    resultado = diagnostico.responder(
        get_sqlite(), g.usuario,
        entero(datos.get("idTest"), "idTest"),
        entero(datos.get("idPregunta"), "idPregunta"),
        entero(datos.get("idOpcion"), "idOpcion"),
    )
    id_usuario = g.usuario["id_usuario"]
    actividad.registrar("diagnostico_respuesta", id_usuario,
                        {"idTest": resultado["idTest"], "idPregunta": datos["idPregunta"]})
    if resultado.get("finalizado"):
        actividad.registrar("diagnostico_finalizado", id_usuario,
                            {"idTest": resultado["idTest"], "aciertos": resultado["aciertos"],
                             "total": resultado["total"], "nivel": resultado["nivel"]})
    return jsonify(resultado)
