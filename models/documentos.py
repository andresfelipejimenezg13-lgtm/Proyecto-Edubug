"""Acceso a las colecciones de MongoDB (datos dinámicos y de alta frecuencia).

Colecciones:
  - actividad_usuario : bitácora de eventos (login, test, envíos al depurador...). Cada tipo de
                        evento guarda un `detalle` con campos distintos -> esquema flexible.
  - comentarios_modulo: comentarios de estudiantes sobre un módulo, con etiquetas, fragmento de
                        código opcional y reacciones (atributos que varían de un comentario a otro).

El vínculo con SQLite es lógico: `idUsuario` e `idModulo` son los ids numéricos de las tablas
usuarios y modulos. Mongo no valida esa relación; lo hace la capa de servicio.
"""
from datetime import datetime, timezone

from bson import ObjectId
from flask import current_app

from models.mongo_db import get_mongo
from services.errores import ErrorServicio


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


# ------------------------------------------------------------------ actividad

def actividad_json(doc):
    return {"id": str(doc["_id"]), "idUsuario": doc["idUsuario"], "tipo": doc["tipo"],
            "fecha": iso(doc["fecha"]), "detalle": doc.get("detalle", {})}


def crear_actividad(id_usuario, tipo, detalle):
    doc = {"idUsuario": id_usuario, "tipo": tipo, "fecha": ahora(), "detalle": detalle}
    doc["_id"] = coleccion("actividad_usuario").insert_one(doc).inserted_id
    return doc


def ultimas_actividades(id_usuario, limite=10, tipo=None):
    filtro = {"idUsuario": id_usuario}
    if tipo:
        filtro["tipo"] = tipo
    cursor = coleccion("actividad_usuario").find(filtro).sort("fecha", -1).limit(limite)
    return list(cursor)


def resumen_actividad(id_usuario):
    """Eventos por tipo (agregación de Mongo): {'login': 3, 'codigo_analizado': 5, ...}."""
    tuberia = [{"$match": {"idUsuario": id_usuario}}, {"$group": {"_id": "$tipo", "total": {"$sum": 1}}}]
    return {fila["_id"]: fila["total"] for fila in coleccion("actividad_usuario").aggregate(tuberia)}


def actividad_por_id(id_actividad):
    return coleccion("actividad_usuario").find_one({"_id": id_actividad})


def eliminar_actividad(id_actividad):
    return coleccion("actividad_usuario").delete_one({"_id": id_actividad}).deleted_count == 1


# ---------------------------------------------------------------- comentarios

def comentario_json(doc, autores=None):
    datos = {"id": str(doc["_id"]), "idModulo": doc["idModulo"], "idUsuario": doc["idUsuario"],
             "texto": doc["texto"], "etiquetas": doc.get("etiquetas", []),
             "reacciones": doc.get("reacciones", {}), "fecha": iso(doc["fecha"]),
             "editadoEn": iso(doc.get("editadoEn"))}
    if doc.get("fragmentoCodigo"):
        datos["fragmentoCodigo"] = doc["fragmentoCodigo"]
    if autores is not None:  # nombre tomado de SQLite (no se duplica en Mongo)
        datos["autor"] = autores.get(doc["idUsuario"], "Usuario eliminado")
    return datos


def crear_comentario(id_usuario, id_modulo, texto, etiquetas, fragmento):
    doc = {"idUsuario": id_usuario, "idModulo": id_modulo, "texto": texto, "etiquetas": etiquetas,
           "reacciones": {}, "fecha": ahora()}
    if fragmento:
        doc["fragmentoCodigo"] = fragmento
    doc["_id"] = coleccion("comentarios_modulo").insert_one(doc).inserted_id
    return doc


def comentarios_de_modulo(id_modulo, limite=50):
    return list(coleccion("comentarios_modulo").find({"idModulo": id_modulo}).sort("fecha", -1).limit(limite))


def contar_comentarios(id_usuario):
    return coleccion("comentarios_modulo").count_documents({"idUsuario": id_usuario})


def comentario_por_id(id_comentario):
    return coleccion("comentarios_modulo").find_one({"_id": id_comentario})


def actualizar_comentario(id_comentario, texto, etiquetas, fragmento):
    cambios = {"texto": texto, "etiquetas": etiquetas, "editadoEn": ahora()}
    operacion = {"$set": cambios}
    if fragmento:
        cambios["fragmentoCodigo"] = fragmento
    else:
        operacion["$unset"] = {"fragmentoCodigo": ""}
    coleccion("comentarios_modulo").update_one({"_id": id_comentario}, operacion)
    return comentario_por_id(id_comentario)


def reaccionar(id_comentario, tipo):
    """Suma 1 a la reacción indicada; el campo se crea solo la primera vez."""
    coleccion("comentarios_modulo").update_one({"_id": id_comentario}, {"$inc": {f"reacciones.{tipo}": 1}})
    return comentario_por_id(id_comentario)


def eliminar_comentario(id_comentario):
    return coleccion("comentarios_modulo").delete_one({"_id": id_comentario}).deleted_count == 1
