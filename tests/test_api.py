"""Pruebas de la API: autenticación, test adaptativo, depurador, recomendaciones, cursos y panel."""
import sqlite3

import pytest

from data.banco_preguntas import PREGUNTAS
from models.sqlite_db import conectar
from tests.conftest import iniciar_sesion, registrar

BANCO = {p["texto"]: p for p in PREGUNTAS}


# ------------------------------------------------------------------ utilidades del test adaptativo

def iniciar(cliente, cabeceras):
    respuesta = cliente.post("/api/diagnostico/iniciar", headers=cabeceras)
    assert respuesta.status_code == 200, respuesta.get_json()
    return respuesta.get_json()


def contestar(cliente, cabeceras, estado, acertar):
    """Contesta la pregunta actual: la correcta (acertar=True) o una incorrecta."""
    pregunta = estado["pregunta"]
    correcta = BANCO[pregunta["texto"]]["correcta"]
    opcion = next(o for o in pregunta["opciones"] if (o["texto"] == correcta) == acertar)
    respuesta = cliente.post("/api/diagnostico/responder", headers=cabeceras, json={
        "idTest": estado["idTest"], "idPregunta": pregunta["idPregunta"], "idOpcion": opcion["idOpcion"]})
    assert respuesta.status_code == 200, respuesta.get_json()
    return respuesta.get_json()


def hacer_test(cliente, cabeceras, patron):
    """Hace un test completo con el patrón de aciertos dado (lista de 5 booleanos). Devuelve (preguntas, resultado)."""
    estado, vistas = iniciar(cliente, cabeceras), []
    for acertar in patron:
        vistas.append(estado["pregunta"])
        estado = contestar(cliente, cabeceras, estado, acertar)
    assert estado["finalizado"] is True
    return vistas, estado


def dificultades(app, id_test):
    conexion = conectar(app.config["SQLITE_PATH"])
    return [f["dificultad"] for f in conexion.execute(
        "SELECT dificultad FROM preguntas_test WHERE id_test = ? ORDER BY orden", (id_test,))]


# ------------------------------------------------------------------ salud, registro y sesión

def test_salud_sin_mongo_configurado(cliente):
    respuesta = cliente.get("/api/salud")
    assert respuesta.status_code == 200
    assert respuesta.get_json() == {"sqlite": "ok", "mongodb": "no configurado"}


def test_salud_con_la_conexion_a_mongo_lista(tmp_path):
    from app import create_app
    app = create_app({"TESTING": True, "SQLITE_PATH": str(tmp_path / "m.db"), "MONGO_URI": "mongomock://"})
    assert app.test_client().get("/api/salud").get_json() == {"sqlite": "ok", "mongodb": "ok"}


def test_registro_y_login(cliente):
    datos = {"nombre": "Ana", "email": "Ana@Correo.com", "password": "secreto1", "rol": "estudiante"}
    registro = cliente.post("/api/usuarios/registro", json=datos)
    assert registro.status_code == 201
    cuerpo = registro.get_json()
    assert cuerpo["usuario"]["email"] == "ana@correo.com"
    assert cuerpo["siguiente"] == "diagnostico"
    assert "password" not in str(cuerpo)

    login = cliente.post("/api/auth/login", json={"email": "ana@correo.com", "password": "secreto1"})
    assert login.status_code == 200 and login.get_json()["token"]


def test_registro_valida_campos(cliente):
    base = {"nombre": "Ana", "email": "ana@correo.com", "password": "secreto1", "rol": "estudiante"}
    registro = lambda **cambios: cliente.post("/api/usuarios/registro", json={**base, **cambios}).status_code
    assert registro(password="123") == 400
    assert registro(email="no-es-correo") == 400
    # el registro público solo crea estudiantes: profesor y admin se piden a un administrador
    assert registro(rol="admin") == 403
    assert registro(rol="profesor") == 403
    assert registro(nombre="  ") == 400
    assert registro() == 201
    assert registro() == 409  # correo repetido
    assert cliente.post("/api/usuarios/registro", data="no es json").status_code == 400


