"""Cursos adicionales de EDUDEBUG con sus módulos (mismo formato de contenido que data/modulos_html.py).

El profesor puede cambiar, agregar o eliminar módulos desde la plataforma (pantalla "Cursos" → "Módulos").
"""

CURSOS_EXTRA = [
    {
        "curso": {"nombre": "CSS Básico", "nivel": "Inicial", "estado": "Activo",
                  "descripcion": "Colores, tipografía, cajas y diseño con Flexbox para darle estilo a tus páginas."},
        "modulos": [
            {"orden": 1, "titulo": "¿Qué es CSS y cómo se conecta al HTML?", "contenido": """CSS es el lenguaje que da estilo a una página: colores, tamaños, espacios y posiciones. HTML pone el contenido y CSS decide cómo se ve.

## Tres formas de usarlo

La más práctica es una hoja de estilos externa, pero para empezar basta con escribir el CSS dentro de la etiqueta <style> en el <head>.

```html
<head>
  <style>
    h1 { color: teal; }
  </style>
</head>
<body>
  <h1>Hola con estilo</h1>
</body>
```

- En línea: con el atributo style dentro de una etiqueta. Sirve para pruebas rápidas.
- Interna: dentro de <style>, como en el ejemplo.
- Externa: un archivo .css enlazado con <link rel="stylesheet" href="estilos.css">.

> Usa la hoja externa en cuanto tu proyecto tenga más de una página: así cambias el diseño en un solo lugar.

## Cómo se escribe una regla

```css
h1 {
  color: teal;
  font-size: 32px;
}
```

Una regla tiene un selector (h1), llaves y, dentro, pares propiedad: valor terminados en punto y coma. Olvidar el punto y coma es el error más común."""},
            {"orden": 2, "titulo": "Selectores: elegir qué estilizar", "contenido": """El selector dice a qué elementos se aplica una regla.

## Los tres básicos

```css
p { color: #333; }
.destacado { font-weight: bold; }
#principal { background: #eef; }
```

- Etiqueta: p afecta a todos los párrafos.
- Clase: .destacado afecta a los elementos con class="destacado". Se puede reutilizar.
- Id: #principal afecta a un único elemento con id="principal".

```html
<p>Un párrafo normal.</p>
<p class="destacado">Un párrafo destacado.</p>
```

## Combinar selectores

- nav a: los enlaces dentro de un <nav>.
- h1, h2: los dos tipos de título a la vez.
- a:hover: un enlace cuando pasas el cursor encima.

> Prefiere clases sobre ids para dar estilo. Son más fáciles de reutilizar y de sobrescribir.

## Cuál gana si hay conflicto

Gana el selector más específico (id sobre clase, clase sobre etiqueta) y, si empatan, el que aparece más abajo."""},
            {"orden": 3, "titulo": "Colores y tipografía", "contenido": """Con pocas propiedades cambias por completo la personalidad de una página.

## Colores

```css
body {
  background-color: #f5f7fb;
  color: #16233d;
}
```

- Por nombre: teal, tomato, white.
- Hexadecimal: #1c7293.
- rgb(28, 114, 147): rojo, verde y azul del 0 al 255.

## Texto

```css
p {
  font-family: Arial, sans-serif;
  font-size: 18px;
  line-height: 1.6;
  text-align: left;
}
```

- font-family: la fuente; pon varias por si la primera no está disponible.
- font-size: el tamaño. Para lectura cómoda usa 16px o más.
- line-height: la altura de línea; 1.5 a 1.7 se lee bien.

> Asegúrate de que haya buen contraste entre el texto y el fondo. Si cuesta leerlo, cambia uno de los dos colores.

## Practica

Cambia el color de fondo de tu página y la fuente de los párrafos. Prueba también con un título de otro color."""},
            {"orden": 4, "titulo": "El modelo de caja", "contenido": """En CSS todo elemento es una caja con cuatro capas, de adentro hacia afuera: contenido, padding, borde y margen.

```css
.tarjeta {
  width: 300px;
  padding: 16px;
  border: 2px solid #1c7293;
  margin: 24px;
}
```

- padding: espacio entre el contenido y el borde.
- border: la línea alrededor.
- margin: espacio entre esta caja y las demás.

## Un truco que ahorra problemas

```css
* {
  box-sizing: border-box;
}
```

Con border-box, el ancho que declaras incluye el padding y el borde. Sin esto, una caja de 300px con padding de 16px termina midiendo 332px.

> Si dos elementos no se separan como esperas, revisa primero el margin y el padding.

## Bordes redondeados y sombras

```css
.tarjeta {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
```"""},
            {"orden": 5, "titulo": "Diseño con Flexbox", "contenido": """Flexbox acomoda elementos en una fila o columna sin dolores de cabeza. Se activa en el contenedor, no en los hijos.

```html
<div class="fila">
  <div>Uno</div>
  <div>Dos</div>
  <div>Tres</div>
</div>
```

```css
.fila {
  display: flex;
  gap: 16px;
  justify-content: space-between;
  align-items: center;
}
```

## Las propiedades más usadas

- display: flex: activa el modo flexible.
- flex-direction: row (fila, por defecto) o column.
- justify-content: reparte los elementos en el eje principal (flex-start, center, space-between).
- align-items: los alinea en el otro eje.
- gap: el espacio entre elementos.
- flex-wrap: wrap: permite que pasen a la línea siguiente si no caben.

> Para centrar algo en la pantalla: display: flex; justify-content: center; align-items: center; en su contenedor.

## Practica

Crea un menú de navegación con cuatro enlaces en fila, con espacio entre ellos."""},
            {"orden": 6, "titulo": "Tu primera página con estilo", "contenido": """Junta todo: HTML con estructura y CSS con selectores, color, caja y Flexbox.

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Mi tarjeta</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: Arial, sans-serif; background: #f5f7fb; margin: 0; }
    .contenedor { display: flex; justify-content: center; padding: 40px; }
    .tarjeta { width: 320px; padding: 24px; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,.12); }
    .tarjeta h1 { color: #1c7293; margin-top: 0; }
  </style>
</head>
<body>
  <div class="contenedor">
    <div class="tarjeta">
      <h1>Ana Pérez</h1>
      <p>Estudiante de desarrollo web.</p>
    </div>
  </div>
</body>
</html>
```

> Pega este código en el editor de EDUDEBUG para comprobar que el HTML no tiene errores.

## Reto

Agrega una segunda tarjeta en la misma fila, cambia los colores y haz que la tarjeta cambie de color al pasar el cursor (:hover)."""},
        ],
    },
    {
        "curso": {"nombre": "JavaScript Básico", "nivel": "Intermedio", "estado": "Activo",
                  "descripcion": "Variables, condiciones, funciones y eventos para que tu página reaccione."},
        "modulos": [
            {"orden": 1, "titulo": "¿Qué es JavaScript?", "contenido": """JavaScript es el lenguaje que le da comportamiento a una página: responder a clics, validar formularios, mostrar u ocultar contenido. HTML es la estructura, CSS el estilo y JavaScript la acción.

## Cómo agregarlo

```html
<button onclick="alert('Hola')">Saludar</button>

<script>
  console.log("La página cargó");
</script>
```

- La etiqueta <script> contiene el código.
- console.log() escribe en la consola del navegador (se abre con F12). Es tu mejor herramienta para encontrar errores.

> Un error de sintaxis en JavaScript detiene todo el script. Cuando algo no funcione, abre la consola: casi siempre dice en qué línea está el problema."""},
            {"orden": 2, "titulo": "Variables y tipos de datos", "contenido": """Una variable es un nombre que guarda un valor para usarlo después.

```js
let nombre = "Ana";
const edad = 20;
let activo = true;
```

- let: variable que puede cambiar.
- const: variable que no se reasigna. Úsala por defecto.
- Evita var: es la forma antigua y da sorpresas.

## Tipos básicos

- Texto (string): "Hola" o 'Hola'.
- Número (number): 42 o 3.14.
- Verdadero o falso (boolean): true, false.
- Sin valor: null y undefined.

```js
let saludo = "Hola, " + nombre;
let total = 5 * 3;
console.log(saludo, total);
```

> Los nombres de variable no llevan espacios ni empiezan con número. Por convención se escriben así: miVariable."""},
            {"orden": 3, "titulo": "Condiciones", "contenido": """Las condiciones permiten que el programa decida qué hacer.

```js
let nota = 7;

if (nota >= 6) {
  console.log("Aprobaste");
} else {
  console.log("A repasar");
}
```

## Operadores de comparación

- === igual (valor y tipo). Evita == a secas.
- !== distinto.
- >, <, >=, <= mayor y menor.

## Combinar condiciones

- && significa "y": las dos deben cumplirse.
- || significa "o": basta con una.
- ! niega la condición.

```js
if (edad >= 18 && activo) {
  console.log("Puede entrar");
}
```

> Un error clásico es escribir = (asignar) donde va === (comparar)."""},
            {"orden": 4, "titulo": "Funciones", "contenido": """Una función es un bloque de código con nombre que puedes ejecutar cuantas veces quieras.

```js
function saludar(nombre) {
  return "Hola, " + nombre;
}

console.log(saludar("Ana"));
console.log(saludar("Luis"));
```

- Los parámetros (nombre) son los datos que recibe.
- return devuelve un resultado a quien llamó la función.

## Funciones flecha

```js
const doble = (n) => n * 2;
console.log(doble(4));
```

> Haz funciones pequeñas que hagan una sola cosa y ponles nombres que digan qué hacen: calcularTotal, validarCorreo."""},
            {"orden": 5, "titulo": "Eventos y el DOM", "contenido": """El DOM es la página vista como un árbol de elementos que JavaScript puede leer y modificar. Los eventos son cosas que pasan: un clic, una tecla, el envío de un formulario.

```html
<button id="boton">Cambiar texto</button>
<p id="mensaje">Texto original</p>

<script>
  const boton = document.getElementById("boton");
  const mensaje = document.getElementById("mensaje");

  boton.addEventListener("click", () => {
    mensaje.textContent = "¡Cambió!";
  });
</script>
```

## Qué pasó aquí

- document.getElementById busca un elemento por su id.
- addEventListener dice: "cuando ocurra este evento, ejecuta esta función".
- textContent cambia el texto del elemento.

> El script debe ir después de los elementos que usa (al final del <body>), o no los encontrará.

## Practica

Haz un contador: un botón que sume 1 cada vez que se pulsa y muestre el número en la página."""},
            {"orden": 6, "titulo": "Arreglos y bucles", "contenido": """Un arreglo guarda una lista de valores y un bucle los recorre.

```js
const frutas = ["manzana", "pera", "uva"];

console.log(frutas[0]);
console.log(frutas.length);

for (const fruta of frutas) {
  console.log("Me gusta la " + fruta);
}
```

## Métodos útiles

- push(valor): agrega al final.
- includes(valor): dice si el arreglo contiene el valor.
- map(función): crea otro arreglo transformando cada elemento.

```js
const numeros = [1, 2, 3];
const dobles = numeros.map((n) => n * 2);
console.log(dobles);
```

> Las posiciones empiezan en 0: el primer elemento es frutas[0].

## Reto

Crea un arreglo con tus materias y muéstralas en una lista <ul> de la página usando un bucle."""},
        ],
    },
    {
        "curso": {"nombre": "Diseño Web Adaptable", "nivel": "Intermedio", "estado": "Activo",
                  "descripcion": "Haz que tus páginas se vean bien en celular, tablet y computador."},
        "modulos": [
            {"orden": 1, "titulo": "Por qué importa adaptar la página", "contenido": """Más de la mitad de las visitas web llegan desde un celular. Una página adaptable (responsive) se acomoda al tamaño de pantalla en lugar de obligar a hacer zoom.

## El primer paso: la etiqueta viewport

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

Va dentro de <head>. Sin ella, el celular muestra la página como si fuera de escritorio y la encoge.

> Diseña primero para pantalla pequeña y luego agrega mejoras para pantallas grandes. A eso se le llama mobile first."""},
            {"orden": 2, "titulo": "Unidades relativas", "contenido": """Los píxeles (px) son fijos. Las unidades relativas se ajustan al contexto.

- %: porcentaje del elemento padre.
- rem: múltiplo del tamaño de letra base de la página (normalmente 16px).
- em: múltiplo del tamaño de letra del propio elemento.
- vw y vh: porcentaje del ancho y del alto de la ventana.

```css
.contenedor {
  width: 90%;
  max-width: 960px;
  margin: 0 auto;
}

h1 {
  font-size: 2rem;
}
```

## Por qué max-width

Con width: 90% la caja se adapta en pantallas pequeñas, y con max-width no se estira demasiado en pantallas enormes.

> Para el texto prefiere rem: respeta el tamaño de letra que la persona haya elegido en su navegador."""},
            {"orden": 3, "titulo": "Media queries", "contenido": """Una media query aplica reglas CSS solo cuando se cumple una condición, normalmente el ancho de pantalla.

```css
.columnas {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

@media (min-width: 768px) {
  .columnas {
    flex-direction: row;
  }
}
```

En celular las columnas van una debajo de la otra; desde 768px de ancho pasan a ir en fila.

## Puntos de corte habituales

- 480px: celulares grandes.
- 768px: tablets.
- 1024px: computadores pequeños.

> Elige los puntos de corte donde tu diseño se rompa, no según un modelo de teléfono.

## Practica

Haz una fila de tres tarjetas que en celular se muestren en columna y en pantallas grandes en una sola fila."""},
            {"orden": 4, "titulo": "Imágenes flexibles y revisión final", "contenido": """Una imagen con ancho fijo se sale de la pantalla en un celular.

```css
img {
  max-width: 100%;
  height: auto;
}
```

Con esto la imagen nunca es más ancha que su contenedor y mantiene su proporción.

## Lista de revisión

- La etiqueta viewport está en el <head>.
- Nada obliga a desplazarse de lado.
- Los botones y enlaces se pueden tocar con el dedo (al menos 44px de alto).
- El texto se lee sin hacer zoom.
- Las imágenes tienen el atributo alt.

```html
<img src="paisaje.jpg" alt="Un lago rodeado de montañas">
```

> Prueba tu página con las herramientas del navegador (F12 y el icono de celular) y también en un teléfono real."""},
        ],
    },
]

# Cursos que se muestran como "Próximamente" (inactivos y sin módulos).
CURSOS_PROXIMOS = [
    {"nombre": "Git y GitHub", "descripcion": "Guarda versiones de tu código y colabora con tu equipo.",
     "nivel": "Inicial", "estado": "Inactivo"},
]
