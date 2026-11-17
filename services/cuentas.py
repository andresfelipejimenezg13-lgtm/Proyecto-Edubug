"""Cuentas de usuario: registro público, alta por el administrador, cambio de rol y perfil completo."""
from werkzeug.security import generate_password_hash

from models.actividad import Actividad
from models.comentario import Comentario
from models.usuario import Usuario
from services import actividad, progreso, recomendaciones
from services.autenticacion import validar_correo, validar_password
from services.errores import ErrorServicio


def _crear(nombre, email, password, rol):
    validar_correo(email)
    validar_password(password)
    usuario = Usuario.crear(nombre, email, generate_password_hash(password), rol)
    if usuario is None:
        raise ErrorServicio(409, "Ya existe una cuenta con este correo.")
    return usuario


def registrar_estudiante(nombre, email, password, rol="estudiante"):
    if rol != "estudiante":
        # Las cuentas de profesor y admin las crea un administrador (POST /api/admin/usuarios).
        validar_correo(email)
        validar_password(password)
        raise ErrorServicio(403, "El registro público solo crea cuentas de estudiante.")
    usuario = _crear(nombre, email, password, rol)
    actividad.registrar("registro", usuario.id, {"rol": rol})
    return usuario


def crear_por_admin(admin, nombre, email, password, rol):
    usuario = _crear(nombre, email, password, rol)
    actividad.registrar("usuario_creado_por_admin", usuario.id, {"rol": rol, "admin": admin.id})
    return usuario


def cambiar_rol(admin, id_usuario, rol):
    """No puedes cambiar tu propio rol: así siempre queda al menos un administrador."""
    objetivo = Usuario.por_id(id_usuario)
    if objetivo is None:
        raise ErrorServicio(404, "No encontramos ese usuario.")
    if objetivo.id == admin.id:
        raise ErrorServicio(409, "No puedes cambiar tu propio rol.")
    anterior = objetivo.rol
    objetivo.cambiar_rol(rol)
    actividad.registrar("rol_cambiado", objetivo.id, {"de": anterior, "a": rol, "admin": admin.id})
    return objetivo


def perfil_completo(solicitante, id_usuario):
    """Combina SQLite (usuario, diagnóstico, progreso, recomendación) con MongoDB (actividad y comentarios).

    Si Mongo no está disponible, la parte SQL se entrega igual y `actividad.disponible` es false.
    """
    if solicitante.id != id_usuario and not solicitante.es_docente:
        raise ErrorServicio(403, "Solo puedes ver tu propio perfil.")
    usuario = Usuario.por_id(id_usuario)
    if usuario is None:
        raise ErrorServicio(404, "No encontramos ese usuario.")

    respuesta = {
        "usuario": usuario.a_dict(con_fecha=True),
        "progreso": progreso.progreso_estudiante(id_usuario) if usuario.es_estudiante else None,
        "recomendacion": recomendaciones.obtener(id_usuario) if usuario.es_estudiante else None,
        "fuentes": {"sql": "SQLite", "nosql": "MongoDB"},
    }
    try:
        respuesta["actividad"] = {
            "disponible": True,
            "ultimas": [a.a_dict() for a in Actividad.ultimas(id_usuario, 10)],
            "totalPorTipo": Actividad.resumen_de(id_usuario),
            "comentariosEscritos": Comentario.contar_de(id_usuario),
        }
    except ErrorServicio as error:
        respuesta["actividad"] = {"disponible": False, "mensaje": error.mensaje}
    except Exception as error:  # Mongo caído: el perfil SQL no debe fallar por eso
        respuesta["actividad"] = {"disponible": False, "mensaje": f"MongoDB no respondió: {error}"}
    return respuesta
