import subprocess
import sys
from pathlib import Path

from quebra_codigo.__main__ import descobrir, main

RAIZ = Path(__file__).resolve().parent.parent
EXEMPLOS = RAIZ / "exemplos"


def _rodar(nome, seed):
    (prop,) = [p for a, p in descobrir(EXEMPLOS / nome)]
    return prop.check(seed=seed, levantar=False, mostrar=False)


def test_bug_ordenar_repetidos_e_encontrado():
    for seed in range(5):
        r = _rodar("ordenar.py", seed)
        assert not r.passou
        (xs,) = r.entrada_reduzida
        assert len(xs) == 2 and xs[0] == xs[1]


def test_bug_inverter_texto_vazio_e_encontrado():
    for seed in range(5):
        r = _rodar("inverter.py", seed)
        assert not r.passou
        assert r.entrada_reduzida == ("",)
        assert isinstance(r.erro, IndexError)


def test_bug_media_lista_vazia_e_encontrado():
    for seed in range(5):
        r = _rodar("media.py", seed)
        assert not r.passou
        assert r.entrada_reduzida == ([],)
        assert isinstance(r.erro, ZeroDivisionError)


def test_bug_remover_duplicados_perde_ordem_e_encontrado():
    for seed in range(5):
        r = _rodar("remover_duplicados.py", seed)
        assert not r.passou
        (xs,) = r.entrada_reduzida
        assert len(xs) == 2 and xs[0] > xs[1]


def test_exemplos_corretos_passam():
    for _, prop in descobrir(EXEMPLOS / "corretos.py"):
        assert prop.check(seed=0, mostrar=False).passou


def test_cli_roda_a_pasta_e_resume(capsys):
    codigo = main([str(EXEMPLOS), "--seed", "123"])
    saida = capsys.readouterr().out
    assert codigo == 1
    assert "resumo: 2 ok, 4 falha(s)" in saida
    assert "--seed 123" in saida


def test_cli_como_modulo():
    proc = subprocess.run(
        [sys.executable, "-m", "quebra_codigo", str(EXEMPLOS), "--seed", "1"],
        capture_output=True, text=True, cwd=RAIZ,
        env={"PYTHONPATH": str(RAIZ / "src"), "PATH": ""},
    )
    assert proc.returncode == 1
    assert "FALHA" in proc.stdout and "seed base=1" in proc.stdout
