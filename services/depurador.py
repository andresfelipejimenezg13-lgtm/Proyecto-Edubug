"""Depurador de HTML: detecta 3 tipos de error y explica cada uno según el nivel del estudiante.

Tipos de error:
  etiqueta_sin_cerrar     etiquetas que se abren y no se cierran (o cierres sin apertura)
  etiqueta_en_mayusculas  nombres de etiqueta escritos con mayúsculas
  atributo_sin_comillas   valores de atributo sin comillas, o con una comilla sin cerrar
  sin_html                el texto no tiene ninguna etiqueta HTML (por ejemplo, letras al azar)
  etiqueta_desconocida    etiquetas que no existen en HTML (por ejemplo <asdf>)
  atributo_faltante       <img> sin src o alt, <a> sin href
  etiqueta_incompleta     una "<" que abre una etiqueta pero nunca se cierra con ">"

Hoy las explicaciones salen de plantillas locales adaptadas al nivel (bajo, medio, alto). Para usar
un servicio de IA bastaría con reemplazar `explicar()` (la columna se llama explicacion_ia).
"""
import re
from bisect import bisect_right

# Elementos que no llevan etiqueta de cierre.
VACIAS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param",
          "source", "track", "wbr"}

ETIQUETA = re.compile(r"<(/?)([A-Za-z][A-Za-z0-9-]*)([^<>]*)>")
ATRIBUTO_SIN_COMILLAS = re.compile(r"""([^\s"'<>/=]+)\s*=\s*(?!["'])([^\s>]+)""")

CONOCIDAS = set("""
a abbr address area article aside audio b base bdi bdo blockquote body br button canvas caption cite code col
colgroup data datalist dd del details dfn dialog div dl dt em embed fieldset figcaption figure footer form h1 h2 h3
h4 h5 h6 head header hgroup hr html i iframe img input ins kbd label legend li link main map mark menu meta meter
nav noscript object ol optgroup option output p param picture pre progress q rp rt ruby s samp script section select
slot small source span strong style sub summary sup table tbody td template textarea tfoot th thead time title tr
track u ul var video wbr
""".split())
INCOMPLETA = re.compile(r"<(/?[A-Za-z][^<>]*)(?=<|\Z)")

TITULOS = {
    "sin_html": "No hay etiquetas HTML",
    "etiqueta_desconocida": "Etiqueta que no existe",
    "atributo_faltante": "Atributo obligatorio ausente",
    "etiqueta_incompleta": "Etiqueta sin terminar",
    "etiqueta_sin_cerrar": "Etiqueta sin cerrar",
    "etiqueta_en_mayusculas": "Etiqueta en mayúsculas",
    "atributo_sin_comillas": "Atributo sin comillas",
}


def _blanquear(texto):
    """Reemplaza todo menos los saltos de línea por espacios (así no cambian los números de línea)."""
    return re.sub(r"[^\n]", " ", texto)


def _limpiar(codigo):
    """Quita comentarios y el contenido de <script> y <style>, que no es HTML."""
    codigo = re.sub(r"<!--.*?-->", lambda m: _blanquear(m.group(0)), codigo, flags=re.S)
    return re.sub(
        r"(<(script|style)\b[^>]*>)(.*?)(</\2\s*>)",
        lambda m: m.group(1) + _blanquear(m.group(3)) + m.group(4),
        codigo, flags=re.S | re.I,
    )


