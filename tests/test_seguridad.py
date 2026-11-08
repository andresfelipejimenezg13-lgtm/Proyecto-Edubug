"""Pruebas de la Entrega 3: hashing, JWT, límite de intentos, política de contraseñas y RBAC."""
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from tests.conftest import iniciar_sesion, registrar

CLAVE = "clave-de-pruebas"  # SECRET_KEY de la fixture `app`


def _token_manual(sub="1", rol="estudiante", clave=CLAVE, minutos=30, emisor="edudebug", algoritmo="HS256"):
    ahora = datetime.now(timezone.utc)
    carga = {"sub": sub, "rol": rol, "iat": ahora, "exp": ahora + timedelta(minutes=minutos), "iss": emisor}
    return jwt.encode(carga, clave, algorithm=algoritmo)


def _cab(token):
    return {"Authorization": "Bearer " + token}


# ----------------------------------------------------------------- hashing

def test_la_contrasena_se_guarda_con_hash(app, cliente):
    registrar(cliente, "Ana", "ana@correo.com", "secreto123")
    registrar(cliente, "Beto", "beto@correo.com", "secreto123")
    import sqlite3
    conexion = sqlite3.connect(app.config["SQLITE_PATH"])
    hashes = [f[0] for f in conexion.execute("SELECT password_hash FROM usuarios WHERE email LIKE '%@correo.com'")]
    assert len(hashes) == 2
    assert all("secreto123" not in h for h in hashes)           # nunca en texto plano
    assert all(h.startswith(("scrypt:", "pbkdf2:")) for h in hashes)
    assert hashes[0] != hashes[1]                                  # misma clave, distinto hash (sal aleatoria)


def test_la_api_nunca_devuelve_el_hash(cliente):
    r = cliente.post("/api/auth/login", json={"email": "estudiante@edudebug.com", "password": "123456"})
    assert "password" not in str(r.get_json()).lower()


# ------------------------------------------------------------ política de claves

@pytest.mark.parametrize("clave", ["abc12", "soloLetrasLargas", "1234567890", ""])
def test_politica_de_contrasenas(cliente, clave):
    r = cliente.post("/api/usuarios/registro",
                     json={"nombre": "Ana", "email": "ana@correo.com", "password": clave, "rol": "estudiante"})
    assert r.status_code == 400


def test_contrasena_valida_se_acepta(cliente):
    r = cliente.post("/api/usuarios/registro",
                     json={"nombre": "Ana", "email": "ana@correo.com", "password": "Segura2026", "rol": "estudiante"})
    assert r.status_code == 201


# ------------------------------------------------------------------------ JWT

def test_el_token_es_un_jwt_firmado_con_sus_claims(cliente):
    r = cliente.post("/api/auth/login", json={"email": "profesor@edudebug.com", "password": "123456"}).get_json()
    assert r["tipoToken"] == "Bearer" and r["expiraEnSegundos"] == 8 * 3600
    assert jwt.get_unverified_header(r["token"])["alg"] == "HS256"
    carga = jwt.decode(r["token"], CLAVE, algorithms=["HS256"], issuer="edudebug")
    assert carga["rol"] == "profesor" and carga["sub"] == str(r["usuario"]["id"])
    assert carga["exp"] > carga["iat"]


def test_token_valido_da_acceso(cliente):
    assert cliente.get("/api/auth/yo", headers=_cab(_token_manual("1"))).status_code == 200


@pytest.mark.parametrize("nombre,token,esperado", [
    ("vencido", _token_manual(minutos=-5), "expiró"),
    ("firma de otra clave", _token_manual(clave="otra-clave-distinta-0123456789abcdef"), "no válida"),
    ("emisor distinto", _token_manual(emisor="otro-sistema"), "no válida"),
    ("basura", "esto.no.es.un.jwt", "no válida"),
])
def test_tokens_invalidos_son_rechazados(cliente, nombre, token, esperado):
    r = cliente.get("/api/auth/yo", headers=_cab(token))
    assert r.status_code == 401, nombre
    assert esperado in r.get_json()["error"].lower()


