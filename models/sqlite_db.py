"""Base relacional (SQLite): las tablas del diagrama de la Fase inicial.

Las 10 tablas del diagrama (usuarios, cursos, modulos, tests_diagnosticos, preguntas_test,
envios_codigo, errores_detectados, recomendaciones, recomendacion_modulos, recomendacion_errores)
más una auxiliar, opciones_pregunta, que guarda las opciones de respuesta de cada pregunta
(así no hay listas dentro de un campo y se mantiene la 3FN).

Medidas de integridad: claves foráneas activas (PRAGMA foreign_keys = ON), modo WAL,
valores únicos y restricciones CHECK.
"""
import os
import sqlite3
from contextlib import contextmanager

from flask import current_app, g
from werkzeug.security import generate_password_hash

from data.cursos_extra import CURSOS_EXTRA, CURSOS_PROXIMOS
from data.modulos_html import CURSO_HTML, MODULOS_HTML, MODULOS_V1

TIPOS_ERROR = ("etiqueta_sin_cerrar", "atributo_sin_comillas", "etiqueta_en_mayusculas",
               "sin_html", "etiqueta_desconocida", "atributo_faltante", "etiqueta_incompleta")
_TIPOS_SQL = ", ".join(f"'{tipo}'" for tipo in TIPOS_ERROR)

COLUMNAS_USUARIOS = """(
    id_usuario     INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre         TEXT NOT NULL,
    email          TEXT NOT NULL UNIQUE,
    password_hash  TEXT NOT NULL,
    rol            TEXT NOT NULL CHECK (rol IN ('estudiante', 'profesor', 'admin')),
    fecha_registro TEXT NOT NULL DEFAULT (datetime('now'))
)"""

ESQUEMA = f"""
CREATE TABLE IF NOT EXISTS usuarios {COLUMNAS_USUARIOS};

CREATE TABLE IF NOT EXISTS cursos (
    id_curso    INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL,
    descripcion TEXT NOT NULL DEFAULT '',
    nivel       TEXT NOT NULL DEFAULT 'Inicial' CHECK (nivel IN ('Inicial', 'Intermedio', 'Avanzado')),
    estado      TEXT NOT NULL DEFAULT 'Activo' CHECK (estado IN ('Activo', 'Inactivo'))
);

CREATE TABLE IF NOT EXISTS modulos (
    id_modulo INTEGER PRIMARY KEY AUTOINCREMENT,
    id_curso  INTEGER NOT NULL REFERENCES cursos(id_curso) ON DELETE CASCADE,
    titulo    TEXT NOT NULL,
    contenido TEXT NOT NULL DEFAULT '',
    orden     INTEGER NOT NULL CHECK (orden >= 1),
    UNIQUE (id_curso, orden)
);

CREATE TABLE IF NOT EXISTS tests_diagnosticos (
    id_test        INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario     INTEGER NOT NULL REFERENCES usuarios(id_usuario),
    nivel_asignado TEXT CHECK (nivel_asignado IN ('bajo', 'medio', 'alto')),
    fecha          TEXT NOT NULL DEFAULT (datetime('now')),
    estado         TEXT NOT NULL DEFAULT 'en_curso' CHECK (estado IN ('en_curso', 'finalizado')),
    CHECK ((estado = 'finalizado') = (nivel_asignado IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS preguntas_test (
    id_pregunta       INTEGER PRIMARY KEY AUTOINCREMENT,
    id_test           INTEGER NOT NULL REFERENCES tests_diagnosticos(id_test) ON DELETE CASCADE,
    orden             INTEGER NOT NULL CHECK (orden >= 1),
    texto             TEXT NOT NULL,
    respuesta         TEXT NOT NULL,
    generada_por_ia   INTEGER NOT NULL DEFAULT 0 CHECK (generada_por_ia IN (0, 1)),
    tema              TEXT NOT NULL,
    dificultad        INTEGER NOT NULL CHECK (dificultad BETWEEN 1 AND 3),
    origen            TEXT,
    respuesta_usuario TEXT,
    es_correcta       INTEGER CHECK (es_correcta IN (0, 1)),
    UNIQUE (id_test, orden),
    CHECK ((respuesta_usuario IS NULL) = (es_correcta IS NULL))
);

CREATE TABLE IF NOT EXISTS opciones_pregunta (
    id_opcion   INTEGER PRIMARY KEY AUTOINCREMENT,
    id_pregunta INTEGER NOT NULL REFERENCES preguntas_test(id_pregunta) ON DELETE CASCADE,
    texto       TEXT NOT NULL,
    UNIQUE (id_pregunta, texto)
);

CREATE TABLE IF NOT EXISTS envios_codigo (
    id_envio    INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario  INTEGER NOT NULL REFERENCES usuarios(id_usuario),
    codigo_html TEXT NOT NULL,
    fecha       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS errores_detectados (
    id_error       INTEGER PRIMARY KEY AUTOINCREMENT,
    id_envio       INTEGER NOT NULL REFERENCES envios_codigo(id_envio) ON DELETE CASCADE,
    tipo           TEXT NOT NULL CHECK (tipo IN ({_TIPOS_SQL})),
    linea          INTEGER NOT NULL CHECK (linea >= 1),
    explicacion_ia TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS recomendaciones (
    id_recomendacion INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario       INTEGER NOT NULL REFERENCES usuarios(id_usuario),
    fecha            TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS recomendacion_modulos (
    id_modulo        INTEGER NOT NULL REFERENCES modulos(id_modulo) ON DELETE CASCADE,
    id_recomendacion INTEGER NOT NULL REFERENCES recomendaciones(id_recomendacion) ON DELETE CASCADE,
    PRIMARY KEY (id_modulo, id_recomendacion)
);

CREATE TABLE IF NOT EXISTS recomendacion_errores (
    tipo_error       TEXT NOT NULL CHECK (tipo_error IN ({_TIPOS_SQL})),
    id_recomendacion INTEGER NOT NULL REFERENCES recomendaciones(id_recomendacion) ON DELETE CASCADE,
    PRIMARY KEY (tipo_error, id_recomendacion)
);

CREATE INDEX IF NOT EXISTS ix_tests_usuario      ON tests_diagnosticos(id_usuario);
CREATE INDEX IF NOT EXISTS ix_preguntas_test     ON preguntas_test(id_test);
CREATE INDEX IF NOT EXISTS ix_envios_usuario     ON envios_codigo(id_usuario);
CREATE INDEX IF NOT EXISTS ix_errores_envio      ON errores_detectados(id_envio);
CREATE INDEX IF NOT EXISTS ix_recomendaciones_u  ON recomendaciones(id_usuario);
"""


