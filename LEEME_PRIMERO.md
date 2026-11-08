# Cómo aplicar la Entrega 3 a tu proyecto (borra este archivo después)

Este zip trae SOLO los archivos que cambian o son nuevos (31). No trae .env, .git, .venv ni instance,
y no pisa tus capturas reales de docs/capturas.

1. Copia tu carpeta "Proyecto Eudebug" como respaldo.
2. Descomprime este zip en otra carpeta (Escritorio).
3. Copia TODO su contenido dentro de "Proyecto Eudebug" y elige "Reemplazar los archivos".
4. Terminal en tu carpeta:
       .venv\Scripts\Activate.ps1
       pip install -r requirements.txt
       python -m pytest -q          (debe decir 108 passed)
       flask --app app run --debug
5. Pruebas en el navegador (http://127.0.0.1:5000):
   - /api/salud  -> sqlite ok, mongodb ok
   - /api/docs   -> Swagger
   - admin@edudebug.com / 123456 -> aparece el botón "Usuarios"
   - estudiante@edudebug.com / 123456 -> NO aparece "Usuarios"; en "Registrarse" ya no hay "Tipo de usuario"
   - 6 contraseñas malas seguidas -> mensaje "Demasiados intentos fallidos"
6. Postman: importa de nuevo postman/EDUDEBUG.postman_collection.json y ejecuta la carpeta
   "6. Seguridad y roles" con el Runner (17 peticiones deben pasar).
7. Capturas: guarda "22 postman seguridad.png" y "23 swagger.png" en docs/capturas.
8. Subir a GitHub (primero cambia la contraseña de Atlas y actualiza tu .env):
       git rm --cached .env
       git add .
       git commit -m "Entrega 3: seguridad, JWT y roles"
       git push
