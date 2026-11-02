"""Conexión opcional a MongoDB.

La aplicación NO depende de MongoDB: todo el modelo vive en SQLite. Este módulo solo deja lista
la conexión para cuando se quiera usar (por ejemplo, con MongoDB Atlas):

- Sin MONGO_URI no se conecta a nada.
- Con MONGO_URI se crea el cliente y /api/salud comprueba que responda.
- "mongomock://" usa una base falsa en memoria (solo para pruebas locales).
"""
import logging

from flask import current_app

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
