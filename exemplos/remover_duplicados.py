"""Bug plantado: remover duplicados perde a ordem original."""
from quebra_codigo import inteiros, listas, propriedade


def remover_duplicados(xs):
    return list(set(xs))  # set não guarda ordem


@propriedade(listas(inteiros(0, 50)))
def remover_duplicados_mantem_a_ordem(xs):
    resultado = remover_duplicados(xs)
    esperado = []
    for x in xs:
        if x not in esperado:
            esperado.append(x)
    return resultado == esperado
