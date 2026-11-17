"""Cursos y módulos que trae EDUDEBUG. Se cargan al crear la base y se completan solos al actualizar.

Formato del contenido de cada módulo (lo muestra la pantalla del módulo):
  - Párrafos separados por una línea en blanco.
  - «## Título» para un subtítulo.
  - Líneas que empiezan con «- » forman una lista.
  - «> texto» es un recuadro de consejo.
  - Un bloque entre ```html y ``` es un ejemplo de código que se puede probar en el editor.
"""

CURSO_HTML = {
    "nombre": "HTML Básico",
    "descripcion": "Fundamentos de HTML para empezar a programar páginas web.",
    "nivel": "Inicial",
    "estado": "Activo",
}

MODULOS_HTML = [
    {"orden": 1, "titulo": "¿Qué es HTML y cómo funciona?",
     "contenido": """HTML es el lenguaje con el que se escribe el contenido de una página web: títulos, textos, imágenes, enlaces y listas. Es el esqueleto de la página; más adelante, el CSS le da estilo.

## Etiquetas: la pieza básica

El navegador lee tu archivo y, según las etiquetas que encuentra, decide qué mostrar. Casi todas las etiquetas tienen una apertura, un contenido y un cierre.

```html
<p>Hola, este es mi primer texto.</p>
```

- Etiqueta de apertura: <p>
- Contenido: Hola, este es mi primer texto.
- Etiqueta de cierre: </p> (lleva una barra)

> Piensa en una etiqueta como una caja con tapa: si abres la caja y no la cierras, todo lo que viene después queda dentro.

## Cómo se ve una página

Escribes el código en un archivo .html y lo abres en el navegador. No necesitas instalar nada más: con un editor de texto y un navegador ya puedes practicar. En EDUDEBUG puedes escribir el código en el editor y revisar tus errores al instante."""},
    {"orden": 2, "titulo": "Estructura básica de HTML",
     "contenido": """Todo documento HTML sigue la misma estructura. Aprenderla una vez te sirve para todas las páginas que hagas.

```html
<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="UTF-8">
    <title>Mi página</title>
  </head>
  <body>
    <h1>Hola Mundo</h1>
  </body>
</html>
```

## Qué hace cada parte

- <!DOCTYPE html> le dice al navegador que usas HTML5.
- <html> contiene todo el documento. El atributo lang="es" indica que está en español.
- <head> guarda información de la página que no se ve directamente, como el <title> que aparece en la pestaña.
- <body> contiene lo que se muestra en la ventana del navegador.

> Todo lo que quieras que la persona vea va dentro de <body>.

## Indentación

Fíjate en que las etiquetas hijas están corridas hacia la derecha. No cambia el resultado, pero hace que tu código sea mucho más fácil de leer y de corregir."""},
    {"orden": 3, "titulo": "Atributos y sintaxis",
     "contenido": """Los atributos agregan información a una etiqueta. Se escriben dentro de la etiqueta de apertura con la forma nombre="valor".

```html
<a href="https://www.google.com">Ir a Google</a>
```

- Etiqueta: <a>
- Atributo: href
- Valor: "https://www.google.com"

## Reglas que conviene recordar

- El valor siempre va entre comillas.
- Puedes poner varios atributos separados por espacios.
- Los atributos solo van en la etiqueta de apertura, nunca en la de cierre.

```html
<img src="gato.jpg" alt="Un gato dormido" width="300">
```

> Un error muy común es olvidar las comillas: src=gato.jpg. Algunos navegadores lo aceptan, pero en cuanto el valor tiene un espacio, el código se rompe. El depurador de EDUDEBUG lo marca como «Atributo sin comillas».

## Atributos que usarás mucho

- href: la dirección a la que lleva un enlace.
- src: la ruta de una imagen.
- alt: el texto que describe la imagen, útil para quien no puede verla.
- id y class: nombres para encontrar y dar estilo a un elemento."""},
    {"orden": 4, "titulo": "Etiquetas fundamentales",
     "contenido": """Con unas pocas etiquetas puedes construir una página completa. Estas son las que más vas a usar.

## Títulos y párrafos

<h1> es el título principal; baja de importancia hasta <h6>. Los párrafos van en <p>.

```html
<h1>Mi blog de cocina</h1>
<h2>Receta de hoy</h2>
<p>Una receta sencilla para el desayuno.</p>
```

## Enlaces e imágenes

```html
<a href="https://es.wikipedia.org">Ir a Wikipedia</a>
<img src="desayuno.jpg" alt="Un desayuno con huevos y pan">
```

> <img> no tiene etiqueta de cierre porque no lleva contenido. Se llama etiqueta vacía; <br> y <hr> funcionan igual.

## Listas

<ul> crea una lista con viñetas y <ol> una lista numerada. Cada elemento va en un <li>.

```html
<ul>
  <li>Huevos</li>
  <li>Pan</li>
  <li>Aguacate</li>
</ul>
```

## Texto con énfasis

- <strong> para resaltar algo importante (se ve en negrita).
- <em> para dar énfasis (se ve en cursiva)."""},
    {"orden": 5, "titulo": "Errores comunes y buenas prácticas",
     "contenido": """Todos cometemos estos errores al empezar. Reconocerlos te ahorra mucho tiempo. Son los mismos que detecta el depurador de EDUDEBUG.

## 1. No cerrar una etiqueta

```html
<p>Hola mundo
```

Falta el </p>. Sin el cierre, el navegador no sabe dónde termina el párrafo.

## 2. Atributos sin comillas

```html
<img src=imagen.jpg alt=Paisaje>
```

El valor de cada atributo debe ir entre comillas: src="imagen.jpg".

## 3. Etiquetas en mayúsculas

```html
<P>Hola</P>
```

HTML las acepta, pero la buena práctica es escribir las etiquetas en minúsculas.

## 4. Anidar mal las etiquetas

```html
<p><strong>Hola</p></strong>
```

Se cierra primero la que se abrió al final: <p><strong>Hola</strong></p>.

> Si el depurador te marca el mismo error varias veces, EDUDEBUG te recomienda volver a este módulo.

## Buenas prácticas

- Escribe las etiquetas en minúsculas.
- Cierra cada etiqueta que abras.
- Indenta el código para que se lea mejor.
- Prueba tu código a menudo, no solo al final."""},
    {"orden": 6, "titulo": "Tablas",
     "contenido": """Las tablas sirven para mostrar datos organizados en filas y columnas, como un horario o una lista de precios. No se usan para armar el diseño de la página.

```html
<table>
  <tr>
    <th>Producto</th>
    <th>Precio</th>
  </tr>
  <tr>
    <td>Cuaderno</td>
    <td>$4.000</td>
  </tr>
  <tr>
    <td>Lápiz</td>
    <td>$1.000</td>
  </tr>
</table>
```

## Las etiquetas de una tabla

- <table> envuelve toda la tabla.
- <tr> es una fila.
- <th> es una celda de encabezado (se ve en negrita y centrada).
- <td> es una celda de datos.

> Cada fila debe tener la misma cantidad de celdas. Si una fila tiene una celda menos, la tabla se ve desalineada.

## Practica

Haz una tabla con tu horario de tres materias: una columna para el día y otra para la hora."""},
    {"orden": 7, "titulo": "Formularios básicos",
     "contenido": """Un formulario permite que la persona escriba datos, como su nombre o su correo. Se construye con <form> y varios campos <input>.

```html
<form>
  <label for="nombre">Nombre</label>
  <input type="text" id="nombre" name="nombre">

  <label for="correo">Correo</label>
  <input type="email" id="correo" name="correo">

  <button type="submit">Enviar</button>
</form>
```

## Cómo funciona

- <label> es el texto que acompaña a un campo. Su atributo for debe coincidir con el id del campo; así, al tocar el texto, se activa el campo.
- <input> es el campo. El atributo type define qué se puede escribir: text, email, password, number...
- <button> envía el formulario.

> Un campo sin <label> es difícil de usar con lector de pantalla. Escribe siempre la etiqueta.

## Otras opciones

```html
<select id="nivel" name="nivel">
  <option>Inicial</option>
  <option>Intermedio</option>
</select>
<textarea name="mensaje" rows="3"></textarea>
```"""},
    {"orden": 8, "titulo": "Etiquetas semánticas y tu primera página",
     "contenido": """Las etiquetas semánticas dicen para qué sirve cada parte de la página. Así los buscadores, los lectores de pantalla y tú mismo entienden mejor su estructura.

## Las más comunes

- <header>: la parte de arriba, con el título o el logo.
- <nav>: el menú de enlaces.
- <main>: el contenido principal.
- <section>: un bloque temático dentro del contenido.
- <footer>: el pie de página.

## Tu primera página completa

Reúne todo lo que aprendiste en un solo archivo:

```html
<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="UTF-8">
    <title>Sobre mí</title>
  </head>
  <body>
    <header>
      <h1>Hola, soy Ana</h1>
      <nav>
        <a href="#gustos">Mis gustos</a>
      </nav>
    </header>
    <main>
      <section id="gustos">
        <h2>Lo que me gusta</h2>
        <ul>
          <li>Leer</li>
          <li>Programar</li>
        </ul>
        <img src="ana.jpg" alt="Foto de Ana">
      </section>
    </main>
    <footer>
      <p>Hecha con HTML</p>
    </footer>
  </body>
</html>
```

> Cuando termines, pégala en el editor y revisa que no tenga errores. Si no los tiene, completaste el curso.

## Reto

Cambia el contenido para que hable de ti: agrega un título, una lista con tus intereses y un enlace a tu sitio favorito."""},
]

MODULOS_V1 = [
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
