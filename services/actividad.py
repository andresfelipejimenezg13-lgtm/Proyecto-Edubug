"""Registro automático de actividad en MongoDB.

`registrar` nunca interrumpe la petición principal: si Mongo no está configurado o falla, el evento
simplemente se omite (se deja una advertencia en el log). Así SQLite sigue siendo la fuente de verdad
y Mongo solo guarda la bitácora.
"""
import json
import logging

from models import documentos

log = logging.getLogger(__name__)

TIPOS_ACTIVIDAD = (
    "registro", "login", "curso_consultado", "tema_visto",
    "diagnostico_iniciado", "diagnostico_respuesta", "diagnostico_finalizado",
    "codigo_analizado", "comentario_creado",
)
MAX_DETALLE = 2000  # caracteres del detalle serializado


def registrar(tipo, id_usuario, detalle=None):
    if not documentos.disponible():
        return None
    try:
        doc = documentos.crear_actividad(id_usuario, tipo, detalle or {})
        return str(doc["_id"])
    except Exception:  # la bitácora es secundaria: nunca debe tumbar la petición
        log.warning("No se pudo guardar la actividad %s en MongoDB", tipo, exc_info=True)
        return None


def validar_detalle(detalle):
    from services.errores import ErrorServicio
    if not isinstance(detalle, dict):
        raise ErrorServicio(400, "El detalle debe ser un objeto JSON.")
    if len(json.dumps(detalle, ensure_ascii=False)) > MAX_DETALLE:
        raise ErrorServicio(400, f"El detalle no puede pasar de {MAX_DETALLE} caracteres.")
    return detalle
