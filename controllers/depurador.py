"""Depurador de código HTML (CU-03, solo estudiantes)."""
from flask import Blueprint, current_app, g, jsonify

from controllers.utilidades import cuerpo_json
from models.sqlite_db import get_sqlite
from services import actividad, depurador, progreso, recomendaciones
from services.errores import ErrorServicio
from services.sesion import requiere_sesion

bp = Blueprint("depurador", __name__, url_prefix="/api/depurador")


@bp.post("/analizar")
@requiere_sesion(rol="estudiante")
def analizar():
    """Recibe {"codigoHtml": "..."}; guarda el envío y los errores y devuelve cada error explicado."""
    datos = cuerpo_json()
    codigo = datos.get("codigoHtml")
    if not isinstance(codigo, str) or not codigo.strip():
        raise ErrorServicio(400, "Escribe o pega tu código HTML antes de validarlo.")
    maximo = current_app.config["MAX_CODIGO_HTML"]
    if len(codigo) > maximo:
        raise ErrorServicio(400, f"El código no puede pasar de {maximo} caracteres.")

    conexion = get_sqlite()
    id_usuario = g.usuario["id_usuario"]
    nivel = progreso.nivel_actual(conexion, id_usuario)

    errores = []
    for error in depurador.analizar(codigo):
        explicado = depurador.explicar(error, nivel)
        errores.append({"tipo": error["tipo"], "linea": error["linea"], "explicacionIA": explicado["explicacion"],
                        "titulo": explicado["titulo"], "solucion": explicado["solucion"],
                        "ejemploIncorrecto": explicado["ejemploIncorrecto"],
                        "ejemploCorrecto": explicado["ejemploCorrecto"]})

    with conexion:
        id_envio = conexion.execute(
            "INSERT INTO envios_codigo (id_usuario, codigo_html) VALUES (?, ?)", (id_usuario, codigo)
        ).lastrowid
        for e in errores:
            conexion.execute(
                "INSERT INTO errores_detectados (id_envio, tipo, linea, explicacion_ia) VALUES (?, ?, ?, ?)",
                (id_envio, e["tipo"], e["linea"], e["explicacionIA"]),
            )

    # Extensión de CU-03: si hay errores recurrentes, se genera (y guarda) una recomendación de estudio.
    id_recomendacion = recomendaciones.generar_si_corresponde(conexion, id_usuario)

    actividad.registrar("codigo_analizado", id_usuario,
                        {"idEnvio": id_envio, "totalErrores": len(errores),
                         "tipos": sorted({e["tipo"] for e in errores}),
                         "recomendacionGenerada": id_recomendacion is not None})

    return jsonify({
        "usuarioId": id_usuario,
        "idEnvio": id_envio,
        "erroresDetectados": errores,
        "nivelDetectado": nivel or "sin_evaluar",
        "recomendacion": recomendaciones.obtener(conexion, id_usuario, id_recomendacion)
        if id_recomendacion else None,
        "progreso": progreso.progreso_estudiante(conexion, id_usuario),
    })
