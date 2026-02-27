# end.md — Tipo de nó `end` (SFF v1.0)

## 1) O que é um `end`
O nó do tipo **`end`** representa um **término válido** do fluxo.

Ele é uma fronteira de saída:
- Fluxos podem ter **múltiplos `end`** (sucesso, falha, cancelamento, etc.)
- Todos os finais válidos devem estar listados em `entry.ends` :contentReference[oaicite:11]{index=11}

Na v1.0:
- deve existir **pelo menos 1** nó `end` :contentReference[oaicite:12]{index=12}
- nós `end` **não podem ter saídas** :contentReference[oaicite:13]{index=13}

---

## 2) Estrutura (schema do node)
```json
"nodes": {
  "end_id": {
    "type": "end",
    "lane": "lane_id",
    "label": "Texto exibido"
  }
}
````

Campos obrigatórios:

* `type`: `"end"`
* `lane`: deve existir em `lanes`
* `label`: texto legível

---

## 3) Regras formais (MUST)

### 3.1 Existência e referência

* MUST existir ao menos 1 node `type = "end"` 
* MUST estar listado em `entry.ends[]` 

### 3.2 Regras de grau do grafo

* MUST **não possuir saídas** 
  Regra prática: não pode existir `edge.from === end_id`.

---

## 4) Relação com `entry` e `edges`

* `entry.ends` é a fonte de verdade dos términos do fluxo 
* `edges` não podem sair de `end`, mas podem chegar nele normalmente 

---

## 5) Exemplo com múltiplos finais

```json
{
  "entry": { "start": "start", "ends": ["end_success", "end_error"] },
  "nodes": {
    "start": { "type": "start", "lane": "user", "label": "Início" },
    "end_success": { "type": "end", "lane": "system", "label": "Finalizado (sucesso)" },
    "end_error":   { "type": "end", "lane": "system", "label": "Finalizado (erro)" }
  }
}
```

---

## 6) Erros comuns (e códigos sugeridos)

* `E_END_MISSING`: nenhum node `type=end`
* `E_ENTRY_END_WRONG_TYPE`: `entry.ends` lista node que não é `end`
* `E_ENTRY_END_HAS_OUTGOING`: existe edge saindo de `end` 
* `E_ENTRY_END_NOT_FOUND`: `entry.ends` referencia node inexistente

---

## 7) Boas práticas

* Modele finais com intenção: `end_success`, `end_fail`, `end_cancel`
* Evite “end genérico” quando há cenários diferentes (melhora auditoria e render)
* Não use `end` como “checkpoint”. Se tem saída, não é `end`.
