# edges.md — Bloco `edges` (SFF v1.0)

## 1. O que é o bloco `edges`

O bloco **`edges`** define as **conexões explícitas** entre nós (`nodes`) do fluxo.

Se `nodes` define **o que existe**,
`edges` define **como as coisas se conectam**.

As `edges` são responsáveis por:

* Sequenciamento (ordem do fluxo)
* Direcionamento (from → to)
* Representação estrutural do grafo
* Coerência entre conexões e ramificações (`decision.branches`)

Na versão 1.0, `edges` é um **array** e é obrigatório na estrutura raiz .

---

## 2. Estrutura Formal

Estrutura de um item em `edges`:

```json
{
  "from": "node_id",
  "to": "node_id",
  "label": "Texto opcional",
  "branch": "true | false | join"
}
```

Definição oficial 

---

## 3. Campos de uma Edge

### 3.1 `from` (obrigatório)

* Tipo: `string`
* ID do nó de origem
* Deve existir em `nodes`

### 3.2 `to` (obrigatório)

* Tipo: `string`
* ID do nó de destino
* Deve existir em `nodes`

### 3.3 `label` (opcional)

* Tipo: `string`
* Texto descritivo para renderização
* Útil para setas (“Sim”, “Não”, “Erro”, “Sucesso”, etc.)

### 3.4 `branch` (opcional, mas crítico para `decision`)

* Tipo: `string`
* Valores permitidos (v1.0): `true`, `false`, `join` 
* Usado para amarrar edges a uma ramificação declarada no nó `decision`

---

## 4. Regras Obrigatórias de Validação

### 4.1 Existência de referências

Regras obrigatórias :

* `edge.from` deve existir em `nodes`
* `edge.to` deve existir em `nodes`

Erros sugeridos:

* `E_EDGE_FROM_NOT_FOUND`
* `E_EDGE_TO_NOT_FOUND`

---

### 4.2 Integridade estrutural do start/end

Estas regras são derivadas das regras globais do formato:

* O nó `start` **não pode possuir entradas** (logo, nenhuma edge pode ter `to = entry.start`) 
* Nós `end` **não podem possuir saídas** (logo, nenhuma edge pode ter `from = end_id`) 

Erros sugeridos:

* `E_ENTRY_START_HAS_INCOMING_EDGE`
* `E_ENTRY_END_HAS_OUTGOING_EDGE`

---

### 4.3 Proibição de contradição com `decision.branches`

A especificação define que:

* `branches` é a **fonte oficial** de ramificação
* `edges` são as conexões estruturais
* `branch` deve corresponder a uma branch válida quando a origem é `decision`
* Não pode haver edge que contradiga branches 

Erros sugeridos:

* `E_DECISION_EDGE_BRANCH_MISMATCH`
* `E_DECISION_EDGE_TARGET_MISMATCH`
* `E_DECISION_MISSING_REQUIRED_EDGE`

---

## 5. Como `edges` se relaciona com `decision.branches`

### 5.1 Fonte de verdade

Quando um nó é `type: "decision"`, a lógica declarada em `branches` diz:

* quais ramos existem (`true` e `false` em boolean)
* para onde cada ramo vai (`next`) 

As edges precisam estar coerentes com isso.

### 5.2 Regra prática (engine)

Para cada `decision` boolean:

* Deve existir uma edge de `from = decision_id` para `to = branches.true.next` com `branch = "true"`
* Deve existir uma edge de `from = decision_id` para `to = branches.false.next` com `branch = "false"`

Se houver edge saindo do decision sem `branch`, o renderizador/engine pode ficar ambíguo. (Boa prática: exigir `branch` sempre em edges que saem de `decision`.)

---

## 6. `branch: "join"` e merges

A spec permite `join` como um valor possível de `branch` na edge .

Quando isso aparece, normalmente está ligado ao campo opcional do `decision`:

```json
"join": {
  "type": "merge",
  "node": "node_id"
}
```

(Definido na seção de `decision`.) 

### Regra recomendada

Se o `decision` declara `join.node`, então:

* Deve existir uma (ou mais) edge(s) com `branch: "join"` levando ao nó `join.node`
* O nó `join.node` deve existir e ser alcançável a partir dos ramos

Erros sugeridos:

* `E_JOIN_NODE_NOT_FOUND`
* `E_JOIN_EDGE_MISSING`

---

## 7. Regras de consistência do grafo (recomendadas no MVP)

A especificação menciona garantias de consistência no processo de leitura/validação (incluindo “nenhum nó isolado” e construção de índices prev/next) .

Regras recomendadas para o validador:

* Não permitir `edge` duplicada exata (`from+to+branch`)
* Não permitir auto-loop simples (`from == to`) (a menos que você defina suporte a loops no futuro)
* Garantir que todo nó (exceto `start`) tenha ao menos 1 entrada, e todo nó (exceto `end`) tenha ao menos 1 saída (regra “sem nós isolados”/“sem nós mortos”)
* Garantir que todos os nós sejam alcançáveis a partir do `start`

Erros sugeridos:

* `E_EDGE_DUPLICATE`
* `E_EDGE_SELF_LOOP`
* `E_NODE_UNREACHABLE`
* `E_NODE_ISOLATED`

---

## 8. Compilação: `prev` e `next`

O motor deve construir índices internos:

```text
prev[node_id] = [...]
next[node_id] = [...]
```

Derivados diretamente de `edges` 

### Observação importante

Esses índices **não pertencem ao arquivo `.sff`**; eles pertencem à estrutura compilada do engine.

---

## 9. Exemplos

### 9.1 Edge simples (process → process)

```json
{ "from": "n_validate", "to": "n_process" }
```

### 9.2 Edge com label (melhor para render)

```json
{ "from": "n_validate", "to": "n_process", "label": "Ok" }
```

### 9.3 Edges de um decision boolean

```json
{ "from": "n_decision", "to": "n_yes", "branch": "true",  "label": "Sim" }
```

```json
{ "from": "n_decision", "to": "n_no",  "branch": "false", "label": "Não" }
```

---

## 10. Checklist do Validador (edges)

* [ ] `edges` existe e é array (bloco raiz obrigatório) 
* [ ] Cada edge tem `from` e `to`
* [ ] `from` existe em `nodes`
* [ ] `to` existe em `nodes`
* [ ] Nenhuma edge aponta para `entry.start` (start sem entradas) 
* [ ] Nenhuma edge sai de nós `end` (end sem saídas) 
* [ ] Para `decision` boolean, existem edges `true` e `false` coerentes com `branches`  
* [ ] Não há edge que contradiga `branches` 

---

## 11. Resumo executivo

* `edges` conectam `nodes` e definem o grafo do fluxo.
* `from`/`to` são obrigatórios e devem existir em `nodes`.
* `branch` é essencial para edges que saem de `decision`.
* `branches` é a fonte oficial da ramificação; `edges` devem ser coerentes com ela 
* O engine usa `edges` para gerar `prev/next` e validar consistência 
