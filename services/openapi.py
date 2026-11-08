"""Especificación OpenAPI 3 de la API de EDUDEBUG (se muestra en /api/docs con Swagger UI).

Se escribe a mano para poder explicar roles y errores; tests/test_docs.py verifica que
cada ruta real de Flask aparezca aquí, así la documentación no se desactualiza.
"""

ESTU, DOC, ADM, TODOS = "estudiante", "profesor/admin", "admin", "cualquier sesión"


def _obj(**props):
    return {"type": "object", "properties": {k: {"type": v} if isinstance(v, str) else v for k, v in props.items()}}


def _cuerpo(esquema, ejemplo):
    return {"required": True, "content": {"application/json": {"schema": esquema, "example": ejemplo}}}


def _op(resumen, quien, tags, cuerpo=None, params=None, codigo="200", extra=None):
    """Una operación. `quien` es el acceso requerido y se escribe en la descripción."""
    publico = quien == "público"
    op = {
        "tags": [tags],
        "summary": resumen,
        "description": f"**Acceso:** {quien}." + ("" if publico else " Requiere `Authorization: Bearer <token>`."),
        "parameters": params or [],
        "responses": {codigo: {"description": "Correcto"}},
    }
    if cuerpo:
        op["requestBody"] = cuerpo
    if not publico:
        op["security"] = [{"bearerAuth": []}]
        op["responses"]["401"] = {"$ref": "#/components/responses/NoAutenticado"}
        if quien not in (TODOS,):
            op["responses"]["403"] = {"$ref": "#/components/responses/Prohibido"}
    op["responses"]["400"] = {"$ref": "#/components/responses/Invalido"}
    op["responses"].update(extra or {})
    return op


def _ruta(nombre, desc="Identificador"):
    return {"name": nombre, "in": "path", "required": True, "description": desc, "schema": {"type": "integer"}}


def _texto_id(nombre, desc):
    return {"name": nombre, "in": "path", "required": True, "description": desc, "schema": {"type": "string"}}


NF = {"404": {"$ref": "#/components/responses/NoEncontrado"}}


