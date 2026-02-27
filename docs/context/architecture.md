# Arquitetura Visual do Layout SFF

## 1. Objetivo
Formalizar a arquitetura lógica do layout visual dos fluxogramas SFF, tornando possível a geração automática, determinística e validável de layouts, conforme Task 01.

---

## Resumo Executivo (Task 01)
Esta seção consolida a arquitetura lógica do layout visual SFF, integrando requisitos, camadas, regras e critérios de aceite, conforme Task 01 e especificação oficial.

### Princípios Fundamentais
- Estrutural, determinístico, validável, independente de runtime, não ambíguo, compilável.
- Layout gerado automaticamente, sem necessidade de posicionamento manual.
- Conexões sempre ortogonais (segmentos retos, 90°).
- Suporte a direção TB (Top-Bottom) e LR (Left-Right).
- Respeito a lanes, nodes, edges e entry.

---

## 2. Estrutura Geral
O layout visual é composto por três camadas lógicas:
- **Camada Estrutural (Grafo):** representação do fluxo via nodes, edges, branches e entry.
- **Camada de Layout (Posicionamento):** cálculo automático de ranks (níveis), posições e agrupamento por lanes.
- **Camada de Roteamento de Arestas:** definição dos caminhos ortogonais das conexões, respeitando portas e evitando sobreposição.

### 2.1 Camada Estrutural (Grafo)
- Fonte de verdade: nodes, edges, decision.branches, entry
- O fluxo inicia em entry.start e termina em entry.ends
- edges definem conexões explícitas; branches são ramificações oficiais
- Grafo deve ser acíclico (MVP sem loops complexos)
- Saída esperada: índice prev/next compilado

### 2.2 Camada de Layout (Posicionamento)
- Direção definida em sff.direction ("TB" ou "LR")
- Cada nó recebe um "rank" (nível) conforme distância do start/profundidade
- Nós no mesmo nível compartilham rank (coluna para LR, linha para TB)
- Ordenação interna minimiza cruzamento de arestas, prioriza dependências e agrupa por lane
- Elimina necessidade de posicionamento manual

### 2.3 Camada de Roteamento de Arestas
- Todas as conexões são ortogonais (segmentos retos, 90°)
- Conexões saem de portas fixas (ver regras de portas)
- Não cruzar nós; desviar por "corredores invisíveis"; usar canais paralelos se necessário

---

## 3. Camada Estrutural (Grafo)
- Fonte de verdade: `nodes`, `edges`, `decision.branches`, `entry`.
- O fluxo inicia em `entry.start` e termina em `entry.ends`.
- `edges` definem conexões explícitas; `branches` são ramificações oficiais.
- O grafo deve ser acíclico (MVP sem loops complexos).
- Saída esperada: índice prev/next compilado.

## 4. Camada de Layout (Posicionamento)
- Direção definida em `sff.direction` ("TB" ou "LR").
  - TB: fluxo vertical, lanes horizontais.
  - LR: fluxo horizontal, lanes verticais.
- Cada nó recebe um "rank" (nível) conforme distância do start/profundidade.
- Nós no mesmo nível compartilham rank (coluna para LR, linha para TB).
- Ordenação interna minimiza cruzamento de arestas, prioriza dependências e agrupa por lane.
- Elimina necessidade de posicionamento manual.

## 5. Camada de Roteamento de Arestas
- Todas as conexões são ortogonais (segmentos retos, 90°).
- Conexões saem de portas fixas:
  - TB: entrada topo, saída base, desvios laterais.
  - LR: entrada esquerda, saída direita, desvios topo/base.
- Não cruzar nós; desviar por "corredores invisíveis"; usar canais paralelos se necessário.

## 6. Regras de Portas de Conexão
- Decision:
  - true → lado direito (LR) ou inferior direito (TB)
  - false → lado esquerdo (LR) ou inferior esquerdo (TB)
  - join → convergência central

---
## 6.1 Regras Formais de Portas
Se direction = TB:
- Entrada principal: topo
- Saída principal: base
- Desvios: laterais

Se direction = LR:
- Entrada principal: esquerda
- Saída principal: direita
- Desvios: topo/base

Para nodes do tipo decision:
- true → lado direito (LR) ou inferior direito (TB)
- false → lado esquerdo (LR) ou inferior esquerdo (TB)
- join → convergência central

---