def _migrar_rol_admin(conexion):
    """Bases creadas antes de la Entrega 3 solo permitían 'estudiante' y 'profesor'.
    SQLite no deja modificar un CHECK, así que se reconstruye la tabla conservando todos los datos."""
    fila = conexion.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'usuarios'").fetchone()
    if fila is None or "'admin'" in fila["sql"]:
        return
    conexion.commit()
    conexion.execute("PRAGMA foreign_keys = OFF")
    conexion.executescript(f"""
        BEGIN;
        CREATE TABLE usuarios_nueva {COLUMNAS_USUARIOS};
        INSERT INTO usuarios_nueva (id_usuario, nombre, email, password_hash, rol, fecha_registro)
            SELECT id_usuario, nombre, email, password_hash, rol, fecha_registro FROM usuarios;
        DROP TABLE usuarios;
        ALTER TABLE usuarios_nueva RENAME TO usuarios;
        COMMIT;
    """)
    conexion.execute("PRAGMA foreign_keys = ON")


def _migrar_tipos_error(conexion):
    """Bases creadas antes solo aceptaban 3 tipos de error. Se reconstruyen las dos tablas que los guardan."""
    fila = conexion.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'errores_detectados'").fetchone()
    if fila is None or "'sin_html'" in fila["sql"]:
        return
    conexion.commit()
    conexion.execute("PRAGMA foreign_keys = OFF")
    conexion.executescript(f"""
        BEGIN;
        CREATE TABLE errores_nueva (
            id_error       INTEGER PRIMARY KEY AUTOINCREMENT,
            id_envio       INTEGER NOT NULL REFERENCES envios_codigo(id_envio) ON DELETE CASCADE,
            tipo           TEXT NOT NULL CHECK (tipo IN ({_TIPOS_SQL})),
            linea          INTEGER NOT NULL CHECK (linea >= 1),
            explicacion_ia TEXT NOT NULL
        );
        INSERT INTO errores_nueva SELECT id_error, id_envio, tipo, linea, explicacion_ia FROM errores_detectados;
        DROP TABLE errores_detectados;
        ALTER TABLE errores_nueva RENAME TO errores_detectados;
        CREATE TABLE rec_errores_nueva (
            tipo_error       TEXT NOT NULL CHECK (tipo_error IN ({_TIPOS_SQL})),
            id_recomendacion INTEGER NOT NULL REFERENCES recomendaciones(id_recomendacion) ON DELETE CASCADE,
            PRIMARY KEY (tipo_error, id_recomendacion)
        );
        INSERT INTO rec_errores_nueva SELECT tipo_error, id_recomendacion FROM recomendacion_errores;
        DROP TABLE recomendacion_errores;
        ALTER TABLE rec_errores_nueva RENAME TO recomendacion_errores;
        COMMIT;
    """)
    conexion.execute("PRAGMA foreign_keys = ON")


