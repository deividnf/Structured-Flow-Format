# process.md — Tipo de nó `process` (SFF v1.0)

## 1) O que é um `process`
O nó do tipo **`process`** representa uma **ação simples** (um passo “linear”) dentro do fluxo.

É o tipo padrão para:
- tarefas humanas (“Preencher formulário”)
- tarefas do sistema (“Validar token”, “Salvar registro”)
- etapas operacionais (“Enviar e-mail”, “Gerar relatório”)

Na v1.0, `process` pode ter um campo opcional `note` :contentReference[oaicite:20]{index=20}.

---

## 2) Estrutura (schema do node)
```json
"nodes": {
  "process_id": {
    "type": "process",
    "lane": "lane_id",
    "label": "Texto exibido",
    "note": "Descrição adicional (opcional)"
  }
}
````

Campos:

* `type`: `"process"`
* `lane`: obrigatório, deve existir em `lanes`
* `label`: obrigatório
* `note`: opcional, para contexto

---

## 3) Regras formais (MUST/SHOULD)

* MUST conter `type/lane/label` como qualquer node 
* SHOULD ter pelo menos 1 entrada e 1 saída **quando estiver no meio do fluxo**

  * exceções: quando o process é imediatamente após `start` (pode ter 0 entradas) ou imediatamente antes de `end` (pode ter 0 saídas)
* MUST ser alcançável a partir do `start` (regra geral de “não ter nós isolados” no engine) 

---

## 4) Relação com `edges`

`process` não cria ramificações por si só.

* Se houver múltiplas saídas a partir de um `process`, isso pode virar ambiguidade.
* Boa prática: quando existe lógica “Sim/Não”, use `decision`.

`edges` são a fonte estrutural das conexões .

---

## 5) Exemplo

```json
{
  "nodes": {
    "validate_input": {
      "type": "process",
      "lane": "backend",
      "label": "Validar dados de entrada",
      "note": "Checar obrigatórios e formato"
    }
  }
}
```

---

## 6) Erros comuns (e códigos sugeridos)

* `E_NODE_LABEL_MISSING`: label ausente
* `E_NODE_LANE_NOT_FOUND`: lane inexistente
* `E_NODE_UNREACHABLE`: process não alcançável a partir do start (após compilação) 

---

## 7) Boas práticas

* `label` = frase curta com verbo (ex.: “Validar pagamento”)
* `note` = detalhe técnico/operacional (ex.: “Aplicar antifraude X”)
* Se o passo tem resultado “duas rotas”, pare e modele isso como `decision`.
