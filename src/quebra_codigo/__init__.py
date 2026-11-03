"""quebra-codigo: testes com entradas aleatórias e shrinking, só com a stdlib."""
from .geradores import (
    Gerador, inteiros, floats, strings, listas, tuplas, dicionarios, um_de,
)
from .nucleo import FalhaDePropriedade, Propriedade, Resultado, check, encolher, propriedade

__all__ = [
    "Gerador", "inteiros", "floats", "strings", "listas", "tuplas", "dicionarios", "um_de",
    "check", "propriedade", "Propriedade", "Resultado", "FalhaDePropriedade", "encolher",
]
