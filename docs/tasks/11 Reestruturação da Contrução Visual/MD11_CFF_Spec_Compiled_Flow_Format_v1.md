
# cpff — Compiled Flow Format

### Especificação Formal v1.0 (Primeira Versão Estrutural)

---

# 1. Introdução

O **cpff (Compiled Flow Format)** é a representação expandida e determinística de um fluxo originalmente definido em `.sff`.

Ele existe para:

* Eliminar ambiguidade estrutural
* Centralizar regras de negócio no compilador
* Transformar conexões implícitas em relações explícitas
* Permitir renderização, exportação e integração com terceiros sem necessidade de análise adicional
* Separar claramente:

  * **Formato declarativo (SFF)** → humano, simples
  * **Formato compilado (cpff)** → máquina, completo

O cpff é um artefato derivado.
Ele nunca substitui o `.sff` como fonte de autoria.

---

# 2. Princípio Arquitetural Fundamental

> O cpff deve conter informação suficiente para que qualquer renderizador desenhe o fluxo sem precisar inferir regras estruturais.

Isso significa:

* Nenhum cálculo de prev/next deve acontecer no export
* Nenhuma decisão de branch deve ser inferida
* Nenhuma análise de profundidade deve ocorrer no layout

Tudo isso já deve estar presente no `.cpff`.

---

# 3. Estrutura Raiz do cpff

```json
{
  "sff_source": { ... },
  "cpff": {
    "version": "1.0",
    "stats": { ... },
    "graph": { ... },
    "layout_context": { ... }
  },
  "lanes": { ... },
  "nodes": { ... },
  "edges": { ... }
}
```

---

# 4. Cabeçalho cpff (Bloco `cpff`)

## 4.1 version (obrigatório)

Versão da especificação cpff.

## 4.2 stats (obrigatório)

Contém métricas estruturais absolutas:

```json
"stats": {
  "nodes_total": 12,
  "edges_total": 14,
  "decision_nodes": 2,
  "branch_edges": 4,
  "joins": 1,
  "lanes_total": 3,
  "max_depth": 6,
  "max_branch_depth": 3
}
```

### Campos obrigatórios:

* nodes_total
* edges_total
* decision_nodes
* branch_edges
* lanes_total

---

# 5. Expansão de Nodes (Obrigatório)

Cada node no cpff deve conter:

## 5.1 Estrutura Base Herdada do SFF

* id
* type
* lane
* label

## 5.2 Bloco `rank` (obrigatório)

```json
"rank": {
  "global": 2,
  "lane": 2,
  "depth": 1,
  "branch_depth": 0
}
```

### Definições:

* global → posição absoluta no fluxo
* lane → posição dentro da lane
* depth → distância do start
* branch_depth → profundidade dentro de branch

---

## 5.3 Bloco `links` (obrigatório)

```json
"links": {
  "prev_nodes": ["validate_data"],
  "next_nodes": ["process_payment"],
  "in_edges": ["e12"],
  "out_edges": ["e13"]
}
```

Nenhum export deve calcular isso.

---

## 5.4 Bloco `branch_context` (condicional)

Presente apenas se o node estiver dentro de branch.

```json
"branch_context": {
  "root_decision": "check_data",
  "branch_label": "true",
  "terminates_soon": false
}
```

---

## 5.5 Bloco `future_metrics` (obrigatório)

```json
"future_metrics": {
  "future_steps": 3,
  "future_decisions": 1,
  "cross_lane_ahead": 1,
  "next_lane_target": "system"
}
```

Esses dados servem para:

* Direcionamento inteligente de branch
* Expansão dinâmica de lane
* Priorização de corredores

---

## 5.6 Bloco `layout_hints` (obrigatório)

```json
"layout_hints": {
  "is_main_path": true,
  "routing_priority": 100,
  "preferred_exit_side": "right",
  "preferred_entry_side": "left"
}
```

---

# 6. Expansão de Edges (Obrigatório)

Cada edge deve conter:

## 6.1 Base herdada

* id
* from
* to
* branch (se houver)

---

## 6.2 Bloco `classification`

```json
"classification": {
  "kind": "main_path",
  "is_cross_lane": false,
  "is_return": false,
  "is_join": false
}
```

Valores possíveis:

* main_path
* branch
* cross_lane
* return
* join

---

## 6.3 Bloco `priority` (obrigatório)

Número determinístico para roteamento.

Regra padrão:

* Main path: 100
* Branch principal: 80
* Branch secundário: 60
* Return: 40
* Join: 30

---

## 6.4 Bloco `routing_constraints`

```json
"routing_constraints": {
  "no_overlap": true,
  "no_cross": true,
  "min_separation": 16
}
```

---

## 6.5 Bloco `routing_hints`

```json
"routing_hints": {
  "backbone_lane": "system",
  "last_mile": true,
  "preferred_channel": 3
}
```

---

# 7. Lanes no cpff

O bloco `lanes` pode conter expansão:

```json
"lanes": {
  "system": {
    "title": "Sistema",
    "order": 2,
    "tracks_total": 13,
    "center_track": 7,
    "expansion_factor": 1.2
  }
}
```

Campos adicionais:

* tracks_total
* center_track
* expansion_factor

---

# 8. Regras Obrigatórias do Compilador

O compilador deve:

1. Garantir coerência total com SFF original
2. Gerar prev/next determinísticos
3. Calcular rank global e por lane
4. Calcular profundidade de branch
5. Calcular métricas futuras
6. Classificar edges
7. Definir prioridade determinística
8. Preencher layout_hints
9. Calcular stats globais
10. Não deixar campos implícitos

---

# 9. O que NÃO pode existir no cpff

* Campos não determinísticos
* Valores dependentes de layout engine específico
* Informações visuais finais (coordenadas x/y)
* Dados redundantes não derivados do SFF

---

# 10. Impacto Arquitetural

Pipeline final:

1. Ler `.sff`
2. Validar estrutura
3. Compilar grafo base
4. Expandir contexto (cpff)
5. Export/render consome apenas cpff

---

# 11. Benefícios Estratégicos

* Renderizador vira módulo simples
* Blueprint futuro fica trivial
* Integração externa possível
* Testabilidade estrutural aumentada
* Escalabilidade do engine
* Determinismo absoluto

---

# 12. Versionamento

Sempre que um campo estrutural for alterado:

* Incrementar versão do cpff
* Manter compatibilidade reversa quando possível
* Registrar alteração em changelog

---

# 13. Conclusão

O cpff é o “esqueleto completo” do fluxo.

Ele transforma:

* Conexões implícitas → Relações explícitas
* Estrutura narrativa → Estrutura matemática
* Heurística reativa → Sistema determinístico
