"""Funciones comunes de los controladores."""
from flask import request

from services.errores import ErrorServicio


def cuerpo_json():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        raise ErrorServicio(400, "El cuerpo de la petición debe ser un JSON válido.")
    return datos


def entero(valor, nombre):
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ErrorServicio(400, f"{nombre} debe ser un número entero.")
    return valor


def texto(datos, campo, nombre, maximo, obligatorio=True):
    valor = datos.get(campo, "")
    if not isinstance(valor, str):
        raise ErrorServicio(400, f"{nombre} no es válido.")
    valor = valor.strip()
    if obligatorio and not valor:
        raise ErrorServicio(400, f"{nombre} es obligatorio.")
    if len(valor) > maximo:
        raise ErrorServicio(400, f"{nombre} no puede tener más de {maximo} caracteres.")
    return valor
