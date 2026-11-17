"""Modelo Usuario (tabla usuarios)."""
import sqlite3

from models.sqlite_db import get_sqlite, transaccion


class Usuario:
    ROLES = ("estudiante", "profesor", "admin")
    DOCENTES = ("profesor", "admin")  # quienes pueden gestionar cursos y ver el progreso del grupo

    def __init__(self, fila):
        self.id = fila["id_usuario"]
        self.nombre = fila["nombre"]
        self.email = fila["email"]
        self.password_hash = fila["password_hash"]
        self.rol = fila["rol"]
        self.fecha_registro = fila["fecha_registro"]

    # ---- consultas
    @classmethod
    def por_id(cls, id_usuario):
        fila = get_sqlite().execute("SELECT * FROM usuarios WHERE id_usuario = ?", (id_usuario,)).fetchone()
        return cls(fila) if fila else None

    @classmethod
    def por_email(cls, email):
        fila = get_sqlite().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
        return cls(fila) if fila else None

    @classmethod
    def listar(cls, rol=None):
        consulta, parametros = "SELECT * FROM usuarios", ()
        if rol:
            consulta, parametros = consulta + " WHERE rol = ?", (rol,)
        return [cls(f) for f in get_sqlite().execute(consulta + " ORDER BY id_usuario", parametros)]

    @classmethod
    def estudiantes(cls):
        filas = get_sqlite().execute("SELECT * FROM usuarios WHERE rol = 'estudiante' ORDER BY nombre")
        return [cls(f) for f in filas]

    # ---- escritura
    @classmethod
    def crear(cls, nombre, email, password_hash, rol):
        """Devuelve el usuario nuevo, o None si el correo ya existe (restricción UNIQUE)."""
        try:
            with transaccion() as conexion:
                cursor = conexion.execute(
                    "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES (?, ?, ?, ?)",
                    (nombre, email, password_hash, rol),
                )
        except sqlite3.IntegrityError:
            return None
        return cls.por_id(cursor.lastrowid)

    def cambiar_rol(self, rol):
        with transaccion() as conexion:
            conexion.execute("UPDATE usuarios SET rol = ? WHERE id_usuario = ?", (rol, self.id))
        self.rol = rol

    # ---- comportamiento
    @property
    def es_estudiante(self):
        return self.rol == "estudiante"

    @property
    def es_docente(self):
        return self.rol in self.DOCENTES

    def a_dict(self, con_fecha=False):
        """Datos que sí se pueden enviar al navegador (nunca el hash de la contraseña)."""
        datos = {"id": self.id, "nombre": self.nombre, "email": self.email, "rol": self.rol}
        if con_fecha:
            datos["fechaRegistro"] = self.fecha_registro
        return datos