def test_token_sin_firma_alg_none_es_rechazado(cliente):
    sin_firma = jwt.encode({"sub": "2", "rol": "admin", "iss": "edudebug",
                            "iat": datetime.now(timezone.utc),
                            "exp": datetime.now(timezone.utc) + timedelta(hours=1)}, key=None, algorithm="none")
    assert cliente.get("/api/auth/yo", headers=_cab(sin_firma)).status_code == 401


def test_el_rol_del_token_no_da_privilegios(cliente):
    """Aunque alguien firmara un token que diga 'admin', el rol real se lee de la base de datos."""
    falso = _token_manual(sub="1", rol="admin")   # el usuario 1 es estudiante
    assert cliente.get("/api/admin/usuarios", headers=_cab(falso)).status_code == 403


def test_token_de_cuenta_inexistente(cliente):
    assert cliente.get("/api/auth/yo", headers=_cab(_token_manual(sub="9999"))).status_code == 401


def test_sin_cabecera_o_esquema_incorrecto(cliente):
    assert cliente.get("/api/cursos").status_code == 401
    assert cliente.get("/api/cursos", headers={"Authorization": "Basic abc"}).status_code == 401


# ------------------------------------------------------------ límite de intentos

def test_bloqueo_tras_demasiados_intentos_fallidos(cliente):
    mala = {"email": "estudiante@edudebug.com", "password": "incorrecta1"}
    for _ in range(5):
        assert cliente.post("/api/auth/login", json=mala).status_code == 401
    assert cliente.post("/api/auth/login", json=mala).status_code == 429
    # incluso con la clave correcta sigue bloqueado mientras dure la ventana
    buena = {"email": "estudiante@edudebug.com", "password": "123456"}
    assert cliente.post("/api/auth/login", json=buena).status_code == 429
    # otra cuenta no se ve afectada
    assert cliente.post("/api/auth/login", json={"email": "profesor@edudebug.com", "password": "123456"}).status_code == 200


def test_un_login_correcto_reinicia_el_contador(cliente):
    mala = {"email": "estudiante@edudebug.com", "password": "incorrecta1"}
    for _ in range(4):
        cliente.post("/api/auth/login", json=mala)
    assert cliente.post("/api/auth/login", json={"email": "estudiante@edudebug.com", "password": "123456"}).status_code == 200
    for _ in range(4):
        assert cliente.post("/api/auth/login", json=mala).status_code == 401   # empieza de cero


def test_el_mensaje_de_login_no_revela_si_la_cuenta_existe(cliente):
    a = cliente.post("/api/auth/login", json={"email": "no-existe@x.com", "password": "abc12345"})
    b = cliente.post("/api/auth/login", json={"email": "estudiante@edudebug.com", "password": "abc12345"})
    assert a.status_code == b.status_code == 401 and a.get_json() == b.get_json()


# ------------------------------------------------------------------------ RBAC

def _sesiones(cliente):
    return {rol: iniciar_sesion(cliente, f"{rol}@edudebug.com") for rol in ("estudiante", "profesor", "admin")}


# (método, ruta, cuerpo, estudiante, profesor, admin) -> códigos esperados
MATRIZ = [
    ("GET",  "/api/cursos",                      None,                          200, 200, 200),
    ("POST", "/api/diagnostico/iniciar",         None,                          200, 403, 403),   # CU-02
    ("POST", "/api/depurador/analizar",          {"codigoHtml": "<p>hola</p>"}, 200, 403, 403),   # CU-03
    ("GET",  "/api/recomendaciones/1",           None,                          200, 200, 200),
    ("GET",  "/api/profesor/progreso/1",         None,                          403, 200, 200),   # CU-05
    ("POST", "/api/cursos",                      {},                            403, 400, 400),   # CU-06 (400 = pasó el permiso)
    ("GET",  "/api/admin/usuarios",              None,                          403, 403, 200),
    ("POST", "/api/admin/usuarios",              {},                            403, 403, 400),
    ("PUT",  "/api/admin/usuarios/1/rol",        {"rol": "estudiante"},         403, 403, 200),
]


