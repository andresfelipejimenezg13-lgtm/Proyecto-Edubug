"""CONTROLADOR de administración (solo rol admin): listar, crear cuentas con rol y cambiar roles."""
from flask import Blueprint, g, jsonify, request

from controllers.utilidades import cuerpo_json, texto
from models.usuario import Usuario
from services import cuentas
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
    usuarios = Usuario.listar(rol)
    return jsonify({"total": len(usuarios), "usuarios": [u.a_dict(con_fecha=True) for u in usuarios]})


@bp.post("/usuarios")
@requiere_sesion(rol="admin")
def crear():
    """Crea una cuenta con el rol indicado (estudiante, profesor o admin)."""
    datos = cuerpo_json()
    usuario = cuentas.crear_por_admin(
        g.usuario,
        texto(datos, "nombre", "El nombre", 80),
        texto(datos, "email", "El correo", 120).lower(),
        str(datos.get("password", "")),
        _rol_valido(datos.get("rol")),
    )
    return jsonify(usuario.a_dict(con_fecha=True)), 201


@bp.put("/usuarios/<int:id_usuario>/rol")
@requiere_sesion(rol="admin")
def cambiar_rol(id_usuario):
    rol = _rol_valido(cuerpo_json().get("rol"))
    return jsonify(cuentas.cambiar_rol(g.usuario, id_usuario, rol).a_dict(con_fecha=True))