def conectar(ruta):
    if ruta != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
    conexion = sqlite3.connect(ruta)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")  # SQLite las trae apagadas por defecto
    conexion.execute("PRAGMA journal_mode = WAL")
    return conexion


def get_sqlite():
    """Una conexión por petición, guardada en `g` y cerrada al terminar."""
    if "sqlite" not in g:
        g.sqlite = conectar(current_app.config["SQLITE_PATH"])
    return g.sqlite


@contextmanager
def transaccion():
    """Agrupa varias escrituras en una sola transacción (todo o nada).

    Se puede anidar: solo la más externa confirma (commit) o deshace (rollback).
    Los modelos la usan al escribir y los servicios la usan para juntar varias escrituras.
    """
    conexion = get_sqlite()
    nivel = g.get("_transacciones", 0)
    g._transacciones = nivel + 1
    try:
        if nivel == 0:
            with conexion:
                yield conexion
        else:
            yield conexion
    finally:
        g._transacciones = nivel


def comprobar():
    """Devuelve 'ok' o 'error: ...' (para /api/salud)."""
    try:
        get_sqlite().execute("SELECT 1").fetchone()
        return "ok"
    except Exception as error:
        return f"error: {error}"


def _cerrar(_error=None):
    conexion = g.pop("sqlite", None)
    if conexion is not None:
        conexion.close()


def _sembrar_curso(conexion):
    cursor = conexion.execute(
        "INSERT INTO cursos (nombre, descripcion, nivel, estado) VALUES (?, ?, ?, ?)",
        (CURSO_HTML["nombre"], CURSO_HTML["descripcion"], CURSO_HTML["nivel"], CURSO_HTML["estado"]),
    )
    for modulo in MODULOS_HTML:
        conexion.execute(
            "INSERT INTO modulos (id_curso, titulo, contenido, orden) VALUES (?, ?, ?, ?)",
            (cursor.lastrowid, modulo["titulo"], modulo["contenido"], modulo["orden"]),
        )


def _sembrar_proximos(conexion):
    for curso in CURSOS_PROXIMOS:
        if not conexion.execute("SELECT 1 FROM cursos WHERE nombre = ?", (curso["nombre"],)).fetchone():
            conexion.execute(
                "INSERT INTO cursos (nombre, descripcion, nivel, estado) VALUES (?, ?, ?, ?)",
                (curso["nombre"], curso["descripcion"], curso["nivel"], curso["estado"]),
            )


def _actualizar_contenido(conexion):
    """Versión 2: completa el curso inicial sin tocar lo que el profesor haya cambiado.

    Agrega los módulos que faltan y reemplaza un módulo solo si su título y texto siguen siendo los originales.
    """
    curso = conexion.execute("SELECT id_curso FROM cursos WHERE nombre = ?", (CURSO_HTML["nombre"],)).fetchone()
    if curso is None:   # el profesor lo borró: no reaparece
        return
    originales = {m["orden"]: m for m in MODULOS_V1}
    for modulo in MODULOS_HTML:
        actual = conexion.execute(
            "SELECT id_modulo, titulo, contenido FROM modulos WHERE id_curso = ? AND orden = ?",
            (curso["id_curso"], modulo["orden"])).fetchone()
        if actual is None:
            conexion.execute(
                "INSERT INTO modulos (id_curso, titulo, contenido, orden) VALUES (?, ?, ?, ?)",
                (curso["id_curso"], modulo["titulo"], modulo["contenido"], modulo["orden"]))
        elif modulo["orden"] in originales and actual["contenido"] == originales[modulo["orden"]]["contenido"] \
                and actual["titulo"] == originales[modulo["orden"]]["titulo"]:
            conexion.execute("UPDATE modulos SET titulo = ?, contenido = ? WHERE id_modulo = ?",
                             (modulo["titulo"], modulo["contenido"], actual["id_modulo"]))


