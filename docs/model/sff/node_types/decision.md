# decision.md — Tipo de nó `decision` (SFF v1.0)

## 1) O que é um `decision`
O nó do tipo **`decision`** representa uma **ramificação lógica** no fluxo.

Ele define:
- que existe um ponto de decisão
- quais ramos existem (branches)
- para onde cada ramo aponta (next)

Na v1.0, `decision` possui:
- `decision.kind` (obrigatório)
- `branches` (obrigatório)
- suporte base para `kind: "boolean"` :contentReference[oaicite:28]{index=28}

---

## 2) Estrutura (schema do node)
Estrutura mínima (boolean):

```json
"nodes": {
  "check_something": {
    "type": "decision",
    "lane": "lane_id",
    "label": "Condição ocorreu?",
    "decision": { "kind": "boolean" },
    "branches": {
      "true":  { "label": "Sim", "next": "node_yes" },
      "false": { "label": "Não", "next": "node_no" }
    }
  }
}
````

Definições formais na spec .

---

## 3) Fonte de verdade: `branches` vs `edges`

Regra-chave do SFF v1.0:

* **`branches` é a fonte oficial da ramificação**
* `edges` são as conexões estruturais que devem ser coerentes com `branches` 

Isso existe para:

* evitar ambiguidades
* permitir validação formal
* manter o fluxo determinístico

---

## 4) Regras formais (MUST)

### 4.1 Estrutura

* MUST conter `decision.kind` 
* MUST conter `branches` 

### 4.2 Regras para `kind: boolean`

* MUST existir branch `true`
* MUST existir branch `false` 
* MUST garantir que cada `branches[...].next` exista em `nodes` 

### 4.3 Coerência com `edges`

Para decisões booleanas, recomenda-se como regra forte do validador:

* MUST existir uma edge:

  * `from = decision_id`
  * `to = branches.true.next`
  * `branch = "true"`
* MUST existir uma edge:

  * `from = decision_id`
  * `to = branches.false.next`
  * `branch = "false"`
    E NÃO pode existir edge saindo do decision que contradiga `branches` .

---

## 5) Join/Merge (opcional)

A spec permite declarar um `join` opcional no decision :

```json
"join": {
  "type": "merge",
  "node": "node_id"
}
```

Propósito:

* indicar um “ponto de reencontro” lógico dos ramos
* facilitar renderização e validações futuras

Regra recomendada:

* Se `join` existir, `join.node` MUST existir em `nodes`.

---

## 6) Exemplos

### 6.1 Decision boolean completo com edges coerentes

```json
{
  "nodes": {
    "d1": {
      "type": "decision",
      "lane": "user",
      "label": "Tem acesso?",
      "decision": { "kind": "boolean" },
      "branches": {
        "true":  { "label": "Sim", "next": "p_allow" },
        "false": { "label": "Não", "next": "p_deny" }
      }
    },
    "p_allow": { "type": "process", "lane": "system", "label": "Permitir" },
    "p_deny":  { "type": "process", "lane": "system", "label": "Negar" }
  },
  "edges": [
    { "from": "d1", "to": "p_allow", "branch": "true",  "label": "Sim" },
    { "from": "d1", "to": "p_deny",  "branch": "false", "label": "Não" }
  ]
}
```

---

## 7) Erros comuns (e códigos sugeridos)

* `E_DECISION_MISSING_BLOCK`: node decision sem `decision`
* `E_DECISION_KIND_MISSING`: sem `decision.kind`
* `E_DECISION_BRANCHES_MISSING`: sem `branches`
* `E_DECISION_BOOLEAN_BRANCH_MISSING`: faltando `true` ou `false`
* `E_DECISION_BRANCH_INVALID_TARGET`: `next` aponta para node inexistente
* `E_DECISION_EDGE_BRANCH_MISMATCH`: edge `branch` não bate com a branch declarada 
* `E_DECISION_EDGE_TARGET_MISMATCH`: edge aponta para destino diferente do `branches.*.next`

---

## 8) Boas práticas

* `label` deve ser uma pergunta objetiva (“Pagamento aprovado?”)
* branches com `label` simples e humano (“Sim” / “Não”)
* use `decision` para ramificação real — evite simular com múltiplas edges saindo de `process`
* mantenha coerência total: se mudar `branches`, atualize as `edges` correspondentes
