import pytest

from quebra_codigo import (
    FalhaDePropriedade, check, dicionarios, floats, inteiros, listas, propriedade, strings, tuplas,
)


def test_propriedade_correta_passa_1000_tentativas():
    r = check(lambda xs: sorted(xs) == sorted(sorted(xs)), [listas(inteiros())], mostrar=False)
    assert r.passou and r.tentativas == 1000


def test_propriedade_correta_com_varios_tipos():
    def prop(n, x, s, t, d):
        return isinstance(n, int) and isinstance(x, float) and isinstance(s, str)

    gens = [inteiros(), floats(), strings(), tuplas(inteiros(), strings()), dicionarios(strings(), inteiros())]
    assert check(prop, gens, mostrar=False).passou


def test_falha_reduz_para_101():
    def nenhum_maior_que_100(xs):
        return all(x <= 100 for x in xs)

    for seed in range(20):
        r = check(nenhum_maior_que_100, [listas(inteiros())], seed=seed, levantar=False, mostrar=False)
        assert not r.passou, seed
        assert r.entrada_reduzida == ([101],), (seed, r.entrada_reduzida)


def test_mesma_seed_reproduz_o_mesmo_erro():
    prop = lambda xs: len(xs) < 7  # noqa: E731
    a = check(prop, [listas(inteiros())], seed=7, levantar=False, mostrar=False)
    b = check(prop, [listas(inteiros())], seed=7, levantar=False, mostrar=False)
    assert a.entrada_original == b.entrada_original
    assert a.entrada_reduzida == b.entrada_reduzida
    assert a.tentativas == b.tentativas


def test_seed_aparece_no_relatorio_e_na_excecao():
    with pytest.raises(FalhaDePropriedade) as info:
        check(lambda n: n < 50, [inteiros()], seed=3, mostrar=False)
    assert "seed:     3" in str(info.value)
    assert info.value.resultado.entrada_reduzida == (50,)
    assert check(lambda n: True, [inteiros()], seed=9, mostrar=False).relatorio().endswith("(seed=9)")


def test_excecao_conta_como_falha_e_e_reduzida():
    def divide(n):
        return 10 // n

    r = check(divide, [inteiros(-5, 5)], seed=1, levantar=False, mostrar=False)
    assert isinstance(r.erro, ZeroDivisionError)
    assert r.entrada_reduzida == (0,)


def test_string_reduz_ate_vazia():
    r = check(lambda s: len(s) > 0, [strings()], seed=5, levantar=False, mostrar=False)
    assert r.entrada_reduzida == ("",)


def test_relatorio_tem_no_maximo_10_linhas():
    r = check(lambda xs: False, [listas(inteiros())], seed=1, levantar=False, mostrar=False)
    assert len(r.relatorio().splitlines()) <= 10


def test_decorator_propriedade():
    @propriedade(inteiros(), inteiros())
    def soma_comutativa(a, b):
        return a + b == b + a

    assert soma_comutativa(1, 2) is True
    assert soma_comutativa.nome == "soma_comutativa"
    assert soma_comutativa.check(seed=1, mostrar=False).passou
