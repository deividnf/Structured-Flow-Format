
# Task — Correção Definitiva do Layout TB/LR (Modelo BPMN Clássico)

## Status
🔄 Em implementação

---

# 1. Objetivo

Corrigir o algoritmo de layout para garantir que:

- O fluxo siga padrão BPMN clássico.
- Lanes fiquem “grudadas” (sem corredores gigantes).
- O eixo principal do fluxo seja respeitado.
- Trocas de lane não causem teleporte visual.
- O layout seja determinístico.
- O SVG gerado seja consistente com o modelo lógico.

Esta task corrige o **motor de layout**, não apenas o export SVG.

---

# 2. Regra Arquitetural Fundamental

## 2.1 Direção TB (Top → Bottom)

- O eixo do fluxo é **Y** (rank_global).
- Lanes devem ser **colunas verticais lado a lado** (offset no eixo X).
- Lanes NÃO alteram Y.
- O fluxo principal ocupa `col_index = 0`.
- Branches ocupam `col_index = ±1` (máximo ±2 se colisão).

### Fórmulas (TB)

```text
node_y = TOP_PADDING + (rank_global * RANK_GAP)

lane_x_offset[lane] = cumulative_lane_width(previous_lanes) + LANE_GAP

node_x = lane_x_offset[lane]
         + LANE_PADDING
         + lane_inner_center_x
         + (col_index * COL_GAP)
````

---

## 2.2 Direção LR (Left → Right)

* O eixo do fluxo é **X** (rank_global).
* Lanes devem ser **linhas horizontais empilhadas** (offset no eixo Y).
* Lanes NÃO alteram X.
* O fluxo principal ocupa `row_index = 0`.
* Branches ocupam `row_index = ±1`.

### Fórmulas (LR)

```text
node_x = LEFT_PADDING + (rank_global * RANK_GAP)

lane_y_offset[lane] = cumulative_lane_height(previous_lanes) + LANE_GAP

node_y = lane_y_offset[lane]
         + LANE_PADDING
         + lane_inner_center_y
         + (row_index * ROW_GAP)
```

---

# 3. Parâmetros Fixos (MVP)

| Parâmetro    | Valor Sugerido |
| ------------ | -------------- |
| LANE_GAP     | 16–24          |
| LANE_PADDING | 24             |
| LANE_HEADER  | 32             |
| RANK_GAP     | 130–160        |
| COL_GAP      | 220–260        |
| ROW_GAP      | 220–260        |
| NODE_W       | 220            |
| NODE_H       | 64             |
| START_END_R  | 26             |

---

# 4. Regras Obrigatórias

## 4.1 Lanes “Grudadas”

* LANE_GAP deve ser pequeno.
* O espaçamento grande deve existir apenas **dentro da lane (padding)**.
* Em TB: todas as lanes devem ter a mesma altura (altura total do fluxo).
* Em LR: todas as lanes devem ter a mesma largura (largura total do fluxo).

---

## 4.2 Eixo Principal

* TB: col_index=0 é eixo principal.
* LR: row_index=0 é eixo principal.
* Todas as decisões devem tentar manter-se próximas do eixo.

---

## 4.3 Branches Compactos

* Decision true → +1
* Decision false → -1
* Só expandir para ±2 se houver colisão detectada.

---

## 4.4 Troca de Lane Sem Teleporte

Quando um edge cruza lane A → lane B:

* TB: herdar `col_index` se não definido.
* LR: herdar `row_index` se não definido.

Isso garante continuidade visual.

---

## 4.5 Routing Ortogonal

* Linhas sempre 90°.
* Preferir rota curta.
* Evitar corredor externo.
* Máximo 2 colunas/linhas laterais além do extremo.

---

## 4.6 Texto e Títulos

### Nodes

* Texto centralizado.
* Wrap automático.
* Máx largura = NODE_W - 24.

### Start/End

Se label > 12 caracteres ou múltiplas linhas:

* Texto fora do círculo/pill (à direita em TB e LR).

### Títulos de Lane

* Devem respeitar largura útil da lane.
* Aplicar wrap ou truncamento com reticências.

---

# 5. SVG – Auto Size Obrigatório

Após posicionamento:

1. Calcular bbox global:

   * nodes
   * labels
   * edges
   * headers

2. Definir:

```text
width  = (maxX - minX) + PADDING
height = (maxY - minY) + PADDING
viewBox = "minX-PADDING minY-PADDING width height"
```

Nenhum elemento pode ser cortado.

---

# 6. Validações Obrigatórias

## 6.1 Validação TB (Multilane)

Rodar:

```bash
python -m core.cli export data/example/checkout_flow.sff --format svg
```

Validar visualmente:

* [ ] Lanes lado a lado (user | system | gateway).
* [ ] Fluxo descendo em Y.
* [ ] Trocas de lane com deslocamento pequeno.
* [ ] Sem corredor gigante vazio.
* [ ] Branches próximas ao eixo principal.

---

## 6.2 Validação TB (Decision)

* [ ] Branch true e false em ±1 coluna.
* [ ] Decision centralizada.
* [ ] Linhas ortogonais.

---

## 6.3 Validação LR

Criar ou usar fluxo LR:

* [ ] Lanes empilhadas verticalmente.
* [ ] Fluxo avançando no eixo X.
* [ ] Branches ±1 linha.
* [ ] Sem afastamento exagerado.

---

# 7. Logs Obrigatórios

### INFO

* direction
* lane_offsets
* rank_global por node
* col_index/row_index por node
* bbox por lane
* bbox global

### WARN

* colisão → expandiu ±2
* label externo aplicado
* truncamento de texto

### ERROR

* node sem lane
* routing impossível
* rank inconsistente

---

# 8. Critérios de Aceite (DoD)

* [ ] TB usa lanes como colunas (offset X).
* [ ] LR usa lanes como linhas (offset Y).
* [ ] Lanes grudadas (gap pequeno).
* [ ] Fluxo principal centralizado.
* [ ] Branches compactos (±1).
* [ ] Troca de lane herda coluna/linha.
* [ ] SVG sem corte (viewBox correto).
* [ ] Logs completos.
* [ ] Determinismo garantido.

---

# 9. Resultado Esperado

Após esta correção:

* O fluxo terá aparência BPMN clássica.
* Lanes não estarão afastadas.
* Não haverá corredor gigante.
* O layout será previsível e auditável.
* O motor estará preparado para PDF sem distorção.
