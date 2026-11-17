"""Test diagnóstico adaptativo: una pregunta a la vez.

Flujo (endpoints del documento):
  POST /api/diagnostico/iniciar    -> crea el test y entrega la primera pregunta.
  POST /api/diagnostico/responder  -> guarda la respuesta y entrega la siguiente pregunta, o cierra
                                      el test y asigna el nivel.

Adaptación: se empieza en dificultad intermedia; cada acierto sube la dificultad de la siguiente
pregunta y cada error la baja (entre 1 y 3). Las preguntas rotan: no se repiten dentro de un test,
se reparten por tema y, entre tests, se prefiere la que el estudiante vio hace más tiempo.

Regla de nivel (por número de aciertos): menos de 2 = bajo; 2 o 3 = medio; 4 o 5 = alto.
"""
import random

from models.diagnostico import PreguntaTest, TestDiagnostico
from models.sqlite_db import transaccion
from services.errores import ErrorServicio
from services.generador_preguntas import obtener_generador

TOTAL_PREGUNTAS = 5
DIFICULTAD_INICIAL = 2
HISTORIAL_MAXIMO = 100


def calcular_nivel(aciertos):
    if aciertos < 2:
        return "bajo"
    if aciertos < 4:
        return "medio"
    return "alto"


def siguiente_pantalla(nivel):
    return "teoria" if nivel == "bajo" else "catalogo"


# ------------------------------------------------------------------ armar las respuestas

def _pregunta_para_cliente(pregunta):
    return {"idPregunta": pregunta.id, "texto": pregunta.texto, "tema": pregunta.tema,
            "opciones": pregunta.opciones()}


def _estado_en_curso(test):
    return {
        "finalizado": False,
        "idTest": test.id,
        "numero": test.respondidas() + 1,
        "total": TOTAL_PREGUNTAS,
        "pregunta": _pregunta_para_cliente(test.pendiente()),
    }


def _resultado(test):
    preguntas = test.preguntas()
    return {
        "finalizado": True,
        "idTest": test.id,
        "aciertos": sum(p.es_correcta for p in preguntas),
        "total": len(preguntas),
        "nivel": test.nivel,
        "siguiente": siguiente_pantalla(test.nivel),
        "detalle": [
            {"texto": p.texto, "tema": p.tema, "acerto": bool(p.es_correcta),
             "tuRespuesta": p.respuesta_usuario, "respuestaCorrecta": p.respuesta}
            for p in preguntas
        ],
    }


def _estado_actual(id_test):
    test = TestDiagnostico.por_id(id_test)
    return _resultado(test) if test.finalizado else _estado_en_curso(test)


# ------------------------------------------------------------------ crear la siguiente pregunta

def _crear_pregunta(test, orden, dificultad):
    usadas = PreguntaTest.usadas_en(test.id)
    historial = PreguntaTest.origenes_vistos(test.usuario_id, test.id, HISTORIAL_MAXIMO)
    nueva = obtener_generador().generar(
        dificultad, {origen for origen, _ in usadas}, {tema for _, tema in usadas}, historial)
    opciones = list(nueva["opciones"])
    random.shuffle(opciones)  # la respuesta correcta no queda siempre en la misma posición
    PreguntaTest.crear(test.id, orden, nueva, opciones)


# ------------------------------------------------------------------ iniciar y responder

def iniciar(usuario):
    # Si dejó un test sin terminar, se retoma: evita "refrescar hasta que salgan preguntas fáciles".
    abierto = TestDiagnostico.abierto_de(usuario.id)
    if abierto:
        return _estado_en_curso(abierto)

    with transaccion():
        test = TestDiagnostico.crear(usuario.id)
        _crear_pregunta(test, 1, DIFICULTAD_INICIAL)
    return _estado_actual(test.id)


def responder(usuario, id_test, id_pregunta, id_opcion):
    test = TestDiagnostico.por_id(id_test, usuario.id)
    if test is None:
        raise ErrorServicio(404, "No encontramos ese test.")

    pregunta = PreguntaTest.de_test(id_pregunta, id_test)
    if pregunta is None:
        raise ErrorServicio(400, "La pregunta no pertenece a este test.")

    # Doble clic o reenvío: la pregunta ya estaba contestada, se devuelve el estado actual sin duplicar nada.
    if pregunta.contestada:
        return _estado_actual(id_test)

    texto_elegido = pregunta.texto_de_opcion(id_opcion)
    if texto_elegido is None:
        raise ErrorServicio(400, "La opción elegida no es válida.")

    es_correcta = 1 if texto_elegido == pregunta.respuesta else 0

    with transaccion():
        if pregunta.registrar_respuesta(texto_elegido, es_correcta):
            respondidas = test.respondidas()
            if respondidas >= TOTAL_PREGUNTAS:
                test.finalizar(calcular_nivel(test.aciertos()))
            else:
                # Acierto: la siguiente es más difícil. Error: más fácil.
                siguiente = pregunta.dificultad + (1 if es_correcta else -1)
                _crear_pregunta(test, respondidas + 1, min(3, max(1, siguiente)))
    return _estado_actual(id_test)
