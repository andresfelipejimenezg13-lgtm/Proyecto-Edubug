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


# ------------------------------------------------------------------ consultas auxiliares

def _pregunta_para_cliente(conexion, fila):
    opciones = conexion.execute(
        "SELECT id_opcion, texto FROM opciones_pregunta WHERE id_pregunta = ? ORDER BY id_opcion",
        (fila["id_pregunta"],),
    ).fetchall()
    return {
        "idPregunta": fila["id_pregunta"],
        "texto": fila["texto"],
        "tema": fila["tema"],
        "opciones": [{"idOpcion": o["id_opcion"], "texto": o["texto"]} for o in opciones],
    }


def _estado_en_curso(conexion, test):
    respondidas = conexion.execute(
        "SELECT COUNT(*) FROM preguntas_test WHERE id_test = ? AND es_correcta IS NOT NULL",
        (test["id_test"],),
    ).fetchone()[0]
    pendiente = conexion.execute(
        "SELECT * FROM preguntas_test WHERE id_test = ? AND es_correcta IS NULL ORDER BY orden LIMIT 1",
        (test["id_test"],),
    ).fetchone()
    return {
        "finalizado": False,
        "idTest": test["id_test"],
        "numero": respondidas + 1,
        "total": TOTAL_PREGUNTAS,
        "pregunta": _pregunta_para_cliente(conexion, pendiente),
    }


def _resultado(conexion, id_test):
    test = conexion.execute("SELECT * FROM tests_diagnosticos WHERE id_test = ?", (id_test,)).fetchone()
    filas = conexion.execute(
        "SELECT * FROM preguntas_test WHERE id_test = ? ORDER BY orden", (id_test,)
    ).fetchall()
    aciertos = sum(f["es_correcta"] for f in filas)
    return {
        "finalizado": True,
        "idTest": id_test,
        "aciertos": aciertos,
        "total": len(filas),
        "nivel": test["nivel_asignado"],
        "siguiente": siguiente_pantalla(test["nivel_asignado"]),
        "detalle": [
            {
                "texto": f["texto"],
                "tema": f["tema"],
                "acerto": bool(f["es_correcta"]),
                "tuRespuesta": f["respuesta_usuario"],
                "respuestaCorrecta": f["respuesta"],
            }
            for f in filas
        ],
    }


def _estado_actual(conexion, id_test):
    test = conexion.execute("SELECT * FROM tests_diagnosticos WHERE id_test = ?", (id_test,)).fetchone()
    if test["estado"] == "finalizado":
        return _resultado(conexion, id_test)
    return _estado_en_curso(conexion, test)


# ------------------------------------------------------------------ crear la siguiente pregunta

