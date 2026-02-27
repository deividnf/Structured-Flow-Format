# entry.md — Bloco `entry` (SFF v1.0)

## 1. O que é o bloco `entry`

O bloco **`entry`** é o **mapa oficial de início e término** do fluxo. Ele define:

* **`start`**: o **nó inicial único** do fluxo (o ponto de entrada).
* **`ends`**: a lista de **nós finais** (pontos de término) do fluxo.

Em outras palavras: `entry` declara, de forma explícita e determinística, **onde o fluxo começa** e **onde ele pode terminar**. Isso é essencial para validação e compilação, porque permite ao motor garantir as regras estruturais do grafo (por exemplo: “start não pode ter entradas” e “end não pode ter saídas”) 

> Observação importante: o SFF é lido como **JSON válido** e passa por validações estruturais/lógicas antes de compilar para grafo interno .

---

## 2. Estrutura do `entry`

Estrutura canônica (SFF v1.0): 

```json
"entry": {
  "start": "node_id",
  "ends": ["node_id"]
}
```

### 2.1 Campos

#### `start` (obrigatório)

* **Tipo**: `string`
* **Significado**: ID do nó que representa o início do fluxo.
* **Obrigatoriedade**: sim.

#### `ends` (obrigatório)

* **Tipo**: `array<string>`
* **Significado**: lista de IDs dos nós que representam términos válidos do fluxo.
* **Obrigatoriedade**: sim, com pelo menos 1 item .

---

## 3. Regras formais (validação obrigatória)

As regras abaixo são consideradas **obrigatórias** no SFF v1.0 (draft) .

### 3.1 Regras de existência e referência

1. `entry.start` **deve existir** como chave em `nodes`.
2. Cada item de `entry.ends[]` **deve existir** como chave em `nodes`.
3. `entry.ends` **deve conter pelo menos um** `node_id` válido .

### 3.2 Regras de tipo (semântica)

4. O nó apontado por `entry.start` **deve ser do tipo** `start`. 
5. Todos os nós listados em `entry.ends[]` **devem ser do tipo** `end`. 

> Isso conecta `entry` diretamente à tipagem definida em `nodes` (ex.: `type: "start" | "end" | "process" | ...`) 

### 3.3 Regras de grau (grafo)

6. O nó `start` **não pode possuir entradas** (nenhuma aresta chegando nele). 
7. Nós `end` **não podem possuir saídas** (nenhuma aresta saindo deles). 

---

## 4. Papel do `entry` no motor (engine) e no compilador

Um motor SFF típico faz:

1. Valida JSON
2. Valida estrutura raiz (inclui `entry`)
3. Valida coerência entre `nodes`, `edges` e regras de tipos
4. Constrói índices internos `prev`/`next` e estrutura compilada  

### 4.1 Por que o `entry` existe, se há `edges`?

Porque `edges` descreve conexões; **`entry` declara intenção semântica**:

* Sem `entry`, o motor teria que “adivinhar” o start (ex.: nó sem entradas) e os ends (ex.: nós sem saídas), o que pode falhar em grafos parciais, inválidos, ou em extensões futuras.
* Com `entry`, o arquivo fica mais **explícito, determinístico e validável** (princípios do SFF) .

---

## 5. Relação entre `entry`, `nodes` e `edges`

### 5.1 `entry` → `nodes`

* `entry.start` e `entry.ends[]` **devem apontar para IDs dentro de `nodes`**.
* Além de existir, precisam respeitar o `type` (`start` para start, `end` para ends) .

### 5.2 `entry` → `edges`

`entry` não define as conexões; ele define **o contrato de fronteira** do grafo:

* `start` não pode ter arestas de entrada (violação se existir algum `edge.to === start`).
* `end` não pode ter arestas de saída (violação se existir algum `edge.from === end`) .

### 5.3 `entry` e decisões (`decision`)

Em decisões (`decision`), as ramificações oficiais são declaradas em `branches` e os `edges` devem ser coerentes com isso .

O `entry` não muda isso — mas impacta validações:

* se um `end` estiver “no meio” de uma branch (ou seja, possuir saída), o motor deve acusar erro.
* se `start` estiver apontado para um nó que recebe uma edge por engano, o motor deve acusar erro.

---

## 6. Exemplos completos

### 6.1 Fluxo mínimo válido (1 start, 1 end)

