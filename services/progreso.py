"""Progreso del estudiante y datos agregados del panel del profesor.

No hay una tabla de progreso: todo se calcula a partir de tests_diagnosticos y envios_codigo.
  - porcentajeCurso: cada envío sin errores avanza el curso un 20 % (máximo 100 %).
  - erroresCorregidos: errores del último envío fallido que se resolvieron en un envío correcto posterior.
"""
from services.diagnostico import siguiente_pantalla  # noqa: F401  (reexportado por comodidad)

NOMBRES_ERROR = {
    "etiqueta_sin_cerrar": "Etiqueta sin cerrar",
    "atributo_sin_comillas": "Atributo sin comillas",
    "etiqueta_en_mayusculas": "Etiqueta en mayúsculas",
}


def nivel_actual(conexion, id_usuario):
    """Nivel del último test finalizado, o None si aún no lo hizo."""
    fila = conexion.execute(
        "SELECT nivel_asignado FROM tests_diagnosticos WHERE id_usuario = ? AND estado = 'finalizado' "
        "ORDER BY id_test DESC LIMIT 1",
        (id_usuario,),
    ).fetchone()
    return fila["nivel_asignado"] if fila else None


def resumen_diagnostico(conexion, id_usuario):
    test = conexion.execute(
        "SELECT * FROM tests_diagnosticos WHERE id_usuario = ? AND estado = 'finalizado' "
        "ORDER BY id_test DESC LIMIT 1",
        (id_usuario,),
    ).fetchone()
    if test is None:
        return None
    total = conexion.execute(
        "SELECT COUNT(*), COALESCE(SUM(es_correcta), 0) FROM preguntas_test WHERE id_test = ?",
        (test["id_test"],),
    ).fetchone()
    return {"idTest": test["id_test"], "aciertos": total[1], "total": total[0], "nivel": test["nivel_asignado"]}


def progreso_estudiante(conexion, id_usuario):
    envios = conexion.execute(
        """
        SELECT v.id_envio, COUNT(e.id_error) AS errores
        FROM envios_codigo v LEFT JOIN errores_detectados e ON e.id_envio = v.id_envio
        WHERE v.id_usuario = ? GROUP BY v.id_envio ORDER BY v.id_envio
        """,
        (id_usuario,),
    ).fetchall()

    correctos, corregidos, pendientes = 0, 0, 0
    for envio in envios:
        if envio["errores"] == 0:
            correctos += 1
            corregidos += pendientes
            pendientes = 0
        else:
            pendientes = envio["errores"]

    return {
        "diagnostico": resumen_diagnostico(conexion, id_usuario),
        "porcentajeCurso": min(100, correctos * 20),
        "erroresCorregidos": corregidos,
        "totalEnvios": len(envios),
    }


def pantalla_inicial(conexion, usuario):
    """A dónde lleva el servidor al usuario al entrar: panel, diagnóstico o catálogo."""
    if usuario["rol"] in ("profesor", "admin"):
        return "panel"
    return "catalogo" if nivel_actual(conexion, usuario["id_usuario"]) else "diagnostico"


def panel_profesor(conexion, curso):
    """Progreso agregado del grupo (CU-05). En el MVP todos los envíos pertenecen al curso inicial."""
    estudiantes = []
    for u in conexion.execute("SELECT * FROM usuarios WHERE rol = 'estudiante' ORDER BY nombre"):
        tests = conexion.execute(
            "SELECT COUNT(*) FROM tests_diagnosticos WHERE id_usuario = ?", (u["id_usuario"],)).fetchone()[0]
        progreso = progreso_estudiante(conexion, u["id_usuario"])
        if tests == 0 and progreso["totalEnvios"] == 0:
            continue  # sin actividad: no cuenta como activo
        errores = conexion.execute(
            "SELECT COUNT(*) FROM errores_detectados e JOIN envios_codigo v ON v.id_envio = e.id_envio "
            "WHERE v.id_usuario = ?", (u["id_usuario"],)).fetchone()[0]
        estudiantes.append({
            "id": u["id_usuario"],
            "nombre": u["nombre"],
            "nivel": nivel_actual(conexion, u["id_usuario"]) or "sin_evaluar",
            "progreso": progreso["porcentajeCurso"],
            "errores": errores,
        })

    top = conexion.execute(
        "SELECT tipo, COUNT(*) AS cantidad FROM errores_detectados GROUP BY tipo "
        "ORDER BY cantidad DESC, tipo LIMIT 3").fetchall()
    total_errores = conexion.execute("SELECT COUNT(*) FROM errores_detectados").fetchone()[0]

    return {
        "cursoId": curso["id_curso"],
        "curso": curso["nombre"],
        "estudiantesActivos": len(estudiantes),
        "promedioProgreso": round(sum(e["progreso"] for e in estudiantes) / len(estudiantes)) if estudiantes else 0,
        "erroresDetectados": total_errores,
        "estudiantes": estudiantes,
        "topErrores": [
            {"tipo": t["tipo"], "nombre": NOMBRES_ERROR[t["tipo"]], "cantidad": t["cantidad"],
             "porcentaje": round(t["cantidad"] * 100 / total_errores)}
            for t in top
        ],
    }
