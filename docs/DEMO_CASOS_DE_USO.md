# Demo funcional de los casos de uso (Entrega 1) — guion para la sustentación

Preparación: `flask --app app run`, abrir http://127.0.0.1:5000 (cuentas en el README, clave `123456`). Mostrar antes `/api/docs`.
Cada caso se puede mostrar en la **aplicación** y/o en **Postman** (carpetas 1–6 de la colección).

| CU | Qué mostrar | Rol | Resultado esperado |
|---|---|---|---|
| **CU-01 Registro e inicio de sesión** | Registrarse como estudiante (solo hay opción estudiante; contraseña débil se rechaza). Iniciar sesión. Mostrar que la contraseña en la BD es un hash. 6 intentos fallidos → bloqueo 429. | Público | Sesión con token JWT; la app lleva a la pantalla según el rol |
| **CU-02 Test diagnóstico adaptativo** | Iniciar el test, responder preguntas, ver el nivel final (bajo/medio/alto) | Estudiante | Nivel asignado y guardado. Con el profesor: **403** |
| **CU-03 Depurador de HTML** | Pegar `<p>Hola <b>mundo</p>`, validar; ver errores con explicación y ejemplo correcto | Estudiante | Errores explicados según el nivel; se guarda el envío |
| **CU-04 Recomendaciones y progreso** | Tras varios errores, abrir Perfil: recomendación de módulos y progreso; evento en la bitácora (MongoDB) | Estudiante | Recomendación visible; otro estudiante no puede verla (**403**) |
| **CU-05 Panel de progreso del grupo** | Entrar como profesor: tabla del grupo por curso | Profesor/Admin | Datos del grupo. Con estudiante: **403** |
| **CU-06 Gestión de cursos y módulos** | Como profesor: crear curso, agregar módulo, editarlo, borrarlo | Profesor/Admin | CRUD completo. Con estudiante: **403** |
| **Extra Entrega 3: RBAC** | Como admin: pantalla **Usuarios**, crear un profesor y cambiar un rol; intentar cambiar el propio (409) | Admin | Solo el admin ve el botón Usuarios; `/api/admin/*` da 403 a los demás |
| **Extra Entrega 2: NoSQL** | Comentar un módulo, reaccionar, ver `perfil-completo` (SQL + Mongo) y la colección en Atlas | Cualquiera | Datos de ambas bases |

## Prueba rápida de seguridad (2 minutos, Postman carpeta 6)
Ejecutar la carpeta *6. Seguridad y roles* con el Runner: las 17 peticiones validan 200/201/400/401/403/409 y deben pasar todas.

## Pruebas automáticas
`python -m pytest -q` → 108 pruebas. Mostrar la salida en la sustentación.