def analizar(codigo):
    """Devuelve la lista de errores: dicts con tipo, linea, variante y datos para explicarlos."""
    limpio = _limpiar(codigo)
    inicios = [0] + [i + 1 for i, c in enumerate(limpio) if c == "\n"]
    linea_de = lambda posicion: bisect_right(inicios, posicion)

    errores = []
    pila = []
    lineas_con_mayusculas = set()

    if not ETIQUETA.search(limpio) and "<" not in limpio:
        errores.append({"tipo": "sin_html", "linea": 1, "variante": "sin_etiquetas"})
    for m in INCOMPLETA.finditer(limpio):
        errores.append({"tipo": "etiqueta_incompleta", "linea": linea_de(m.start()), "variante": "sin_mayor",
                        "etiqueta": m.group(1).split()[0].lstrip("/").lower()})

    for m in ETIQUETA.finditer(limpio):
        cierre, nombre_original, resto = m.group(1) == "/", m.group(2), m.group(3)
        nombre = nombre_original.lower()
        linea = linea_de(m.start())

        # --- mayúsculas (una vez por línea)
        if nombre_original != nombre and linea not in lineas_con_mayusculas:
            lineas_con_mayusculas.add(linea)
            errores.append({"tipo": "etiqueta_en_mayusculas", "linea": linea,
                            "variante": "mayusculas", "etiqueta": nombre_original})

        # --- comillas (solo en etiquetas de apertura)
        if not cierre:
            sin_comillas = ATRIBUTO_SIN_COMILLAS.search(resto)
            if sin_comillas:
                errores.append({"tipo": "atributo_sin_comillas", "linea": linea,
                                "variante": "sin_comillas", "etiqueta": nombre,
                                "atributo": sin_comillas.group(1)})
            elif resto.count('"') % 2 == 1:
                errores.append({"tipo": "atributo_sin_comillas", "linea": linea,
                                "variante": "comilla_abierta", "etiqueta": nombre})

        # --- etiquetas que no existen (no se apilan para no sumar más ruido)
        if nombre not in CONOCIDAS and "-" not in nombre:
            errores.append({"tipo": "etiqueta_desconocida", "linea": linea, "variante": "desconocida", "etiqueta": nombre})
            continue

        # --- atributos que no pueden faltar
        if not cierre:
            requeridos = {"img": ("src", "alt"), "a": ("href",)}.get(nombre, ())
            for atributo in requeridos:
                if not re.search(r"(?<![\w-])" + atributo + r"\s*=", resto):
                    errores.append({"tipo": "atributo_faltante", "linea": linea, "variante": "falta_atributo",
                                    "etiqueta": nombre, "atributo": atributo})

        # --- etiquetas sin cerrar (pila)
        if nombre in VACIAS:
            continue
        if cierre:
            posicion = next((i for i in range(len(pila) - 1, -1, -1) if pila[i][0] == nombre), None)
            if posicion is None:
                errores.append({"tipo": "etiqueta_sin_cerrar", "linea": linea,
                                "variante": "cierre_sin_apertura", "etiqueta": nombre})
            else:
                for abierta, linea_abierta in pila[posicion + 1:]:
                    errores.append({"tipo": "etiqueta_sin_cerrar", "linea": linea_abierta,
                                    "variante": "falta_cierre", "etiqueta": abierta})
                del pila[posicion:]
        elif not resto.rstrip().endswith("/"):
            pila.append((nombre, linea))

    for abierta, linea_abierta in pila:
        errores.append({"tipo": "etiqueta_sin_cerrar", "linea": linea_abierta,
                        "variante": "falta_cierre", "etiqueta": abierta})

    vistos, unicos = set(), []
    for e in sorted(errores, key=lambda e: (e["linea"], e["tipo"])):
        clave = (e["tipo"], e["linea"], e.get("etiqueta"), e.get("atributo"), e["variante"])
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(e)
    return unicos


