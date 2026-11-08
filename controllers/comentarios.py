"""Comentarios de los módulos (MongoDB): CRUD completo y reacciones."""
from flask import Blueprint, g, jsonify

from controllers.utilidades import cuerpo_json, texto
from models import curso as modelo_curso
from models import documentos
from models import usuario as modelo_usuario
from models.sqlite_db import get_sqlite
from services import actividad
from services.errores import ErrorServicio
from services.sesion import DOCENTES, requiere_sesion

bp = Blueprint("comentarios", __name__, url_prefix="/api")

REACCIONES = ("util", "gracias", "confuso")


def _campos(datos):
    cuerpo = texto(datos, "texto", "El comentario", 1000)
    etiquetas = datos.get("etiquetas", [])
    if not isinstance(etiquetas, list) or len(etiquetas) > 5 or \
            any(not isinstance(e, str) or not e.strip() or len(e) > 30 for e in etiquetas):
        raise ErrorServicio(400, "Las etiquetas deben ser una lista de máximo 5 textos de hasta 30 caracteres.")
    fragmento = texto(datos, "fragmentoCodigo", "El fragmento de código", 2000, obligatorio=False)
    return cuerpo, [e.strip().lower() for e in etiquetas], fragmento


def _propio_o_404(id_comentario, permitir_profesor=False):
    identificador = documentos.objeto_id(id_comentario, "El id del comentario")
    doc = documentos.comentario_por_id(identificador)
    if doc is None:
        raise ErrorServicio(404, "No encontramos ese comentario.")
    es_autor = doc["idUsuario"] == g.usuario["id_usuario"]
    if not es_autor and not (permitir_profesor and g.usuario["rol"] in DOCENTES):
        raise ErrorServicio(403, "Solo el autor puede modificar este comentario.")
    return identificador, doc


def _nombres(docs):
    """Nombres de los autores, consultados en SQLite (el comentario solo guarda el idUsuario)."""
    conexion = get_sqlite()
    nombres = {}
    for id_usuario in {d["idUsuario"] for d in docs}:
        fila = modelo_usuario.por_id(conexion, id_usuario)
        if fila:
            nombres[id_usuario] = fila["nombre"]
    return nombres


@bp.post("/modulos/<int:id_modulo>/comentarios")
@requiere_sesion()
def crear(id_modulo):
    """CREATE. Cuerpo: {"texto", "etiquetas": [..], "fragmentoCodigo": ".."}."""
    if modelo_curso.obtener_modulo(get_sqlite(), id_modulo) is None:
        raise ErrorServicio(404, "No encontramos ese módulo.")
    cuerpo, etiquetas, fragmento = _campos(cuerpo_json())
    doc = documentos.crear_comentario(g.usuario["id_usuario"], id_modulo, cuerpo, etiquetas, fragmento)
    actividad.registrar("comentario_creado", g.usuario["id_usuario"],
                        {"idModulo": id_modulo, "idComentario": str(doc["_id"])})
    return jsonify(documentos.comentario_json(doc, _nombres([doc]))), 201


@bp.get("/modulos/<int:id_modulo>/comentarios")
@requiere_sesion()
def listar(id_modulo):
    """READ (lista). Une Mongo (comentarios) con SQLite (nombre del autor)."""
    if modelo_curso.obtener_modulo(get_sqlite(), id_modulo) is None:
        raise ErrorServicio(404, "No encontramos ese módulo.")
    docs = documentos.comentarios_de_modulo(id_modulo)
    nombres = _nombres(docs)
    return jsonify({"idModulo": id_modulo, "total": len(docs),
                    "comentarios": [documentos.comentario_json(d, nombres) for d in docs]})


@bp.get("/comentarios/<id_comentario>")
@requiere_sesion()
def detalle(id_comentario):
    """READ (uno)."""
    identificador = documentos.objeto_id(id_comentario, "El id del comentario")
    doc = documentos.comentario_por_id(identificador)
    if doc is None:
        raise ErrorServicio(404, "No encontramos ese comentario.")
    return jsonify(documentos.comentario_json(doc, _nombres([doc])))


@bp.put("/comentarios/<id_comentario>")
@requiere_sesion()
def actualizar(id_comentario):
    """UPDATE. Solo el autor. Si no envías fragmentoCodigo, se quita."""
    identificador, _ = _propio_o_404(id_comentario)
    cuerpo, etiquetas, fragmento = _campos(cuerpo_json())
    doc = documentos.actualizar_comentario(identificador, cuerpo, etiquetas, fragmento)
    return jsonify(documentos.comentario_json(doc, _nombres([doc])))


@bp.post("/comentarios/<id_comentario>/reacciones")
@requiere_sesion()
def reaccionar(id_comentario):
    """UPDATE parcial ($inc). Cuerpo: {"tipo": "util" | "gracias" | "confuso"}."""
    identificador = documentos.objeto_id(id_comentario, "El id del comentario")
    if documentos.comentario_por_id(identificador) is None:
        raise ErrorServicio(404, "No encontramos ese comentario.")
    tipo = cuerpo_json().get("tipo")
    if tipo not in REACCIONES:
        raise ErrorServicio(400, "La reacción debe ser: " + ", ".join(REACCIONES) + ".")
    doc = documentos.reaccionar(identificador, tipo)
    return jsonify(documentos.comentario_json(doc, _nombres([doc])))


@bp.delete("/comentarios/<id_comentario>")
@requiere_sesion()
def eliminar(id_comentario):
    """DELETE. El autor, o cualquier profesor (moderación)."""
    identificador, _ = _propio_o_404(id_comentario, permitir_profesor=True)
    documentos.eliminar_comentario(identificador)
    return jsonify({"eliminado": True})
