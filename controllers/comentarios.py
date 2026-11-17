"""CONTROLADOR de los comentarios de los módulos (MongoDB): CRUD completo y reacciones."""
from flask import Blueprint, g, jsonify

from controllers.utilidades import cuerpo_json, texto
from models.comentario import Comentario
from models.curso import Modulo
from models.usuario import Usuario
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


def _comentario_o_404(id_comentario):
    comentario = Comentario.por_id(id_comentario)
    if comentario is None:
        raise ErrorServicio(404, "No encontramos ese comentario.")
    return comentario


def _propio_o_404(id_comentario, permitir_profesor=False):
    comentario = _comentario_o_404(id_comentario)
    es_autor = comentario.id_usuario == g.usuario.id
    if not es_autor and not (permitir_profesor and g.usuario.rol in DOCENTES):
        raise ErrorServicio(403, "Solo el autor puede modificar este comentario.")
    return comentario


def _nombres(comentarios):
    """Nombres de los autores, consultados en SQLite (el comentario solo guarda el idUsuario)."""
    nombres = {}
    for id_usuario in {c.id_usuario for c in comentarios}:
        usuario = Usuario.por_id(id_usuario)
        if usuario:
            nombres[id_usuario] = usuario.nombre
    return nombres


@bp.post("/modulos/<int:id_modulo>/comentarios")
@requiere_sesion()
def crear(id_modulo):
    """CREATE. Cuerpo: {"texto", "etiquetas": [..], "fragmentoCodigo": ".."}."""
    if Modulo.obtener(id_modulo) is None:
        raise ErrorServicio(404, "No encontramos ese módulo.")
    cuerpo, etiquetas, fragmento = _campos(cuerpo_json())
    comentario = Comentario.crear(g.usuario.id, id_modulo, cuerpo, etiquetas, fragmento)
    actividad.registrar("comentario_creado", g.usuario.id,
                        {"idModulo": id_modulo, "idComentario": str(comentario.id)})
    return jsonify(comentario.a_dict(_nombres([comentario]))), 201


@bp.get("/modulos/<int:id_modulo>/comentarios")
@requiere_sesion()
def listar(id_modulo):
    """READ (lista). Une Mongo (comentarios) con SQLite (nombre del autor)."""
    if Modulo.obtener(id_modulo) is None:
        raise ErrorServicio(404, "No encontramos ese módulo.")
    comentarios = Comentario.de_modulo(id_modulo)
    nombres = _nombres(comentarios)
    return jsonify({"idModulo": id_modulo, "total": len(comentarios),
                    "comentarios": [c.a_dict(nombres) for c in comentarios]})


@bp.get("/comentarios/<id_comentario>")
@requiere_sesion()
def detalle(id_comentario):
    """READ (uno)."""
    comentario = _comentario_o_404(id_comentario)
    return jsonify(comentario.a_dict(_nombres([comentario])))


@bp.put("/comentarios/<id_comentario>")
@requiere_sesion()
def actualizar(id_comentario):
    """UPDATE. Solo el autor. Si no envías fragmentoCodigo, se quita."""
    comentario = _propio_o_404(id_comentario)
    cuerpo, etiquetas, fragmento = _campos(cuerpo_json())
    actualizado = comentario.actualizar(cuerpo, etiquetas, fragmento)
    return jsonify(actualizado.a_dict(_nombres([actualizado])))


@bp.post("/comentarios/<id_comentario>/reacciones")
@requiere_sesion()
def reaccionar(id_comentario):
    """UPDATE parcial ($inc). Cuerpo: {"tipo": "util" | "gracias" | "confuso"}."""
    comentario = _comentario_o_404(id_comentario)
    tipo = cuerpo_json().get("tipo")
    if tipo not in REACCIONES:
        raise ErrorServicio(400, "La reacción debe ser: " + ", ".join(REACCIONES) + ".")
    actualizado = comentario.reaccionar(tipo)
    return jsonify(actualizado.a_dict(_nombres([actualizado])))


@bp.delete("/comentarios/<id_comentario>")
@requiere_sesion()
def eliminar(id_comentario):
    """DELETE. El autor, o cualquier profesor (moderación)."""
    _propio_o_404(id_comentario, permitir_profesor=True).eliminar()
    return jsonify({"eliminado": True})
