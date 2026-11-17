"""Modelos EnvioCodigo y ErrorDetectado (tablas envios_codigo y errores_detectados)."""
from models.sqlite_db import get_sqlite, transaccion


class EnvioCodigo:
    @classmethod
    def registrar(cls, id_usuario, codigo_html, errores):
        """Guarda el envío y sus errores en una sola transacción. `errores`: [{tipo, linea, explicacion}]."""
        with transaccion() as conexion:
            id_envio = conexion.execute(
                "INSERT INTO envios_codigo (id_usuario, codigo_html) VALUES (?, ?)", (id_usuario, codigo_html)
            ).lastrowid
            for e in errores:
                conexion.execute(
                    "INSERT INTO errores_detectados (id_envio, tipo, linea, explicacion_ia) VALUES (?, ?, ?, ?)",
                    (id_envio, e["tipo"], e["linea"], e["explicacion"]))
        return id_envio

    @classmethod
    def resumen_de(cls, id_usuario):
        """Un elemento por envío, en orden: [{'id': 3, 'errores': 2}, ...]."""
        filas = get_sqlite().execute(
            """
            SELECT v.id_envio, COUNT(e.id_error) AS errores
            FROM envios_codigo v LEFT JOIN errores_detectados e ON e.id_envio = v.id_envio
            WHERE v.id_usuario = ? GROUP BY v.id_envio ORDER BY v.id_envio
            """, (id_usuario,))
        return [{"id": f["id_envio"], "errores": f["errores"]} for f in filas]


class ErrorDetectado:
    @classmethod
    def contar_de(cls, id_usuario):
        return get_sqlite().execute(
            "SELECT COUNT(*) FROM errores_detectados e JOIN envios_codigo v ON v.id_envio = e.id_envio "
            "WHERE v.id_usuario = ?", (id_usuario,)).fetchone()[0]

    @classmethod
    def contar_todos(cls):
        return get_sqlite().execute("SELECT COUNT(*) FROM errores_detectados").fetchone()[0]

    @classmethod
    def mas_frecuentes(cls, limite=3):
        filas = get_sqlite().execute(
            "SELECT tipo, COUNT(*) AS cantidad FROM errores_detectados GROUP BY tipo "
            "ORDER BY cantidad DESC, tipo LIMIT ?", (limite,))
        return [{"tipo": f["tipo"], "cantidad": f["cantidad"]} for f in filas]

    @classmethod
    def recurrentes_de(cls, id_usuario, umbral):
        """Tipos de error que el estudiante repitió en al menos `umbral` envíos distintos."""
        filas = get_sqlite().execute(
            """
            SELECT e.tipo, COUNT(DISTINCT e.id_envio) AS envios
            FROM errores_detectados e JOIN envios_codigo v ON v.id_envio = e.id_envio
            WHERE v.id_usuario = ?
            GROUP BY e.tipo HAVING COUNT(DISTINCT e.id_envio) >= ?
            ORDER BY envios DESC, e.tipo
            """, (id_usuario, umbral))
        return [f["tipo"] for f in filas]