def explicar(error, nivel):
    """Explicación del error adaptada al nivel (bajo, medio, alto; None = sin evaluar)."""
    n, l, v = error.get("etiqueta", ""), error["linea"], error["variante"]
    nivel = nivel if nivel in ("bajo", "medio", "alto") else "medio"

    if v == "falta_cierre":
        base = f"La etiqueta <{n}> abierta en la línea {l} no tiene su etiqueta de cierre </{n}>."
        extra = {
            "bajo": f" En HTML, la mayoría de etiquetas funcionan como una caja: se abren con <{n}> y se cierran "
                    f"con </{n}> para que el navegador sepa dónde termina el contenido.",
            "medio": f" Agrega </{n}> donde termina el contenido de ese elemento.",
            "alto": " Revisa la anidación: se cierra en orden inverso al de apertura.",
        }[nivel]
        solucion = f"Agrega la etiqueta de cierre </{n}> después del contenido."
        incorrecto, correcto = f"<{n}>Contenido", f"<{n}>Contenido</{n}>"
    elif v == "cierre_sin_apertura":
        base = f"Hay una etiqueta de cierre </{n}> en la línea {l} que no tiene una <{n}> abierta antes."
        extra = {
            "bajo": " Cada cierre debe corresponder a una apertura: revisa si falta abrir la etiqueta o si sobra este cierre.",
            "medio": " Agrega la apertura o elimina el cierre.",
            "alto": "",
        }[nivel]
        solucion = f"Agrega la etiqueta de apertura <{n}> o elimina el cierre que sobra."
        incorrecto, correcto = f"</{n}>", f"<{n}>Contenido</{n}>"
    elif v == "mayusculas":
        minus = n.lower()
        base = f"La etiqueta <{n}> de la línea {l} está escrita con mayúsculas."
        extra = {
            "bajo": " HTML no distingue entre mayúsculas y minúsculas, pero la buena práctica pide minúsculas para "
                    "que el código sea uniforme y fácil de leer.",
            "medio": f" Escríbela en minúsculas: <{minus}>.",
            "alto": " Usa minúsculas en los nombres de etiqueta.",
        }[nivel]
        solucion = "Escribe las etiquetas HTML en minúsculas."
        incorrecto, correcto = f"<{n.upper()}>Contenido</{n.upper()}>", f"<{minus}>Contenido</{minus}>"
    elif v == "sin_comillas":
        a = error["atributo"]
        base = f"El atributo {a} de la etiqueta <{n}> en la línea {l} tiene un valor sin comillas."
        extra = {
            "bajo": f' El valor de un atributo va entre comillas, por ejemplo {a}="valor", para que el navegador '
                    "sepa dónde empieza y termina.",
            "medio": f' Encierra el valor entre comillas: {a}="valor".',
            "alto": " Coloca el valor entre comillas.",
        }[nivel]
        solucion = "Coloca el valor completo del atributo entre comillas."
        incorrecto, correcto = f"<{n} {a}=valor>", f'<{n} {a}="valor">'
    elif v == "sin_etiquetas":
        base = "No encontramos ninguna etiqueta HTML en tu código: solo hay texto suelto."
        extra = {
            "bajo": " HTML se escribe con etiquetas entre < y >, por ejemplo <p>Hola</p>. Sin ellas, el navegador no sabe "
                    "qué es un título, un párrafo o una imagen.",
            "medio": " Envuelve el texto en etiquetas, por ejemplo <p>Hola</p>.",
            "alto": " Escribe el contenido dentro de etiquetas HTML.",
        }[nivel]
        solucion = "Escribe el texto dentro de etiquetas HTML, como <h1> o <p>."
        incorrecto, correcto = "Hola mundo", "<p>Hola mundo</p>"
    elif v == "desconocida":
        base = f"La etiqueta <{n}> de la línea {l} no existe en HTML."
        extra = {
            "bajo": " Revisa cómo la escribiste: puede tener una letra de más o de menos. Algunas etiquetas comunes son "
                    "<p>, <h1>, <a>, <img>, <ul> y <div>.",
            "medio": " Revisa el nombre; ¿quisiste escribir <p>, <div> u otra?",
            "alto": " Corrige el nombre o usa una etiqueta válida.",
        }[nivel]
        solucion = "Escribe el nombre correcto de la etiqueta (por ejemplo p, div, h1, a, img)."
        incorrecto, correcto = f"<{n}>Contenido</{n}>", "<p>Contenido</p>"
    elif v == "falta_atributo":
        a = error["atributo"]
        base = f"La etiqueta <{n}> de la línea {l} no tiene el atributo {a}."
        extra = {
            "src": " Sin src, la imagen no sabe de dónde cargarse.",
            "alt": " El atributo alt describe la imagen para quien no puede verla y aparece si la imagen falla.",
            "href": " Sin href, el enlace no lleva a ningún lugar.",
        }.get(a, "") if nivel != "alto" else ""
        solucion = f'Agrega el atributo {a}="..." a la etiqueta <{n}>.'
        correcto = {"src": '<img src="foto.jpg" alt="Descripción">', "alt": '<img src="foto.jpg" alt="Descripción">',
                    "href": '<a href="https://ejemplo.com">Ir</a>'}.get(a, f'<{n} {a}="valor">')
        incorrecto = {"src": '<img alt="Descripción">', "alt": '<img src="foto.jpg">', "href": "<a>Ir</a>"}.get(a, f"<{n}>")
    elif v == "sin_mayor":
        base = f"La etiqueta <{n}> de la línea {l} empieza con < pero nunca termina con >."
        extra = {
            "bajo": " Toda etiqueta se escribe entre < y >. Si falta el >, el navegador no sabe dónde acaba la etiqueta.",
            "medio": " Agrega el > al final de la etiqueta.",
            "alto": "",
        }[nivel]
        solucion = "Agrega el símbolo > al final de la etiqueta."
        incorrecto, correcto = f"<{n}", f"<{n}>"
    else:  # comilla_abierta
        base = f"La etiqueta <{n}> de la línea {l} tiene una comilla que se abre pero no se cierra."
        extra = {
            "bajo": ' Cada comilla que abre un valor necesita su pareja que lo cierra, por ejemplo src="imagen.jpg".',
            "medio": " Agrega la comilla que falta al final del valor.",
            "alto": "",
        }[nivel]
        solucion = "Agrega la comilla que falta al final del valor del atributo."
        incorrecto, correcto = '<img src="imagen.jpg>', '<img src="imagen.jpg">'

    return {
        "titulo": TITULOS[error["tipo"]],
        "explicacion": (base + extra).strip(),
        "solucion": solucion,
        "ejemploIncorrecto": incorrecto,
        "ejemploCorrecto": correcto,
    }


