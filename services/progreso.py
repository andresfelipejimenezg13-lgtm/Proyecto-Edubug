"""Progreso del estudiante y datos agregados del panel del profesor.

No hay una tabla de progreso: todo se calcula a partir de los tests y los envíos de código.
  - porcentajeCurso: cada envío sin errores avanza el curso un 20 % (máximo 100 %).
  - erroresCorregidos: errores del último envío fallido que se resolvieron en un envío correcto posterior.
"""
from models.diagnostico import TestDiagnostico
from models.envio import EnvioCodigo, ErrorDetectado
from models.usuario import Usuario

NOMBRES_ERROR = {
    "etiqueta_sin_cerrar": "Etiqueta sin cerrar",
    "atributo_sin_comillas": "Atributo sin comillas",
    "etiqueta_en_mayusculas": "Etiqueta en mayúsculas",
    "sin_html": "No hay etiquetas HTML",
    "etiqueta_desconocida": "Etiqueta que no existe",
    "atributo_faltante": "Atributo obligatorio ausente",
    "etiqueta_incompleta": "Etiqueta sin terminar",
}


def nivel_actual(id_usuario):
    """Nivel del último test finalizado, o None si aún no lo hizo."""
    return TestDiagnostico.nivel_actual(id_usuario)


def resumen_diagnostico(id_usuario):
    test = TestDiagnostico.ultimo_finalizado_de(id_usuario)
    if test is None:
        return None
    return {"idTest": test.id, "aciertos": test.aciertos(), "total": len(test.preguntas()), "nivel": test.nivel}


def progreso_estudiante(id_usuario):
    envios = EnvioCodigo.resumen_de(id_usuario)
    correctos, corregidos, pendientes = 0, 0, 0
    for envio in envios:
        if envio["errores"] == 0:
            correctos += 1
            corregidos += pendientes
            pendientes = 0
        else:
            pendientes = envio["errores"]

    return {
        "diagnostico": resumen_diagnostico(id_usuario),
        "porcentajeCurso": min(100, correctos * 20),
        "erroresCorregidos": corregidos,
        "totalEnvios": len(envios),
    }


def pantalla_inicial(usuario):
    """A dónde lleva el servidor al usuario al entrar: panel, diagnóstico o catálogo."""
    if usuario.es_docente:
        return "panel"
    return "catalogo" if nivel_actual(usuario.id) else "diagnostico"


def panel_profesor(curso):
    """Progreso agregado del grupo (CU-05). En el MVP todos los envíos pertenecen al curso inicial."""
    estudiantes = []
    for u in Usuario.estudiantes():
        progreso = progreso_estudiante(u.id)
        if TestDiagnostico.contar_de(u.id) == 0 and progreso["totalEnvios"] == 0:
            continue  # sin actividad: no cuenta como activo
        estudiantes.append({
            "id": u.id,
            "nombre": u.nombre,
            "nivel": nivel_actual(u.id) or "sin_evaluar",
            "progreso": progreso["porcentajeCurso"],
            "errores": ErrorDetectado.contar_de(u.id),
        })

    total_errores = ErrorDetectado.contar_todos()
    return {
        "cursoId": curso.id,
        "curso": curso.nombre,
        "estudiantesActivos": len(estudiantes),
        "promedioProgreso": round(sum(e["progreso"] for e in estudiantes) / len(estudiantes)) if estudiantes else 0,
        "erroresDetectados": total_errores,
        "estudiantes": estudiantes,
        "topErrores": [
            {"tipo": t["tipo"], "nombre": NOMBRES_ERROR[t["tipo"]], "cantidad": t["cantidad"],
             "porcentaje": round(t["cantidad"] * 100 / total_errores)}
            for t in ErrorDetectado.mas_frecuentes(3)
        ],
    }
