# delay.md — Tipo de nó `delay` (SFF v1.0)

## 1) O que é um `delay`
O nó do tipo **`delay`** representa uma **espera temporal** antes de prosseguir no fluxo.

Use para:
- aguardar resposta de sistema/terceiro
- janela de cooldown
- SLA mínimo / retry backoff (no modelo lógico)
- “esperar X segundos/minutos” como parte do processo

Na v1.0, `delay` exige o bloco adicional `delay` com intervalo em segundos :contentReference[oaicite:25]{index=25}.

---

## 2) Estrutura (schema do node)
```json
"nodes": {
  "wait_api": {
    "type": "delay",
    "lane": "backend",
    "label": "Aguardar resposta",
    "delay": {
      "min_seconds": 1,
      "max_seconds": 5
    }
  }
}
````

Campos obrigatórios:

* `type`: `"delay"`
* `lane`: obrigatório
* `label`: obrigatório
* `delay.min_seconds`: number
* `delay.max_seconds`: number 

---

## 3) Regras formais (MUST)

* MUST conter `delay.min_seconds` e `delay.max_seconds` 
* MUST garantir:

  * `min_seconds >= 0`
  * `max_seconds >= min_seconds`
* SHOULD ser usado quando a espera é parte “real” do fluxo (evite delay artificial para “organizar diagrama”)

---

## 4) Relação com `edges`

`delay` é um nó linear: o avanço ocorre via `edges` como qualquer node.

Exemplo típico:

* process → delay → process

---

## 5) Exemplo completo

```json
{
  "nodes": {
    "submit_request": { "type": "process", "lane": "user", "label": "Enviar requisição" },
    "wait": {
      "type": "delay",
      "lane": "system",
      "label": "Aguardar processamento",
      "delay": { "min_seconds": 5, "max_seconds": 30 }
    },
    "finish": { "type": "end", "lane": "system", "label": "Concluído" }
  },
  "edges": [
    { "from": "submit_request", "to": "wait" },
    { "from": "wait", "to": "finish" }
  ]
}
```

---

## 6) Erros comuns (e códigos sugeridos)

* `E_DELAY_MISSING_BLOCK`: node `delay` sem o objeto `delay`
* `E_DELAY_INVALID_RANGE`: `max_seconds < min_seconds`
* `E_DELAY_NEGATIVE`: `min_seconds < 0`
* `E_NODE_LANE_NOT_FOUND`, `E_NODE_LABEL_MISSING`

---

## 7) Boas práticas

* Labels explícitos: “Aguardar resposta do provedor”
* Intervalos realistas (para documentação/contrato)
* Se for “aguardar evento externo” (sem tempo definido), considere modelar como `process` + `note` (até existir suporte futuro a eventos)
