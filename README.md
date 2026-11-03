# quebra-codigo

Mini biblioteca de testes com entradas aleatórias (*property-based testing*)
escrita do zero, só com a biblioteca padrão do Python 3.10+.

Ela roda uma função com milhares de entradas aleatórias, acha a primeira
que faz a função errar e **reduz** esse caso até o menor exemplo possível
que ainda falha. Nada de Hypothesis: geração, seed, shrinking e CLI estão
em `src/quebra_codigo`.

## Instalação

Não precisa instalar nada além do `pytest` (só para rodar os testes):

```
pip install pytest
```

Para usar a biblioteca, basta ter `src/` no `PYTHONPATH`
(ou `pip install -e .`).

## Como usar

```python
from quebra_codigo import check, propriedade, inteiros, listas, strings

# 1) Direto, com check(...)
def nenhum_maior_que_100(xs):
    return all(x <= 100 for x in xs)

check(nenhum_maior_que_100, [listas(inteiros())], tentativas=1000, seed=42)

# 2) Com o decorator
@propriedade(strings(), inteiros(0, 5))
def repetir_tem_tamanho_certo(s, n):
    return len(s * n) == len(s) * n

repetir_tem_tamanho_certo.check()
```

Uma propriedade **falha** quando retorna `False` ou levanta uma exceção.
Quando falha, `check` imprime o relatório e levanta `FalhaDePropriedade`
(use `levantar=False` para só receber o `Resultado`).

Geradores disponíveis, todos combináveis:

- `inteiros(min, max)`, `floats(min, max)`
- `strings(tamanho_max, alfabeto)`
- `listas(gerador, tamanho_max, tamanho_min)`
- `tuplas(g1, g2, ...)`
- `dicionarios(gerador_chave, gerador_valor, tamanho_max)`
- `um_de(a, b, c)`

Ex.: `listas(tuplas(inteiros(), dicionarios(strings(), floats())))`.

### CLI

```
python -m quebra_codigo exemplos/            # seed aleatória
python -m quebra_codigo exemplos/ --seed 2024
```

A CLI importa cada `.py` da pasta, roda todas as funções decoradas com
`@propriedade` e mostra um resumo. Sai com código 1 se algo falhou.

## Exemplo de saída real

Saída de `python -m quebra_codigo exemplos/ --seed 2024` na pasta de
exemplos, que tem quatro bugs plantados e duas propriedades corretas:

```
quebra-codigo: 6 propriedade(s) em exemplos  (seed base=2024)

OK   concatenar_preserva_tamanho: 1000 tentativas passaram (seed=2024)

OK   soma_e_comutativa: 1000 tentativas passaram (seed=2025)

FALHA inverter_duas_vezes_volta_ao_original
  seed:     2026
  tentativa: 15
  original: ''
  reduzida: ''  (0 passos)
  erro:     IndexError: string index out of range

FALHA media_fica_entre_minimo_e_maximo
  seed:     2027
  tentativa: 7
  original: []
  reduzida: []  (0 passos)
  erro:     ZeroDivisionError: division by zero

FALHA ordenar_preserva_os_elementos
  seed:     2028
  tentativa: 1
  original: [5, 0, 11, 11, 8]
  reduzida: [11, 11]  (17 passos)
  erro:     propriedade retornou False

FALHA remover_duplicados_mantem_a_ordem
  seed:     2029
  tentativa: 1
  original: [30, 11, 47, 11, 44, 26, 33]
  reduzida: [1, 0]  (39 passos)
  erro:     propriedade retornou False

============================================================
resumo: 2 ok, 4 falha(s)
  x inverter.py::inverter_duas_vezes_volta_ao_original  seed=2026  reduzida: ''
  x media.py::media_fica_entre_minimo_e_maximo  seed=2027  reduzida: []
  x ordenar.py::ordenar_preserva_os_elementos  seed=2028  reduzida: [11, 11]
  x remover_duplicados.py::remover_duplicados_mantem_a_ordem  seed=2029  reduzida: [1, 0]

repetir: python -m quebra_codigo exemplos --seed 2024
```

Os bugs plantados em `exemplos/`:

- `ordenar.py`: usa `set` e perde números repetidos → reduzido a `[11, 11]`
- `inverter.py`: acessa `texto[0]` e quebra com texto vazio → `''`
- `media.py`: divide por `len(xs)` e quebra com lista vazia → `[]`
- `remover_duplicados.py`: `list(set(xs))` perde a ordem → `[1, 0]`

## Rodando os testes

```
python -m pytest
```

## Decisões técnicas

**Seed.** `check` sorteia uma seed de 32 bits (ou usa a que você passar),
cria um `random.Random(seed)` próprio e mostra a seed em todo relatório.
Como nada usa o `random` global, a mesma seed gera a mesma sequência de
entradas e reproduz exatamente o mesmo erro. Na CLI, a propriedade `i`
usa `seed_base + i`, então uma só seed base reproduz a rodada inteira.

**Geradores são objetos, não funções.** Cada gerador implementa
`gerar(rng)` e `encolher(valor)`. Assim o shrinking de uma lista de tuplas
de dicionários sai de graça: a lista pede candidatos menores a cada
elemento, que pede a cada parte, e assim por diante.

**Shrinking guloso.** Quando uma entrada falha, pedimos ao gerador uma
sequência de candidatos "menores", do mais agressivo ao mais tímido.
Aceitamos o primeiro que ainda falha e recomeçamos a partir dele; paramos
quando nenhum candidato falha (mínimo local) ou após 2000 passos.
As estratégias por tipo:

- inteiros: `0`, depois o positivo (se negativo), depois bisseção rumo a 0
  e por fim `n-1`. Por isso "nenhum > 100" sempre reduz a `[101]`.
- floats: `0.0`, parte inteira, metade, positivo.
- strings: vazia, metades, sem um caractere, depois caracteres mais simples.
- listas: lista vazia, remove metades, blocos cada vez menores, um por um;
  só depois reduz cada elemento no lugar.
- tuplas e dicionários: reduz cada parte/entrada; dicionários também
  perdem entradas e tentam chaves menores quando não colidem.

**Exceções contam como falha.** Qualquer exceção na propriedade é tratada
como falha (e reduzida), porque é assim que bugs como lista vazia e texto
vazio aparecem na prática.

**Relatório curto.** No máximo 6 linhas por falha (nome, seed, tentativa,
original, reduzida, erro), com valores longos truncados.

## Limitações conhecidas

- O shrinking reduz um elemento por vez. Por isso `[11, 11]` não vira
  `[0, 0]`: mudar só um dos dois quebra a repetição que causa o bug.
- Não há geração de valores "espertos" por propriedade (sem *targeting*),
  nem estatísticas de cobertura.
- Dicionários precisam de chaves hasheáveis; o gerador não checa isso.
