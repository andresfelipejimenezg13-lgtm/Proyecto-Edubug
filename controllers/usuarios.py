"""Registro público de estudiantes y perfil del usuario."""
import re

from flask import Blueprint, g, jsonify
from werkzeug.security import generate_password_hash

from controllers.auth import respuesta_de_sesion
from controllers.utilidades import cuerpo_json, texto
from models import documentos
from models import usuario as modelo_usuario
from models.sqlite_db import get_sqlite
from services import actividad, progreso, recomendaciones
from services.errores import ErrorServicio
from services.sesion import DOCENTES, requiere_sesion

bp = Blueprint("usuarios", __name__, url_prefix="/api/usuarios")

CORREO_VALIDO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validar_password(password):
    """Política de contraseñas: mínimo 8 caracteres, con al menos una letra y un número."""
    if len(password) < 8 or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise ErrorServicio(400, "La contraseña debe tener mínimo 8 caracteres, con letras y números.")


@bp.post("/registro")
def registro():
    datos = cuerpo_json()
    nombre = texto(datos, "nombre", "El nombre", 80)
    email = texto(datos, "email", "El correo", 120).lower()
    password = str(datos.get("password", ""))
    rol = datos.get("rol", "estudiante")

    if not CORREO_VALIDO.match(email):
        raise ErrorServicio(400, "El correo no es válido.")
    validar_password(password)
    if rol != "estudiante":
        # Las cuentas de profesor y admin las crea un administrador (POST /api/admin/usuarios).
        raise ErrorServicio(403, "El registro público solo crea cuentas de estudiante.")

    id_usuario = modelo_usuario.crear(get_sqlite(), nombre, email, generate_password_hash(password), rol)
    if id_usuario is None:
        raise ErrorServicio(409, "Ya existe una cuenta con este correo.")

    usuario = modelo_usuario.por_id(get_sqlite(), id_usuario)
    actividad.registrar("registro", id_usuario, {"rol": rol})
    return jsonify(respuesta_de_sesion(usuario)), 201


@bp.get("/<int:id_usuario>/perfil-completo")
@requiere_sesion()
def perfil_completo(id_usuario):
    """Endpoint combinado (persistencia políglota).

    SQLite (datos estructurados): usuario, diagnóstico, progreso y última recomendación.
    MongoDB (datos dinámicos): últimas 10 actividades, eventos por tipo y comentarios escritos.
    Si Mongo no está disponible, la parte SQL se entrega igual y `actividad.disponible` es false.
    """
    if g.usuario["id_usuario"] != id_usuario and g.usuario["rol"] not in DOCENTES:
        raise ErrorServicio(403, "Solo puedes ver tu propio perfil.")

    conexion = get_sqlite()
    fila = modelo_usuario.por_id(conexion, id_usuario)
    if fila is None:
        raise ErrorServicio(404, "No encontramos ese usuario.")

    es_estudiante = fila["rol"] == "estudiante"
    respuesta = {
        "usuario": {**modelo_usuario.publico(fila), "fechaRegistro": fila["fecha_registro"]},
        "progreso": progreso.progreso_estudiante(conexion, id_usuario) if es_estudiante else None,
        "recomendacion": recomendaciones.obtener(conexion, id_usuario) if es_estudiante else None,
        "fuentes": {"sql": "SQLite", "nosql": "MongoDB"},
    }

    try:
        docs = documentos.ultimas_actividades(id_usuario, 10)
        respuesta["actividad"] = {
            "disponible": True,
            "ultimas": [documentos.actividad_json(d) for d in docs],
            "totalPorTipo": documentos.resumen_actividad(id_usuario),
            "comentariosEscritos": documentos.contar_comentarios(id_usuario),
        }
    except ErrorServicio as error:
        respuesta["actividad"] = {"disponible": False, "mensaje": error.mensaje}
    except Exception as error:  # Mongo caído: el perfil SQL no debe fallar por eso
        respuesta["actividad"] = {"disponible": False, "mensaje": f"MongoDB no respondió: {error}"}
    return jsonify(respuesta)
