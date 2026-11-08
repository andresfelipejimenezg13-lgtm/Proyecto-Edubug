# EDUDEBUG — Plataforma para aprender HTML (Entrega 3: Seguridad, Autenticación y Cierre)

Plataforma para aprender HTML básico. Backend Flask (Python).
- **SQL (SQLite, 11 tablas):** datos estructurados — usuarios, cursos, módulos, tests, envíos de código, errores, recomendaciones.
- **NoSQL (MongoDB):** datos dinámicos y de alta frecuencia — bitácora de actividad y comentarios de los módulos.


## 0. Seguridad (Entrega 3)
| Requisito | Cómo se cumple |
|---|---|
| **Hashing de contraseñas** | Registro y login con `werkzeug.security` (hash con sal aleatoria; la contraseña nunca se guarda ni se devuelve). Política: mínimo 8 caracteres con letras y números. |
| **Autenticación con JWT** | `POST /api/auth/login` entrega un token firmado (HS256, `exp`, `iss=edudebug`) que se envía como `Authorization: Bearer <token>`. Sin token, vencido o manipulado → **401**. |
| **Roles y permisos (RBAC)** | 3 roles: `estudiante`, `profesor`, `admin`. Rol equivocado → **403**. El rol se vuelve a leer de la base en cada petición: un token no puede "ascender" a nadie. |
| **Protección extra** | Límite de intentos de login (5 fallos / 15 min → **429**), mensaje de error genérico (no revela qué correos existen), cabeceras de seguridad, el registro público solo crea estudiantes. |
| **Documentación de la API** | Swagger interactivo en **`/api/docs`** (JSON en `/api/openapi.json`) y resumen en [`docs/API.md`](docs/API.md). Un test verifica que cubra todas las rutas reales. |
| **Demo de los casos de uso** | Guion paso a paso de CU-01 a CU-06 en [`docs/DEMO_CASOS_DE_USO.md`](docs/DEMO_CASOS_DE_USO.md). |

**Matriz de permisos**
| Operación | Sin sesión | Estudiante | Profesor | Admin |
|---|:-:|:-:|:-:|:-:|
| Registro, login, `/api/salud`, `/api/docs` | ✅ | ✅ | ✅ | ✅ |
| Ver cursos, comentar, actividad propia, recomendaciones propias | ❌ 401 | ✅ | ✅ | ✅ |
| Diagnóstico y depurador (CU-02, CU-03) | ❌ 401 | ✅ | ❌ 403 | ❌ 403 |
| Crear/editar/borrar cursos y módulos (CU-06), panel de progreso (CU-05) | ❌ 401 | ❌ 403 | ✅ | ✅ |
| Moderar (borrar) comentarios ajenos | ❌ 401 | ❌ 403 | ✅ | ✅ |
| Crear cuentas de profesor/admin y cambiar roles (`/api/admin/*`) | ❌ 401 | ❌ 403 | ❌ 403 | ✅ |

**Cuentas demo** (clave `123456`, solo con `SEED_DEMO=1`): `estudiante@edudebug.com`, `profesor@edudebug.com`, `admin@edudebug.com`. En producción pon `SEED_DEMO=0` y define `ADMIN_EMAIL` / `ADMIN_PASSWORD` en el `.env`.
Si ya tenías una base de datos anterior, se actualiza sola al arrancar (agrega el rol `admin` sin perder datos).

**Variables de seguridad** (`.env`): `SECRET_KEY` (firma los tokens), `TOKEN_HORAS`, `LOGIN_MAX_INTENTOS`, `LOGIN_VENTANA_MIN`.

## 1. ¿Qué parte del problema se beneficia de NoSQL? (Entrega 2)
| Dato | Por qué no encaja en tablas | Colección |
|---|---|---|
| Bitácora de actividad (login, test, envíos, temas vistos…) | Alto volumen de escrituras; cada tipo de evento guarda campos distintos (`detalle` variable); solo se inserta y se consulta por usuario y fecha | `actividad_usuario` |
| Comentarios de módulos | Atributos opcionales y cambiantes: etiquetas, fragmento de código, reacciones que aparecen según se usan | `comentarios_modulo` |

Lo que sí es estructurado y relacional (cuentas, notas del test, errores detectados, recomendaciones) **se queda en SQL**.
La justificación completa está en el documento PDF de la entrega.

