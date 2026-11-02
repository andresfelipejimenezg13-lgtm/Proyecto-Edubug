"""Pruebas de la capa NoSQL (MongoDB simulado con mongomock) y del endpoint SQL + NoSQL."""
from tests.conftest import iniciar_sesion, registrar

CODIGO_MALO = "<DIV class=caja>\n<p>Hola\n</DIV>"


def _estudiante(c):
    return iniciar_sesion(c, "estudiante@edudebug.com")


def _profesor(c):
    return iniciar_sesion(c, "profesor@edudebug.com")


def _tipos(c, h, **params):
    r = c.get("/api/actividad", headers=h, query_string={"limite": 100, **params})
    assert r.status_code == 200
    return [a["tipo"] for a in r.get_json()["actividades"]]


# ------------------------------------------------------------ salud y sin Mongo

def test_salud_con_mongo_ok(cliente_mongo):
    r = cliente_mongo.get("/api/salud")
    assert r.status_code == 200 and r.get_json()["mongodb"] == "ok"


def test_sin_mongo_los_endpoints_nosql_responden_503_y_el_resto_funciona(cliente, estudiante):
    assert cliente.get("/api/actividad", headers=estudiante).status_code == 503
    assert cliente.get("/api/modulos/1/comentarios", headers=estudiante).status_code == 503
    # el resto de la app sigue funcionando
    assert cliente.post("/api/diagnostico/iniciar", headers=estudiante).status_code == 200
    # y el perfil combinado entrega la parte SQL avisando que Mongo no está
    r = cliente.get("/api/usuarios/1/perfil-completo", headers=estudiante)
    assert r.status_code == 200
    assert r.get_json()["actividad"]["disponible"] is False
    assert r.get_json()["usuario"]["email"] == "estudiante@edudebug.com"


# ------------------------------------------------------- registro automático

def test_la_actividad_se_registra_sola(cliente_mongo):
    c = cliente_mongo
    h = _estudiante(c)                                               # login
    c.post("/api/diagnostico/iniciar", headers=h)
    c.post("/api/depurador/analizar", headers=h, json={"codigoHtml": CODIGO_MALO})
    c.get("/api/cursos/1", headers=h)
    tipos = _tipos(c, h)
    for esperado in ("login", "diagnostico_iniciado", "codigo_analizado", "curso_consultado"):
        assert esperado in tipos


def test_actividad_codigo_analizado_guarda_detalle_variable(cliente_mongo):
    c = cliente_mongo
    h = _estudiante(c)
    c.post("/api/depurador/analizar", headers=h, json={"codigoHtml": CODIGO_MALO})
    evento = c.get("/api/actividad", headers=h, query_string={"tipo": "codigo_analizado"}).get_json()["actividades"][0]
    assert evento["idUsuario"] == 1
    assert evento["detalle"]["totalErrores"] == 4
    assert "etiqueta_sin_cerrar" in evento["detalle"]["tipos"]


def test_registro_de_cuenta_nueva_queda_en_la_bitacora(cliente_mongo):
    h, _ = registrar(cliente_mongo, "Camila", "camila@correo.com")
    assert "registro" in _tipos(cliente_mongo, h)


def test_diagnostico_completo_registra_respuestas_y_cierre(cliente_mongo):
    c = cliente_mongo
    h = _estudiante(c)
    estado = c.post("/api/diagnostico/iniciar", headers=h).get_json()
    for _ in range(5):
        estado = c.post("/api/diagnostico/responder", headers=h, json={
            "idTest": estado["idTest"], "idPregunta": estado["pregunta"]["idPregunta"],
            "idOpcion": estado["pregunta"]["opciones"][0]["idOpcion"]}).get_json()
    assert estado["finalizado"] is True
    tipos = _tipos(c, h)
    assert tipos.count("diagnostico_respuesta") == 5
    assert "diagnostico_finalizado" in tipos


# --------------------------------------------------------------- CRUD actividad

def test_crud_actividad_manual(cliente_mongo):
    c = cliente_mongo
    h = _estudiante(c)
    creado = c.post("/api/actividad", headers=h, json={"tipo": "tema_visto", "detalle": {"tema": 3}})
    assert creado.status_code == 201
    id_ev = creado.get_json()["id"]
    assert creado.get_json()["detalle"] == {"tema": 3}
    assert "tema_visto" in _tipos(c, h)
    assert c.delete(f"/api/actividad/{id_ev}", headers=h).status_code == 200
    assert "tema_visto" not in _tipos(c, h)
    assert c.delete(f"/api/actividad/{id_ev}", headers=h).status_code == 404


