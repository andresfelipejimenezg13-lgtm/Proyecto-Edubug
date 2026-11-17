"""CONTROLADOR del test diagnóstico adaptativo (CU-02, solo estudiantes)."""
from flask import Blueprint, g, jsonify

from controllers.utilidades import cuerpo_json, entero
from services import actividad, diagnostico
from services.sesion import requiere_sesion

bp = Blueprint("diagnostico", __name__, url_prefix="/api/diagnostico")


@bp.post("/iniciar")
@requiere_sesion(rol="estudiante")
def iniciar():
    """Crea el test (o retoma el que quedó abierto) y entrega la pregunta actual."""
    estado = diagnostico.iniciar(g.usuario)
    actividad.registrar("diagnostico_iniciado", g.usuario.id, {"idTest": estado["idTest"]})
    return jsonify(estado)


@bp.post("/responder")
@requiere_sesion(rol="estudiante")
def responder():
    """Recibe {"idTest", "idPregunta", "idOpcion"}; devuelve la siguiente pregunta o el nivel final."""
    datos = cuerpo_json()
    resultado = diagnostico.responder(
        g.usuario,
        entero(datos.get("idTest"), "idTest"),
        entero(datos.get("idPregunta"), "idPregunta"),
        entero(datos.get("idOpcion"), "idOpcion"),
    )
    actividad.registrar("diagnostico_respuesta", g.usuario.id,
                        {"idTest": resultado["idTest"], "idPregunta": datos["idPregunta"]})
    if resultado.get("finalizado"):
        actividad.registrar("diagnostico_finalizado", g.usuario.id,
                            {"idTest": resultado["idTest"], "aciertos": resultado["aciertos"],
                             "total": resultado["total"], "nivel": resultado["nivel"]})
    return jsonify(resultado)
