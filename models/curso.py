"""Acceso a las tablas cursos y modulos."""
import sqlite3


# ------------------------------------------------------------------ cursos

def listar(conexion):
    return conexion.execute(
        """
        SELECT c.*, (SELECT COUNT(*) FROM modulos m WHERE m.id_curso = c.id_curso) AS total_modulos
        FROM cursos c ORDER BY c.id_curso
        """
    ).fetchall()


def obtener(conexion, id_curso):
    return conexion.execute(
        """
        SELECT c.*, (SELECT COUNT(*) FROM modulos m WHERE m.id_curso = c.id_curso) AS total_modulos
        FROM cursos c WHERE c.id_curso = ?
        """,
        (id_curso,),
    ).fetchone()


def crear(conexion, nombre, descripcion, nivel, estado):
    with conexion:
        cursor = conexion.execute(
            "INSERT INTO cursos (nombre, descripcion, nivel, estado) VALUES (?, ?, ?, ?)",
            (nombre, descripcion, nivel, estado),
        )
    return cursor.lastrowid


def actualizar(conexion, id_curso, nombre, descripcion, nivel, estado):
    with conexion:
        cursor = conexion.execute(
            "UPDATE cursos SET nombre = ?, descripcion = ?, nivel = ?, estado = ? WHERE id_curso = ?",
            (nombre, descripcion, nivel, estado, id_curso),
        )
    return cursor.rowcount > 0


def eliminar(conexion, id_curso):
    """Borra el curso; sus módulos se borran en cascada."""
    with conexion:
        cursor = conexion.execute("DELETE FROM cursos WHERE id_curso = ?", (id_curso,))
    return cursor.rowcount > 0


# ------------------------------------------------------------------ módulos

def modulos_de(conexion, id_curso):
    return conexion.execute(
        "SELECT * FROM modulos WHERE id_curso = ? ORDER BY orden", (id_curso,)
    ).fetchall()


def obtener_modulo(conexion, id_modulo):
    return conexion.execute("SELECT * FROM modulos WHERE id_modulo = ?", (id_modulo,)).fetchone()


def crear_modulo(conexion, id_curso, titulo, contenido, orden=None):
    """Devuelve el id del módulo nuevo o None si ya existe un módulo con ese orden."""
    try:
        with conexion:
            if orden is None:
                orden = conexion.execute(
                    "SELECT COALESCE(MAX(orden), 0) + 1 FROM modulos WHERE id_curso = ?", (id_curso,)
                ).fetchone()[0]
            cursor = conexion.execute(
                "INSERT INTO modulos (id_curso, titulo, contenido, orden) VALUES (?, ?, ?, ?)",
                (id_curso, titulo, contenido, orden),
            )
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None


def actualizar_modulo(conexion, id_modulo, titulo, contenido, orden):
    """True si se actualizó, False si no existe, None si el orden ya está ocupado."""
    try:
        with conexion:
            cursor = conexion.execute(
                "UPDATE modulos SET titulo = ?, contenido = ?, orden = ? WHERE id_modulo = ?",
                (titulo, contenido, orden, id_modulo),
            )
        return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        return None


def eliminar_modulo(conexion, id_modulo):
    with conexion:
        cursor = conexion.execute("DELETE FROM modulos WHERE id_modulo = ?", (id_modulo,))
    return cursor.rowcount > 0