@pytest.mark.parametrize("metodo,ruta,cuerpo,est,prof,adm", MATRIZ)
def test_matriz_de_permisos_por_rol(cliente, metodo, ruta, cuerpo, est, prof, adm):
    sesiones = _sesiones(cliente)
    for rol, esperado in (("estudiante", est), ("profesor", prof), ("admin", adm)):
        r = cliente.open(ruta, method=metodo, json=cuerpo, headers=sesiones[rol])
        assert r.status_code == esperado, f"{metodo} {ruta} como {rol}: {r.status_code} {r.get_json()}"
    # sin sesión, todo es 401
    assert cliente.open(ruta, method=metodo, json=cuerpo).status_code == 401


def test_un_estudiante_no_ve_datos_de_otro(cliente):
    h, id_otro = registrar(cliente, "Otro", "otro@correo.com", "secreto123")
    assert cliente.get("/api/usuarios/1/perfil-completo", headers=h).status_code == 403
    assert cliente.get("/api/recomendaciones/1", headers=h).status_code == 403
    assert cliente.get(f"/api/usuarios/{id_otro}/perfil-completo", headers=h).status_code == 200


# --------------------------------------------------- administración de usuarios

def test_registro_publico_no_puede_crear_profesor_ni_admin(cliente):
    for rol in ("profesor", "admin"):
        r = cliente.post("/api/usuarios/registro",
                         json={"nombre": "X", "email": f"{rol}@x.com", "password": "secreto123", "rol": rol})
        assert r.status_code == 403


def test_admin_crea_profesor_y_este_puede_iniciar_sesion(cliente):
    admin = iniciar_sesion(cliente, "admin@edudebug.com")
    r = cliente.post("/api/admin/usuarios", headers=admin, json={
        "nombre": "Leandro", "email": "leandro@correo.com", "password": "Docente2026", "rol": "profesor"})
    assert r.status_code == 201 and r.get_json()["rol"] == "profesor"
    login = cliente.post("/api/auth/login", json={"email": "leandro@correo.com", "password": "Docente2026"})
    assert login.status_code == 200 and login.get_json()["siguiente"] == "panel"
    assert cliente.post("/api/admin/usuarios", headers=admin, json={
        "nombre": "Dup", "email": "leandro@correo.com", "password": "Docente2026", "rol": "profesor"}).status_code == 409


def test_admin_valida_los_datos_al_crear(cliente):
    admin = iniciar_sesion(cliente, "admin@edudebug.com")
    base = {"nombre": "Ana", "email": "ana@correo.com", "password": "Segura2026", "rol": "profesor"}
    assert cliente.post("/api/admin/usuarios", headers=admin, json={**base, "rol": "dios"}).status_code == 400
    assert cliente.post("/api/admin/usuarios", headers=admin, json={**base, "password": "123"}).status_code == 400
    assert cliente.post("/api/admin/usuarios", headers=admin, json={**base, "email": "mal"}).status_code == 400


def test_cambio_de_rol_se_aplica_de_inmediato_con_el_mismo_token(cliente):
    admin = iniciar_sesion(cliente, "admin@edudebug.com")
    h, id_u = registrar(cliente, "Ana", "ana@correo.com", "secreto123")
    assert cliente.get("/api/profesor/progreso/1", headers=h).status_code == 403
    assert cliente.put(f"/api/admin/usuarios/{id_u}/rol", headers=admin, json={"rol": "profesor"}).status_code == 200
    assert cliente.get("/api/profesor/progreso/1", headers=h).status_code == 200   # mismo token, nuevo permiso
    cliente.put(f"/api/admin/usuarios/{id_u}/rol", headers=admin, json={"rol": "estudiante"})
    assert cliente.get("/api/profesor/progreso/1", headers=h).status_code == 403


