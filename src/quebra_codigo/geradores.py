"""Geradores de valores aleatórios.

Cada gerador sabe fazer duas coisas:
- ``gerar(rng)``: produzir um valor usando um ``random.Random``;
- ``encolher(valor)``: propor versões "menores" de um valor que falhou.

Os geradores são combináveis: ``listas(inteiros())`` gera listas de inteiros,
``tuplas(inteiros(), strings())`` gera pares, etc.
"""

from __future__ import annotations

import math
import random
import string
from dataclasses import dataclass
from typing import Any, Callable, Iterator, Sequence


class Gerador:
    """Classe base. Subclasses implementam ``gerar`` e ``encolher``."""

    def gerar(self, rng: random.Random) -> Any:  # pragma: no cover - abstrato
        raise NotImplementedError

    def encolher(self, valor: Any) -> Iterator[Any]:
        """Candidatos menores que ``valor``. Por padrão, nenhum."""
        return iter(())

    def mapear(self, funcao: Callable[[Any], Any]) -> "Gerador":
        """Aplica ``funcao`` a cada valor gerado (sem shrinking)."""
        return _Mapeado(self, funcao)


# ---------------------------------------------------------------------------
# Números
# ---------------------------------------------------------------------------


def _caminho_para_zero(n: int) -> Iterator[int]:
    """Candidatos entre 0 e ``n``, do mais perto de 0 ao mais perto de ``n``."""
    if n == 0:
        return
    yield 0
    if n < 0:
        yield -n  # tenta o positivo primeiro: é "mais simples"
    sinal = 1 if n > 0 else -1
    mag = abs(n)
    vistos = {0, mag}
    # bisseção: mag/2, 3mag/4, ... e também mag-1
    passo = mag // 2
    while passo > 0:
        cand = mag - passo
        if cand not in vistos:
            vistos.add(cand)
            yield sinal * cand
        passo //= 2
    if mag - 1 not in vistos:
        yield sinal * (mag - 1)


@dataclass(frozen=True)
class Inteiros(Gerador):
    minimo: int = -1000
    maximo: int = 1000

    def gerar(self, rng: random.Random) -> int:
        return rng.randint(self.minimo, self.maximo)

    def encolher(self, valor: int) -> Iterator[int]:
        alvo = min(max(0, self.minimo), self.maximo)  # 0 ou o limite mais perto
        for cand in _caminho_para_zero(valor - alvo):
            cand += alvo
            if self.minimo <= cand <= self.maximo:
                yield cand


@dataclass(frozen=True)
class Floats(Gerador):
    minimo: float = -1000.0
    maximo: float = 1000.0

    def gerar(self, rng: random.Random) -> float:
        # Alguns valores "especiais" aparecem com mais frequência.
        r = rng.random()
        if r < 0.05:
            return 0.0
        if r < 0.10:
            return float(rng.randint(int(self.minimo), int(self.maximo)))
        return rng.uniform(self.minimo, self.maximo)

    def encolher(self, valor: float) -> Iterator[float]:
        if valor == 0.0 or math.isnan(valor) or math.isinf(valor):
            return
        candidatos = [0.0]
        inteiro = float(math.trunc(valor))
        if inteiro != valor:
            candidatos.append(inteiro)
        candidatos.append(valor / 2)
        if valor < 0:
            candidatos.append(-valor)
        for cand in candidatos:
            if cand != valor and self.minimo <= cand <= self.maximo:
                yield cand


# ---------------------------------------------------------------------------
# Strings
# ---------------------------------------------------------------------------

ALFABETO_PADRAO = string.ascii_letters + string.digits + " áéíóúãõçÁÉ!?.,-_"


