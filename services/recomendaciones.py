"""Recomendador de rutas de estudio.

Cuando un estudiante repite el mismo tipo de error en al menos UMBRAL envíos distintos, se guarda una
recomendación (tablas recomendaciones, recomendacion_errores y recomendacion_modulos) con los módulos
del curso que conviene repasar. Se genera una nueva solo si el conjunto de errores recurrentes cambió.

Los módulos se eligen por su número de orden dentro del primer curso (HTML Básico en el MVP).
"""

UMBRAL = 2

# Qué módulos (por orden) repasar según el tipo de error.
MODULOS_POR_ERROR = {
    "etiqueta_sin_cerrar": [2, 5],
    "atributo_sin_comillas": [3],
    "etiqueta_en_mayusculas": [5],
}


def _errores_recurrentes(conexion, id_usuario):
    filas = conexion.execute(
        """
        SELECT e.tipo, COUNT(DISTINCT e.id_envio) AS envios
        FROM errores_detectados e
        JOIN envios_codigo v ON v.id_envio = e.id_envio
        WHERE v.id_usuario = ?
        GROUP BY e.tipo HAVING COUNT(DISTINCT e.id_envio) >= ?
        ORDER BY envios DESC, e.tipo
        """,
        (id_usuario, UMBRAL),
    ).fetchall()
    return [f["tipo"] for f in filas]


def _ultima_id(conexion, id_usuario):
    fila = conexion.execute(
        "SELECT id_recomendacion FROM recomendaciones WHERE id_usuario = ? "
        "ORDER BY id_recomendacion DESC LIMIT 1",
        (id_usuario,),
    ).fetchone()
    return fila["id_recomendacion"] if fila else None


def generar_si_corresponde(conexion, id_usuario):
    """Crea una recomendación nueva si hace falta y devuelve su id (o None)."""
    recurrentes = _errores_recurrentes(conexion, id_usuario)
    if not recurrentes:
        return None

    ultima = _ultima_id(conexion, id_usuario)
    if ultima is not None:
        previos = {
            f["tipo_error"] for f in conexion.execute(
                "SELECT tipo_error FROM recomendacion_errores WHERE id_recomendacion = ?", (ultima,))
        }
        if previos == set(recurrentes):
            return None

    curso = conexion.execute("SELECT id_curso FROM cursos ORDER BY id_curso LIMIT 1").fetchone()
    if curso is None:
        return None
    ordenes = []
    for tipo in recurrentes:
        for orden in MODULOS_POR_ERROR.get(tipo, []):
            if orden not in ordenes:
                ordenes.append(orden)
    modulos = [
        f["id_modulo"] for f in conexion.execute(
            f"SELECT id_modulo FROM modulos WHERE id_curso = ? AND orden IN ({','.join('?' * len(ordenes))}) "
            "ORDER BY orden",
            (curso["id_curso"], *ordenes),
        )
    ] if ordenes else []
    if not modulos:
        return None

    with conexion:
        id_recomendacion = conexion.execute(
            "INSERT INTO recomendaciones (id_usuario) VALUES (?)", (id_usuario,)
        ).lastrowid
        for tipo in recurrentes:
            conexion.execute(
                "INSERT INTO recomendacion_errores (tipo_error, id_recomendacion) VALUES (?, ?)",
                (tipo, id_recomendacion),
            )
        for id_modulo in modulos:
            conexion.execute(
                "INSERT INTO recomendacion_modulos (id_modulo, id_recomendacion) VALUES (?, ?)",
                (id_modulo, id_recomendacion),
            )
    return id_recomendacion


def obtener(conexion, id_usuario, id_recomendacion=None):
    """Última recomendación del usuario (o la indicada), en el formato del documento."""
    if id_recomendacion is None:
        id_recomendacion = _ultima_id(conexion, id_usuario)
    vacia = {"usuarioId": id_usuario, "idRecomendacion": None, "fecha": None,
             "modulosSugeridos": [], "basadoEnErrores": []}
    if id_recomendacion is None:
        return vacia

    cabecera = conexion.execute(
        "SELECT * FROM recomendaciones WHERE id_recomendacion = ?", (id_recomendacion,)
    ).fetchone()
    modulos = conexion.execute(
        """
        SELECT m.id_modulo, m.titulo, m.orden, c.nombre AS curso
        FROM recomendacion_modulos rm
        JOIN modulos m ON m.id_modulo = rm.id_modulo
        JOIN cursos c ON c.id_curso = m.id_curso
        WHERE rm.id_recomendacion = ? ORDER BY c.id_curso, m.orden
        """,
        (id_recomendacion,),
    ).fetchall()
    errores = conexion.execute(
        "SELECT tipo_error FROM recomendacion_errores WHERE id_recomendacion = ? ORDER BY tipo_error",
        (id_recomendacion,),
    ).fetchall()
    return {
        "usuarioId": id_usuario,
        "idRecomendacion": id_recomendacion,
        "fecha": cabecera["fecha"],
        "modulosSugeridos": [
            {"curso": m["curso"], "modulo": m["titulo"], "idModulo": m["id_modulo"], "orden": m["orden"]}
            for m in modulos
        ],
        "basadoEnErrores": [e["tipo_error"] for e in errores],
    }
