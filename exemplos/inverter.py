"""Bug plantado: inverter texto quebra com texto vazio."""
from quebra_codigo import propriedade, strings


def inverter(texto):
    if texto[0] == texto[-1]:  # IndexError quando texto == ""
        return texto[::-1]
    return "".join(reversed(texto))


@propriedade(strings())
def inverter_duas_vezes_volta_ao_original(texto):
    return inverter(inverter(texto)) == texto