## 2. Estructura de los documentos
```jsonc
// actividad_usuario
{ "_id": ObjectId, "idUsuario": 1, "tipo": "codigo_analizado",
  "fecha": ISODate, "detalle": { "idEnvio": 2, "totalErrores": 4, "tipos": ["etiqueta_sin_cerrar"] } }

// comentarios_modulo
{ "_id": ObjectId, "idUsuario": 1, "idModulo": 2, "texto": "¿Por qué el DOCTYPE va primero?",
  "etiquetas": ["duda"], "fragmentoCodigo": "<!DOCTYPE html>",      // opcional
  "reacciones": { "util": 2, "gracias": 1 },                        // los campos se crean al usarse
  "fecha": ISODate, "editadoEn": ISODate }                          // editadoEn solo si se editó
```
**Vínculo con SQL:** `idUsuario` e `idModulo` son los ids numéricos de `usuarios.id_usuario` y `modulos.id_modulo`.
Mongo no valida esa relación: la valida la capa de servicio (p. ej. el módulo debe existir en SQLite).
El nombre del autor **no se duplica** en Mongo; se consulta en SQLite al responder.
Índices: `actividad_usuario (idUsuario, fecha↓)`, `(tipo)`; `comentarios_modulo (idModulo, fecha↓)`, `(idUsuario)`.

## 3. Cómo se conecta
1. Crea un clúster gratuito en MongoDB Atlas, un usuario de base de datos y en *Network Access* permite tu IP.
2. En *Connect → Drivers* copia la cadena y ponla en `.env`:
   ```
   MONGO_URI=mongodb+srv://USUARIO:CONTRASENA@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   MONGO_DB=edudebug
   ```
3. Arranca la app y abre `/api/salud`: debe decir `"mongodb": "ok"`.
Sin `MONGO_URI` la app sigue funcionando con SQLite; los endpoints NoSQL responden 503 y el perfil entrega solo la parte SQL.
Si Mongo falla en medio de una petición, la bitácora se omite en silencio y la operación principal no se rompe.
Las colecciones e índices se crean solos en el primer uso.

> **Nota para quien clone este repositorio.** El archivo `.env` (con la contraseña real de Atlas) **no se sube a GitHub** a propósito: es información secreta. Por eso el repositorio solo incluye la plantilla `.env.example`. Para ejecutar el proyecto hay que copiarla como `.env` y completar `SECRET_KEY` y `MONGO_URI` con una cadena de conexión propia. Los datos de la aplicación no están en el repositorio: viven en MongoDB Atlas (NoSQL) y en el archivo local de SQLite (SQL, ignorado por Git). Las capturas de `docs/capturas/` muestran la aplicación funcionando contra un clúster real de Atlas.

## 4. Operaciones CRUD sobre MongoDB
| Operación | Endpoint | Colección |
|---|---|---|
| CREATE | `POST /api/actividad` (tipo `tema_visto`) · automático en login, registro, test, depurador, consulta de curso | actividad_usuario |
| READ | `GET /api/actividad?limite=10&tipo=login` | actividad_usuario |
| DELETE | `DELETE /api/actividad/{id}` (solo el dueño) | actividad_usuario |
| CREATE | `POST /api/modulos/{idModulo}/comentarios` | comentarios_modulo |
| READ | `GET /api/modulos/{idModulo}/comentarios` · `GET /api/comentarios/{id}` | comentarios_modulo |
| UPDATE | `PUT /api/comentarios/{id}` (solo el autor) · `POST /api/comentarios/{id}/reacciones` (`$inc`) | comentarios_modulo |
| DELETE | `DELETE /api/comentarios/{id}` (autor o profesor) | comentarios_modulo |

## 5. Endpoint que combina SQL y NoSQL
`GET /api/usuarios/{id}/perfil-completo` (el propio usuario o un profesor)
- **SQLite:** usuario, progreso, diagnóstico y última recomendación.
- **MongoDB:** últimas 10 actividades, total de eventos por tipo (agregación `$group`) y cantidad de comentarios.

También `GET /api/modulos/{id}/comentarios`: los comentarios salen de Mongo y el nombre del autor de SQLite.

## 6. Ejecutar
```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env        # y completa MONGO_URI
flask --app app run --debug   # http://127.0.0.1:5000
```
Cuentas demo: `estudiante@`, `profesor@` y `admin@edudebug.com`, clave `123456`. Documentación interactiva: http://127.0.0.1:5000/api/docs
Si vienes de una versión anterior, borra la carpeta `instance/`.

## 7. Pruebas y evidencias de ejecución
**Evidencias reales (MongoDB Atlas):**
- Salida impresa del flujo completo contra Atlas: [`docs/evidencia_atlas.txt`](docs/evidencia_atlas.txt) (generada con `python scripts/demo_evidencia.py`).
- Capturas de Postman y de Atlas, en `docs/capturas/`:

| # | Qué muestra | Archivo |
|---|---|---|
| 1 | Salud: SQLite y MongoDB responden `ok` | [01 salud.png](docs/capturas/01%20salud.png) |
| 2 | Login del estudiante (se registra el evento `login` en Mongo) | [02 login.png](docs/capturas/02%20login.png) |
| 3 | Depurador: errores detectados y recomendación (SQL) + evento en Mongo | [03 depurador.png](docs/capturas/03%20depurador.png) |
| 4 | Recomendaciones guardadas en SQL | [04 recomendaciones.png](docs/capturas/04%20recomendaciones.png) |
| 5 | CREATE actividad (Mongo) | [05 crear actividad.png](docs/capturas/05%20crear%20actividad.png) |
| 6 | READ actividad: últimas 10 | [06 listar actividad.png](docs/capturas/06%20listar%20actividad.png) |
| 7 | READ actividad filtrada por tipo | [07 filtrar actividad.png](docs/capturas/07%20filtrar%20actividad.png) |
| 8 | CREATE comentario (Mongo) | [08 crear comentario.png](docs/capturas/08%20crear%20comentario.png) |
| 9 | READ comentarios del módulo (Mongo + autor desde SQL) | [09 listar comentarios.png](docs/capturas/09%20listar%20comentarios.png) |
| 10 | READ de un comentario | [10 ver comentario.png](docs/capturas/10%20ver%20comentario.png) |
| 11 | UPDATE comentario | [11 editar comentario.png](docs/capturas/11%20editar%20comentario.png) |
| 12 | UPDATE parcial con `$inc` (reacciones) | [12 reaccion.png](docs/capturas/12%20reaccion.png) |
| 13 | **Endpoint combinado SQL + NoSQL** (parte 1) | [13a perfil completo.png](docs/capturas/13a%20perfil%20completo.png) |
| 14 | **Endpoint combinado SQL + NoSQL** (parte 2) | [13b perfil completo.png](docs/capturas/13b%20perfil%20completo.png) |
| 15 | Colección `actividad_usuario` en MongoDB Atlas | [14 atlas actividad usuario.png](docs/capturas/14%20atlas%20actividad%20usuario.png) |
| 16 | Colección `comentarios_modulo` en MongoDB Atlas | [15 atlas comentarios modulo.png](docs/capturas/15%20atlas%20comentarios%20modulo.png) |
| 17 | DELETE comentario | [16 eliminar comentario.png](docs/capturas/16%20eliminar%20comentario.png) |
| 18 | DELETE actividad | [17 eliminar actividad.png](docs/capturas/17%20eliminar%20actividad.png) |
| 19 | `python -m pytest -q`: 66 pruebas pasando | [18 pruebas.png](docs/capturas/18%20pruebas.png) |

**Pruebas automáticas:** `python -m pytest -q` → 108 pruebas (API SQL, capa NoSQL, 39 de seguridad/RBAC y 3 de la documentación; usan MongoDB simulado con `mongomock`). Resultado en `docs/resultado_pruebas.txt`.

**Postman:** importar `postman/EDUDEBUG.postman_collection.json`; la carpeta *5. NoSQL* contiene las peticiones de MongoDB y la carpeta *6. Seguridad y roles* prueba 401/403/409 y el flujo del administrador (ejecutarla en orden). En el cuerpo de *Responder* (diagnóstico) escribir los ids como números sin comillas.

**Material simulado (no es de Atlas):** `docs/evidencia_ejecucion_simulada.txt` y `docs/capturas/perfil-actividad-simulado.png` se generaron con MongoDB simulado en memoria.

**Autores:** Andrés Felipe Jiménez Gaitán y Dylan Santiago Martínez Millares · Nuevas Tecnologías · Docente: Leandro Pájaro Fuentes.

## 8. Estructura del proyecto
`app.py`, `config.py` · `models/` (SQLite, `mongo_db.py` conexión, `documentos.py` acceso a colecciones) · `controllers/` (endpoints) ·
`services/` (diagnóstico adaptativo, depurador, recomendaciones, progreso, `actividad.py` bitácora) · `data/` · `frontend/` · `tests/` · `scripts/` · `postman/` · `docs/`.

## 9. Despliegue en Render
Build `pip install -r requirements.txt` · Start `gunicorn "app:create_app()"` · variables `SECRET_KEY` (larga y secreta), `MONGO_URI`, `MONGO_DB`, `SEED_DEMO=0`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`.
El limitador de login vive en memoria de cada proceso (suficiente para este proyecto; para varios servidores se movería a Redis/Mongo).
En Atlas permite el acceso desde Render (Network Access, p. ej. `0.0.0.0/0` para pruebas académicas).
El disco gratuito de Render es efímero: SQLite se reinicia en cada despliegue; Mongo Atlas conserva sus datos.

## 10. Evidencias de la Entrega 3
| Qué muestra | Archivo |
|---|---|
| Registro solo de estudiantes y requisitos de contraseña | [20 registro con politica de contrasena.png](docs/capturas/20%20registro%20con%20politica%20de%20contrasena.png) |
| Pantalla de administración: crear cuentas y cambiar roles (RBAC) | [21 admin usuarios y roles.png](docs/capturas/21%20admin%20usuarios%20y%20roles.png) |
| 108 pruebas automáticas (39 de seguridad) | [`docs/resultado_pruebas.txt`](docs/resultado_pruebas.txt) |
| Postman: carpeta *6. Seguridad y roles* (401/403/409/200) | Tomar captura del Runner y guardarla en `docs/capturas/22 postman seguridad.png` |
| Swagger en `/api/docs` | Tomar captura y guardarla en `docs/capturas/23 swagger.png` |