@dataclass(frozen=True)
class Strings(Gerador):
    tamanho_max: int = 20
    alfabeto: str = ALFABETO_PADRAO

    def gerar(self, rng: random.Random) -> str:
        n = rng.randint(0, self.tamanho_max)
        return "".join(rng.choice(self.alfabeto) for _ in range(n))

    def encolher(self, valor: str) -> Iterator[str]:
        # 1) mais curtas: vazia, metades, sem um caractere
        if valor:
            yield ""
        n = len(valor)
        if n > 1:
            yield valor[: n // 2]
            yield valor[n // 2 :]
        for i in range(n):
            yield valor[:i] + valor[i + 1 :]
        # 2) mesmo tamanho, caracteres "mais simples" (a, depois 0, espaço)
        for i, ch in enumerate(valor):
            for simples in "a0 ":
                if simples in self.alfabeto and ch != simples and simples < ch:
                    yield valor[:i] + simples + valor[i + 1 :]
                    break


# ---------------------------------------------------------------------------
# Coleções
# ---------------------------------------------------------------------------


def _encolher_sequencia(itens: Sequence[Any], elemento: Gerador, minimo: int) -> Iterator[list]:
    """Remove pedaços, depois reduz cada elemento."""
    itens = list(itens)
    n = len(itens)
    # Perder elementos: tudo, metades, blocos, um por um.
    if n > minimo:
        if minimo == 0:
            yield []
        tamanho_bloco = n // 2
        while tamanho_bloco >= 1:
            for inicio in range(0, n - tamanho_bloco + 1, tamanho_bloco):
                resto = itens[:inicio] + itens[inicio + tamanho_bloco :]
                if len(resto) >= minimo:
                    yield resto
            tamanho_bloco //= 2
    # Reduzir cada elemento, mantendo o tamanho.
    for i, item in enumerate(itens):
        for menor in elemento.encolher(item):
            yield itens[:i] + [menor] + itens[i + 1 :]


@dataclass(frozen=True)
class Listas(Gerador):
    elemento: Gerador
    tamanho_max: int = 10
    tamanho_min: int = 0

    def gerar(self, rng: random.Random) -> list:
        n = rng.randint(self.tamanho_min, self.tamanho_max)
        return [self.elemento.gerar(rng) for _ in range(n)]

    def encolher(self, valor: list) -> Iterator[list]:
        return _encolher_sequencia(valor, self.elemento, self.tamanho_min)


@dataclass(frozen=True)
class Tuplas(Gerador):
    """Tupla de tamanho fixo: uma posição por gerador."""

    partes: tuple[Gerador, ...]

    def gerar(self, rng: random.Random) -> tuple:
        return tuple(g.gerar(rng) for g in self.partes)

    def encolher(self, valor: tuple) -> Iterator[tuple]:
        itens = list(valor)
        for i, (g, item) in enumerate(zip(self.partes, itens)):
            for menor in g.encolher(item):
                yield tuple(itens[:i] + [menor] + itens[i + 1 :])


@dataclass(frozen=True)
class Dicionarios(Gerador):
    chave: Gerador
    valor: Gerador
    tamanho_max: int = 5

    def gerar(self, rng: random.Random) -> dict:
        n = rng.randint(0, self.tamanho_max)
        return {self.chave.gerar(rng): self.valor.gerar(rng) for _ in range(n)}

    def encolher(self, d: dict) -> Iterator[dict]:
        chaves = list(d)
        # Perder entradas.
        if d:
            yield {}
        for k in chaves:
            yield {c: v for c, v in d.items() if c != k}
        # Reduzir valores.
        for k in chaves:
            for menor in self.valor.encolher(d[k]):
                yield {**d, k: menor}
        # Reduzir chaves (só se a nova chave não colidir).
        for k in chaves:
            for menor in self.chave.encolher(k):
                if menor not in d:
                    yield {(menor if c == k else c): v for c, v in d.items()}


# ---------------------------------------------------------------------------
# Combinadores
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Mapeado(Gerador):
    base: Gerador
    funcao: Callable[[Any], Any]

    def gerar(self, rng: random.Random) -> Any:
        return self.funcao(self.base.gerar(rng))


@dataclass(frozen=True)
class UmDe(Gerador):
    """Escolhe um valor fixo entre as opções dadas."""

    opcoes: tuple[Any, ...]

    def gerar(self, rng: random.Random) -> Any:
        return rng.choice(self.opcoes)

    def encolher(self, valor: Any) -> Iterator[Any]:
        # Opções anteriores na lista são consideradas "menores".
        for op in self.opcoes:
            if op == valor:
                return
            yield op


# ---------------------------------------------------------------------------
# Funções de conveniência (a API pública)
# ---------------------------------------------------------------------------


def inteiros(minimo: int = -1000, maximo: int = 1000) -> Inteiros:
    return Inteiros(minimo, maximo)


def floats(minimo: float = -1000.0, maximo: float = 1000.0) -> Floats:
    return Floats(minimo, maximo)


def strings(tamanho_max: int = 20, alfabeto: str = ALFABETO_PADRAO) -> Strings:
    return Strings(tamanho_max, alfabeto)


def listas(elemento: Gerador, tamanho_max: int = 10, tamanho_min: int = 0) -> Listas:
    return Listas(elemento, tamanho_max, tamanho_min)


def tuplas(*partes: Gerador) -> Tuplas:
    return Tuplas(tuple(partes))


def dicionarios(chave: Gerador, valor: Gerador, tamanho_max: int = 5) -> Dicionarios:
    return Dicionarios(chave, valor, tamanho_max)


def um_de(*opcoes: Any) -> UmDe:
    return UmDe(tuple(opcoes))
