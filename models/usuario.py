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
