# Endpoints verificados

Generado con `python -m scripts.verificar_endpoints --md docs/ENDPOINTS_VERIFICADOS.md`.

Cada celda es el código HTTP obtenido. **401** = falta iniciar sesión, **403** = rol sin permiso, **400/404** = el rol sí puede entrar (se probó con cuerpo vacío o id inexistente para no modificar datos).

| Método | Ruta | Controlador (función) | Acceso | Sin sesión | Estudiante | Profesor | Admin |
|---|---|---|---|:-:|:-:|:-:|:-:|
| GET | `/` | `vista.pagina_principal` | público | 200 | 200 | 200 | 200 |
| GET | `/api/actividad` | `actividad.listar` | cualquier sesión | 401 | 200 | 200 | 200 |
| POST | `/api/actividad` | `actividad.crear` | cualquier sesión | 401 | 400 | 400 | 400 |
| DELETE | `/api/actividad/<id_actividad>` | `actividad.eliminar` | cualquier sesión | 401 | 404 | 404 | 404 |
| GET | `/api/admin/usuarios` | `admin.listar` | sesión: admin | 401 | 403 | 403 | 200 |
| POST | `/api/admin/usuarios` | `admin.crear` | sesión: admin | 401 | 403 | 403 | 400 |
| PUT | `/api/admin/usuarios/<int:id_usuario>/rol` | `admin.cambiar_rol` | sesión: admin | 401 | 403 | 403 | 400 |
| POST | `/api/auth/login` | `auth.login` | público | 401 | 401 | 401 | 401 |
| GET | `/api/auth/yo` | `auth.yo` | cualquier sesión | 401 | 200 | 200 | 200 |
| DELETE | `/api/comentarios/<id_comentario>` | `comentarios.eliminar` | cualquier sesión | 401 | 404 | 404 | 404 |
| GET | `/api/comentarios/<id_comentario>` | `comentarios.detalle` | cualquier sesión | 401 | 404 | 404 | 404 |
| PUT | `/api/comentarios/<id_comentario>` | `comentarios.actualizar` | cualquier sesión | 401 | 404 | 404 | 404 |
| POST | `/api/comentarios/<id_comentario>/reacciones` | `comentarios.reaccionar` | cualquier sesión | 401 | 404 | 404 | 404 |
| GET | `/api/cursos` | `cursos.listar` | cualquier sesión | 401 | 200 | 200 | 200 |
| POST | `/api/cursos` | `cursos.crear` | sesión: profesor, admin | 401 | 403 | 400 | 400 |
| DELETE | `/api/cursos/<int:id_curso>` | `cursos.eliminar` | sesión: profesor, admin | 401 | 403 | 404 | 404 |
| GET | `/api/cursos/<int:id_curso>` | `cursos.detalle` | cualquier sesión | 401 | 404 | 404 | 404 |
| PUT | `/api/cursos/<int:id_curso>` | `cursos.actualizar` | sesión: profesor, admin | 401 | 403 | 404 | 404 |
| POST | `/api/cursos/<int:id_curso>/modulos` | `cursos.crear_modulo` | sesión: profesor, admin | 401 | 403 | 404 | 404 |
| POST | `/api/depurador/analizar` | `depurador.analizar` | sesión: estudiante | 401 | 400 | 403 | 403 |
| POST | `/api/diagnostico/iniciar` | `diagnostico.iniciar` | sesión: estudiante | 401 | 200 | 403 | 403 |
| POST | `/api/diagnostico/responder` | `diagnostico.responder` | sesión: estudiante | 401 | 400 | 403 | 403 |
| GET | `/api/docs` | `app.documentacion` | público | 200 | 200 | 200 | 200 |
| DELETE | `/api/modulos/<int:id_modulo>` | `cursos.eliminar_modulo` | sesión: profesor, admin | 401 | 403 | 404 | 404 |
| PUT | `/api/modulos/<int:id_modulo>` | `cursos.actualizar_modulo` | sesión: profesor, admin | 401 | 403 | 404 | 404 |
| GET | `/api/modulos/<int:id_modulo>/comentarios` | `comentarios.listar` | cualquier sesión | 401 | 404 | 404 | 404 |
| POST | `/api/modulos/<int:id_modulo>/comentarios` | `comentarios.crear` | cualquier sesión | 401 | 404 | 404 | 404 |
| GET | `/api/openapi.json` | `app.especificacion` | público | 200 | 200 | 200 | 200 |
| GET | `/api/profesor/progreso/<int:curso_id>` | `profesor.progreso_grupo` | sesión: profesor, admin | 401 | 403 | 404 | 404 |
| GET | `/api/recomendaciones/<int:usuario_id>` | `recomendaciones.obtener` | cualquier sesión (estudiante: solo lo suyo) | 401 | 403 | 404 | 404 |
| GET | `/api/salud` | `app.salud` | público | 200 | 200 | 200 | 200 |
| GET | `/api/usuarios/<int:id_usuario>/perfil-completo` | `usuarios.perfil_completo` | cualquier sesión (estudiante: solo lo suyo) | 401 | 403 | 404 | 404 |
| POST | `/api/usuarios/registro` | `usuarios.registro` | público | 400 | 400 | 400 | 400 |

**33 endpoints verificados, 0 errores.**
