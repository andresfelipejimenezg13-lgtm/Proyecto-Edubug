"""Cada endpoint respeta su regla de acceso (401 sin sesión, 403 rol equivocado, rol correcto sí entra)."""
from app import create_app
from scripts.verificar_endpoints import verificar


def test_todos_los_endpoints_cumplen_su_regla_de_acceso(tmp_path):
    app = create_app({"TESTING": True, "SQLITE_PATH": str(tmp_path / "e.db"), "MONGO_URI": "mongomock://",
                      "SECRET_KEY": "clave-de-pruebas", "SEED_DEMO": True})
    filas, errores = verificar(app)
    assert len(filas) >= 30
    assert errores == []