def construir():
    curso = _cuerpo(_obj(nombre="string", descripcion="string", nivel={"type": "string", "enum": ["Inicial", "Intermedio", "Avanzado"]},
                         estado={"type": "string", "enum": ["Activo", "Inactivo"]}),
                    {"nombre": "HTML desde cero", "descripcion": "Etiquetas básicas", "nivel": "Inicial", "estado": "Activo"})
    modulo = _cuerpo(_obj(titulo="string", contenido="string", orden="integer"),
                     {"titulo": "Listas", "contenido": "<ul>...</ul>", "orden": 4})
    comentario = _cuerpo(_obj(texto="string", etiquetas={"type": "array", "items": {"type": "string"}}, fragmentoCodigo="string"),
                         {"texto": "¿Por qué no cierra la etiqueta?", "etiquetas": ["html", "duda"], "fragmentoCodigo": "<p>Hola"})
    rutas = {
        "/api/salud": {"get": _op("Estado de SQLite y MongoDB", "público", "Sistema")},
        "/api/usuarios/registro": {"post": _op(
            "Registro público (solo estudiantes)", "público", "Autenticación",
            _cuerpo(_obj(nombre="string", email="string", password="string"),
                    {"nombre": "Ana Ruiz", "email": "ana@correo.com", "password": "Clave1234"}),
            codigo="201", extra={"403": {"description": "Se intentó registrar otro rol distinto de estudiante"},
                                 "409": {"description": "Correo ya registrado"}})},
        "/api/auth/login": {"post": _op(
            "Inicio de sesión: devuelve el token JWT", "público", "Autenticación",
            _cuerpo(_obj(email="string", password="string"), {"email": "estudiante@edudebug.com", "password": "123456"}),
            extra={"401": {"description": "Correo o contraseña incorrectos (mensaje genérico)"},
                   "429": {"description": "Demasiados intentos fallidos (5 en 15 min por IP + correo)"}})},
        "/api/auth/yo": {"get": _op("Usuario de la sesión actual", TODOS, "Autenticación")},
        "/api/admin/usuarios": {
            "get": _op("Listar usuarios (filtro ?rol=)", ADM, "Administración",
                       params=[{"name": "rol", "in": "query", "schema": {"type": "string", "enum": ["estudiante", "profesor", "admin"]}}]),
            "post": _op("Crear cuenta de cualquier rol", ADM, "Administración",
                        _cuerpo(_obj(nombre="string", email="string", password="string", rol="string"),
                                {"nombre": "Leandro Pájaro", "email": "leandro@correo.com", "password": "Clave1234", "rol": "profesor"}),
                        codigo="201", extra={"409": {"description": "Correo ya registrado"}})},
        "/api/admin/usuarios/{id_usuario}/rol": {"put": _op(
            "Cambiar el rol de un usuario", ADM, "Administración",
            _cuerpo(_obj(rol="string"), {"rol": "profesor"}), params=[_ruta("id_usuario")],
            extra={**NF, "409": {"description": "No puedes cambiar tu propio rol"}})},
        "/api/diagnostico/iniciar": {"post": _op("CU-02 Iniciar (o retomar) el test diagnóstico", ESTU, "Diagnóstico")},
        "/api/diagnostico/responder": {"post": _op(
            "CU-02 Responder una pregunta del test", ESTU, "Diagnóstico",
            _cuerpo(_obj(idTest="integer", idPregunta="integer", idOpcion="integer"),
                    {"idTest": 1, "idPregunta": 3, "idOpcion": 9}), extra=NF)},
        "/api/depurador/analizar": {"post": _op(
            "CU-03 Analizar código HTML y explicar los errores", ESTU, "Depurador",
            _cuerpo(_obj(codigoHtml="string"), {"codigoHtml": "<p>Hola <b>mundo</p>"}))},
        "/api/recomendaciones/{usuario_id}": {"get": _op(
            "CU-04 Recomendaciones de estudio (un estudiante solo ve las suyas)", TODOS, "Progreso",
            params=[_ruta("usuario_id")], extra=NF)},
        "/api/profesor/progreso/{curso_id}": {"get": _op(
            "CU-05 Panel de progreso del grupo", DOC, "Progreso", params=[_ruta("curso_id")], extra=NF)},
        "/api/usuarios/{id_usuario}/perfil-completo": {"get": _op(
            "Perfil combinado SQLite + MongoDB (propio, o cualquiera si eres docente)", TODOS, "Progreso",
            params=[_ruta("id_usuario")], extra=NF)},
        "/api/cursos": {
            "get": _op("CU-06 Listar cursos", TODOS, "Cursos"),
            "post": _op("CU-06 Crear curso", DOC, "Cursos", curso, codigo="201")},
        "/api/cursos/{id_curso}": {
            "get": _op("CU-06 Detalle del curso con sus módulos", TODOS, "Cursos", params=[_ruta("id_curso")], extra=NF),
            "put": _op("CU-06 Editar curso", DOC, "Cursos", curso, params=[_ruta("id_curso")], extra=NF),
            "delete": _op("CU-06 Eliminar curso", DOC, "Cursos", params=[_ruta("id_curso")], extra=NF)},
        "/api/cursos/{id_curso}/modulos": {"post": _op(
            "CU-06 Crear módulo", DOC, "Cursos", modulo, params=[_ruta("id_curso")], codigo="201",
            extra={**NF, "409": {"description": "Ya existe un módulo con ese orden"}})},
        "/api/modulos/{id_modulo}": {
            "put": _op("CU-06 Editar módulo", DOC, "Cursos", modulo, params=[_ruta("id_modulo")],
                       extra={**NF, "409": {"description": "Ya existe un módulo con ese orden"}}),
            "delete": _op("CU-06 Eliminar módulo", DOC, "Cursos", params=[_ruta("id_modulo")], extra=NF)},
        "/api/modulos/{id_modulo}/comentarios": {
            "get": _op("Listar comentarios del módulo (MongoDB + nombres de SQLite)", TODOS, "Comentarios (MongoDB)",
                       params=[_ruta("id_modulo")], extra=NF),
            "post": _op("Crear comentario", TODOS, "Comentarios (MongoDB)", comentario, params=[_ruta("id_modulo")],
                        codigo="201", extra=NF)},
        "/api/comentarios/{id_comentario}": {
            "get": _op("Ver un comentario", TODOS, "Comentarios (MongoDB)", params=[_texto_id("id_comentario", "ObjectId de Mongo")], extra=NF),
            "put": _op("Editar comentario (solo el autor)", "autor del comentario", "Comentarios (MongoDB)", comentario,
                       params=[_texto_id("id_comentario", "ObjectId de Mongo")], extra=NF),
            "delete": _op("Eliminar comentario (autor o docente)", "autor, profesor o admin", "Comentarios (MongoDB)",
                          params=[_texto_id("id_comentario", "ObjectId de Mongo")], extra=NF)},
        "/api/comentarios/{id_comentario}/reacciones": {"post": _op(
            "Reaccionar a un comentario", TODOS, "Comentarios (MongoDB)",
            _cuerpo(_obj(tipo={"type": "string", "enum": ["util", "gracias", "confuso"]}), {"tipo": "util"}),
            params=[_texto_id("id_comentario", "ObjectId de Mongo")], extra=NF)},
        "/api/actividad": {
            "get": _op("Mis últimos eventos (?limite=1..100, ?tipo=)", TODOS, "Actividad (MongoDB)",
                       params=[{"name": "limite", "in": "query", "schema": {"type": "integer"}},
                               {"name": "tipo", "in": "query", "schema": {"type": "string"}}]),
            "post": _op("Registrar evento manual (tema_visto)", TODOS, "Actividad (MongoDB)",
                        _cuerpo(_obj(tipo="string", detalle="object"), {"tipo": "tema_visto", "detalle": {"tema": 3}}), codigo="201")},
        "/api/actividad/{id_actividad}": {"delete": _op(
            "Borrar un evento propio", TODOS, "Actividad (MongoDB)", params=[_texto_id("id_actividad", "ObjectId de Mongo")], extra=NF)},
    }
    error = {"description": "", "content": {"application/json": {"schema": _obj(error="string")}}}
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "EDUDEBUG API", "version": "3.0.0",
            "description": ("API para aprender HTML básico. Autenticación con JWT (HS256, `iss=edudebug`): "
                            "haz `POST /api/auth/login`, copia el `token` y pulsa **Authorize**. "
                            "Roles: `estudiante`, `profesor`, `admin`. El rol se vuelve a leer de la base en cada petición. "
                            "Todos los errores devuelven `{\"error\": \"mensaje\"}`."),
        },
        "servers": [{"url": "/"}],
        "tags": [{"name": n} for n in ("Sistema", "Autenticación", "Administración", "Diagnóstico", "Depurador",
                                        "Progreso", "Cursos", "Comentarios (MongoDB)", "Actividad (MongoDB)")],
        "paths": rutas,
        "components": {
            "securitySchemes": {"bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}},
            "responses": {
                "NoAutenticado": {**error, "description": "401 Falta el token, es inválido o expiró"},
                "Prohibido": {**error, "description": "403 Tu rol no permite esta operación"},
                "Invalido": {**error, "description": "400 Datos inválidos"},
                "NoEncontrado": {**error, "description": "404 No existe el recurso"},
            },
        },
    }


PAGINA_DOCS = """<!doctype html><html lang="es"><head><meta charset="utf-8"><title>EDUDEBUG API</title>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui.css"></head>
<body><div id="ui"></div><script src="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui-bundle.js"></script>
<script>SwaggerUIBundle({url:"/api/openapi.json",dom_id:"#ui",persistAuthorization:true})</script></body></html>"""