def test_reglas_de_seguridad_del_cambio_de_rol(cliente):
    admin = iniciar_sesion(cliente, "admin@edudebug.com")
    # un admin no puede cambiarse su propio rol: así el sistema nunca se queda sin administradores
    assert cliente.put("/api/admin/usuarios/3/rol", headers=admin, json={"rol": "profesor"}).status_code == 409
    assert cliente.put("/api/admin/usuarios/999/rol", headers=admin, json={"rol": "profesor"}).status_code == 404
    assert cliente.put("/api/admin/usuarios/1/rol", headers=admin, json={"rol": "dios"}).status_code == 400


def test_listar_usuarios_con_filtro(cliente):
    admin = iniciar_sesion(cliente, "admin@edudebug.com")
    todos = cliente.get("/api/admin/usuarios", headers=admin).get_json()
    assert todos["total"] == 3 and all("password" not in str(u) for u in todos["usuarios"])
    solo = cliente.get("/api/admin/usuarios?rol=profesor", headers=admin).get_json()
    assert [u["email"] for u in solo["usuarios"]] == ["profesor@edudebug.com"]
    assert cliente.get("/api/admin/usuarios?rol=x", headers=admin).status_code == 400


# ------------------------------------------------------ admin inicial por variables

def test_admin_inicial_desde_variables_de_entorno(tmp_path):
    from app import create_app
    app = create_app({"TESTING": True, "SQLITE_PATH": str(tmp_path / "x.db"), "MONGO_URI": "", "SECRET_KEY": CLAVE,
                      "SEED_DEMO": False, "ADMIN_EMAIL": "jefe@edudebug.com", "ADMIN_PASSWORD": "Inicial2026"})
    c = app.test_client()
    r = c.post("/api/auth/login", json={"email": "jefe@edudebug.com", "password": "Inicial2026"})
    assert r.status_code == 200 and r.get_json()["usuario"]["rol"] == "admin"


# --------------------------------------------------- migración de una base antigua

def test_una_base_anterior_sin_rol_admin_se_migra_sin_perder_datos(tmp_path):
    import sqlite3
    from app import create_app
    ruta = str(tmp_path / "vieja.db")
    primera = create_app({"TESTING": True, "SQLITE_PATH": ruta, "MONGO_URI": "", "SECRET_KEY": CLAVE, "SEED_DEMO": True})
    # simulamos la tabla de la entrega anterior (CHECK solo con 2 roles)
    con = sqlite3.connect(ruta)
    con.execute("PRAGMA foreign_keys = OFF")
    con.executescript("""
        CREATE TABLE usuarios_vieja (id_usuario INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
            rol TEXT NOT NULL CHECK (rol IN ('estudiante', 'profesor')),
            fecha_registro TEXT NOT NULL DEFAULT (datetime('now')));
        INSERT INTO usuarios_vieja SELECT * FROM usuarios WHERE rol IN ('estudiante', 'profesor');
        DROP TABLE usuarios; ALTER TABLE usuarios_vieja RENAME TO usuarios;
    """)
    con.commit(); con.close()
    segunda = create_app({"TESTING": True, "SQLITE_PATH": ruta, "MONGO_URI": "", "SECRET_KEY": CLAVE, "SEED_DEMO": True})
    c = segunda.test_client()
    assert c.post("/api/auth/login", json={"email": "estudiante@edudebug.com", "password": "123456"}).status_code == 200
    assert c.post("/api/auth/login", json={"email": "admin@edudebug.com", "password": "123456"}).status_code == 200


# -------------------------------------------------------- cabeceras de seguridad

def test_cabeceras_de_seguridad(cliente):
    r = cliente.get("/api/salud")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Cache-Control"] == "no-store"
