"""Modelo Comentario (colección comentarios_modulo de MongoDB).

Atributos opcionales y cambiantes: etiquetas, fragmento de código, reacciones que aparecen según se usan.
idUsuario e idModulo son los ids de las tablas usuarios y modulos de SQLite (vínculo lógico).
"""
from models.mongo_db import ahora, coleccion, iso, objeto_id

NOMBRE = "comentarios_modulo"


class Comentario:
    def __init__(self, doc):
        self.id = doc["_id"]
        self.id_modulo = doc["idModulo"]
        self.id_usuario = doc["idUsuario"]
        self.texto = doc["texto"]
        self.etiquetas = doc.get("etiquetas", [])
        self.reacciones = doc.get("reacciones", {})
        self.fragmento = doc.get("fragmentoCodigo")
        self.fecha = doc["fecha"]
        self.editado_en = doc.get("editadoEn")

    @classmethod
    def por_id(cls, texto_id):
        """Devuelve el comentario o None; lanza 400 si el id no tiene formato válido."""
        doc = coleccion(NOMBRE).find_one({"_id": objeto_id(texto_id, "El id del comentario")})
        return cls(doc) if doc else None

    @classmethod
    def crear(cls, id_usuario, id_modulo, texto, etiquetas, fragmento):
        doc = {"idUsuario": id_usuario, "idModulo": id_modulo, "texto": texto, "etiquetas": etiquetas,
               "reacciones": {}, "fecha": ahora()}
        if fragmento:
            doc["fragmentoCodigo"] = fragmento
        doc["_id"] = coleccion(NOMBRE).insert_one(doc).inserted_id
        return cls(doc)

    @classmethod
    def de_modulo(cls, id_modulo, limite=50):
        cursor = coleccion(NOMBRE).find({"idModulo": id_modulo}).sort("fecha", -1).limit(limite)
        return [cls(d) for d in cursor]

    @classmethod
    def contar_de(cls, id_usuario):
        return coleccion(NOMBRE).count_documents({"idUsuario": id_usuario})

    def actualizar(self, texto, etiquetas, fragmento):
        cambios = {"texto": texto, "etiquetas": etiquetas, "editadoEn": ahora()}
        operacion = {"$set": cambios}
        if fragmento:
            cambios["fragmentoCodigo"] = fragmento
        else:
            operacion["$unset"] = {"fragmentoCodigo": ""}
        coleccion(NOMBRE).update_one({"_id": self.id}, operacion)
        return Comentario.por_id(str(self.id))

    def reaccionar(self, tipo):
        """Suma 1 a la reacción indicada; el campo se crea solo la primera vez."""
        coleccion(NOMBRE).update_one({"_id": self.id}, {"$inc": {f"reacciones.{tipo}": 1}})
        return Comentario.por_id(str(self.id))

    def eliminar(self):
        coleccion(NOMBRE).delete_one({"_id": self.id})

    def a_dict(self, autores=None):
        datos = {"id": str(self.id), "idModulo": self.id_modulo, "idUsuario": self.id_usuario,
                 "texto": self.texto, "etiquetas": self.etiquetas, "reacciones": self.reacciones,
                 "fecha": iso(self.fecha), "editadoEn": iso(self.editado_en)}
        if self.fragmento:
            datos["fragmentoCodigo"] = self.fragmento
        if autores is not None:  # nombre tomado de SQLite (no se duplica en Mongo)
            datos["autor"] = autores.get(self.id_usuario, "Usuario eliminado")
        return datos