def _sembrar_cursos_extra(conexion):
    """Versión 3: crea los cursos adicionales con sus módulos. Si el curso ya existe y está vacío
    (los «Próximamente» de la versión 2), lo completa y lo activa; si ya tiene módulos, no lo toca."""
    for item in CURSOS_EXTRA:
        datos = item["curso"]
        curso = conexion.execute("SELECT id_curso FROM cursos WHERE nombre = ?", (datos["nombre"],)).fetchone()
        if curso is None:
            id_curso = conexion.execute(
                "INSERT INTO cursos (nombre, descripcion, nivel, estado) VALUES (?, ?, ?, ?)",
                (datos["nombre"], datos["descripcion"], datos["nivel"], datos["estado"])).lastrowid
        else:
            id_curso = curso["id_curso"]
            if conexion.execute("SELECT 1 FROM modulos WHERE id_curso = ?", (id_curso,)).fetchone():
                continue
            conexion.execute("UPDATE cursos SET descripcion = ?, nivel = ?, estado = ? WHERE id_curso = ?",
                             (datos["descripcion"], datos["nivel"], datos["estado"], id_curso))
        for modulo in item["modulos"]:
            conexion.execute("INSERT INTO modulos (id_curso, titulo, contenido, orden) VALUES (?, ?, ?, ?)",
                             (id_curso, modulo["titulo"], modulo["contenido"], modulo["orden"]))


def _sembrar_usuarios_demo(conexion):
    for nombre, email, rol in (
        ("Estudiante Demo", "estudiante@edudebug.com", "estudiante"),
        ("Profesor Demo", "profesor@edudebug.com", "profesor"),
        ("Administrador Demo", "admin@edudebug.com", "admin"),
    ):
        existe = conexion.execute("SELECT 1 FROM usuarios WHERE email = ?", (email,)).fetchone()
        if not existe:
            conexion.execute(
                "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES (?, ?, ?, ?)",
                (nombre, email, generate_password_hash("123456"), rol),
            )


def _sembrar_admin(conexion, email, password):
    if email and password and not conexion.execute("SELECT 1 FROM usuarios WHERE email = ?", (email,)).fetchone():
        conexion.execute(
            "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES (?, ?, ?, 'admin')",
            ("Administrador", email, generate_password_hash(password)),
        )


def init_app(app):
    app.teardown_appcontext(_cerrar)
    with app.app_context():
        conexion = get_sqlite()

        columnas = {fila["name"] for fila in conexion.execute("PRAGMA table_info(usuarios)")}
        if columnas and "id_usuario" not in columnas:
            raise RuntimeError(
                "La base SQLite en '%s' es de una versión anterior de EDUDEBUG. "
                "Borra ese archivo (y sus .db-wal / .db-shm) o cambia SQLITE_PATH, y vuelve a iniciar."
                % app.config["SQLITE_PATH"]
            )

        conexion.executescript(ESQUEMA)
        _migrar_rol_admin(conexion)
        _migrar_tipos_error(conexion)
        conexion.executescript(ESQUEMA)  # recrea índices que la migración pudiera haber eliminado
        conexion.execute("BEGIN IMMEDIATE")
        version = conexion.execute("PRAGMA user_version").fetchone()[0]
        if version == 0:
            _sembrar_curso(conexion)  # solo al crear la base: si el profesor borra el curso, no reaparece
        elif version == 1:
            _actualizar_contenido(conexion)   # bases anteriores: se completa el contenido una sola vez
        if version < 3:
            _sembrar_cursos_extra(conexion)
            _sembrar_proximos(conexion)
            conexion.execute("PRAGMA user_version = 3")
        if app.config["SEED_DEMO"]:
            _sembrar_usuarios_demo(conexion)
        _sembrar_admin(conexion, app.config["ADMIN_EMAIL"], app.config["ADMIN_PASSWORD"])
        conexion.commit()
