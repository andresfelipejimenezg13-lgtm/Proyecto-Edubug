"""Modelos Curso y Modulo (tablas cursos y modulos)."""
import sqlite3

from models.sqlite_db import get_sqlite, transaccion

_CON_TOTAL = "SELECT c.*, (SELECT COUNT(*) FROM modulos m WHERE m.id_curso = c.id_curso) AS total_modulos FROM cursos c"


class Curso:
    NIVELES = ("Inicial", "Intermedio", "Avanzado")
    ESTADOS = ("Activo", "Inactivo")

    def __init__(self, fila):
        self.id = fila["id_curso"]
        self.nombre = fila["nombre"]
        self.descripcion = fila["descripcion"]
        self.nivel = fila["nivel"]
        self.estado = fila["estado"]
        self.total_modulos = fila["total_modulos"]

    @classmethod
    def listar(cls):
        return [cls(f) for f in get_sqlite().execute(_CON_TOTAL + " ORDER BY c.id_curso")]

    @classmethod
    def obtener(cls, id_curso):
        fila = get_sqlite().execute(_CON_TOTAL + " WHERE c.id_curso = ?", (id_curso,)).fetchone()
        return cls(fila) if fila else None

    @classmethod
    def primero(cls):
        fila = get_sqlite().execute(_CON_TOTAL + " ORDER BY c.id_curso LIMIT 1").fetchone()
        return cls(fila) if fila else None

    @classmethod
    def crear(cls, nombre, descripcion, nivel, estado):
        with transaccion() as conexion:
            cursor = conexion.execute(
                "INSERT INTO cursos (nombre, descripcion, nivel, estado) VALUES (?, ?, ?, ?)",
                (nombre, descripcion, nivel, estado),
            )
        return cls.obtener(cursor.lastrowid)

    def actualizar(self, nombre, descripcion, nivel, estado):
        with transaccion() as conexion:
            conexion.execute(
                "UPDATE cursos SET nombre = ?, descripcion = ?, nivel = ?, estado = ? WHERE id_curso = ?",
                (nombre, descripcion, nivel, estado, self.id),
            )
        return Curso.obtener(self.id)

    def eliminar(self):
        """Borra el curso; sus módulos se borran en cascada."""
        with transaccion() as conexion:
            conexion.execute("DELETE FROM cursos WHERE id_curso = ?", (self.id,))

    def modulos(self):
        return Modulo.de_curso(self.id)

    @property
    def disponible(self):
        """Un curso está disponible para practicar cuando está activo y ya tiene módulos."""
        return self.estado == "Activo" and self.total_modulos > 0

    def a_dict(self):
        return {"id": self.id, "nombre": self.nombre, "descripcion": self.descripcion, "nivel": self.nivel,
                "estado": self.estado, "totalModulos": self.total_modulos, "disponible": self.disponible}


class Modulo:
    def __init__(self, fila):
        self.id = fila["id_modulo"]
        self.curso_id = fila["id_curso"]
        self.titulo = fila["titulo"]
        self.contenido = fila["contenido"]
        self.orden = fila["orden"]

    @classmethod
    def de_curso(cls, id_curso):
        filas = get_sqlite().execute("SELECT * FROM modulos WHERE id_curso = ? ORDER BY orden", (id_curso,))
        return [cls(f) for f in filas]

    @classmethod
    def obtener(cls, id_modulo):
        fila = get_sqlite().execute("SELECT * FROM modulos WHERE id_modulo = ?", (id_modulo,)).fetchone()
        return cls(fila) if fila else None

    @classmethod
    def ids_por_orden(cls, id_curso, ordenes):
        """Ids de los módulos de un curso que tienen alguno de esos números de orden (en orden)."""
        if not ordenes:
            return []
        filas = get_sqlite().execute(
            f"SELECT id_modulo FROM modulos WHERE id_curso = ? AND orden IN ({','.join('?' * len(ordenes))}) "
            "ORDER BY orden", (id_curso, *ordenes))
        return [f["id_modulo"] for f in filas]

    @classmethod
    def crear(cls, id_curso, titulo, contenido, orden=None):
        """Devuelve el módulo nuevo o None si ya existe uno con ese orden en el curso."""
        try:
            with transaccion() as conexion:
                if orden is None:
                    orden = conexion.execute(
                        "SELECT COALESCE(MAX(orden), 0) + 1 FROM modulos WHERE id_curso = ?", (id_curso,)
                    ).fetchone()[0]
                cursor = conexion.execute(
                    "INSERT INTO modulos (id_curso, titulo, contenido, orden) VALUES (?, ?, ?, ?)",
                    (id_curso, titulo, contenido, orden),
                )
        except sqlite3.IntegrityError:
            return None
        return cls.obtener(cursor.lastrowid)

    def actualizar(self, titulo, contenido, orden):
        """Devuelve el módulo actualizado o None si el orden ya está ocupado."""
        try:
            with transaccion() as conexion:
                conexion.execute(
                    "UPDATE modulos SET titulo = ?, contenido = ?, orden = ? WHERE id_modulo = ?",
                    (titulo, contenido, orden, self.id),
                )
        except sqlite3.IntegrityError:
            return None
        return Modulo.obtener(self.id)

    def eliminar(self):
        with transaccion() as conexion:
            conexion.execute("DELETE FROM modulos WHERE id_modulo = ?", (self.id,))

    def a_dict(self, con_contenido=True):
        datos = {"id": self.id, "cursoId": self.curso_id, "titulo": self.titulo, "orden": self.orden}
        if con_contenido:
            datos["contenido"] = self.contenido
        return datos