def test_actividad_validaciones(cliente_mongo):
    c = cliente_mongo
    h = _estudiante(c)
    assert c.post("/api/actividad", headers=h, json={"tipo": "login"}).status_code == 400   # solo el servidor
    assert c.post("/api/actividad", headers=h, json={"tipo": "tema_visto", "detalle": "x"}).status_code == 400
    assert c.post("/api/actividad", headers=h, json={"tipo": "tema_visto", "detalle": {"a": "x" * 3000}}).status_code == 400
    assert c.get("/api/actividad", headers=h, query_string={"limite": 0}).status_code == 400
    assert c.get("/api/actividad", headers=h, query_string={"limite": "abc"}).status_code == 400
    assert c.get("/api/actividad", headers=h, query_string={"tipo": "inventado"}).status_code == 400
    assert c.delete("/api/actividad/no-es-un-id", headers=h).status_code == 400
    assert c.get("/api/actividad").status_code == 401


def test_no_se_puede_borrar_actividad_ajena(cliente_mongo):
    c = cliente_mongo
    h = _estudiante(c)
    id_ev = c.post("/api/actividad", headers=h, json={"tipo": "tema_visto"}).get_json()["id"]
    otro, _ = registrar(c, "Otro", "otro@correo.com")
    assert c.delete(f"/api/actividad/{id_ev}", headers=otro).status_code == 404
    assert "tema_visto" in _tipos(c, h)


def test_limite_de_actividad(cliente_mongo):
    c = cliente_mongo
    h = _estudiante(c)
    for i in range(12):
        c.post("/api/actividad", headers=h, json={"tipo": "tema_visto", "detalle": {"tema": i}})
    r = c.get("/api/actividad", headers=h, query_string={"limite": 5}).get_json()
    assert r["total"] == 5
    assert r["actividades"][0]["detalle"]["tema"] == 11   # la más reciente primero


# -------------------------------------------------------------- CRUD comentarios

def test_crud_comentarios(cliente_mongo):
    c = cliente_mongo
    h = _estudiante(c)
    r = c.post("/api/modulos/2/comentarios", headers=h, json={
        "texto": "No entiendo por qué el DOCTYPE va primero", "etiquetas": ["Duda", "estructura"],
        "fragmentoCodigo": "<!DOCTYPE html>"})
    assert r.status_code == 201
    com = r.get_json()
    assert com["etiquetas"] == ["duda", "estructura"]
    assert com["fragmentoCodigo"] == "<!DOCTYPE html>" and com["autor"] != "Usuario eliminado"
    id_com = com["id"]

    lista = c.get("/api/modulos/2/comentarios", headers=h).get_json()
    assert lista["total"] == 1 and lista["comentarios"][0]["id"] == id_com
    assert c.get("/api/modulos/3/comentarios", headers=h).get_json()["total"] == 0

    assert c.get(f"/api/comentarios/{id_com}", headers=h).status_code == 200

    r = c.put(f"/api/comentarios/{id_com}", headers=h, json={"texto": "Ya lo entendí", "etiquetas": []})
    assert r.status_code == 200
    editado = r.get_json()
    assert editado["texto"] == "Ya lo entendí" and editado["editadoEn"] is not None
    assert "fragmentoCodigo" not in editado        # al no enviarlo, el campo desaparece (esquema flexible)

    assert c.delete(f"/api/comentarios/{id_com}", headers=h).status_code == 200
    assert c.get(f"/api/comentarios/{id_com}", headers=h).status_code == 404


def test_comentario_validaciones(cliente_mongo):
    c = cliente_mongo
    h = _estudiante(c)
    assert c.post("/api/modulos/999/comentarios", headers=h, json={"texto": "x"}).status_code == 404
    assert c.post("/api/modulos/1/comentarios", headers=h, json={"texto": "  "}).status_code == 400
    assert c.post("/api/modulos/1/comentarios", headers=h, json={"texto": "x" * 1001}).status_code == 400
    assert c.post("/api/modulos/1/comentarios", headers=h, json={"texto": "x", "etiquetas": "a"}).status_code == 400
    assert c.post("/api/modulos/1/comentarios", headers=h, json={"texto": "x", "etiquetas": list("abcdef")}).status_code == 400
    assert c.get("/api/comentarios/xyz", headers=h).status_code == 400


def test_solo_el_autor_edita_y_el_profesor_modera(cliente_mongo):
    c = cliente_mongo
    h = _estudiante(c)
    id_com = c.post("/api/modulos/1/comentarios", headers=h, json={"texto": "hola"}).get_json()["id"]
    otro, _ = registrar(c, "Otro", "otro@correo.com")
    assert c.put(f"/api/comentarios/{id_com}", headers=otro, json={"texto": "robado"}).status_code == 403
    assert c.delete(f"/api/comentarios/{id_com}", headers=otro).status_code == 403
    assert c.delete(f"/api/comentarios/{id_com}", headers=_profesor(c)).status_code == 200


