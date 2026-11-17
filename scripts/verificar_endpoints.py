"""Verifica TODOS los endpoints de la API contra su regla de acceso (RBAC) y genera la tabla.

Para cada ruta registrada en Flask comprueba, con una base temporal y tokens reales de cada rol:
  - sin sesión            -> debe responder 401 (si la ruta exige sesión)
  - rol sin permiso       -> debe responder 403
  - rol con permiso       -> NO debe responder 401/403 ni 5xx (se usan ids que no existen y cuerpo vacío,
                             así no se modifica nada: lo normal es 400 o 404)

Uso:
    python -m scripts.verificar_endpoints               imprime la tabla
    python -m scripts.verificar_endpoints --md docs/ENDPOINTS_VERIFICADOS.md
"""
import argparse
import re
import sys
import tempfile
from pathlib import Path

ROLES = ("estudiante", "profesor", "admin")
CUENTAS = {"estudiante": "estudiante@edudebug.com", "profesor": "profesor@edudebug.com", "admin": "admin@edudebug.com"}


# Rutas abiertas a cualquier sesión, pero donde el estudiante solo puede consultar SUS propios datos:
# con el id de otra persona recibe 403 (la regla se aplica dentro del controlador).
SOLO_LO_PROPIO = {"/api/recomendaciones/<int:usuario_id>", "/api/usuarios/<int:id_usuario>/perfil-completo"}


def _ruta_de_prueba(regla):
    """Reemplaza <int:x> por un id que no existe y <texto> por un ObjectId válido pero inexistente."""
    ruta = re.sub(r"<int:[^>]+>", "999999", regla.rule)
    return re.sub(r"<[^>]+>", "0" * 24, ruta)


def _dueno(vista):
    """Nombre del controlador (archivo) y de la función que atiende la ruta."""
    funcion = getattr(vista, "__wrapped__", vista)
    return funcion.__module__.split(".")[-1], funcion.__name__


def verificar(app):
    """Devuelve (filas, errores). Cada fila describe un endpoint con el código obtenido por cada rol."""
    cliente = app.test_client()
    cabeceras = {}
    for rol, correo in CUENTAS.items():
        r = cliente.post("/api/auth/login", json={"email": correo, "password": "123456"})
        cabeceras[rol] = {"Authorization": "Bearer " + r.get_json()["token"]}

    filas, errores = [], []
    for regla in sorted(app.url_map.iter_rules(), key=lambda r: (r.rule, sorted(r.methods))):
        if regla.endpoint == "static":
            continue
        vista = app.view_functions[regla.endpoint]
        controlador, funcion = _dueno(vista)
        exige = getattr(vista, "requiere_sesion", False)
        permitidos = getattr(vista, "roles_permitidos", ()) or ROLES
        ruta = _ruta_de_prueba(regla)
        propio = regla.rule in SOLO_LO_PROPIO
        for metodo in sorted(regla.methods - {"HEAD", "OPTIONS"}):
            envio = {"json": {}} if metodo in ("POST", "PUT", "PATCH") else {}
            fila = {"metodo": metodo, "ruta": regla.rule, "controlador": f"{controlador}.{funcion}",
                    "acceso": ("sesión: " + ", ".join(permitidos)) if exige and len(permitidos) < 3
                    else (("cualquier sesión (estudiante: solo lo suyo)" if propio else "cualquier sesión")
                          if exige else "público")}
            if exige:
                fila["sin_sesion"] = cliente.open(ruta, method=metodo, **envio).status_code
                if fila["sin_sesion"] != 401:
                    errores.append(f"{metodo} {regla.rule}: sin sesión devolvió {fila['sin_sesion']} (esperado 401)")
                for rol in ROLES:
                    codigo = cliente.open(ruta, method=metodo, headers=cabeceras[rol], **envio).status_code
                    fila[rol] = codigo
                    if propio and rol == "estudiante":
                        if codigo != 403:
                            errores.append(f"{metodo} {regla.rule}: el estudiante no debería ver datos ajenos ({codigo})")
                        continue
                    if rol in permitidos and (codigo in (401, 403) or codigo >= 500):
                        errores.append(f"{metodo} {regla.rule}: el rol {rol} debería entrar y devolvió {codigo}")
                    if rol not in permitidos and codigo != 403:
                        errores.append(f"{metodo} {regla.rule}: el rol {rol} debería recibir 403 y devolvió {codigo}")
            else:
                codigo = cliente.open(ruta, method=metodo, **envio).status_code
                fila.update(sin_sesion=codigo, **{rol: codigo for rol in ROLES})
                if codigo >= 500:
                    errores.append(f"{metodo} {regla.rule}: respondió {codigo}")
            filas.append(fila)
    return filas, errores


def crear_app_de_prueba():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app import create_app
    carpeta = tempfile.mkdtemp()
    return create_app({"TESTING": True, "SQLITE_PATH": carpeta + "/verificacion.db", "MONGO_URI": "mongomock://",
                       "SECRET_KEY": "clave-de-verificacion", "SEED_DEMO": True})


def tabla_markdown(filas):
    lineas = ["| Método | Ruta | Controlador (función) | Acceso | Sin sesión | Estudiante | Profesor | Admin |",
              "|---|---|---|---|:-:|:-:|:-:|:-:|"]
    for f in filas:
        lineas.append(f"| {f['metodo']} | `{f['ruta']}` | `{f['controlador']}` | {f['acceso']} | "
                      f"{f['sin_sesion']} | {f['estudiante']} | {f['profesor']} | {f['admin']} |")
    return "\n".join(lineas)


if __name__ == "__main__":
    analizador = argparse.ArgumentParser()
    analizador.add_argument("--md", help="archivo Markdown donde guardar la tabla")
    argumentos = analizador.parse_args()
    filas, errores = verificar(crear_app_de_prueba())
    tabla = tabla_markdown(filas)
    print(tabla)
    print(f"\n{len(filas)} endpoints verificados, {len(errores)} errores.")
    for e in errores:
        print("  ERROR:", e)
    if argumentos.md:
        Path(argumentos.md).write_text(
            "# Endpoints verificados\n\nGenerado con `python -m scripts.verificar_endpoints --md docs/ENDPOINTS_VERIFICADOS.md`.\n\n"
            "Cada celda es el código HTTP obtenido. **401** = falta iniciar sesión, **403** = rol sin permiso, "
            "**400/404** = el rol sí puede entrar (se probó con cuerpo vacío o id inexistente para no modificar datos).\n\n"
            + tabla + f"\n\n**{len(filas)} endpoints verificados, {len(errores)} errores.**\n", encoding="utf8")
    sys.exit(1 if errores else 0)
