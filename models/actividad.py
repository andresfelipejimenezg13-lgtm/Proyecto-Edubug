"""Modelo Actividad (colección actividad_usuario de MongoDB).

Bitácora de eventos (login, test, envíos al depurador...). Cada tipo de evento guarda un `detalle` con campos
distintos, por eso es un documento y no una tabla. El vínculo con SQLite es lógico: idUsuario es usuarios.id_usuario.
"""
from models.mongo_db import ahora, coleccion, disponible, iso, objeto_id  # noqa: F401  (disponible se reexporta)

NOMBRE = "actividad_usuario"


class Actividad:
    def __init__(self, doc):
        self.id = doc["_id"]
        self.id_usuario = doc["idUsuario"]
        self.tipo = doc["tipo"]
        self.fecha = doc["fecha"]
        self.detalle = doc.get("detalle", {})

    @classmethod
    def crear(cls, id_usuario, tipo, detalle):
        doc = {"idUsuario": id_usuario, "tipo": tipo, "fecha": ahora(), "detalle": detalle}
        doc["_id"] = coleccion(NOMBRE).insert_one(doc).inserted_id
        return cls(doc)

    @classmethod
    def ultimas(cls, id_usuario, limite=10, tipo=None):
        filtro = {"idUsuario": id_usuario}
        if tipo:
            filtro["tipo"] = tipo
        return [cls(d) for d in coleccion(NOMBRE).find(filtro).sort("fecha", -1).limit(limite)]

    @classmethod
    def resumen_de(cls, id_usuario):
        """Eventos por tipo (agregación de Mongo): {'login': 3, 'codigo_analizado': 5, ...}."""
        tuberia = [{"$match": {"idUsuario": id_usuario}}, {"$group": {"_id": "$tipo", "total": {"$sum": 1}}}]
        return {fila["_id"]: fila["total"] for fila in coleccion(NOMBRE).aggregate(tuberia)}

    @classmethod
    def por_id(cls, texto_id):
        doc = coleccion(NOMBRE).find_one({"_id": objeto_id(texto_id, "El id de la actividad")})
        return cls(doc) if doc else None

    def eliminar(self):
        coleccion(NOMBRE).delete_one({"_id": self.id})

    def a_dict(self):
        return {"id": str(self.id), "idUsuario": self.id_usuario, "tipo": self.tipo,
                "fecha": iso(self.fecha), "detalle": self.detalle}
