"""Bug plantado: média de lista vazia divide por zero."""
from quebra_codigo import floats, listas, propriedade


def media(xs):
    return sum(xs) / len(xs)


@propriedade(listas(floats(0.0, 100.0)))
def media_fica_entre_minimo_e_maximo(xs):
    m = media(xs)
    return not xs or min(xs) <= m <= max(xs)