def test_reacciones_crean_campos_dinamicos(cliente_mongo):
    c = cliente_mongo
    h = _estudiante(c)
    id_com = c.post("/api/modulos/1/comentarios", headers=h, json={"texto": "hola"}).get_json()["id"]
    assert c.get(f"/api/comentarios/{id_com}", headers=h).get_json()["reacciones"] == {}
    c.post(f"/api/comentarios/{id_com}/reacciones", headers=h, json={"tipo": "util"})
    c.post(f"/api/comentarios/{id_com}/reacciones", headers=_profesor(c), json={"tipo": "util"})
    r = c.post(f"/api/comentarios/{id_com}/reacciones", headers=h, json={"tipo": "gracias"})
    assert r.get_json()["reacciones"] == {"util": 2, "gracias": 1}
    assert c.post(f"/api/comentarios/{id_com}/reacciones", headers=h, json={"tipo": "odio"}).status_code == 400


def test_comentario_resuelve_el_autor_desde_sql(cliente_mongo):
    c = cliente_mongo
    h, id_u = registrar(c, "Camila Rojas", "camila@correo.com")
    c.post("/api/modulos/1/comentarios", headers=h, json={"texto": "hola"})
    lista = c.get("/api/modulos/1/comentarios", headers=h).get_json()
    assert lista["comentarios"][0]["autor"] == "Camila Rojas"
    assert lista["comentarios"][0]["idUsuario"] == id_u


# ----------------------------------------------------- endpoint combinado SQL+NoSQL

def test_perfil_completo_une_sql_y_mongo(cliente_mongo):
    c = cliente_mongo
    h = _estudiante(c)
    for _ in range(2):
        c.post("/api/depurador/analizar", headers=h, json={"codigoHtml": CODIGO_MALO})
    c.post("/api/modulos/1/comentarios", headers=h, json={"texto": "hola"})

    r = c.get("/api/usuarios/1/perfil-completo", headers=h)
    assert r.status_code == 200
    d = r.get_json()
    # SQL
    assert d["usuario"]["email"] == "estudiante@edudebug.com" and "fechaRegistro" in d["usuario"]
    assert d["progreso"]["totalEnvios"] == 2
    assert d["recomendacion"]["modulosSugeridos"]                 # se generó por errores repetidos
    # Mongo
    act = d["actividad"]
    assert act["disponible"] is True
    assert act["totalPorTipo"]["codigo_analizado"] == 2
    assert act["comentariosEscritos"] == 1
    assert len(act["ultimas"]) <= 10 and act["ultimas"][0]["tipo"] == "comentario_creado"


def test_perfil_completo_limita_a_10_actividades(cliente_mongo):
    c = cliente_mongo
    h = _estudiante(c)
    for i in range(15):
        c.post("/api/actividad", headers=h, json={"tipo": "tema_visto", "detalle": {"tema": i}})
    d = c.get("/api/usuarios/1/perfil-completo", headers=h).get_json()
    assert len(d["actividad"]["ultimas"]) == 10
    assert d["actividad"]["totalPorTipo"]["tema_visto"] == 15


def test_perfil_completo_permisos(cliente_mongo):
    c = cliente_mongo
    otro, id_otro = registrar(c, "Otro", "otro@correo.com")
    assert c.get("/api/usuarios/1/perfil-completo", headers=otro).status_code == 403
    assert c.get(f"/api/usuarios/{id_otro}/perfil-completo", headers=otro).status_code == 200
    assert c.get("/api/usuarios/1/perfil-completo", headers=_profesor(c)).status_code == 200   # el profesor puede
    assert c.get("/api/usuarios/999/perfil-completo", headers=_profesor(c)).status_code == 404
    assert c.get("/api/usuarios/1/perfil-completo").status_code == 401


def test_perfil_de_profesor_no_tiene_progreso(cliente_mongo):
    c = cliente_mongo
    d = c.get("/api/usuarios/2/perfil-completo", headers=_profesor(c)).get_json()
    assert d["progreso"] is None and d["recomendacion"] is None
    assert d["actividad"]["disponible"] is True


def test_si_mongo_falla_la_peticion_principal_no_se_rompe(app_mongo, monkeypatch):
    from models import documentos
    c = app_mongo.test_client()
    h = _estudiante(c)

    def roto(*a, **k):
        raise RuntimeError("Mongo caído")
    monkeypatch.setattr(documentos, "crear_actividad", roto)
    # la bitácora falla en silencio y el flujo principal continúa
    assert c.post("/api/depurador/analizar", headers=h, json={"codigoHtml": CODIGO_MALO}).status_code == 200
    assert c.post("/api/diagnostico/iniciar", headers=h).status_code == 200