# ------------------------------------------------------------------ caso de uso completo (CU-03)

def procesar(usuario, codigo):
    """Analiza el código, lo guarda con sus errores, genera una recomendación si corresponde y arma la respuesta.

    Es lo que hace el endpoint POST /api/depurador/analizar; el controlador solo valida la entrada.
    """
    from models.envio import EnvioCodigo
    from services import actividad, progreso, recomendaciones

    nivel = progreso.nivel_actual(usuario.id)

    errores = []
    for error in analizar(codigo):
        explicado = explicar(error, nivel)
        errores.append({"tipo": error["tipo"], "linea": error["linea"], "explicacionIA": explicado["explicacion"],
                        "titulo": explicado["titulo"], "solucion": explicado["solucion"],
                        "ejemploIncorrecto": explicado["ejemploIncorrecto"],
                        "ejemploCorrecto": explicado["ejemploCorrecto"]})

    id_envio = EnvioCodigo.registrar(
        usuario.id, codigo,
        [{"tipo": e["tipo"], "linea": e["linea"], "explicacion": e["explicacionIA"]} for e in errores])

    # Extensión de CU-03: si hay errores recurrentes, se genera (y guarda) una recomendación de estudio.
    id_recomendacion = recomendaciones.generar_si_corresponde(usuario.id)

    actividad.registrar("codigo_analizado", usuario.id,
                        {"idEnvio": id_envio, "totalErrores": len(errores),
                         "tipos": sorted({e["tipo"] for e in errores}),
                         "recomendacionGenerada": id_recomendacion is not None})

    return {
        "usuarioId": usuario.id,
        "idEnvio": id_envio,
        "erroresDetectados": errores,
        "nivelDetectado": nivel or "sin_evaluar",
        "recomendacion": recomendaciones.obtener(usuario.id, id_recomendacion) if id_recomendacion else None,
        "progreso": progreso.progreso_estudiante(usuario.id),
    }
