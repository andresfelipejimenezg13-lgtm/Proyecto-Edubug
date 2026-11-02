"""Generador de preguntas del test diagnóstico adaptativo.

Hoy usa el banco local (data/banco_preguntas.py). Para conectar un servicio de IA más adelante basta
con crear otra clase con el mismo método `generar()` y devolverla desde `obtener_generador()`; el
resto del test (adaptación de dificultad, guardado en preguntas_test, niveles) no cambia.
"""
import random

from data.banco_preguntas import PREGUNTAS
from services.errores import ErrorServicio


class GeneradorLocal:
    """Elige preguntas del banco local (generada_por_ia = 0)."""

    def __init__(self, banco=PREGUNTAS, rng=random):
        self.banco = banco
        self.rng = rng

    def generar(self, dificultad, excluir, temas_usados, historial):
        """Devuelve una pregunta nueva.

        - dificultad: la deseada (1 a 3); si ya no quedan, la más cercana.
        - excluir: ids del banco que ya salieron en este test.
        - temas_usados: temas de este test (se prefiere un tema distinto).
        - historial: ids del banco que el estudiante vio antes, del más reciente al más antiguo
          (se prefiere la que vio hace más tiempo o nunca, para que el test rote).
        """
        candidatas = [p for p in self.banco if p["id"] not in excluir]
        if not candidatas:
            raise ErrorServicio(503, "No hay preguntas disponibles para continuar el test.")

        distancia = lambda p: abs(p["dificultad"] - dificultad)
        minima = min(distancia(p) for p in candidatas)
        candidatas = [p for p in candidatas if distancia(p) == minima]

        def antiguedad(p):
            return historial.index(p["id"]) if p["id"] in historial else len(historial) + 1

        puntaje = lambda p: (p["tema"] not in temas_usados, antiguedad(p))
        mejor = max(puntaje(p) for p in candidatas)
        elegida = self.rng.choice([p for p in candidatas if puntaje(p) == mejor])

        return {
            "origen": elegida["id"],
            "texto": elegida["texto"],
            "respuesta": elegida["correcta"],
            "opciones": [elegida["correcta"]] + list(elegida["incorrectas"]),
            "tema": elegida["tema"],
            "dificultad": elegida["dificultad"],
            "generada_por_ia": 0,
        }


_generador = GeneradorLocal()


def obtener_generador():
    return _generador
