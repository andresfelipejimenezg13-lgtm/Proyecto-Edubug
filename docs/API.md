# EDUDEBUG — Documentación técnica de la API

Documentación **interactiva** (probar peticiones desde el navegador): `GET /api/docs` (Swagger UI). Especificación OpenAPI 3: `GET /api/openapi.json`.

## Autenticación
1. `POST /api/auth/login` con `{"email","password"}` → `{"token","tipoToken":"Bearer","expiraEnSegundos","usuario","siguiente",...}`.
2. En cada petición protegida: `Authorization: Bearer <token>`.
3. El token es un **JWT HS256** con `sub` (id), `rol`, `iat`, `exp` e `iss="edudebug"`, firmado con `SECRET_KEY`. Dura `TOKEN_HORAS` (8 por defecto).
4. El rol efectivo se lee de la base en cada petición, no del token.

## Formato de errores
Siempre `{"error": "mensaje"}`.
| Código | Significado |
|---|---|
| 400 | Datos inválidos (campos faltantes, contraseña débil, tipos incorrectos) |
| 401 | Sin token, token inválido/vencido, o credenciales incorrectas |
| 403 | Sesión válida pero el rol (o la propiedad del recurso) no lo permite |
| 404 | El recurso no existe |
| 409 | Conflicto (correo repetido, orden de módulo repetido, cambiar tu propio rol) |
| 429 | Demasiados intentos de login fallidos (5 en 15 min por IP + correo) |
| 503 | MongoDB no configurado o sin respuesta (endpoints NoSQL) |

## Endpoints
Acceso: **P** público · **S** cualquier sesión · **E** estudiante · **D** profesor o admin · **A** admin.
| Método y ruta | Acceso | Descripción |
|---|:-:|---|
| `GET /api/salud` | P | Estado de SQLite y MongoDB |
| `POST /api/usuarios/registro` | P | Registro (solo crea estudiantes) |
| `POST /api/auth/login` | P | Inicio de sesión, devuelve el JWT |
| `GET /api/auth/yo` | S | Usuario de la sesión |
| `GET /api/admin/usuarios?rol=` | A | Listar usuarios |
| `POST /api/admin/usuarios` | A | Crear cuenta de cualquier rol |
| `PUT /api/admin/usuarios/{id}/rol` | A | Cambiar rol (no el propio) |
| `POST /api/diagnostico/iniciar` | E | CU-02 iniciar/retomar test |
| `POST /api/diagnostico/responder` | E | CU-02 responder pregunta `{idTest,idPregunta,idOpcion}` |
| `POST /api/depurador/analizar` | E | CU-03 analizar HTML `{codigoHtml}` |
| `GET /api/recomendaciones/{usuarioId}` | S | CU-04 (el estudiante solo ve las suyas) |
| `GET /api/profesor/progreso/{cursoId}` | D | CU-05 panel de progreso del grupo |
| `GET /api/usuarios/{id}/perfil-completo` | S | SQL + Mongo (propio, o cualquiera si eres docente) |
| `GET /api/cursos` · `GET /api/cursos/{id}` | S | CU-06 consultar |
| `POST /api/cursos` · `PUT/DELETE /api/cursos/{id}` | D | CU-06 gestionar cursos |
| `POST /api/cursos/{id}/modulos` · `PUT/DELETE /api/modulos/{id}` | D | CU-06 gestionar módulos |
| `GET/POST /api/modulos/{id}/comentarios` | S | Comentarios (MongoDB) |
| `GET/PUT/DELETE /api/comentarios/{id}` | S | PUT solo el autor; DELETE autor o docente |
| `POST /api/comentarios/{id}/reacciones` | S | `{tipo: util\|gracias\|confuso}` |
| `GET/POST /api/actividad` · `DELETE /api/actividad/{id}` | S | Bitácora propia (MongoDB) |

## Ejemplo rápido (curl)
```bash
TOKEN=$(curl -s -X POST localhost:5000/api/auth/login -H "Content-Type: application/json" \
  -d '{"email":"estudiante@edudebug.com","password":"123456"}' | python -c "import sys,json;print(json.load(sys.stdin)['token'])")
curl -s localhost:5000/api/cursos -H "Authorization: Bearer $TOKEN"
```
