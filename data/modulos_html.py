"""Curso inicial (HTML Básico) y sus 5 módulos. Se cargan una sola vez, al crear la base de datos."""

CURSO_HTML = {
    "nombre": "HTML Básico",
    "descripcion": "Fundamentos de HTML para empezar a programar páginas web.",
    "nivel": "Inicial",
    "estado": "Activo",
}

MODULOS_HTML = [
    {"orden": 1, "titulo": "¿Qué es HTML y cómo funciona?",
     "contenido": "HTML es el lenguaje que utilizamos para crear y organizar el contenido de una página web. "
                  "Podemos verlo como el esqueleto de una página: con él colocamos títulos, textos, imágenes, "
                  "enlaces y listas.\n\nEjemplo: <p>Hola, este es mi primer texto.</p>\n"
                  "Etiqueta: <p>. Contenido: Hola, este es mi primer texto."},
    {"orden": 2, "titulo": "Estructura básica de HTML",
     "contenido": "Un documento HTML se organiza así: <!DOCTYPE html> indica que usamos HTML5; <html> contiene "
                  "todo el documento; <head> guarda información de la página (como el <title>) y <body> contiene "
                  "lo que se ve en el navegador.\n\nEjemplo:\n<!DOCTYPE html>\n<html>\n  <head>\n"
                  "    <title>Mi página</title>\n  </head>\n  <body>\n    <h1>Hola Mundo</h1>\n  </body>\n</html>"},
    {"orden": 3, "titulo": "Atributos y sintaxis",
     "contenido": "Los atributos agregan información a una etiqueta. Se escriben dentro de la etiqueta de "
                  "apertura con la forma clave=\"valor\", siempre con el valor entre comillas.\n\n"
                  "Ejemplo: <a href=\"https://www.google.com\">Ir a Google</a>\n"
                  "Etiqueta: <a>. Atributo: href. Valor: \"https://www.google.com\"."},
    {"orden": 4, "titulo": "Etiquetas fundamentales",
     "contenido": "Texto: <h1> hasta <h6> para títulos y <p> para párrafos. Enlaces e imágenes: <a href=\"...\"> y "
                  "<img src=\"...\" alt=\"...\">. Listas: <ul> para listas sin orden, <ol> para listas numeradas y "
                  "<li> para cada elemento."},
    {"orden": 5, "titulo": "Errores comunes y buenas prácticas",
     "contenido": "1) No cerrar una etiqueta: <p>Hola mundo  (falta </p>). 2) No cerrar las comillas de un "
                  "atributo: <img src=\"imagen.jpg>. 3) Anidar mal las etiquetas: <p><strong>Hola</p></strong>. "
                  "Buena práctica: escribir las etiquetas en minúsculas y mantener el código ordenado con "
                  "buena indentación."},
]
