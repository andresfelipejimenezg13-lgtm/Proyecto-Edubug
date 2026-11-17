"""CONTROLADOR de la VISTA: entrega la interfaz (la «V» del MVC).

El código de la vista está en frontend/ (proyecto Vue 3 + Vite: src/views/*.vue, src/components/*.vue,
src/router, src/services, src/store). Se compila con «npm run build» y el resultado queda en
frontend/dist/, que es lo que entrega Flask. Desde que el navegador la descarga, todo dato lo pide
a la API (/api/...) con fetch.

    GET /   ->  frontend/dist/index.html          (abrir http://127.0.0.1:5000/)
"""
import os

from flask import Blueprint, current_app, send_from_directory

bp = Blueprint("vista", __name__)

AVISO = ("<h2>La vista todavía no está compilada</h2>"
         "<p>Entra a la carpeta <code>frontend</code> y ejecuta <code>npm install</code> y luego "
         "<code>npm run build</code>. La API sí funciona: <a href='/api/docs'>/api/docs</a></p>")


@bp.get("/")
def pagina_principal():
    """Entrega la página principal compilada; los scripts y estilos salen de frontend/dist/assets/."""
    if not os.path.exists(os.path.join(current_app.static_folder, "index.html")):
        return AVISO, 503
    return send_from_directory(current_app.static_folder, "index.html")
