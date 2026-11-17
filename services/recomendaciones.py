"""Recomendador de rutas de estudio.

Cuando un estudiante repite el mismo tipo de error en al menos UMBRAL envíos distintos, se guarda una
recomendación con los módulos del curso que conviene repasar. Se genera una nueva solo si el conjunto
de errores recurrentes cambió.

Los módulos se eligen por su número de orden dentro del primer curso (HTML Básico en el MVP).
"""
from models.curso import Curso, Modulo
from models.envio import ErrorDetectado
from models.recomendacion import Recomendacion

UMBRAL = 2

# Qué módulos (por orden) repasar según el tipo de error.
MODULOS_POR_ERROR = {
    "etiqueta_sin_cerrar": [2, 5],
    "atributo_sin_comillas": [3],
    "etiqueta_en_mayusculas": [5],
    "sin_html": [1, 2],
    "etiqueta_desconocida": [4],
    "atributo_faltante": [3, 4],
    "etiqueta_incompleta": [2, 3],
}


def generar_si_corresponde(id_usuario):
    """Crea una recomendación nueva si hace falta y devuelve su id (o None)."""
    recurrentes = ErrorDetectado.recurrentes_de(id_usuario, UMBRAL)
    if not recurrentes:
        return None

    ultima = Recomendacion.ultima_id(id_usuario)
    if ultima is not None and set(Recomendacion.tipos_de_error(ultima)) == set(recurrentes):
        return None  # los errores recurrentes no cambiaron

    curso = Curso.primero()
    if curso is None:
        return None
    ordenes = []
    for tipo in recurrentes:
        for orden in MODULOS_POR_ERROR.get(tipo, []):
            if orden not in ordenes:
                ordenes.append(orden)
    modulos = Modulo.ids_por_orden(curso.id, ordenes)
    if not modulos:
        return None
    return Recomendacion.crear(id_usuario, recurrentes, modulos)


def obtener(id_usuario, id_recomendacion=None):
    """Última recomendación del usuario (o la indicada), en el formato del documento."""
    if id_recomendacion is None:
        id_recomendacion = Recomendacion.ultima_id(id_usuario)
    if id_recomendacion is None:
        return {"usuarioId": id_usuario, "idRecomendacion": None, "fecha": None,
                "modulosSugeridos": [], "basadoEnErrores": []}
    detalle = Recomendacion.detalle(id_recomendacion)
    return {
        "usuarioId": id_usuario,
        "idRecomendacion": id_recomendacion,
        "fecha": detalle["fecha"],
        "modulosSugeridos": detalle["modulos"],
        "basadoEnErrores": Recomendacion.tipos_de_error(id_recomendacion),
    }
