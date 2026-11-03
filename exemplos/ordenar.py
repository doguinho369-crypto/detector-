"""Bug plantado: a ordenação perde números repetidos."""
from quebra_codigo import inteiros, listas, propriedade


def ordenar(xs):
    """Ordena... mas usa set no meio e descarta repetidos."""
    return sorted(set(xs))


@propriedade(listas(inteiros(0, 20)))
def ordenar_preserva_os_elementos(xs):
    return sorted(ordenar(xs)) == sorted(xs)
