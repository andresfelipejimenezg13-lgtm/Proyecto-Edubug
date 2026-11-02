# EDUDEBUG — Persistencia políglota (SQLite + MongoDB)

Plataforma para aprender HTML básico. Backend Flask (Python).
- **SQL (SQLite, 11 tablas):** datos estructurados — usuarios, cursos, módulos, tests, envíos de código, errores, recomendaciones.
- **NoSQL (MongoDB):** datos dinámicos y de alta frecuencia — bitácora de actividad y comentarios de los módulos.

## 1. ¿Qué parte del problema se beneficia de NoSQL?
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
Cuentas demo: `estudiante@edudebug.com` / `profesor@edudebug.com`, clave `123456`.
Si vienes de una versión anterior, borra la carpeta `instance/`.

## 7. Pruebas y evidencias de ejecución
- **Pruebas automáticas:** `python -m pytest -q` → 66 pruebas (46 de la API SQL + 20 de la capa NoSQL; usan MongoDB simulado con `mongomock`). Resultado: `docs/resultado_pruebas.txt`.
- **Flujo completo impreso:** `python scripts/demo_evidencia.py` (usa tu Atlas si hay `MONGO_URI`). Guarda la salida con
  `python scripts/demo_evidencia.py > docs/evidencia_atlas.txt`.
- **Postman:** importar `postman/EDUDEBUG.postman_collection.json`; la carpeta *5. NoSQL* contiene las peticiones nuevas.
- Incluido en `docs/`: `evidencia_ejecucion_simulada.txt` (corrida con Mongo **simulado** en memoria) y la captura `capturas/perfil-actividad-simulado.png`.
- **Pendiente del equipo:** capturas de Atlas/Compass con las colecciones `actividad_usuario` y `comentarios_modulo`, y de Postman, guardadas en `docs/capturas/`.

## 8. Estructura del proyecto
`app.py`, `config.py` · `models/` (SQLite, `mongo_db.py` conexión, `documentos.py` acceso a colecciones) · `controllers/` (endpoints) ·
`services/` (diagnóstico adaptativo, depurador, recomendaciones, progreso, `actividad.py` bitácora) · `data/` · `frontend/` · `tests/` · `scripts/` · `postman/` · `docs/`.

## 9. Despliegue en Render
Build `pip install -r requirements.txt` · Start `gunicorn "app:create_app()"` · variables `SECRET_KEY`, `MONGO_URI`, `MONGO_DB`.
En Atlas permite el acceso desde Render (Network Access, p. ej. `0.0.0.0/0` para pruebas académicas).
El disco gratuito de Render es efímero: SQLite se reinicia en cada despliegue; Mongo Atlas conserva sus datos.
