"""Administración de usuarios (solo rol admin): listar, crear cuentas con rol y cambiar roles."""
from flask import Blueprint, g, jsonify, request
from werkzeug.security import generate_password_hash

from controllers.usuarios import CORREO_VALIDO, validar_password
from controllers.utilidades import cuerpo_json, texto
from models import usuario as modelo_usuario
from models.sqlite_db import get_sqlite
from services import actividad
from services.errores import ErrorServicio
from services.sesion import ROLES, requiere_sesion

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def _rol_valido(rol):
    if rol not in ROLES:
        raise ErrorServicio(400, "El rol debe ser uno de: " + ", ".join(ROLES) + ".")
    return rol


@bp.get("/usuarios")
@requiere_sesion(rol="admin")
def listar():
    """Lista todas las cuentas. Filtro opcional: ?rol=profesor."""
    rol = request.args.get("rol")
    if rol:
        _rol_valido(rol)
    filas = modelo_usuario.listar(get_sqlite(), rol)
    return jsonify({"total": len(filas), "usuarios": [modelo_usuario.con_fecha(f) for f in filas]})


@bp.post("/usuarios")
@requiere_sesion(rol="admin")
def crear():
    """Crea una cuenta con el rol indicado (estudiante, profesor o admin)."""
    datos = cuerpo_json()
    nombre = texto(datos, "nombre", "El nombre", 80)
    email = texto(datos, "email", "El correo", 120).lower()
    password = str(datos.get("password", ""))
    rol = _rol_valido(datos.get("rol"))
    if not CORREO_VALIDO.match(email):
        raise ErrorServicio(400, "El correo no es válido.")
    validar_password(password)

    id_usuario = modelo_usuario.crear(get_sqlite(), nombre, email, generate_password_hash(password), rol)
    if id_usuario is None:
        raise ErrorServicio(409, "Ya existe una cuenta con este correo.")
    actividad.registrar("usuario_creado_por_admin", id_usuario, {"rol": rol, "admin": g.usuario["id_usuario"]})
    return jsonify(modelo_usuario.con_fecha(modelo_usuario.por_id(get_sqlite(), id_usuario))), 201


@bp.put("/usuarios/<int:id_usuario>/rol")
@requiere_sesion(rol="admin")
def cambiar_rol(id_usuario):
    """Cambia el rol de una cuenta. No puedes cambiar tu propio rol: así siempre queda al menos un administrador."""
    rol = _rol_valido(cuerpo_json().get("rol"))
    conexion = get_sqlite()
    objetivo = modelo_usuario.por_id(conexion, id_usuario)
    if objetivo is None:
        raise ErrorServicio(404, "No encontramos ese usuario.")
    if id_usuario == g.usuario["id_usuario"]:
        raise ErrorServicio(409, "No puedes cambiar tu propio rol.")

    anterior = objetivo["rol"]
    modelo_usuario.cambiar_rol(conexion, id_usuario, rol)
    actividad.registrar("rol_cambiado", id_usuario, {"de": anterior, "a": rol, "admin": g.usuario["id_usuario"]})
    return jsonify(modelo_usuario.con_fecha(modelo_usuario.por_id(conexion, id_usuario)))