def test_login_incorrecto(cliente):
    assert cliente.post("/api/auth/login", json={"email": "estudiante@edudebug.com", "password": "mala"}).status_code == 401
    assert cliente.post("/api/auth/login", json={"email": "nadie@correo.com", "password": "123456"}).status_code == 401


def test_navegacion_inicial_por_rol(cliente, estudiante, profesor):
    assert cliente.get("/api/auth/yo", headers=profesor).get_json()["siguiente"] == "panel"
    assert cliente.get("/api/auth/yo", headers=estudiante).get_json()["siguiente"] == "diagnostico"


def test_endpoints_protegidos(cliente, estudiante, profesor):
    assert cliente.post("/api/diagnostico/iniciar").status_code == 401
    assert cliente.post("/api/diagnostico/iniciar", headers={"Authorization": "Bearer falso"}).status_code == 401
    assert cliente.post("/api/diagnostico/iniciar", headers=profesor).status_code == 403
    assert cliente.post("/api/depurador/analizar", headers=profesor, json={"codigoHtml": "<p>"}).status_code == 403
    assert cliente.get("/api/profesor/progreso/1", headers=estudiante).status_code == 403


def test_la_pagina_se_sirve_desde_flask(cliente):
    assert cliente.get("/").status_code == 200
    assert cliente.get("/estilos.css").status_code == 200
    assert cliente.get("/script.js").status_code == 200
    assert cliente.get("/api/no-existe").status_code == 404


# ------------------------------------------------------------------ modelo de datos

