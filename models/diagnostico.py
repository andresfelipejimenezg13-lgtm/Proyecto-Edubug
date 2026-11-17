"""Modelos TestDiagnostico y PreguntaTest (tablas tests_diagnosticos, preguntas_test, opciones_pregunta)."""
from models.sqlite_db import get_sqlite, transaccion


class TestDiagnostico:
    __test__ = False  # evita que pytest lo tome por una clase de pruebas

    def __init__(self, fila):
        self.id = fila["id_test"]
        self.usuario_id = fila["id_usuario"]
        self.nivel = fila["nivel_asignado"]
        self.estado = fila["estado"]

    # ---- consultas
    @classmethod
    def por_id(cls, id_test, id_usuario=None):
        consulta, parametros = "SELECT * FROM tests_diagnosticos WHERE id_test = ?", [id_test]
        if id_usuario is not None:
            consulta, parametros = consulta + " AND id_usuario = ?", parametros + [id_usuario]
        fila = get_sqlite().execute(consulta, parametros).fetchone()
        return cls(fila) if fila else None

    @classmethod
    def abierto_de(cls, id_usuario):
        fila = get_sqlite().execute(
            "SELECT * FROM tests_diagnosticos WHERE id_usuario = ? AND estado = 'en_curso' "
            "ORDER BY id_test DESC LIMIT 1", (id_usuario,)).fetchone()
        return cls(fila) if fila else None

    @classmethod
    def ultimo_finalizado_de(cls, id_usuario):
        fila = get_sqlite().execute(
            "SELECT * FROM tests_diagnosticos WHERE id_usuario = ? AND estado = 'finalizado' "
            "ORDER BY id_test DESC LIMIT 1", (id_usuario,)).fetchone()
        return cls(fila) if fila else None

    @classmethod
    def nivel_actual(cls, id_usuario):
        """Nivel del último test finalizado, o None si aún no lo hizo."""
        test = cls.ultimo_finalizado_de(id_usuario)
        return test.nivel if test else None

    @classmethod
    def contar_de(cls, id_usuario):
        return get_sqlite().execute(
            "SELECT COUNT(*) FROM tests_diagnosticos WHERE id_usuario = ?", (id_usuario,)).fetchone()[0]

    # ---- escritura
    @classmethod
    def crear(cls, id_usuario):
        with transaccion() as conexion:
            cursor = conexion.execute("INSERT INTO tests_diagnosticos (id_usuario) VALUES (?)", (id_usuario,))
        return cls.por_id(cursor.lastrowid)

    def finalizar(self, nivel):
        with transaccion() as conexion:
            conexion.execute(
                "UPDATE tests_diagnosticos SET nivel_asignado = ?, estado = 'finalizado' "
                "WHERE id_test = ? AND estado = 'en_curso'", (nivel, self.id))
        self.nivel, self.estado = nivel, "finalizado"

    # ---- preguntas del test
    @property
    def finalizado(self):
        return self.estado == "finalizado"

    def preguntas(self):
        filas = get_sqlite().execute("SELECT * FROM preguntas_test WHERE id_test = ? ORDER BY orden", (self.id,))
        return [PreguntaTest(f) for f in filas]

    def pendiente(self):
        fila = get_sqlite().execute(
            "SELECT * FROM preguntas_test WHERE id_test = ? AND es_correcta IS NULL ORDER BY orden LIMIT 1",
            (self.id,)).fetchone()
        return PreguntaTest(fila) if fila else None

    def respondidas(self):
        return get_sqlite().execute(
            "SELECT COUNT(*) FROM preguntas_test WHERE id_test = ? AND es_correcta IS NOT NULL",
            (self.id,)).fetchone()[0]

    def aciertos(self):
        return get_sqlite().execute(
            "SELECT COALESCE(SUM(es_correcta), 0) FROM preguntas_test WHERE id_test = ?", (self.id,)).fetchone()[0]


class PreguntaTest:
    def __init__(self, fila):
        self.id = fila["id_pregunta"]
        self.test_id = fila["id_test"]
        self.orden = fila["orden"]
        self.texto = fila["texto"]
        self.respuesta = fila["respuesta"]
        self.tema = fila["tema"]
        self.dificultad = fila["dificultad"]
        self.origen = fila["origen"]
        self.respuesta_usuario = fila["respuesta_usuario"]
        self.es_correcta = fila["es_correcta"]

    @property
    def contestada(self):
        return self.es_correcta is not None

    @classmethod
    def de_test(cls, id_pregunta, id_test):
        fila = get_sqlite().execute(
            "SELECT * FROM preguntas_test WHERE id_pregunta = ? AND id_test = ?", (id_pregunta, id_test)).fetchone()
        return cls(fila) if fila else None

    @classmethod
    def usadas_en(cls, id_test):
        """(origen, tema) de las preguntas ya creadas en el test."""
        filas = get_sqlite().execute("SELECT origen, tema FROM preguntas_test WHERE id_test = ?", (id_test,))
        return [(f["origen"], f["tema"]) for f in filas]

    @classmethod
    def origenes_vistos(cls, id_usuario, id_test, limite):
        """Orígenes de las preguntas que el estudiante vio en otros tests (las más recientes primero)."""
        filas = get_sqlite().execute(
            """
            SELECT p.origen FROM preguntas_test p
            JOIN tests_diagnosticos t ON t.id_test = p.id_test
            WHERE t.id_usuario = ? AND p.id_test != ? AND p.origen IS NOT NULL
            ORDER BY p.id_pregunta DESC LIMIT ?
            """, (id_usuario, id_test, limite))
        return [f["origen"] for f in filas]

    @classmethod
    def crear(cls, id_test, orden, nueva, opciones):
        """Guarda la pregunta con sus opciones. `nueva` es el diccionario del generador de preguntas."""
        with transaccion() as conexion:
            cursor = conexion.execute(
                "INSERT INTO preguntas_test (id_test, orden, texto, respuesta, generada_por_ia, tema, dificultad, "
                "origen) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (id_test, orden, nueva["texto"], nueva["respuesta"], nueva["generada_por_ia"],
                 nueva["tema"], nueva["dificultad"], nueva["origen"]))
            for texto in opciones:
                conexion.execute("INSERT INTO opciones_pregunta (id_pregunta, texto) VALUES (?, ?)",
                                 (cursor.lastrowid, texto))
        return cursor.lastrowid

    def opciones(self):
        filas = get_sqlite().execute(
            "SELECT id_opcion, texto FROM opciones_pregunta WHERE id_pregunta = ? ORDER BY id_opcion", (self.id,))
        return [{"idOpcion": f["id_opcion"], "texto": f["texto"]} for f in filas]

    def texto_de_opcion(self, id_opcion):
        fila = get_sqlite().execute(
            "SELECT texto FROM opciones_pregunta WHERE id_opcion = ? AND id_pregunta = ?",
            (id_opcion, self.id)).fetchone()
        return fila["texto"] if fila else None

    def registrar_respuesta(self, texto, es_correcta):
        """Guarda la respuesta solo si la pregunta sigue sin contestar (dos clics simultáneos no se pisan)."""
        with transaccion() as conexion:
            return conexion.execute(
                "UPDATE preguntas_test SET respuesta_usuario = ?, es_correcta = ? "
                "WHERE id_pregunta = ? AND es_correcta IS NULL", (texto, es_correcta, self.id)).rowcount > 0
