"""Acceso a la tabla usuarios."""
import sqlite3


def crear(conexion, nombre, email, password_hash, rol):
    try:
        with conexion:
            cursor = conexion.execute(
                "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES (?, ?, ?, ?)",
                (nombre, email, password_hash, rol),
            )
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None  # correo repetido (restricción UNIQUE)


def por_email(conexion, email):
    return conexion.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()


def por_id(conexion, id_usuario):
    return conexion.execute("SELECT * FROM usuarios WHERE id_usuario = ?", (id_usuario,)).fetchone()


def publico(fila):
    """Datos que sí se pueden enviar al navegador (nunca el hash)."""
    return {"id": fila["id_usuario"], "nombre": fila["nombre"], "email": fila["email"], "rol": fila["rol"]}


def con_fecha(fila):
    return {**publico(fila), "fechaRegistro": fila["fecha_registro"]}


def listar(conexion, rol=None):
    consulta = "SELECT * FROM usuarios"
    parametros = ()
    if rol:
        consulta += " WHERE rol = ?"
        parametros = (rol,)
    return conexion.execute(consulta + " ORDER BY id_usuario", parametros).fetchall()


def cambiar_rol(conexion, id_usuario, rol):
    with conexion:
        conexion.execute("UPDATE usuarios SET rol = ? WHERE id_usuario = ?", (rol, id_usuario))

