
# Fase Visual 01 — Renderização das Lanes (Boxes/Baias) com Títulos

## Status
🧱 Base visual (lane-only) — prioridade máxima

---

## 1. Objetivo

Implementar um modo de exportação **LANE-ONLY** para SVG, capaz de desenhar **somente as lanes (boxes/baias)** com:

- Layout correto por direção (TB/LR)
- Títulos posicionados no “começo” da lane
- Título rotacionado quando aplicável
- Lanes “grudadas” com gap pequeno
- Canvas auto-ajustável (viewBox correto)
- Logs claros e validação via terminal

> Nesta fase, NÃO desenhar nodes, edges, textos de nodes, routing, ou qualquer elemento do fluxo.
> O foco é: **desenhar as faixas corretamente**.

---

## 2. Definições

### 2.1 O que é uma Lane
Uma lane é uma “baia” (box/faixa) que delimita uma área visual do diagrama.  
Cada lane tem:
- `id`
- `title`
- `order`

A ordem visual deve respeitar `lane.order`.

---

## 3. Regra de Orientação (validação obrigatória)

Antes de desenhar qualquer coisa, o motor deve validar:

- Se `direction = TB` → o fluxo cresce verticalmente.
- Se `direction = LR` → o fluxo cresce horizontalmente.

**Mas nesta fase** não desenhamos o fluxo; usamos `direction` para definir a orientação das lanes.

---

## 4. Layout das Lanes por Direção

### 4.1 Caso A — Lanes Horizontais (empilhadas) + Título Vertical na esquerda

**Quando usar:** `direction = TB` (padrão mais comum para fluxos que descem)

- As lanes são faixas horizontais **uma embaixo da outra**
- Todas têm a **mesma largura**
- O título da lane fica no **início da faixa (lado esquerdo)**
- O título fica **rotacionado (vertical)** para parecer BPMN:
  - texto “em pé”, lendo de baixo para cima ou de cima para baixo (definir 1 padrão)

**Estrutura visual:**
- Uma coluna “header” fixa à esquerda (faixa do título)
- Um corpo da lane à direita (área vazia nesta fase)

Exemplo mental:
```

[ Título (vertical) ] [                Lane body                ]
[ Título (vertical) ] [                Lane body                ]
[ Título (vertical) ] [                Lane body                ]

```

### 4.2 Caso B — Lanes Verticais (lado a lado) + Título Horizontal no topo

**Quando usar:** `direction = LR` (fluxo que cresce para a direita)

- As lanes são colunas verticais **lado a lado**
- Todas têm a **mesma altura**
- O título fica no **topo** (horizontal, sem rotação)
- Cada lane tem um header superior (faixa do título) e um corpo abaixo

Exemplo mental:
```

+---------+ +---------+ +---------+
| title   | | title   | | title   |
|         | |         | |         |
|  body   | |  body   | |  body   |
+---------+ +---------+ +---------+

```

---

## 5. Geometria (MVP com tamanhos fixos)

Nesta fase, o tamanho pode ser fixo (não depende de nodes):

### Parâmetros (recomendado)
- `LANE_GAP = 10 ~ 18` (bem pequeno: lanes “grudadas”)
- `PADDING = 24`
- `TITLE_BAR = 56` (barra onde fica o título na esquerda/topo)
- `LANE_BODY_W = 900` (largura do corpo — fixa por enquanto)
- `LANE_BODY_H = 240` (altura do corpo — fixa por enquanto)

### Tamanho por direção

#### direction=TB (lanes empilhadas)
- `lane_width = TITLE_BAR + LANE_BODY_W`
- `lane_height = LANE_BODY_H`
- `total_height = N_lanes * lane_height + (N_lanes-1)*LANE_GAP + 2*PADDING`
- `total_width  = lane_width + 2*PADDING`

#### direction=LR (lanes lado a lado)
- `lane_width = LANE_BODY_W`
- `lane_height = TITLE_BAR + LANE_BODY_H`
- `total_width  = N_lanes * lane_width + (N_lanes-1)*LANE_GAP + 2*PADDING`
- `total_height = lane_height + 2*PADDING`

---

## 6. Regras do Título

### 6.1 direction=TB (título vertical na esquerda)
- O texto deve ficar dentro da barra esquerda (`TITLE_BAR`)
- Rotação obrigatória:
  - `transform="rotate(-90 ...)"` (ou +90, mas escolher 1 padrão)
- Centralizar no meio da barra

### 6.2 direction=LR (título horizontal no topo)
- Texto dentro da barra superior (`TITLE_BAR`)
- Sem rotação
- Alinhado à esquerda com padding pequeno, ou centralizado (definir 1 padrão)

### 6.3 Títulos grandes
Se o título for grande:
- Permitir wrap simples (quebrar em 2 linhas) OU truncar com reticências
- Mas nunca ultrapassar a barra do título

---

## 7. SVG obrigatório (auto-size correto)

O export deve gerar SVG com:
- `width` e `height` coerentes
- `viewBox` coerente
- Sem “espremer” conteúdo

> Nesta fase, como tudo é fixo, o bbox é simples e previsível.

---

## 8. CLI / Export

Adicionar um modo de exportação de lanes:

### Opção 1 (recomendada)
- `python -m core.cli export <file> --format svg --lanes-only`

### Opção 2
- `python -m core.cli lanes <file>`

Escolher apenas **uma** e documentar no README.

---

## 9. Validações (obrigatórias)

### 9.1 Validação Visual TB
1) Use um .sff com 3 lanes (user/system/gateway)
2) Execute `lanes-only`
3) Confirmar:
- [ ] Lanes empilhadas (uma embaixo da outra)
- [ ] Títulos na esquerda
- [ ] Títulos rotacionados verticalmente
- [ ] Lanes grudadas (gap pequeno)
- [ ] SVG com viewBox correto

### 9.2 Validação Visual LR
1) Crie/edite um .sff com `direction=LR`
2) Execute `lanes-only`
3) Confirmar:
- [ ] Lanes lado a lado
- [ ] Títulos no topo (horizontal)
- [ ] Gap pequeno entre lanes
- [ ] SVG com viewBox correto

### 9.3 Logs
- [ ] INFO com direction + quantidade de lanes + dimensões finais
- [ ] INFO com posição e tamanho de cada lane
- [ ] ERROR se direction inválida
- [ ] ERROR se lanes vazias ou order duplicado

---

## 10. Critérios de Aceite

A fase está concluída quando:

- [ ] `lanes-only` gera SVG correto em TB
- [ ] `lanes-only` gera SVG correto em LR
- [ ] Títulos estão no lugar certo (esquerda/topo)
- [ ] Rotação está correta quando TB
- [ ] Lanes ficam grudadas (sem corredores)
- [ ] viewBox/auto-size corretos
- [ ] logs claros e rastreáveis
- [ ] README atualizado com comandos e exemplos

---

## 11. Próxima Fase (não implementar agora)

Somente após lanes estarem perfeitas:
- Posicionar nodes dentro das lanes
- Centralizar fluxo
- Routing ortogonal
- Export PDF

Foco atual: **LANES, somente LANES.**
