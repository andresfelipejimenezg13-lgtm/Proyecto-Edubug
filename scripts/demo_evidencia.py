"""Ejecuta el flujo SQL + MongoDB completo y lo imprime (sirve como evidencia de ejecución).

Uso (con el entorno virtual activado, desde la carpeta del proyecto):
    python scripts/demo_evidencia.py

- Si en .env tienes MONGO_URI (Atlas), los datos se guardan en tu base real.
- Si no hay MONGO_URI, usa una base Mongo simulada en memoria y lo avisa.
- SQLite se crea en un archivo temporal: no toca tu base normal.
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from config import Config  # noqa: E402


def mostrar(titulo, respuesta, recorte=None):
    print(f"\n=== {titulo}")
    print(f"HTTP {respuesta.status_code}")
    cuerpo = json.dumps(respuesta.get_json(), indent=2, ensure_ascii=False)
    lineas = cuerpo.splitlines()
    if recorte and len(lineas) > recorte:
        lineas = lineas[:recorte] + ["  ..."]
    print("\n".join(lineas))


def main():
    uri = Config.MONGO_URI.strip()
    simulado = not uri
    configuracion = {"SQLITE_PATH": os.path.join(tempfile.mkdtemp(), "demo.db"), "SEED_DEMO": True,
                     "MONGO_URI": uri or "mongomock://"}
    app = create_app(configuracion)
    c = app.test_client()

    print("Base NoSQL:", "SIMULADA en memoria (mongomock)" if simulado else "MongoDB real (MONGO_URI)")
    mostrar("GET /api/salud", c.get("/api/salud"))

    login = c.post("/api/auth/login", json={"email": "estudiante@edudebug.com", "password": "123456"})
    h = {"Authorization": "Bearer " + login.get_json()["token"]}
    mostrar("POST /api/auth/login  (se guarda el evento 'login' en Mongo)", login, 8)

    for i in range(2):
        r = c.post("/api/depurador/analizar", headers=h, json={"codigoHtml": "<DIV class=caja>\n<p>Hola\n</DIV>"})
    mostrar("POST /api/depurador/analizar (2.º envío: guarda 'codigo_analizado' y genera recomendación)", r, 12)

    r = c.post("/api/actividad", headers=h, json={"tipo": "tema_visto", "detalle": {"tema": 3}})
    mostrar("POST /api/actividad  (CREATE actividad)", r)
    id_actividad = r.get_json()["id"]

    r = c.post("/api/modulos/2/comentarios", headers=h, json={
        "texto": "¿Por qué el DOCTYPE va primero?", "etiquetas": ["duda"], "fragmentoCodigo": "<!DOCTYPE html>"})
    mostrar("POST /api/modulos/2/comentarios  (CREATE comentario)", r)
    id_comentario = r.get_json()["id"]

    mostrar("POST /api/comentarios/{id}/reacciones  (UPDATE parcial con $inc)",
            c.post(f"/api/comentarios/{id_comentario}/reacciones", headers=h, json={"tipo": "util"}))
    mostrar("PUT /api/comentarios/{id}  (UPDATE)",
            c.put(f"/api/comentarios/{id_comentario}", headers=h, json={"texto": "Ya lo entendí", "etiquetas": ["resuelto"]}))
    mostrar("GET /api/modulos/2/comentarios  (READ: Mongo + nombre del autor desde SQLite)",
            c.get("/api/modulos/2/comentarios", headers=h))
    mostrar("GET /api/usuarios/1/perfil-completo  (ENDPOINT COMBINADO SQL + NoSQL)",
            c.get("/api/usuarios/1/perfil-completo", headers=h))
    mostrar("DELETE /api/comentarios/{id}  (DELETE)", c.delete(f"/api/comentarios/{id_comentario}", headers=h))
    mostrar("DELETE /api/actividad/{id}  (DELETE)", c.delete(f"/api/actividad/{id_actividad}", headers=h))

    if simulado:
        print("\nNOTA: esta ejecución usó MongoDB simulado. Para evidencia real, define MONGO_URI en .env.")


if __name__ == "__main__":
    main()