```json
{
  "sff": { "version": "1.0", "id": "flow_001", "title": "Fluxo mínimo", "direction": "TB" },
  "entry": { "start": "n_start", "ends": ["n_end"] },
  "lanes": {
    "lane_main": { "title": "Principal", "order": 1 }
  },
  "nodes": {
    "n_start": { "type": "start", "lane": "lane_main", "label": "Início" },
    "n_end":   { "type": "end",   "lane": "lane_main", "label": "Fim" }
  },
  "edges": [
    { "from": "n_start", "to": "n_end" }
  ]
}
```

O que isso garante:

* Existe 1 `start` e pelo menos 1 `end` (regra global) 
* `entry.start` aponta para nó tipo `start`
* `entry.ends[]` aponta para nós tipo `end`
* `start` não tem entradas; `end` não tem saídas

### 6.2 Fluxo com múltiplos finais (vários `end`)

Útil quando há “términos” diferentes: sucesso, falha, cancelamento etc.

```json
"entry": {
  "start": "n_start",
  "ends": ["n_success", "n_fail", "n_cancel"]
}
```

Regras:

* todos `n_success`, `n_fail`, `n_cancel` **devem ser type `end`**
* nenhum deles pode ter saída (edge saindo) 

---

## 7. Erros comuns e como validar (checklist do validador)

Abaixo, uma lista objetiva do que o validador deve checar especificamente para `entry`.

### 7.1 Estrutura e tipos

* [ ] Existe `entry` no root do arquivo (SFF v1.0 exige) 
* [ ] `entry.start` existe e é string
* [ ] `entry.ends` existe e é array
* [ ] `entry.ends.length >= 1` 

### 7.2 Referências

* [ ] `nodes[entry.start]` existe
* [ ] Para cada `endId` em `entry.ends`, `nodes[endId]` existe 

### 7.3 Semântica de tipo

* [ ] `nodes[entry.start].type === "start"` 
* [ ] Para cada `endId`, `nodes[endId].type === "end"` 

### 7.4 Regras de grau do grafo

Considerando `edges` como lista:

* [ ] Não existe `edge` com `to === entry.start` (start sem entradas) 
* [ ] Para cada `endId` em `entry.ends`, não existe `edge` com `from === endId` (end sem saídas) 

---

## 8. Recomendações de design (boas práticas)

Essas práticas ajudam a manter o SFF simples e “compilável” com menos ambiguidade (alinhado aos princípios: explícito, determinístico, validável) :

1. **IDs de `start` e `end` semânticos**
   Ex.: `start_main`, `end_success`, `end_error`, `end_cancel`.

2. **Múltiplos finais só quando fazem sentido**
   Se o fluxo sempre termina do mesmo jeito, use um `end` único.

3. **Não “reaproveitar” end como nó intermediário**
   Se um nó tem saídas, ele **não** pode ser `end`.

4. **Trate `entry` como a “fonte de verdade” dos limites**
   Mesmo que visualmente o grafo pareça ter outro começo/fim, o motor segue `entry`.

---

## 9. Mensagens de erro sugeridas (para o validador)

Para facilitar debug por humanos e agentes:

* `E_ENTRY_MISSING`: bloco `entry` ausente.
* `E_ENTRY_START_MISSING`: `entry.start` ausente.
* `E_ENTRY_ENDS_MISSING`: `entry.ends` ausente.
* `E_ENTRY_ENDS_EMPTY`: `entry.ends` vazio (deve ter ao menos 1).
* `E_ENTRY_START_NOT_FOUND`: `entry.start` não existe em `nodes`.
* `E_ENTRY_END_NOT_FOUND`: algum ID em `entry.ends` não existe em `nodes`.
* `E_ENTRY_START_WRONG_TYPE`: `entry.start` não é `type: start`.
* `E_ENTRY_END_WRONG_TYPE`: algum `end` listado não é `type: end`.
* `E_ENTRY_START_HAS_INCOMING`: `start` possui entrada (edge chegando).
* `E_ENTRY_END_HAS_OUTGOING`: um `end` possui saída (edge saindo).

Esses erros são diretamente derivados das regras explícitas do bloco `entry` .

---

## 10. Resumo executivo (para modelos/agentes)

* `entry` define **fronteira do fluxo**: 1 entrada (`start`) e 1+ saídas (`ends`).
* `start` deve ser nó `type: start` e **não** pode ter entradas.
* cada `end` deve ser `type: end` e **não** pode ter saídas.
* `entry` é crítico para validação/compilação determinística do grafo interno (`prev`/`next`) 
