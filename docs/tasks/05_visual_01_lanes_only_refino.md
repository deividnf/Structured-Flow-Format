
# Fase Visual 01 — Refino BPMN das Lanes (Sem Gap + Retângulos Retos)

## Status
🧱 Refinamento da base visual (lane-only)

---

## 1. Objetivo

Ajustar o render LANE-ONLY para ficar com aparência BPMN clássica:

- Lanes totalmente coladas (sem margem/gap entre elas)
- Bordas retas (sem arredondamento)
- Aparência de “um retângulo único” dividido em faixas
- Mesma dimensão no eixo fixo:
  - direction=TB → todas as lanes com a MESMA LARGURA
  - direction=LR → todas as lanes com a MESMA ALTURA

> Ainda não desenhar nodes/edges/routing. Apenas lanes.

---

## 2. Regras Obrigatórias

### 2.1 Lanes coladas (zero gap)
- `LANE_GAP` deve ser **0** entre lanes.
- O espaço deve existir somente como **PADDING externo do canvas**, não entre lanes.

✅ Correto:
- Uma lane encosta na outra sem nenhum espaço.

❌ Errado:
- “Cards” separados com margem.

---

### 2.2 Bordas retas
- Proibido usar `rx/ry` em `<rect>` das lanes.
- Resultado: cantos retos.

> Se existir arredondamento hoje, remover.

---

### 2.3 Dimensão fixa no eixo correto

#### direction=TB
- Lanes empilhadas verticalmente (uma embaixo da outra)
- Todas têm a **MESMA LARGURA TOTAL**
- Altura pode ser fixa nesta fase (ex.: LANE_H), mas deve ser igual entre lanes.

#### direction=LR
- Lanes lado a lado horizontalmente (colunas)
- Todas têm a **MESMA ALTURA TOTAL**
- Largura pode ser fixa nesta fase (ex.: LANE_W), mas deve ser igual entre lanes.

---

### 2.4 Conjunto único (“container”)
Além de desenhar as lanes, desenhar um “container” externo:

- Um único retângulo externo envolvendo todas as lanes (borda leve).
- Dentro dele, as lanes ficam divididas.

Isso reforça visualmente “um único bloco”.

---

## 3. Estrutura Visual da Lane (TB)

### 3.1 Layout TB (BPMN)
- Lane = retângulo horizontal
- Título:
  - Uma barra fixa à esquerda (`TITLE_BAR_W`)
  - Texto rotacionado verticalmente dentro dessa barra

**Sem arredondamento, sem gap.**

---

## 4. Estrutura Visual da Lane (LR)

### 4.1 Layout LR (BPMN)
- Lane = retângulo vertical (coluna)
- Título:
  - Barra fixa no topo (`TITLE_BAR_H`)
  - Texto horizontal (sem rotação)

**Sem arredondamento, sem gap.**

---

## 5. Parâmetros Fixos (MVP)

- `CANVAS_PADDING = 24`
- `LANE_GAP = 0`  ✅ obrigatório
- `TITLE_BAR = 56`
- `LANE_BODY_W = 900`
- `LANE_BODY_H = 240`
- `CONTAINER_BORDER = 1` (ou leve)
- `LANE_BORDER = 1` (ou leve)

---

## 6. Cálculo de Tamanho (Sem Gap)

### 6.1 direction=TB
- `lane_width = TITLE_BAR + LANE_BODY_W`
- `lane_height = LANE_BODY_H`
- `total_height = (N_lanes * lane_height) + 2*CANVAS_PADDING`
- `total_width  = lane_width + 2*CANVAS_PADDING`

### 6.2 direction=LR
- `lane_width = LANE_BODY_W`
- `lane_height = TITLE_BAR + LANE_BODY_H`
- `total_width  = (N_lanes * lane_width) + 2*CANVAS_PADDING`
- `total_height = lane_height + 2*CANVAS_PADDING`

---

## 7. Validações Obrigatórias

### 7.1 Validação Visual (TB)
Rodar:
```bash
python -m core.cli export exemplo/checkout_flow.sff --format svg --lanes-only
````

Checklist:

* [ ] Não existe espaço entre lanes (LANE_GAP=0)
* [ ] Bordas retas (sem arredondamento)
* [ ] Todas as lanes têm a mesma largura
* [ ] O conjunto parece um único retângulo dividido
* [ ] Títulos na esquerda, rotacionados

---

### 7.2 Validação Visual (LR)

Alterar direction para LR em um exemplo e rodar:

```bash
python -m core.cli export exemplo/<arquivo_LR>.sff --format svg --lanes-only
```

Checklist:

* [ ] Não existe espaço entre lanes (LANE_GAP=0)
* [ ] Bordas retas
* [ ] Todas as lanes têm a mesma altura
* [ ] O conjunto parece um único retângulo dividido
* [ ] Títulos no topo, horizontais

---

## 8. Logs Obrigatórios

* INFO: direction, qtd_lanes, lane_width/lane_height, total_width/total_height
* INFO: retângulo container (x,y,w,h)
* ERROR: direction inválida
* ERROR: lanes vazias / order duplicado

---

## 9. Critério de Aceite (DoD)

* [ ] LANE_GAP=0 aplicado
* [ ] Sem arredondamento
* [ ] Dimensão fixa correta (TB largura / LR altura)
* [ ] Container único desenhado
* [ ] Títulos posicionados e orientados corretamente
* [ ] SVG com viewBox correto, sem cortes
* [ ] Logs completos