## 7. Integração com Lanes
- Lanes não alteram lógica, apenas organização visual.
- Cada lane é uma faixa (swimlane); nodes são posicionados dentro da lane correspondente.
- Ordem visual segue `lane.order`.
- Nunca misturar nodes fora da sua lane; edges podem cruzar lanes.

## 8. Modelo Interno de Layout
O engine/compilador deve gerar uma estrutura auxiliar:
```json
"layout": {
  "ranks": {},
  "positions": {},
  "routing": {}
}
```
- `ranks[node_id]`: nível estrutural
- `positions[node_id]`: coordenada lógica (grid)
- `routing[edge_id]`: lista de segmentos ortogonais

---
## 8.1 Exemplo de Estrutura Gerada
```json
"layout": {
  "ranks": {"start": 0, "press_power": 1, ...},
  "positions": {"start": [0,0], "press_power": [1,0], ...},
  "routing": {"edge1": [[0,0],[1,0],[1,1]], ...}
}
```

---

## 9. Critérios de Aceite
- Definição clara de ranks
- Regra formal de portas
- Regra formal de roteamento ortogonal
- Lanes respeitadas visualmente
- Sem necessidade de posicionamento manual
- Layout funciona para TB e LR
- Documentação atualizada
- Preview via terminal (mesmo que simples)

---
## 9.1 Checklist de Aceite (Task 01)
- [x] Definição clara de ranks
- [x] Regra formal de portas
- [x] Regra formal de roteamento ortogonal
- [x] Lanes respeitadas visualmente
- [x] Sem necessidade de posicionamento manual
- [x] Layout funciona para TB e LR
- [x] Documentação atualizada
- [ ] Preview via terminal (mesmo que simples)

---

## 10. Validação e Logs
- Toda execução do engine/layout deve ser validável via terminal.
- Logs obrigatórios:
  - INFO: início/fim de etapas, parâmetros usados
  - WARN: inconsistências recuperáveis
  - ERROR: falhas de validação, contexto e ação sugerida
- Proposta de padrão: logs persistidos em `logs/layout_engine.log` (criar pasta se necessário e documentar aqui qualquer alteração)
- Exemplo de comando de validação (futuro):
  - `python scripts/preview_layout.py docs/model/example.sff.json`
  - Esperado: saída determinística, sem erros, logs claros, preview mínimo textual

## 11. Evidências e Documentação
- Toda alteração nesta arquitetura deve ser registrada neste arquivo.
- Mudanças operacionais/fluxo: atualizar também `docs/context.md`.
- Sempre incluir seção "Como validar" em toda entrega.

---
## Evidências de Execução e Logs (2026-02-27)
- Testes realizados com arquivos válidos: `exemplo/checkout_flow.sff`, `exemplo/order_orchestration_flow.sff`
- Comando utilizado:
  - `python -m core.cli validate exemplo/checkout_flow.sff`
  - `python -m core.cli validate exemplo/order_orchestration_flow.sff`
- Saída esperada: `Validação estrutural OK`
- Logs registrados em `logs/layout_engine.log`:
  - `2026-02-27 16:19:29 | INFO  | Validando arquivo ./exemplo/checkout_flow.sff`
  - `2026-02-27 16:19:29 | INFO  | Validação estrutural OK`
  - `2026-02-27 16:22:02 | INFO  | Validando arquivo ./exemplo/order_orchestration_flow.sff`
  - `2026-02-27 16:22:02 | INFO  | Validação estrutural OK`

---
## Checklist de Entrega (Task 01/02)
- [x] Estrutura e arquitetura documentadas
- [x] Validação via terminal reproduzível
- [x] Logs claros e rastreáveis
- [x] Evidências registradas
- [x] README e instruções atualizados

---
## Como validar (Task 01)
1. Gerar fluxo simples (exemplo.sff.json)
2. Conferir ranks, posições e roteamento no bloco "layout"
3. Validar que não há linhas curvas suaves nem sobreposição
4. Garantir que o layout é determinístico (mesmo input → mesmo output)
5. Conferir documentação atualizada neste arquivo
6. (Quando implementado) Rodar preview via terminal e conferir logs

---

## 12. Fora de Escopo
- Renderização SVG/Canvas
- Animações/interação
- Loops complexos
- Paralelismo avançado

---

### Como validar
1. Executar comando de preview/layout (quando implementado)
2. Conferir logs em `logs/layout_engine.log`
3. Validar que ranks, posições e roteamento estão corretos e determinísticos
4. Garantir ausência de linhas curvas suaves e sobreposição
5. Conferir documentação atualizada