def test_las_tablas_del_diagrama_existen(app):
    conexion = conectar(app.config["SQLITE_PATH"])
    tablas = {f["name"] for f in conexion.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    esperadas = {"usuarios", "cursos", "modulos", "tests_diagnosticos", "preguntas_test", "envios_codigo",
                 "errores_detectados", "recomendaciones", "recomendacion_modulos", "recomendacion_errores",
                 "opciones_pregunta"}
    assert esperadas <= tablas


def test_sqlite_tiene_claves_foraneas_y_restricciones(app):
    conexion = conectar(app.config["SQLITE_PATH"])
    assert conexion.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    for sql in (
        "INSERT INTO envios_codigo (id_usuario, codigo_html) VALUES (999, 'x')",          # FK
        "INSERT INTO errores_detectados (id_envio, tipo, linea, explicacion_ia) VALUES (1, 'otro', 1, 'x')",  # CHECK tipo
        "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES ('a', 'estudiante@edudebug.com', 'x', 'estudiante')",  # UNIQUE
        "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES ('a', 'b@c.com', 'x', 'superusuario')",  # CHECK rol
    ):
        with pytest.raises(sqlite3.IntegrityError):
            conexion.execute(sql)


def test_base_de_una_version_anterior_da_un_error_claro(tmp_path):
    ruta = tmp_path / "vieja.db"
    antigua = sqlite3.connect(ruta)
    antigua.execute("CREATE TABLE usuarios (id INTEGER PRIMARY KEY, correo TEXT)")
    antigua.commit()
    antigua.close()
    from app import create_app
    with pytest.raises(RuntimeError, match="versión anterior"):
        create_app({"SQLITE_PATH": str(ruta)})


# ------------------------------------------------------------------ test diagnóstico adaptativo

def test_iniciar_entrega_una_pregunta_sin_la_respuesta(cliente, estudiante):
    estado = iniciar(cliente, estudiante)
    assert estado["finalizado"] is False
    assert (estado["numero"], estado["total"]) == (1, 5)
    pregunta = estado["pregunta"]
    assert len(pregunta["opciones"]) == 3
    assert "respuesta" not in pregunta and "correcta" not in pregunta


def test_la_dificultad_se_adapta_a_las_respuestas(app, cliente, estudiante):
    _, resultado = hacer_test(cliente, estudiante, [True] * 5)
    assert dificultades(app, resultado["idTest"]) == [2, 3, 3, 3, 3]
    _, resultado = hacer_test(cliente, estudiante, [False] * 5)
    assert dificultades(app, resultado["idTest"]) == [2, 1, 1, 1, 1]
    _, resultado = hacer_test(cliente, estudiante, [True, False, True, False, True])
    assert dificultades(app, resultado["idTest"]) == [2, 3, 2, 3, 2]


@pytest.mark.parametrize("aciertos,nivel,siguiente", [
    (0, "bajo", "teoria"), (1, "bajo", "teoria"), (2, "medio", "catalogo"),
    (3, "medio", "catalogo"), (4, "alto", "catalogo"), (5, "alto", "catalogo")])
def test_regla_de_niveles(cliente, estudiante, aciertos, nivel, siguiente):
    _, resultado = hacer_test(cliente, estudiante, [True] * aciertos + [False] * (5 - aciertos))
    assert resultado["aciertos"] == aciertos and resultado["total"] == 5
    assert resultado["nivel"] == nivel and resultado["siguiente"] == siguiente
    assert len(resultado["detalle"]) == 5
    assert sum(d["acerto"] for d in resultado["detalle"]) == aciertos


def test_no_repite_preguntas_y_reparte_los_temas(cliente, estudiante):
    for patron in ([True] * 5, [False] * 5):
        vistas, _ = hacer_test(cliente, estudiante, patron)
        assert len({p["texto"] for p in vistas}) == 5
        assert len({p["tema"] for p in vistas}) == 5


def test_las_preguntas_rotan_entre_tests(cliente, estudiante):
    primero, _ = hacer_test(cliente, estudiante, [True] * 5)
    segundo, _ = hacer_test(cliente, estudiante, [True] * 5)
    dificiles = lambda vistas: {p["texto"] for p in vistas if BANCO[p["texto"]]["dificultad"] == 3}
    assert dificiles(primero) and dificiles(segundo)
    assert not dificiles(primero) & dificiles(segundo)  # el 2.º test usa preguntas que no había visto


def test_las_opciones_se_mezclan(cliente, estudiante):
    posiciones = set()
    for _ in range(4):
        vistas, _ = hacer_test(cliente, estudiante, [True] * 5)
        for p in vistas:
            correcta = BANCO[p["texto"]]["correcta"]
            posiciones.add(next(i for i, o in enumerate(p["opciones"]) if o["texto"] == correcta))
    assert len(posiciones) > 1


def test_iniciar_retoma_el_test_abierto(cliente, estudiante):
    primero = iniciar(cliente, estudiante)
    assert iniciar(cliente, estudiante) == primero
    siguiente = contestar(cliente, estudiante, primero, True)
    assert iniciar(cliente, estudiante) == siguiente and siguiente["numero"] == 2


def test_responder_valida_los_datos(cliente, estudiante):
    estado = iniciar(cliente, estudiante)
    pregunta = estado["pregunta"]
    enviar = lambda cuerpo: cliente.post("/api/diagnostico/responder", headers=estudiante, json=cuerpo).status_code
    valido = {"idTest": estado["idTest"], "idPregunta": pregunta["idPregunta"],
              "idOpcion": pregunta["opciones"][0]["idOpcion"]}
    assert enviar({**valido, "idOpcion": 99999}) == 400                 # opción de otra pregunta
    assert enviar({**valido, "idOpcion": "1"}) == 400                   # no es entero
    assert enviar({**valido, "idPregunta": 99999}) == 400
    assert enviar({**valido, "idTest": 99999}) == 404
    assert enviar({"idTest": estado["idTest"]}) == 400


def test_no_se_puede_responder_el_test_de_otro(cliente, estudiante):
    estado = iniciar(cliente, estudiante)
    otro, _ = registrar(cliente, "Otro", "otro@correo.com")
    respuesta = cliente.post("/api/diagnostico/responder", headers=otro, json={
        "idTest": estado["idTest"], "idPregunta": estado["pregunta"]["idPregunta"],
        "idOpcion": estado["pregunta"]["opciones"][0]["idOpcion"]})
    assert respuesta.status_code == 404


def test_doble_clic_no_duplica_nada(app, cliente, estudiante):
    estado = iniciar(cliente, estudiante)
    pregunta = estado["pregunta"]
    cuerpo = {"idTest": estado["idTest"], "idPregunta": pregunta["idPregunta"],
              "idOpcion": pregunta["opciones"][0]["idOpcion"]}
    primera = cliente.post("/api/diagnostico/responder", headers=estudiante, json=cuerpo).get_json()
    segunda = cliente.post("/api/diagnostico/responder", headers=estudiante, json=cuerpo).get_json()
    assert primera == segunda and primera["numero"] == 2
    conexion = conectar(app.config["SQLITE_PATH"])
    assert conexion.execute("SELECT COUNT(*) FROM preguntas_test").fetchone()[0] == 2


def test_reenviar_la_ultima_respuesta_devuelve_el_mismo_resultado(cliente, estudiante):
    estado = iniciar(cliente, estudiante)
    ultimo = None
    while not estado["finalizado"]:
        ultimo = {"idTest": estado["idTest"], "idPregunta": estado["pregunta"]["idPregunta"],
                  "idOpcion": estado["pregunta"]["opciones"][0]["idOpcion"]}
        estado = cliente.post("/api/diagnostico/responder", headers=estudiante, json=ultimo).get_json()
    repetido = cliente.post("/api/diagnostico/responder", headers=estudiante, json=ultimo).get_json()
    assert repetido == estado


def test_el_perfil_refleja_el_diagnostico(cliente, estudiante):
    assert cliente.get("/api/auth/yo", headers=estudiante).get_json()["progreso"]["diagnostico"] is None
    hacer_test(cliente, estudiante, [True, True, True, False, False])
    yo = cliente.get("/api/auth/yo", headers=estudiante).get_json()
    assert yo["siguiente"] == "catalogo"
    assert yo["progreso"]["diagnostico"] == {"idTest": 1, "aciertos": 3, "total": 5, "nivel": "medio"}


# ------------------------------------------------------------------ depurador

def analizar(cliente, cabeceras, codigo):
    respuesta = cliente.post("/api/depurador/analizar", headers=cabeceras, json={"codigoHtml": codigo})
    assert respuesta.status_code == 200, respuesta.get_json()
    return respuesta.get_json()


def tipos(respuesta):
    return [(e["tipo"], e["linea"]) for e in respuesta["erroresDetectados"]]


def test_codigo_correcto_no_tiene_errores(cliente, estudiante):
    codigo = '<!DOCTYPE html>\n<html>\n<head><title>Hola</title></head>\n<body>\n<img src="a.jpg" alt="x">\n<br>\n<p>Texto</p>\n</body>\n</html>'
    respuesta = analizar(cliente, estudiante, codigo)
    assert respuesta["erroresDetectados"] == []
    assert respuesta["progreso"]["porcentajeCurso"] == 20
    assert respuesta["usuarioId"] == 1 and respuesta["nivelDetectado"] == "sin_evaluar"


def test_detecta_etiqueta_sin_cerrar_con_su_linea(cliente, estudiante):
    respuesta = analizar(cliente, estudiante, "<div>\n<h2>Fin de la pagina\n</div>")
    assert tipos(respuesta) == [("etiqueta_sin_cerrar", 2)]
    assert "h2" in respuesta["erroresDetectados"][0]["explicacionIA"]


def test_detecta_cierre_sin_apertura(cliente, estudiante):
    respuesta = analizar(cliente, estudiante, "<p>Hola</p>\n</div>")
    assert tipos(respuesta) == [("etiqueta_sin_cerrar", 2)]


def test_detecta_mayusculas(cliente, estudiante):
    respuesta = analizar(cliente, estudiante, "<p>bien</p>\n<DIV>Contenido</DIV>")
    assert tipos(respuesta) == [("etiqueta_en_mayusculas", 2)]


def test_detecta_atributos_sin_comillas_y_comilla_abierta(cliente, estudiante):
    respuesta = analizar(cliente, estudiante, '<img src=imagen.jpg>\n<a href="https://x.com>Ir</a>')
    assert tipos(respuesta) == [("atributo_sin_comillas", 1), ("atributo_sin_comillas", 2)]


def test_las_comillas_simples_y_los_comentarios_no_dan_falsos_errores(cliente, estudiante):
    codigo = "<a href='x.html'>Ir</a>\n<!-- <div> sin cerrar -->\n<script>if (a < b) { x = '<p>'; }</script>"
    assert analizar(cliente, estudiante, codigo)["erroresDetectados"] == []


def test_mal_anidado_se_detecta(cliente, estudiante):
    respuesta = analizar(cliente, estudiante, "<p><strong>Hola</p></strong>")
    assert {t for t, _ in tipos(respuesta)} == {"etiqueta_sin_cerrar"}


def test_la_explicacion_se_adapta_al_nivel(cliente, estudiante):
    codigo = "<div>\nhola"
    sin_nivel = analizar(cliente, estudiante, codigo)["erroresDetectados"][0]["explicacionIA"]
    hacer_test(cliente, estudiante, [False] * 5)  # nivel bajo
    bajo = analizar(cliente, estudiante, codigo)
    assert bajo["nivelDetectado"] == "bajo"
    assert len(bajo["erroresDetectados"][0]["explicacionIA"]) > len(sin_nivel)  # más detallada para principiantes
    hacer_test(cliente, estudiante, [True] * 5)  # nivel alto
    alto = analizar(cliente, estudiante, codigo)
    assert alto["nivelDetectado"] == "alto"
    assert len(alto["erroresDetectados"][0]["explicacionIA"]) < len(bajo["erroresDetectados"][0]["explicacionIA"])


def test_el_envio_y_los_errores_se_guardan(app, cliente, estudiante):
    analizar(cliente, estudiante, "<DIV>\n<p>x")
    conexion = conectar(app.config["SQLITE_PATH"])
    assert conexion.execute("SELECT COUNT(*) FROM envios_codigo").fetchone()[0] == 1
    guardados = conexion.execute("SELECT tipo, linea, explicacion_ia FROM errores_detectados").fetchall()
    assert len(guardados) == 3 and all(g["explicacion_ia"] for g in guardados)


def test_el_depurador_valida_la_entrada(cliente, estudiante):
    enviar = lambda cuerpo: cliente.post("/api/depurador/analizar", headers=estudiante, json=cuerpo).status_code
    assert enviar({"codigoHtml": "   "}) == 400
    assert enviar({"codigoHtml": 5}) == 400
    assert enviar({}) == 400
    assert enviar({"codigoHtml": "x" * 20001}) == 400


def test_progreso_del_curso_y_errores_corregidos(cliente, estudiante):
    analizar(cliente, estudiante, "<div>\n<p>x</p>")                 # 1 error
    analizar(cliente, estudiante, "<DIV>\n<p>x")                     # 3 errores (el último fallido)
    r = analizar(cliente, estudiante, "<div><p>x</p></div>")         # correcto: corrige los 3 pendientes
    assert r["progreso"]["porcentajeCurso"] == 20 and r["progreso"]["erroresCorregidos"] == 3
    for _ in range(6):
        r = analizar(cliente, estudiante, "<p>ok</p>")
    assert r["progreso"]["porcentajeCurso"] == 100  # tope


# ------------------------------------------------------------------ recomendaciones

def test_recomendacion_por_errores_recurrentes(cliente, estudiante):
    uno = analizar(cliente, estudiante, "<div>\ntexto")
    assert uno["recomendacion"] is None  # un solo envío no es "recurrente"
    dos = analizar(cliente, estudiante, "<p>\nhola")
    rec = dos["recomendacion"]
    assert rec["basadoEnErrores"] == ["etiqueta_sin_cerrar"]
    assert [m["modulo"] for m in rec["modulosSugeridos"]] == ["Estructura básica de HTML", "Errores comunes y buenas prácticas"]
    assert rec["modulosSugeridos"][0]["curso"] == "HTML Básico"
    # sin cambios en los errores recurrentes no se crea otra recomendación
    assert analizar(cliente, estudiante, "<h1>\nhola")["recomendacion"] is None
    # un tipo nuevo que se vuelve recurrente sí genera una nueva
    analizar(cliente, estudiante, "<img src=a.jpg>")
    nueva = analizar(cliente, estudiante, "<img src=b.jpg>")["recomendacion"]
    assert set(nueva["basadoEnErrores"]) == {"etiqueta_sin_cerrar", "atributo_sin_comillas"}


def test_consultar_recomendaciones_y_permisos(cliente, estudiante, profesor):
    analizar(cliente, estudiante, "<div>")
    analizar(cliente, estudiante, "<div>")
    propia = cliente.get("/api/recomendaciones/1", headers=estudiante).get_json()
    assert propia["usuarioId"] == 1 and propia["basadoEnErrores"] == ["etiqueta_sin_cerrar"]
    assert cliente.get("/api/recomendaciones/1", headers=profesor).status_code == 200
    otro, id_otro = registrar(cliente, "Otro", "otro@correo.com")
    assert cliente.get("/api/recomendaciones/1", headers=otro).status_code == 403
    assert cliente.get(f"/api/recomendaciones/{id_otro}", headers=otro).get_json()["modulosSugeridos"] == []
    assert cliente.get("/api/recomendaciones/999", headers=profesor).status_code == 404


# ------------------------------------------------------------------ cursos y módulos

def test_catalogo_de_cursos(cliente, estudiante):
    cursos = cliente.get("/api/cursos", headers=estudiante).get_json()["cursos"]
    assert len(cursos) == 1
    assert cursos[0]["nombre"] == "HTML Básico" and cursos[0]["totalModulos"] == 5 and cursos[0]["disponible"] is True
    detalle = cliente.get("/api/cursos/1", headers=estudiante).get_json()
    assert [m["orden"] for m in detalle["modulos"]] == [1, 2, 3, 4, 5]
    assert cliente.get("/api/cursos/99", headers=estudiante).status_code == 404
    assert cliente.get("/api/cursos").status_code == 401


def test_crud_de_cursos_solo_para_profesores(cliente, estudiante, profesor):
    nuevo = {"nombre": "CSS Básico", "descripcion": "Estilos para páginas web", "nivel": "Inicial", "estado": "Activo"}
    assert cliente.post("/api/cursos", headers=estudiante, json=nuevo).status_code == 403

    creado = cliente.post("/api/cursos", headers=profesor, json=nuevo)
    assert creado.status_code == 201
    curso = creado.get_json()
    assert curso["totalModulos"] == 0 and curso["disponible"] is False  # sin módulos: "próximamente"

    editado = cliente.put(f"/api/cursos/{curso['id']}", headers=profesor,
                          json={**nuevo, "nombre": "CSS Intermedio", "nivel": "Intermedio"})
    assert editado.get_json()["nombre"] == "CSS Intermedio" and editado.get_json()["nivel"] == "Intermedio"

    for malo in ({**nuevo, "nombre": ""}, {**nuevo, "descripcion": " "}, {**nuevo, "nivel": "Experto"}, {**nuevo, "estado": "X"}):
        assert cliente.post("/api/cursos", headers=profesor, json=malo).status_code == 400
    assert cliente.put("/api/cursos/99", headers=profesor, json=nuevo).status_code == 404

    assert cliente.delete(f"/api/cursos/{curso['id']}", headers=profesor).status_code == 200
    assert cliente.get(f"/api/cursos/{curso['id']}", headers=profesor).status_code == 404


def test_crud_de_modulos_y_borrado_en_cascada(app, cliente, profesor):
    curso = cliente.post("/api/cursos", headers=profesor,
                         json={"nombre": "JS", "descripcion": "Intro a JavaScript"}).get_json()
    url = f"/api/cursos/{curso['id']}/modulos"
    uno = cliente.post(url, headers=profesor, json={"titulo": "Variables", "contenido": "let x = 1"})
    assert uno.status_code == 201 and uno.get_json()["orden"] == 1
    dos = cliente.post(url, headers=profesor, json={"titulo": "Funciones"}).get_json()
    assert dos["orden"] == 2
    assert cliente.post(url, headers=profesor, json={"titulo": "Repetido", "orden": 1}).status_code == 409
    assert cliente.post(url, headers=profesor, json={"titulo": ""}).status_code == 400

    editado = cliente.put(f"/api/modulos/{dos['id']}", headers=profesor, json={"titulo": "Funciones II", "orden": 5})
    assert editado.get_json()["titulo"] == "Funciones II" and editado.get_json()["orden"] == 5
    assert cliente.put(f"/api/modulos/{dos['id']}", headers=profesor, json={"titulo": "X", "orden": 1}).status_code == 409
    assert cliente.get(f"/api/cursos/{curso['id']}", headers=profesor).get_json()["disponible"] is True

    assert cliente.delete(f"/api/modulos/{uno.get_json()['id']}", headers=profesor).status_code == 200
    assert cliente.delete("/api/modulos/9999", headers=profesor).status_code == 404

    cliente.delete(f"/api/cursos/{curso['id']}", headers=profesor)  # borra el curso y sus módulos
    conexion = conectar(app.config["SQLITE_PATH"])
    assert conexion.execute("SELECT COUNT(*) FROM modulos WHERE id_curso = ?", (curso["id"],)).fetchone()[0] == 0


def test_borrar_un_modulo_recomendado_no_rompe(cliente, estudiante, profesor):
    analizar(cliente, estudiante, "<div>")
    analizar(cliente, estudiante, "<div>")
    ids = [m["idModulo"] for m in cliente.get("/api/recomendaciones/1", headers=profesor).get_json()["modulosSugeridos"]]
    assert ids and cliente.delete(f"/api/modulos/{ids[0]}", headers=profesor).status_code == 200
    assert len(cliente.get("/api/recomendaciones/1", headers=profesor).get_json()["modulosSugeridos"]) == len(ids) - 1


# ------------------------------------------------------------------ panel del profesor

def test_panel_del_profesor_con_datos_reales(cliente, profesor):
    vacio = cliente.get("/api/profesor/progreso/1", headers=profesor).get_json()
    assert vacio["estudiantesActivos"] == 0 and vacio["promedioProgreso"] == 0 and vacio["topErrores"] == []

    ana, _ = registrar(cliente, "Ana", "ana@correo.com")
    luis, _ = registrar(cliente, "Luis", "luis@correo.com")
    registrar(cliente, "Inactivo", "inactivo@correo.com")  # sin actividad: no cuenta

    hacer_test(cliente, ana, [True] * 5)
    analizar(cliente, ana, "<div>\n<DIV>")           # 3 errores: 1 sin cerrar... (ver abajo)
    for _ in range(2):
        analizar(cliente, ana, "<p>ok</p>")           # 40 %
    analizar(cliente, luis, "<img src=a.jpg>")        # 1 error, 0 %

    panel = cliente.get("/api/profesor/progreso/1", headers=profesor).get_json()
    assert panel["curso"] == "HTML Básico" and panel["estudiantesActivos"] == 2
    por_nombre = {e["nombre"]: e for e in panel["estudiantes"]}
    assert por_nombre["Ana"]["progreso"] == 40 and por_nombre["Ana"]["nivel"] == "alto"
    assert por_nombre["Luis"]["progreso"] == 0 and por_nombre["Luis"]["nivel"] == "sin_evaluar"
    assert panel["promedioProgreso"] == 20
    assert panel["erroresDetectados"] == por_nombre["Ana"]["errores"] + por_nombre["Luis"]["errores"]
    assert sum(t["cantidad"] for t in panel["topErrores"]) == panel["erroresDetectados"]
    assert all(0 < t["porcentaje"] <= 100 for t in panel["topErrores"]) and len(panel["topErrores"]) <= 3
    assert cliente.get("/api/profesor/progreso/99", headers=profesor).status_code == 404
