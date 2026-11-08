"""Punto de entrada de la API de EDUDEBUG.

Local:   flask --app app run --debug
Render:  gunicorn "app:create_app()"
"""
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from config import Config
from controllers import (actividad, admin, auth, comentarios, cursos, depurador, diagnostico, profesor,
                         recomendaciones, usuarios)
from models import mongo_db, sqlite_db
from services import openapi
from services.errores import ErrorServicio


def create_app(configuracion=None):
    app = Flask(__name__, static_folder="frontend", static_url_path="")
    app.config.from_object(Config)
    if configuracion:
        app.config.update(configuracion)

    origenes = app.config["CORS_ORIGINS"]
    CORS(app, resources={r"/api/*": {"origins": "*" if origenes == "*" else origenes.split(",")}})

    sqlite_db.init_app(app)
    mongo_db.init_app(app)

    for modulo in (auth, usuarios, diagnostico, depurador, recomendaciones, profesor, cursos,
                   actividad, comentarios, admin):
        app.register_blueprint(modulo.bp)

    @app.after_request
    def cabeceras_de_seguridad(respuesta):
        respuesta.headers["X-Content-Type-Options"] = "nosniff"
        respuesta.headers["X-Frame-Options"] = "DENY"
        respuesta.headers["Referrer-Policy"] = "no-referrer"
        if request.path.startswith("/api/"):
            respuesta.headers["Cache-Control"] = "no-store"  # las respuestas de la API no se guardan en caché
        return respuesta

    @app.get("/")
    def pagina_principal():
        """Entrega la página (index.html, estilos.css y script.js de la carpeta frontend/)."""
        return send_from_directory(app.static_folder, "index.html")

    @app.get("/api/openapi.json")
    def especificacion():
        return jsonify(openapi.construir())

    @app.get("/api/docs")
    def documentacion():
        """Swagger UI con la documentación interactiva de la API."""
        return openapi.PAGINA_DOCS

    @app.get("/api/salud")
    def salud():
        """Comprueba que las bases respondan (útil para Render y para Postman)."""
        estado = {"sqlite": "ok", "mongodb": mongo_db.comprobar()}
        try:
            sqlite_db.get_sqlite().execute("SELECT 1").fetchone()
        except Exception as error:
            estado["sqlite"] = f"error: {error}"
        correcto = estado["sqlite"] == "ok" and estado["mongodb"] in ("ok", "no configurado")
        return jsonify(estado), 200 if correcto else 503

    @app.errorhandler(ErrorServicio)
    def error_controlado(error):
        return jsonify({"error": error.mensaje}), error.estado

    @app.errorhandler(HTTPException)
    def error_http(error):
        return jsonify({"error": error.description}), error.code

    @app.errorhandler(Exception)
    def error_inesperado(error):
        app.logger.exception("Error no controlado")
        return jsonify({"error": "Ocurrió un error en el servidor."}), 500

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
