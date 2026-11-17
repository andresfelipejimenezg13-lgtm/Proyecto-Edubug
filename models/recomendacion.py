"""Modelo Recomendacion (tablas recomendaciones, recomendacion_errores y recomendacion_modulos)."""
from models.sqlite_db import get_sqlite, transaccion


class Recomendacion:
    @classmethod
    def ultima_id(cls, id_usuario):
        fila = get_sqlite().execute(
            "SELECT id_recomendacion FROM recomendaciones WHERE id_usuario = ? "
            "ORDER BY id_recomendacion DESC LIMIT 1", (id_usuario,)).fetchone()
        return fila["id_recomendacion"] if fila else None

    @classmethod
    def tipos_de_error(cls, id_recomendacion):
        filas = get_sqlite().execute(
            "SELECT tipo_error FROM recomendacion_errores WHERE id_recomendacion = ? ORDER BY tipo_error",
            (id_recomendacion,))
        return [f["tipo_error"] for f in filas]

    @classmethod
    def crear(cls, id_usuario, tipos_error, ids_modulo):
        """Guarda la recomendación con sus errores y módulos en una sola transacción."""
        with transaccion() as conexion:
            id_recomendacion = conexion.execute(
                "INSERT INTO recomendaciones (id_usuario) VALUES (?)", (id_usuario,)).lastrowid
            for tipo in tipos_error:
                conexion.execute("INSERT INTO recomendacion_errores (tipo_error, id_recomendacion) VALUES (?, ?)",
                                 (tipo, id_recomendacion))
            for id_modulo in ids_modulo:
                conexion.execute("INSERT INTO recomendacion_modulos (id_modulo, id_recomendacion) VALUES (?, ?)",
                                 (id_modulo, id_recomendacion))
        return id_recomendacion

    @classmethod
    def detalle(cls, id_recomendacion):
        """Fecha y módulos sugeridos de una recomendación."""
        conexion = get_sqlite()
        cabecera = conexion.execute(
            "SELECT * FROM recomendaciones WHERE id_recomendacion = ?", (id_recomendacion,)).fetchone()
        modulos = conexion.execute(
            """
            SELECT m.id_modulo, m.id_curso, m.titulo, m.orden, c.nombre AS curso
            FROM recomendacion_modulos rm
            JOIN modulos m ON m.id_modulo = rm.id_modulo
            JOIN cursos c ON c.id_curso = m.id_curso
            WHERE rm.id_recomendacion = ? ORDER BY c.id_curso, m.orden
            """, (id_recomendacion,)).fetchall()
        return {"fecha": cabecera["fecha"],
                "modulos": [{"curso": m["curso"], "modulo": m["titulo"], "idModulo": m["id_modulo"], "idCurso": m["id_curso"],
                             "orden": m["orden"]} for m in modulos]}
