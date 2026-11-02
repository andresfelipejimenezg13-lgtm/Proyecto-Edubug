import pytest

from app import create_app


@pytest.fixture()
def app(tmp_path):
    return create_app({
        "TESTING": True,
        "SQLITE_PATH": str(tmp_path / "prueba.db"),
        "MONGO_URI": "",
        "SECRET_KEY": "clave-de-pruebas",
        "SEED_DEMO": True,
    })


@pytest.fixture()
def cliente(app):
    return app.test_client()


def iniciar_sesion(cliente, email, password="123456"):
    respuesta = cliente.post("/api/auth/login", json={"email": email, "password": password})
    assert respuesta.status_code == 200, respuesta.get_json()
    return {"Authorization": "Bearer " + respuesta.get_json()["token"]}


def registrar(cliente, nombre, email, password="secreto1", rol="estudiante"):
    respuesta = cliente.post("/api/usuarios/registro",
                             json={"nombre": nombre, "email": email, "password": password, "rol": rol})
    assert respuesta.status_code == 201, respuesta.get_json()
    return {"Authorization": "Bearer " + respuesta.get_json()["token"]}, respuesta.get_json()["usuario"]["id"]


@pytest.fixture()
def estudiante(cliente):
    return iniciar_sesion(cliente, "estudiante@edudebug.com")


@pytest.fixture()
def profesor(cliente):
    return iniciar_sesion(cliente, "profesor@edudebug.com")


@pytest.fixture()
def app_mongo(tmp_path):
    """App con SQLite + MongoDB simulado en memoria (mongomock)."""
    return create_app({
        "TESTING": True,
        "SQLITE_PATH": str(tmp_path / "prueba_mongo.db"),
        "MONGO_URI": "mongomock://",
        "SECRET_KEY": "clave-de-pruebas",
        "SEED_DEMO": True,
    })


@pytest.fixture()
def cliente_mongo(app_mongo):
    return app_mongo.test_client()
