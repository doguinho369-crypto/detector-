"""CLI: ``python -m quebra_codigo PASTA [--seed N] [--tentativas N]``.

Importa cada ``*.py`` da pasta, encontra as funções decoradas com
``@propriedade`` e roda todas, mostrando um resumo ao final.
"""

from __future__ import annotations

import argparse
import importlib.util
import secrets
import sys
from pathlib import Path

from .nucleo import Propriedade, Resultado


def _carregar_modulo(caminho: Path):
    spec = importlib.util.spec_from_file_location(f"qc_exemplo_{caminho.stem}", caminho)
    modulo = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(modulo)
    return modulo


def descobrir(pasta: Path) -> list[tuple[str, Propriedade]]:
    """Lista ``(arquivo, propriedade)`` para cada @propriedade da pasta."""
    encontradas = []
    arquivos = [pasta] if pasta.is_file() else sorted(pasta.glob("*.py"))
    for arquivo in arquivos:
        if arquivo.name.startswith("_"):
            continue
        modulo = _carregar_modulo(arquivo)
        for nome in dir(modulo):
            obj = getattr(modulo, nome)
            if isinstance(obj, Propriedade):
                encontradas.append((arquivo.name, obj))
    return encontradas


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m quebra_codigo")
    parser.add_argument("pasta", help="pasta (ou arquivo .py) com propriedades")
    parser.add_argument("--seed", type=int, default=None, help="seed base (padrão: aleatória)")
    parser.add_argument("--tentativas", type=int, default=None, help="sobrescreve as tentativas")
    args = parser.parse_args(argv)

    pasta = Path(args.pasta)
    if not pasta.exists():
        print(f"erro: {pasta} não existe", file=sys.stderr)
        return 2

    propriedades = descobrir(pasta)
    if not propriedades:
        print(f"nenhuma @propriedade encontrada em {pasta}")
        return 1

    seed_base = args.seed if args.seed is not None else secrets.randbelow(2**32)
    print(f"quebra-codigo: {len(propriedades)} propriedade(s) em {pasta}  (seed base={seed_base})\n")

    resultados: list[tuple[str, Resultado]] = []
    for i, (arquivo, prop) in enumerate(propriedades):
        opcoes = {}
        if args.tentativas is not None:
            opcoes["tentativas"] = args.tentativas
        # Cada propriedade usa uma seed derivada da base, para serem independentes.
        r = prop.check(seed=seed_base + i, levantar=False, mostrar=True, **opcoes)
        print()
        resultados.append((arquivo, r))

    falhas = [(a, r) for a, r in resultados if not r.passou]
    print("=" * 60)
    print(f"resumo: {len(resultados) - len(falhas)} ok, {len(falhas)} falha(s)")
    for arquivo, r in falhas:
        print(f"  x {arquivo}::{r.nome}  seed={r.seed}  reduzida: {_curto(r)}")
    if falhas:
        print(f"\nrepetir: python -m quebra_codigo {pasta} --seed {seed_base}")
    return 1 if falhas else 0


def _curto(r: Resultado) -> str:
    texto = ", ".join(repr(a) for a in (r.entrada_reduzida or ()))
    return texto if len(texto) <= 40 else texto[:37] + "..."


if __name__ == "__main__":
    sys.exit(main())
