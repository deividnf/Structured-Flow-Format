# Correção Definitiva do Layout TB/LR (Modelo BPMN Clássico)

## Status
✅ Implementação concluída

---

# 1. Objetivo

O algoritmo de layout foi corrigido para garantir:
- Fluxo BPMN clássico
- Lanes "grudadas" (sem corredores gigantes)
- Eixo principal do fluxo respeitado
- Trocas de lane sem teleporte visual
- Layout determinístico
- SVG consistente com o modelo lógico

---

# 2. Regra Arquitetural Fundamental

## 2.1 Direção TB (Top → Bottom)
- Eixo do fluxo: **Y** (rank_global)
- Lanes: **colunas verticais lado a lado** (offset X)
- Lanes NÃO alteram Y
- Fluxo principal: `col_index = 0`
- Branches: `col_index = ±1` (máximo ±2 se colisão)

### Fórmulas (TB)
```
node_y = TOP_PADDING + (rank_global * RANK_GAP)
lane_x_offset[lane] = cumulative_lane_width(previous_lanes) + LANE_GAP
node_x = lane_x_offset[lane] + LANE_PADDING + lane_inner_center_x + (col_index * COL_GAP)
```

## 2.2 Direção LR (Left → Right)
- Eixo do fluxo: **X** (rank_global)
- Lanes: **linhas horizontais empilhadas** (offset Y)
- Lanes NÃO alteram X
- Fluxo principal: `row_index = 0`
- Branches: `row_index = ±1`

### Fórmulas (LR)
```
node_x = LEFT_PADDING + (rank_global * RANK_GAP)
lane_y_offset[lane] = cumulative_lane_height(previous_lanes) + LANE_GAP
node_y = lane_y_offset[lane] + LANE_PADDING + lane_inner_center_y + (row_index * ROW_GAP)
```

---

# 3. Parâmetros Fixos (MVP)
| Parâmetro    | Valor Utilizado |
| ------------ | -------------- |
| LANE_GAP     | 16             |
| LANE_PADDING | 24             |
| LANE_HEADER  | 32             |
| RANK_GAP     | 130            |
| COL_GAP      | 220            |
| ROW_GAP      | 220            |
| NODE_W       | 220            |
| NODE_H       | 64             |
| START_END_R  | 26             |

---

# 4. Regras Obrigatórias

## 4.1 Lanes “Grudadas”
- LANE_GAP pequeno
- Espaçamento grande apenas dentro da lane (padding)
- TB: todas as lanes mesma altura
- LR: todas as lanes mesma largura

## 4.2 Eixo Principal
- TB: col_index=0
- LR: row_index=0
- Decisões próximas ao eixo

## 4.3 Branches Compactos
- Decision true → +1
- Decision false → -1
- Só expandir para ±2 se colisão

## 4.4 Troca de Lane Sem Teleporte
- TB: herda col_index
- LR: herda row_index

## 4.5 Routing Ortogonal
- Linhas 90°
- Rota curta
- Máximo ±2 colunas/linhas laterais

## 4.6 Texto e Títulos
- Nodes: texto centralizado, wrap automático
- Start/End: texto externo se >12 caracteres
- Títulos de lane: wrap/truncamento

---

# 5. SVG – Auto Size Obrigatório
- Bbox global: nodes, labels, edges, headers
- width = (maxX - minX) + PADDING
- height = (maxY - minY) + PADDING
- viewBox = "minX-PADDING minY-PADDING width height"
- Nenhum elemento cortado

---

# 6. Validações Obrigatórias

## 6.1 TB (Multilane)
- Lanes lado a lado
- Fluxo descendo em Y
- Trocas de lane com deslocamento pequeno
- Sem corredor vazio
- Branches próximas ao eixo

## 6.2 TB (Decision)
- Branches ±1 coluna
- Decision centralizada
- Linhas ortogonais

## 6.3 LR
- Lanes empilhadas
- Fluxo avançando em X
- Branches ±1 linha
- Sem afastamento exagerado

---

# 7. Logs Obrigatórios
- INFO: direction, lane_offsets, rank_global, col_index/row_index, bbox por lane, bbox global
- WARN: colisão ±2, label externo, truncamento
- ERROR: node sem lane, routing impossível, rank inconsistente

---

# 8. Critérios de Aceite (DoD)
- TB: lanes como colunas
- LR: lanes como linhas
- Lanes grudadas
- Fluxo principal centralizado
- Branches compactos
- Troca de lane herda coluna/linha
- SVG sem corte
- Logs completos
- Determinismo garantido

---

# 9. Resultado Esperado
- Aparência BPMN clássica
- Lanes próximas
- Sem corredor gigante
- Layout previsível e auditável
- Pronto para exportação PDF sem distorção
