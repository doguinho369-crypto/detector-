"""Núcleo: ``check``, shrinking, decorator ``@propriedade`` e relatório."""

from __future__ import annotations

import random
import secrets
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

from .geradores import Gerador, Tuplas


class FalhaDePropriedade(AssertionError):
    """Levantada por ``check`` quando a propriedade falha."""

    def __init__(self, resultado: "Resultado"):
        super().__init__(resultado.relatorio())
        self.resultado = resultado


@dataclass
class Resultado:
    nome: str
    seed: int
    tentativas: int
    passou: bool
    entrada_original: tuple | None = None
    entrada_reduzida: tuple | None = None
    erro: BaseException | None = None
    passos_shrink: int = 0
    duracao: float = 0.0

    def relatorio(self) -> str:
        """Relatório curto (no máximo 10 linhas)."""
        if self.passou:
            return (
                f"OK   {self.nome}: {self.tentativas} tentativas passaram "
                f"(seed={self.seed})"
            )
        linhas = [
            f"FALHA {self.nome}",
            f"  seed:     {self.seed}",
            f"  tentativa: {self.tentativas}",
            f"  original: {_fmt(self.entrada_original)}",
            f"  reduzida: {_fmt(self.entrada_reduzida)}  ({self.passos_shrink} passos)",
            f"  erro:     {_fmt_erro(self.erro)}",
        ]
        return "\n".join(linhas)


def _fmt(args: tuple | None, limite: int = 70) -> str:
    if args is None:
        return "-"
    texto = ", ".join(repr(a) for a in args)
    if len(texto) > limite:
        texto = texto[: limite - 3] + "..."
    return texto


def _fmt_erro(erro: BaseException | None) -> str:
    if erro is None:
        return "propriedade retornou False"
    msg = str(erro).splitlines()[0] if str(erro) else ""
    texto = f"{type(erro).__name__}: {msg}" if msg else type(erro).__name__
    return texto[:100]


def _falha(propriedade: Callable[..., Any], args: tuple) -> BaseException | None | bool:
    """Retorna False se passou; senão a exceção (ou None se retornou False)."""
    try:
        resultado = propriedade(*args)
    except Exception as exc:  # noqa: BLE001 - qualquer erro é uma falha
        return exc
    if resultado is False:
        return None
    return False


def encolher(
    propriedade: Callable[..., Any],
    gerador: Gerador,
    args: tuple,
    max_passos: int = 2000,
) -> tuple[tuple, BaseException | None, int]:
    """Reduz ``args`` enquanto a propriedade continuar falhando.

    Estratégia gulosa: pede candidatos ao gerador, aceita o primeiro que ainda
    falha e recomeça a partir dele. Para quando nenhum candidato falha.
    """
    atual = args
    erro_atual = _falha(propriedade, atual)
    passos = 0
    while passos < max_passos:
        for cand in gerador.encolher(atual):
            passos += 1
            cand = tuple(cand)
            if cand == atual:
                continue
            r = _falha(propriedade, cand)
            if r is not False:
                atual, erro_atual = cand, r
                break
            if passos >= max_passos:
                break
        else:
            break  # ninguém falhou: mínimo local
    return atual, (erro_atual if erro_atual is not False else None), passos


def check(
    propriedade: Callable[..., Any],
    geradores: Sequence[Gerador] | Gerador,
    tentativas: int = 1000,
    seed: int | None = None,
    nome: str | None = None,
    levantar: bool = True,
    mostrar: bool = True,
) -> Resultado:
    """Roda ``propriedade`` com entradas aleatórias; para na primeira falha.

    A propriedade falha se retornar ``False`` ou levantar uma exceção.
    """
    if isinstance(geradores, Gerador):
        geradores = [geradores]
    gerador = Tuplas(tuple(geradores))
    if seed is None:
        seed = secrets.randbelow(2**32)
    nome = nome or getattr(propriedade, "__name__", "propriedade")
    rng = random.Random(seed)
    inicio = time.perf_counter()

    for i in range(1, tentativas + 1):
        args = gerador.gerar(rng)
        r = _falha(propriedade, args)
        if r is False:
            continue
        reduzida, erro, passos = encolher(propriedade, gerador, args)
        resultado = Resultado(
            nome=nome, seed=seed, tentativas=i, passou=False,
            entrada_original=args, entrada_reduzida=reduzida, erro=erro,
            passos_shrink=passos, duracao=time.perf_counter() - inicio,
        )
        if mostrar:
            print(resultado.relatorio())
        if levantar:
            raise FalhaDePropriedade(resultado)
        return resultado

    resultado = Resultado(
        nome=nome, seed=seed, tentativas=tentativas, passou=True,
        duracao=time.perf_counter() - inicio,
    )
    if mostrar:
        print(resultado.relatorio())
    return resultado


@dataclass
class Propriedade:
    """Função decorada com ``@propriedade``. Chamável com ``.check(...)``."""

    funcao: Callable[..., Any]
    geradores: tuple[Gerador, ...]
    tentativas: int = 1000
    extras: dict = field(default_factory=dict)

    @property
    def nome(self) -> str:
        return self.funcao.__name__

    def __call__(self, *args: Any) -> Any:
        return self.funcao(*args)

    def check(self, seed: int | None = None, **kw: Any) -> Resultado:
        opcoes = {"tentativas": self.tentativas, "nome": self.nome, **kw}
        return check(self.funcao, self.geradores, seed=seed, **opcoes)


def propriedade(*geradores: Gerador, tentativas: int = 1000) -> Callable[[Callable], Propriedade]:
    """Decorator: ``@propriedade(inteiros(), listas(strings()))``."""

    def decorador(funcao: Callable[..., Any]) -> Propriedade:
        return Propriedade(funcao, tuple(geradores), tentativas)

    return decorador
