import random

from quebra_codigo import dicionarios, floats, inteiros, listas, strings, tuplas


def _amostra(gerador, seed, n=50):
    rng = random.Random(seed)
    return [gerador.gerar(rng) for _ in range(n)]


def test_mesma_seed_gera_a_mesma_sequencia():
    g = listas(tuplas(inteiros(), strings(), dicionarios(strings(5), floats())))
    assert _amostra(g, 42) == _amostra(g, 42)


def test_seeds_diferentes_geram_sequencias_diferentes():
    g = listas(inteiros())
    assert _amostra(g, 1) != _amostra(g, 2)


def test_tipos_e_limites():
    rng = random.Random(0)
    for _ in range(200):
        assert 0 <= inteiros(0, 10).gerar(rng) <= 10
        assert -1.0 <= floats(-1.0, 1.0).gerar(rng) <= 1.0
        assert len(strings(tamanho_max=5).gerar(rng)) <= 5
        assert 2 <= len(listas(inteiros(), tamanho_max=4, tamanho_min=2).gerar(rng)) <= 4
        t = tuplas(inteiros(), strings()).gerar(rng)
        assert isinstance(t, tuple) and len(t) == 2
        d = dicionarios(strings(3), inteiros()).gerar(rng)
        assert isinstance(d, dict)


def test_encolher_inteiro_vai_em_direcao_a_zero():
    cands = list(inteiros().encolher(10))
    assert cands[0] == 0
    assert all(0 <= c < 10 for c in cands)
    assert 9 in cands


def test_encolher_inteiro_negativo_tenta_o_positivo():
    cands = list(inteiros().encolher(-7))
    assert cands[:2] == [0, 7]


def test_encolher_lista_remove_elementos_e_reduz_cada_um():
    cands = list(listas(inteiros()).encolher([5, 6]))
    assert cands[0] == []
    assert [6] in cands and [5] in cands
    assert [0, 6] in cands and [5, 0] in cands


def test_encolher_string_fica_mais_curta():
    cands = list(strings().encolher("abc"))
    assert cands[0] == ""
    assert "ab" in cands and "bc" in cands


def test_encolher_tupla_e_dicionario_reduzem_cada_parte():
    assert (0, "x") in tuplas(inteiros(), strings()).encolher((3, "x"))
    assert (3, "") in tuplas(inteiros(), strings()).encolher((3, "x"))
    cands = list(dicionarios(strings(), inteiros()).encolher({"a": 5}))
    assert {} in cands and {"a": 0} in cands