def _crear_pregunta(conexion, id_test, id_usuario, orden, dificultad):
    usadas = conexion.execute(
        "SELECT origen, tema FROM preguntas_test WHERE id_test = ?", (id_test,)
    ).fetchall()
    historial = [
        f["origen"]
        for f in conexion.execute(
            """
            SELECT p.origen FROM preguntas_test p
            JOIN tests_diagnosticos t ON t.id_test = p.id_test
            WHERE t.id_usuario = ? AND p.id_test != ? AND p.origen IS NOT NULL
            ORDER BY p.id_pregunta DESC LIMIT ?
            """,
            (id_usuario, id_test, HISTORIAL_MAXIMO),
        )
    ]
    nueva = obtener_generador().generar(
        dificultad,
        {f["origen"] for f in usadas},
        {f["tema"] for f in usadas},
        historial,
    )
    cursor = conexion.execute(
        """
        INSERT INTO preguntas_test (id_test, orden, texto, respuesta, generada_por_ia, tema, dificultad, origen)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (id_test, orden, nueva["texto"], nueva["respuesta"], nueva["generada_por_ia"],
         nueva["tema"], nueva["dificultad"], nueva["origen"]),
    )
    opciones = list(nueva["opciones"])
    random.shuffle(opciones)  # la respuesta correcta no queda siempre en la misma posición
    for texto in opciones:
        conexion.execute(
            "INSERT INTO opciones_pregunta (id_pregunta, texto) VALUES (?, ?)",
            (cursor.lastrowid, texto),
        )


# ------------------------------------------------------------------ iniciar y responder

def iniciar(conexion, usuario):
    # Si dejó un test sin terminar, se retoma: evita "refrescar hasta que salgan preguntas fáciles".
    abierto = conexion.execute(
        "SELECT * FROM tests_diagnosticos WHERE id_usuario = ? AND estado = 'en_curso' "
        "ORDER BY id_test DESC LIMIT 1",
        (usuario["id_usuario"],),
    ).fetchone()
    if abierto:
        return _estado_en_curso(conexion, abierto)

    with conexion:
        id_test = conexion.execute(
            "INSERT INTO tests_diagnosticos (id_usuario) VALUES (?)", (usuario["id_usuario"],)
        ).lastrowid
        _crear_pregunta(conexion, id_test, usuario["id_usuario"], 1, DIFICULTAD_INICIAL)
    return _estado_actual(conexion, id_test)


def responder(conexion, usuario, id_test, id_pregunta, id_opcion):
    test = conexion.execute(
        "SELECT * FROM tests_diagnosticos WHERE id_test = ? AND id_usuario = ?",
        (id_test, usuario["id_usuario"]),
    ).fetchone()
    if test is None:
        raise ErrorServicio(404, "No encontramos ese test.")

    pregunta = conexion.execute(
        "SELECT * FROM preguntas_test WHERE id_pregunta = ? AND id_test = ?", (id_pregunta, id_test)
    ).fetchone()
    if pregunta is None:
        raise ErrorServicio(400, "La pregunta no pertenece a este test.")

    # Doble clic o reenvío: la pregunta ya estaba contestada, se devuelve el estado actual sin duplicar nada.
    if pregunta["es_correcta"] is not None:
        return _estado_actual(conexion, id_test)

    opcion = conexion.execute(
        "SELECT * FROM opciones_pregunta WHERE id_opcion = ? AND id_pregunta = ?", (id_opcion, id_pregunta)
    ).fetchone()
    if opcion is None:
        raise ErrorServicio(400, "La opción elegida no es válida.")

    es_correcta = 1 if opcion["texto"] == pregunta["respuesta"] else 0

    with conexion:
        # Condicional: solo si sigue sin contestar, así dos clics simultáneos no se pisan.
        guardada = conexion.execute(
            "UPDATE preguntas_test SET respuesta_usuario = ?, es_correcta = ? "
            "WHERE id_pregunta = ? AND es_correcta IS NULL",
            (opcion["texto"], es_correcta, id_pregunta),
        ).rowcount
        if guardada:
            respondidas = conexion.execute(
                "SELECT COUNT(*) FROM preguntas_test WHERE id_test = ? AND es_correcta IS NOT NULL",
                (id_test,),
            ).fetchone()[0]
            if respondidas >= TOTAL_PREGUNTAS:
                aciertos = conexion.execute(
                    "SELECT SUM(es_correcta) FROM preguntas_test WHERE id_test = ?", (id_test,)
                ).fetchone()[0]
                conexion.execute(
                    "UPDATE tests_diagnosticos SET nivel_asignado = ?, estado = 'finalizado' "
                    "WHERE id_test = ? AND estado = 'en_curso'",
                    (calcular_nivel(aciertos), id_test),
                )
            else:
                # Acierto: la siguiente es más difícil. Error: más fácil.
                siguiente = pregunta["dificultad"] + (1 if es_correcta else -1)
                _crear_pregunta(
                    conexion, id_test, usuario["id_usuario"], respondidas + 1, min(3, max(1, siguiente))
                )
    return _estado_actual(conexion, id_test)
