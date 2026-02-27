# nodes.md — Bloco `nodes` (SFF v1.0)

---

## 1. O que é o bloco `nodes`

O bloco **`nodes`** define os **elementos estruturais do fluxo**.

Cada node representa:

* Um ponto de execução
* Uma ação
* Uma decisão
* Um atraso
* Um início
* Um término

Se `edges` define **conexões**,
`nodes` define **entidades estruturais do grafo**.

Sem `nodes`, não existe fluxo.

---

## 2. Estrutura Formal

O bloco `nodes` é um **dicionário indexado por ID**:

```json
"nodes": {
  "node_id": {
    "type": "tipo_do_no",
    "lane": "lane_id",
    "label": "Texto exibido"
  }
}
```

Definição oficial na especificação 

---

## 3. Estrutura Base Obrigatória

Cada node DEVE conter:

| Campo | Tipo   | Obrigatório |
| ----- | ------ | ----------- |
| type  | string | sim         |
| lane  | string | sim         |
| label | string | sim         |

---

## 4. Regras Globais de Validação

### 4.1 IDs

* `node_id` deve ser único
* `node_id` é a chave primária do nó
* Não pode haver duplicidade

Erro sugerido:

* `E_NODE_DUPLICATE_ID`

---

### 4.2 Campo `type`

* Deve ser um dos tipos permitidos
* Não pode ser omitido
* Define comportamento estrutural

Erro sugerido:

* `E_NODE_TYPE_INVALID`

Tipos permitidos v1.0 :

* `start`
* `end`
* `process`
* `decision`
* `delay`

---

### 4.3 Campo `lane`

* Deve existir no bloco `lanes`
* Não pode ser omitido
* Não pode ser null

Erro sugerido:

* `E_NODE_LANE_NOT_FOUND`

---

### 4.4 Campo `label`

* Texto legível
* Obrigatório
* Usado para renderização

Erro sugerido:

* `E_NODE_LABEL_MISSING`

---

## 5. Tipos de Node (v1.0)

---

# 5.1 `start`

Representa início do fluxo.

Regras obrigatórias:

* Deve existir exatamente 1 `start` no fluxo 
* Deve corresponder a `entry.start`
* Não pode ter entradas (`prev` vazio)

Estrutura mínima:

```json
"start_node": {
  "type": "start",
  "lane": "lane_id",
  "label": "Início"
}
```

---

# 5.2 `end`

Representa término do fluxo.

Regras obrigatórias:

* Deve existir ao menos 1 
* Não pode possuir saídas
* Deve estar listado em `entry.ends`

Estrutura:

```json
"end_node": {
  "type": "end",
  "lane": "lane_id",
  "label": "Fim"
}
```

---

# 5.3 `process`

Representa uma ação simples.

Pode conter campo opcional:

```json
"note": "Texto adicional"
```

Exemplo:

```json
"process_payment": {
  "type": "process",
  "lane": "backend",
  "label": "Processar pagamento",
  "note": "Executa validação antifraude"
}
```

---

# 5.4 `delay`

Representa espera temporal.

Estrutura adicional obrigatória:

```json
"delay": {
  "min_seconds": number,
  "max_seconds": number
}
```

Regras:

* `min_seconds` ≥ 0
* `max_seconds` ≥ min_seconds

Erro sugerido:

* `E_DELAY_INVALID_RANGE`

Exemplo:

```json
"wait_api": {
  "type": "delay",
  "lane": "backend",
  "label": "Aguardar resposta",
  "delay": {
    "min_seconds": 1,
    "max_seconds": 5
  }
}
```

---

# 5.5 `decision`

Representa ramificação lógica.

Estrutura obrigatória:

```json
"decision": {
  "kind": "boolean"
}
```

Estrutura obrigatória de branches:

```json
"branches": {
  "true": {
    "label": "Sim",
    "next": "node_id"
  },
  "false": {
    "label": "Não",
    "next": "node_id"
  }
}
```

Definição oficial 

---

## Regras para Decision

* Deve conter `decision.kind`
* Deve conter `branches`
* Para `kind: boolean`:

  * Deve existir `true`
  * Deve existir `false`
* Cada `branches[*].next` deve existir em `nodes`
* Opcionalmente pode conter `join`

Estrutura opcional:

```json
"join": {
  "type": "merge",
  "node": "node_id"
}
```

---

## 6. Relação com `edges`

Regras críticas:

* Toda `edge.from` deve existir em `nodes`
* Toda `edge.to` deve existir em `nodes`
* Para `decision`, `edges` deve refletir `branches`
* Não pode haver edge que contradiga branches 

---

## 7. Regras Estruturais Globais

O engine deve garantir:

* Existe exatamente 1 `start`
* Existe ao menos 1 `end`
* Não existem nós isolados
* Todos os nós são alcançáveis a partir do `start`
* Nenhuma referência inexistente
* `start` não possui entradas
* `end` não possui saídas 

---

## 8. Índices Internos (Compilação)

Durante compilação:

```json
prev[node_id] = [...]
next[node_id] = [...]
```

Construídos a partir de `edges` 

Esses índices não fazem parte do arquivo `.sff`, mas fazem parte do modelo compilado.

---

## 9. Erros Sugeridos

* `E_NODE_DUPLICATE_ID`
* `E_NODE_TYPE_INVALID`
* `E_NODE_LANE_NOT_FOUND`
* `E_NODE_LABEL_MISSING`
* `E_START_MULTIPLE`
* `E_START_MISSING`
* `E_END_MISSING`
* `E_DECISION_BRANCH_MISSING`
* `E_DECISION_BRANCH_INVALID_TARGET`
* `E_NODE_UNREACHABLE`
* `E_NODE_ISOLATED`

---

## 10. Boas Práticas

### 10.1 IDs semânticos

Bom:

* `validate_payment`
* `check_inventory`
* `start_checkout`

Evite:

* `n1`
* `x2`

---

### 10.2 Não sobrecarregue `label`

Label é para leitura humana.
Regras estruturais devem estar em campos formais.

---

### 10.3 Use `decision` para lógica real

Não simule decisões com múltiplos edges saindo de um `process`.

---

## 11. Resumo Executivo

O bloco `nodes`:

* Define as entidades estruturais do fluxo
* É obrigatório 
* É indexado por ID único
* Cada nó possui `type`, `lane`, `label`
* Tipos determinam regras estruturais
* Trabalha em conjunto com `entry` e `edges`
* É validado antes da compilação
