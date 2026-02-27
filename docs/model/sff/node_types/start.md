# start.md — Tipo de nó `start` (SFF v1.0)

## 1) O que é um `start`
O nó do tipo **`start`** representa o **ponto de entrada único** de um fluxo SFF.

Ele é o “marco zero” do grafo:
- é a referência obrigatória do `entry.start`
- é o nó a partir do qual o engine determina alcançabilidade, caminho principal e validações estruturais

Na v1.0:
- deve existir **exatamente 1** nó do tipo `start` no arquivo :contentReference[oaicite:2]{index=2}
- o `entry.start` deve apontar para esse nó, e ele deve ter `type: "start"` :contentReference[oaicite:3]{index=3}

---

## 2) Estrutura (schema do node)
Todo node no SFF segue a estrutura base do bloco `nodes` :contentReference[oaicite:4]{index=4}:

```json
"nodes": {
  "start_id": {
    "type": "start",
    "lane": "lane_id",
    "label": "Texto exibido"
  }
}
````

### Campos

* `type` (**obrigatório**): deve ser `"start"`
* `lane` (**obrigatório**): deve existir em `lanes`
* `label` (**obrigatório**): texto legível para renderização

---

## 3) Regras formais (MUST)

### 3.1 Existência e unicidade

* MUST existir **exatamente 1** node com `type = "start"` 
* MUST ser referenciado por `entry.start` 

### 3.2 Regras de grau do grafo

* MUST **não possuir entradas** (nenhuma edge pode apontar para o start) 
  Regra prática: não pode existir `edge.to === entry.start`.

### 3.3 Regras de conectividade

* SHOULD possuir ao menos 1 saída (um fluxo que “começa e não vai a lugar nenhum” é geralmente inválido em casos reais)
* MUST ser alcançável por definição (é a raiz da análise)

---

## 4) Relação com `entry` e `edges`

* `entry.start` deve existir e apontar para um node `type: "start"` 
* `edges` definem para onde o fluxo segue após o `start` 

---

## 5) Exemplo mínimo válido

```json
{
  "entry": { "start": "n_start", "ends": ["n_end"] },
  "nodes": {
    "n_start": { "type": "start", "lane": "main", "label": "Início" },
    "n_end":   { "type": "end",   "lane": "main", "label": "Fim" }
  },
  "edges": [
    { "from": "n_start", "to": "n_end" }
  ]
}
```

---

## 6) Erros comuns (e códigos sugeridos)

* `E_START_MISSING`: nenhum node `type=start`
* `E_START_MULTIPLE`: mais de um node `type=start`
* `E_ENTRY_START_WRONG_TYPE`: `entry.start` aponta para node que não é `start`
* `E_ENTRY_START_HAS_INCOMING`: existe edge chegando no `start` (violação de grau) 
* `E_NODE_LANE_NOT_FOUND`: `lane` inexistente em `lanes`

---

## 7) Boas práticas

* Use IDs semânticos: `start`, `start_main`, `start_checkout`
* Label curto e claro: “Início”, “Início do fluxo”
* Não “reaproveite” start como passo de negócio — ele é fronteira estrutural