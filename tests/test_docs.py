"""La documentación OpenAPI debe cubrir exactamente las rutas reales de la API."""
import re


def _normal(ruta):
    ruta = re.sub(r"<(?:int:)?([^>]+)>", r"{\1}", ruta)
    return ruta


def test_openapi_cubre_todas_las_rutas(app, cliente):
    spec = cliente.get("/api/openapi.json").get_json()
    reales = set()
    for r in app.url_map.iter_rules():
        if r.rule.startswith("/api/") and r.rule not in ("/api/docs", "/api/openapi.json"):
            for m in r.methods - {"HEAD", "OPTIONS"}:
                reales.add((m.lower(), _normal(r.rule)))
    doc = {(m, p) for p, ops in spec["paths"].items() for m in ops}
    # los nombres de parámetro pueden diferir (id_comentario vs <id_comentario>): comparar por forma
    forma = lambda s: {(m, re.sub(r"\{[^}]+\}", "{}", p)) for m, p in s}
    assert forma(reales) == forma(doc), (forma(reales) ^ forma(doc))


def test_docs_publicas_y_swagger(cliente):
    assert cliente.get("/api/docs").status_code == 200
    assert b"swagger-ui" in cliente.get("/api/docs").data
    spec = cliente.get("/api/openapi.json").get_json()
    assert spec["openapi"].startswith("3.")
    assert "bearerAuth" in spec["components"]["securitySchemes"]


def test_rutas_protegidas_marcan_seguridad(cliente):
    spec = cliente.get("/api/openapi.json").get_json()
    for ruta in ("/api/auth/login", "/api/usuarios/registro", "/api/salud"):
        for op in spec["paths"][ruta].values():
            assert "security" not in op
    assert spec["paths"]["/api/admin/usuarios"]["get"]["security"]
