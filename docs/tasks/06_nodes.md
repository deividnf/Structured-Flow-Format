
# Fase Visual 02 — Inserção de Nodes nas Lanes (Sem Routing Avançado)

## Status
🔄 Em implementação

---

# 1. Objetivo

Após a Fase 01 (lanes-only), agora o motor deve:

- Inserir nodes dentro das lanes corretamente
- Respeitar direction (TB / LR)
- Centralizar o fluxo principal
- Adaptar automaticamente o tamanho das lanes conforme necessidade
- Manter layout limpo e previsível
- NÃO implementar routing complexo ainda

> Nesta fase, o foco é posicionamento estrutural dos nodes.
> Edges podem ser ignoradas ou desenhadas de forma simples (reta básica).

---

# 2. Pré-condição Obrigatória

A Fase 01 deve estar 100% validada:

- Lanes corretas
- Títulos corretos
- viewBox correto
- Lanes grudadas

Se Fase 01 falhar, esta fase NÃO deve ser iniciada.

---

# 3. Conceito Estrutural

## 3.1 Separação de Responsabilidade

- Lanes definem regiões.
- Nodes ocupam posições dentro dessas regiões.
- Direction define eixo principal.
- Lane NÃO define avanço temporal.

---

# 4. Regras de Posicionamento por Direção

---

## 4.1 direction = TB (Fluxo vertical)

### Eixo principal
- Rank_global define avanço em Y.
- Y cresce para baixo.

### Lanes
- Lanes são colunas verticais lado a lado.
- Offset em X apenas.

### Colunas internas (col_index)
- Fluxo principal: col_index = 0
- Branch true: +1
- Branch false: -1
- Máximo ±2 se colisão

### Cálculo

```text
node_y = TOP_PADDING + (rank_global * RANK_GAP)

node_x = lane_x_offset[lane]
         + LANE_PADDING
         + (LANE_BODY_W / 2)
         + (col_index * COL_GAP)
````

---

## 4.2 direction = LR (Fluxo horizontal)

### Eixo principal

* Rank_global define avanço em X.
* X cresce para direita.

### Lanes

* Lanes são linhas horizontais empilhadas.
* Offset em Y apenas.

### Linhas internas (row_index)

* Fluxo principal: row_index = 0
* Branch true: +1
* Branch false: -1

### Cálculo

```text
node_x = LEFT_PADDING + (rank_global * RANK_GAP)

node_y = lane_y_offset[lane]
         + LANE_PADDING
         + (LANE_BODY_H / 2)
         + (row_index * ROW_GAP)
```

---

# 5. Regras de Adaptação Automática (Essencial)

Nesta fase começa a adaptação real do layout.

## 5.1 Adaptação Horizontal (TB)

Se um node usar col_index ±1 ou ±2:

* A largura da lane deve expandir automaticamente.
* LANE_BODY_W deve se ajustar para comportar:

  * (máximo col_index absoluto * COL_GAP * 2)
  * * NODE_W
  * * LANE_PADDING * 2

## 5.2 Adaptação Vertical (LR)

Se row_index expandir:

* LANE_BODY_H deve se ajustar automaticamente.
* Mesmo princípio aplicado verticalmente.

---

# 6. Centralização do Fluxo

Mesmo com branches:

* O eixo principal (col_index=0 ou row_index=0)
  deve permanecer centralizado visualmente dentro da lane.

Isso significa:

* Após calcular largura final da lane,
  recalcular centro interno da lane antes de desenhar nodes.

---

# 7. Texto dos Nodes

## 7.1 Process / Delay / Decision

* Texto centralizado
* Wrap automático
* Nunca ultrapassar NODE_W - 24

## 7.2 Start / End

Se label > 12 caracteres ou multi-linha:

* Texto fora do shape (lado direito no TB)
* Evitar deformar círculo

---

# 8. SVG Ajustes

Após inserir nodes:

1. Recalcular bbox global
2. Ajustar viewBox
3. Garantir que nenhuma parte seja cortada

---

# 9. O que NÃO fazer nesta fase

* Não implementar routing ortogonal completo
* Não otimizar cruzamento de edges
* Não fazer PDF
* Não mexer na CLI nativa
* Não fazer batch

---

# 10. Validações Obrigatórias

## 10.1 TB — Fluxo Simples

* [ ] Nodes centralizados
* [ ] Fluxo descendo
* [ ] Lanes coladas
* [ ] Sem desalinhamento

## 10.2 TB — Com Decision

* [ ] Branch ±1 coluna
* [ ] Lane expande automaticamente
* [ ] Eixo principal continua central

## 10.3 LR — Fluxo Horizontal

* [ ] Nodes avançando no eixo X
* [ ] Lanes empilhadas
* [ ] Branch ±1 linha

---

# 11. Logs Obrigatórios

### INFO

* direction
* rank_global por node
* col_index/row_index por node
* largura/altura final de cada lane
* bbox global final

### WARN

* colisão detectada → expandiu ±2
* label externo aplicado

### ERROR

* node sem lane
* rank inválido
* lane inexistente

---

# 12. Critérios de Aceite (DoD)

* [ ] Nodes posicionados corretamente dentro das lanes
* [ ] Lanes adaptam tamanho automaticamente
* [ ] Fluxo principal centralizado
* [ ] direction TB e LR funcionando
* [ ] SVG auto-size correto
* [ ] Sem corredores gigantes
* [ ] Logs completos
* [ ] Determinismo garantido

---

# 13. Resultado Esperado

Após esta fase:

* O diagrama já terá forma real de fluxograma
* Lanes corretas
* Nodes corretamente distribuídos
* Layout previsível e estável
* Base sólida para implementar routing ortogonal real (Fase 03)
