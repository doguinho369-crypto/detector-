"""Propriedades sem bug, para o resumo mostrar também os casos OK."""
from quebra_codigo import dicionarios, inteiros, propriedade, strings, tuplas


@propriedade(inteiros(), inteiros())
def soma_e_comutativa(a, b):
    return a + b == b + a


@propriedade(tuplas(strings(), strings()), dicionarios(strings(), inteiros()))
def concatenar_preserva_tamanho(par, d):
    a, b = par
    return len(a + b) == len(a) + len(b) and len(dict(d)) == len(d)
