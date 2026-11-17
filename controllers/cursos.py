"""CONTROLADOR del catálogo de cursos (CU-04) y de la gestión de cursos y módulos (CU-06)."""
from flask import Blueprint, g, jsonify

from controllers.utilidades import cuerpo_json, entero, texto
from models.curso import Curso, Modulo
from services import actividad
from services.errores import ErrorServicio
from services.sesion import DOCENTES, requiere_sesion

bp = Blueprint("cursos", __name__, url_prefix="/api")

def _datos_curso(datos):
    nivel = datos.get("nivel", "Inicial")
    estado = datos.get("estado", "Activo")
    if nivel not in Curso.NIVELES:
        raise ErrorServicio(400, "El nivel no es válido.")
    if estado not in Curso.ESTADOS:
        raise ErrorServicio(400, "El estado no es válido.")
    return (texto(datos, "nombre", "El nombre del curso", 120),
            texto(datos, "descripcion", "La descripción del curso", 500), nivel, estado)


def _curso_o_404(id_curso):
    curso = Curso.obtener(id_curso)
    if curso is None:
        raise ErrorServicio(404, "No encontramos ese curso.")
    return curso


# ------------------------------------------------------------------ cursos

@bp.get("/cursos")
@requiere_sesion()
def listar():
    return jsonify({"cursos": [c.a_dict() for c in Curso.listar()]})


@bp.get("/cursos/<int:id_curso>")
@requiere_sesion()
def detalle(id_curso):
    curso = _curso_o_404(id_curso)
    datos = curso.a_dict()
    datos["modulos"] = [m.a_dict() for m in curso.modulos()]
    actividad.registrar("curso_consultado", g.usuario.id, {"idCurso": id_curso})
    return jsonify(datos)


@bp.post("/cursos")
@requiere_sesion(rol=DOCENTES)
def crear():
    nombre, descripcion, nivel, estado = _datos_curso(cuerpo_json())
    return jsonify(Curso.crear(nombre, descripcion, nivel, estado).a_dict()), 201


@bp.put("/cursos/<int:id_curso>")
@requiere_sesion(rol=DOCENTES)
def actualizar(id_curso):
    curso = _curso_o_404(id_curso)
    nombre, descripcion, nivel, estado = _datos_curso(cuerpo_json())
    return jsonify(curso.actualizar(nombre, descripcion, nivel, estado).a_dict())


@bp.delete("/cursos/<int:id_curso>")
@requiere_sesion(rol=DOCENTES)
def eliminar(id_curso):
    _curso_o_404(id_curso).eliminar()
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
    modulo = Modulo.crear(id_curso, titulo, contenido, orden)
    if modulo is None:
        raise ErrorServicio(409, "Ya existe un módulo con ese orden en el curso.")
    return jsonify(modulo.a_dict()), 201


@bp.put("/modulos/<int:id_modulo>")
@requiere_sesion(rol=DOCENTES)
def actualizar_modulo(id_modulo):
    actual = Modulo.obtener(id_modulo)
    if actual is None:
        raise ErrorServicio(404, "No encontramos ese módulo.")
    titulo, contenido, orden = _datos_modulo(cuerpo_json(), orden_obligatorio=False)
    modulo = actual.actualizar(titulo, contenido, orden if orden is not None else actual.orden)
    if modulo is None:
        raise ErrorServicio(409, "Ya existe un módulo con ese orden en el curso.")
    return jsonify(modulo.a_dict())


@bp.delete("/modulos/<int:id_modulo>")
@requiere_sesion(rol=DOCENTES)
def eliminar_modulo(id_modulo):
    modulo = Modulo.obtener(id_modulo)
    if modulo is None:
        raise ErrorServicio(404, "No encontramos ese módulo.")
    modulo.eliminar()
    return jsonify({"eliminado": True})
