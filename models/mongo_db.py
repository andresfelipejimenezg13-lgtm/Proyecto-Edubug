"""Conexión opcional a MongoDB.

La aplicación NO depende de MongoDB: todo el modelo vive en SQLite. Este módulo solo deja lista
la conexión para cuando se quiera usar (por ejemplo, con MongoDB Atlas):

- Sin MONGO_URI no se conecta a nada.
- Con MONGO_URI se crea el cliente y /api/salud comprueba que responda.
- "mongomock://" usa una base falsa en memoria (solo para pruebas locales).
"""
import logging
from datetime import datetime, timezone

from bson import ObjectId
from flask import current_app

from services.errores import ErrorServicio

log = logging.getLogger(__name__)


def _crear_cliente(uri):
    if uri.startswith("mongomock://"):
        import mongomock  # solo para desarrollo y pruebas (requirements-dev.txt)
        log.warning("MONGO_URI=mongomock://: usando MongoDB falso en memoria.")
        return mongomock.MongoClient(), "mongomock"
    from pymongo import MongoClient
    return MongoClient(uri, serverSelectionTimeoutMS=8000), "mongodb"


def get_mongo():
    """Base de datos Mongo lista para usar, o None si no se configuró MONGO_URI."""
    return current_app.extensions.get("mongo_db")


def ahora():
    return datetime.now(timezone.utc)


def iso(fecha):
    """Fecha en formato ISO 8601 UTC (Mongo puede devolverla sin zona horaria)."""
    if fecha is None:
        return None
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)
    return fecha.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def disponible():
    return get_mongo() is not None


def coleccion(nombre):
    """Devuelve la colección o lanza 503 si no hay MONGO_URI. Crea los índices la primera vez."""
    base = get_mongo()
    if base is None:
        raise ErrorServicio(503, "MongoDB no está configurado (falta MONGO_URI).")
    if not current_app.extensions.get("mongo_indices"):
        base["actividad_usuario"].create_index([("idUsuario", 1), ("fecha", -1)])
        base["actividad_usuario"].create_index([("tipo", 1)])
        base["comentarios_modulo"].create_index([("idModulo", 1), ("fecha", -1)])
        base["comentarios_modulo"].create_index([("idUsuario", 1)])
        current_app.extensions["mongo_indices"] = True
    return base[nombre]


def objeto_id(texto, nombre="El identificador"):
    if not isinstance(texto, str) or not ObjectId.is_valid(texto):
        raise ErrorServicio(400, f"{nombre} no es válido.")
    return ObjectId(texto)


def modo_mongo():
    return current_app.extensions.get("mongo_modo")


def comprobar():
    """Devuelve 'no configurado', 'ok' o 'error: ...' (para /api/salud)."""
    cliente = current_app.extensions.get("mongo_cliente")
    if cliente is None:
        return "no configurado"
    try:
        cliente.admin.command("ping")
        return "ok"
    except Exception as error:
        return f"error: {error}"


def init_app(app):
    uri = (app.config.get("MONGO_URI") or "").strip()
    app.extensions["mongo_cliente"] = None
    app.extensions["mongo_db"] = None
    app.extensions["mongo_modo"] = None
    if not uri:
        return
    cliente, modo = _crear_cliente(uri)  # la conexión real se abre al primer uso
    app.extensions["mongo_cliente"] = cliente
    app.extensions["mongo_db"] = cliente[app.config["MONGO_DB"]]
    app.extensions["mongo_modo"] = modo
