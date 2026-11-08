"""Catálogo de cursos (CU-04) y gestión de cursos y módulos (CU-06)."""
from flask import Blueprint, g, jsonify

from controllers.utilidades import cuerpo_json, entero, texto
from models import curso as modelo_curso
from models.sqlite_db import get_sqlite
from services import actividad
from services.errores import ErrorServicio
from services.sesion import DOCENTES, requiere_sesion

bp = Blueprint("cursos", __name__, url_prefix="/api")

NIVELES = ("Inicial", "Intermedio", "Avanzado")
ESTADOS = ("Activo", "Inactivo")


def _curso_json(fila):
    return {
        "id": fila["id_curso"],
        "nombre": fila["nombre"],
        "descripcion": fila["descripcion"],
        "nivel": fila["nivel"],
        "estado": fila["estado"],
        "totalModulos": fila["total_modulos"],
        # Un curso está disponible para practicar cuando está activo y ya tiene módulos.
        "disponible": fila["estado"] == "Activo" and fila["total_modulos"] > 0,
    }


def _modulo_json(fila, con_contenido=True):
    datos = {"id": fila["id_modulo"], "cursoId": fila["id_curso"], "titulo": fila["titulo"], "orden": fila["orden"]}
    if con_contenido:
        datos["contenido"] = fila["contenido"]
    return datos


def _datos_curso(datos):
    nivel = datos.get("nivel", "Inicial")
    estado = datos.get("estado", "Activo")
    if nivel not in NIVELES:
        raise ErrorServicio(400, "El nivel no es válido.")
    if estado not in ESTADOS:
        raise ErrorServicio(400, "El estado no es válido.")
    return (texto(datos, "nombre", "El nombre del curso", 120),
            texto(datos, "descripcion", "La descripción del curso", 500), nivel, estado)


def _curso_o_404(id_curso):
    curso = modelo_curso.obtener(get_sqlite(), id_curso)
    if curso is None:
        raise ErrorServicio(404, "No encontramos ese curso.")
    return curso


# ------------------------------------------------------------------ cursos

@bp.get("/cursos")
@requiere_sesion()
def listar():
    return jsonify({"cursos": [_curso_json(c) for c in modelo_curso.listar(get_sqlite())]})


@bp.get("/cursos/<int:id_curso>")
@requiere_sesion()
def detalle(id_curso):
    curso = _curso_o_404(id_curso)
    datos = _curso_json(curso)
    datos["modulos"] = [_modulo_json(m) for m in modelo_curso.modulos_de(get_sqlite(), id_curso)]
    actividad.registrar("curso_consultado", g.usuario["id_usuario"], {"idCurso": id_curso})
    return jsonify(datos)


@bp.post("/cursos")
@requiere_sesion(rol=DOCENTES)
def crear():
    nombre, descripcion, nivel, estado = _datos_curso(cuerpo_json())
    id_curso = modelo_curso.crear(get_sqlite(), nombre, descripcion, nivel, estado)
    return jsonify(_curso_json(modelo_curso.obtener(get_sqlite(), id_curso))), 201


@bp.put("/cursos/<int:id_curso>")
@requiere_sesion(rol=DOCENTES)
def actualizar(id_curso):
    _curso_o_404(id_curso)
    nombre, descripcion, nivel, estado = _datos_curso(cuerpo_json())
    modelo_curso.actualizar(get_sqlite(), id_curso, nombre, descripcion, nivel, estado)
    return jsonify(_curso_json(modelo_curso.obtener(get_sqlite(), id_curso)))


@bp.delete("/cursos/<int:id_curso>")
@requiere_sesion(rol=DOCENTES)
def eliminar(id_curso):
    _curso_o_404(id_curso)
    modelo_curso.eliminar(get_sqlite(), id_curso)
    return jsonify({"eliminado": True})


# ------------------------------------------------------------------ módulos

def _datos_modulo(datos, orden_obligatorio):
    titulo = texto(datos, "titulo", "El título del módulo", 150)
    contenido = texto(datos, "contenido", "El contenido del módulo", 20000, obligatorio=False)
    orden = datos.get("orden")
    if orden is None and not orden_obligatorio:
        return titulo, contenido, None
    orden = entero(orden, "El orden")
    if orden < 1:
        raise ErrorServicio(400, "El orden debe ser 1 o mayor.")
    return titulo, contenido, orden


@bp.post("/cursos/<int:id_curso>/modulos")
@requiere_sesion(rol=DOCENTES)
def crear_modulo(id_curso):
    _curso_o_404(id_curso)
    titulo, contenido, orden = _datos_modulo(cuerpo_json(), orden_obligatorio=False)
    id_modulo = modelo_curso.crear_modulo(get_sqlite(), id_curso, titulo, contenido, orden)
    if id_modulo is None:
        raise ErrorServicio(409, "Ya existe un módulo con ese orden en el curso.")
    return jsonify(_modulo_json(modelo_curso.obtener_modulo(get_sqlite(), id_modulo))), 201


@bp.put("/modulos/<int:id_modulo>")
@requiere_sesion(rol=DOCENTES)
def actualizar_modulo(id_modulo):
    actual = modelo_curso.obtener_modulo(get_sqlite(), id_modulo)
    if actual is None:
        raise ErrorServicio(404, "No encontramos ese módulo.")
    titulo, contenido, orden = _datos_modulo(cuerpo_json(), orden_obligatorio=False)
    resultado = modelo_curso.actualizar_modulo(
        get_sqlite(), id_modulo, titulo, contenido, orden if orden is not None else actual["orden"])
    if resultado is None:
        raise ErrorServicio(409, "Ya existe un módulo con ese orden en el curso.")
    return jsonify(_modulo_json(modelo_curso.obtener_modulo(get_sqlite(), id_modulo)))


@bp.delete("/modulos/<int:id_modulo>")
@requiere_sesion(rol=DOCENTES)
def eliminar_modulo(id_modulo):
    if not modelo_curso.eliminar_modulo(get_sqlite(), id_modulo):
        raise ErrorServicio(404, "No encontramos ese módulo.")
    return jsonify({"eliminado": True})
