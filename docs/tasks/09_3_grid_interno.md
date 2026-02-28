# Task 09.3 — Grid Interno (Eixos/Tracks) + Snap + Colisão Real + Auto-Resize

## Contexto (por que essa task existe)
Depois da correção do rank (09.2), o fluxo passou a ter progressão correta:

- ranks consistentes e determinísticos ✅
- detecção de ciclo/DAG ✅

Mas ainda existem problemas de **layout fino**:

1) **Grid/Tracks não estão sendo respeitados** (nodes “soltos” dentro das lanes)  
2) **Tamanho do diagrama (SVG) não se ajusta bem ao conteúdo** (muito vazio ou comprimido)  
3) **Colisão visual** (formas e textos encostando/colidindo)  
4) **Branches** não ocupam eixos laterais de maneira consistente (track 0/±1/±2…)  
5) **Sem “reserva de espaço” por rank e por track** (o diagrama não cria um “slot” por posição)

Objetivo: tornar o posicionamento **estritamente baseado em slots** (rank x track) e garantir:
- sem sobreposição de shapes
- sem sobreposição de textos
- layout alinhado ao grid
- lanes e canvas dimensionados automaticamente

---

## Objetivo (o que deve mudar)
Implementar um sistema de posicionamento por **grade interna (subgrid)**:

- Dentro de cada lane existem **tracks (eixos)**: `0, +1, -1, +2, -2, ...`
- O fluxo principal usa `track = 0`
- Branches usam tracks laterais (ex: true → +1, false → -1)
- Cada node ocupa um **slot único**: `(lane_id, rank, track)`
- Não é permitido dois nodes no mesmo slot
- Todo `x,y` deve ser derivado do slot e depois “snapado” ao grid final

---

## Definições
### Rank
Eixo de progressão do fluxo:
- TB: rank ↑ controla Y (top→bottom)
- LR: rank ↑ controla X (left→right)

### Track
Eixo transversal dentro da lane:
- TB: track controla X (esquerda↔direita dentro da lane)
- LR: track controla Y (cima↔baixo dentro da lane)

### Slot
Chave de posição:
`slot = (lane_id, rank, track)`

---

## Regras de Layout (Fonte de verdade)

### Regra 1 — Rank sempre vem primeiro
- Rank é calculado antes de qualquer track/posicionamento.
- Se algum node não tem rank: ERROR + abort.

### Regra 2 — Track 0 é o eixo principal
- Se não houver decisão/branch, tudo fica em `track=0`.

### Regra 3 — Branches ocupam tracks laterais (simétrico)
Ordem padrão para distribuir branches:
1) +1
2) -1
3) +2
4) -2
...

### Regra 4 — Um slot não pode ter 2 nodes
Se existir colisão de slot, deve ocorrer realocação automática de track.

---

## Parte A — “Subgrid” de verdade (slots)
### A1) Estrutura occupied
Criar e usar obrigatoriamente:

- `occupied_slots[(lane_id, rank, track)] = node_id`
- `occupied_bboxes = [(node_id, bbox)]` para colisão geométrica final

### A2) Política de alocação do slot
Quando for posicionar um node com rank conhecido:

1) definir `track_preferido`
2) se slot já ocupado, procurar track livre na sequência:
   `0, +1, -1, +2, -2, +3, -3...`
3) fixar o primeiro track livre
4) registrar WARN quando realocar

> Importante: essa colisão é **por slot**, não por bbox.

---

## Parte B — Snap ao Grid (sem quebrar o slot)
Hoje o “snap” parece estar “puxando” nodes para posições que colidem.
A regra correta é:

1) calcular `x,y` a partir do slot (rank+track)
2) snapar para grid
3) revalidar colisão geométrica (bbox) pós-snap

### B1) Grid recomendado
- GRID_X = 20 ou 40
- GRID_Y = 20 ou 24

Snap:
- `x = round(x / GRID_X) * GRID_X`
- `y = round(y / GRID_Y) * GRID_Y`

### B2) Regra crítica
**Nunca** snapar de um jeito que faça dois nodes caírem no mesmo slot.
Se isso acontecer, ajustar:
- aumentar GAP
- ou recalcular track
- ou aplicar um “micro-offset” fixo por track (mantendo alinhamento)

---

## Parte C — Espaçamento (evitar “achatamento” e “vazio gigante”)
O layout precisa de gaps coerentes com as dimensões das formas.

### C1) Dimensões base
Definir dimensões por tipo:
- process: `NODE_W`, `NODE_H`
- decision: `DIAMOND_W`, `DIAMOND_H`
- start/end: `CIRCLE_D`

### C2) GAP mínimo automático (por segurança)
Para TB:
- `RANK_GAP >= max(NODE_H, DIAMOND_H, CIRCLE_D) + 80`
Para LR:
- `RANK_GAP >= max(NODE_W, DIAMOND_W, CIRCLE_D) + 80`

Para tracks:
- `TRACK_GAP >= max(NODE_W, DIAMOND_W, CIRCLE_D) + 60` (TB)
- `TRACK_GAP >= max(NODE_H, DIAMOND_H, CIRCLE_D) + 60` (LR)

> Isso evita nodes encostarem mesmo com textos.

---

## Parte D — Colisão geométrica real (bbox)
Mesmo com slots, texto e formas podem colidir se:
- labels longos
- shapes diferentes
- snap agressivo

### D1) BBOX por node (mínimo)
Calcular bbox aproximado:
- process bbox = retângulo + padding
- decision bbox = bounding box do losango + padding
- circle bbox = circ + padding
- texto bbox = estimativa `len(chars) * font_size * 0.6`

### D2) Política: BBOX nunca sobrepõe
Após posicionar todos nodes (pós-snap):

1) detectar interseções bbox
2) para cada colisão:
   - priorizar mover no eixo do track (não no rank)
   - se não resolver, empurrar rank para frente (promover rank do node colidido)
3) registrar WARN em cada resolução
4) se exceder N tentativas, ERROR + abort (evitar loop infinito)

> Importante: esse “empurrar rank” deve preservar DAG visual (não pode voltar).

---

## Parte E — Auto-Resize do SVG e das Lanes
### E1) Canvas deve se basear no conteúdo real
Calcular bounding box global:
- min_x, min_y, max_x, max_y considerando **todos nodes + labels + lane headers**
Aplicar padding:
- `PAD = 80` (mínimo)

SVG final:
- width = (max_x - min_x) + PAD*2
- height = (max_y - min_y) + PAD*2
- viewBox = (min_x - PAD, min_y - PAD, width, height)

### E2) Lanes devem ser uniformes
Independentemente do conteúdo:
- TB: todas lanes têm a **mesma largura**
- LR: todas lanes têm a **mesma altura**

Como calcular:
- encontrar lane_content_size máximo (considerando tracks)
- aplicar em todas

---

## Parte F — Regras de Texto (não quebrar forma)
### F1) Texto dentro da forma (regra padrão)
- process: texto sempre dentro, quebrado em linhas
- decision: texto dentro (menor), se não couber → texto fora (top ou bottom)
- start/end: preferir texto fora (acima/abaixo) quando longo

### F2) Auto-wrap obrigatório
Se texto exceder a largura:
- quebrar em N linhas com max chars por linha
- recalcular bbox do texto

---

## Logs obrigatórios
### INFO
- [RANK_ASSIGN] (já existe)
- [TRACK_ASSIGN] (já existe)
- [SLOT_ASSIGN] node_id=..., lane=..., rank=..., track=...
- [GRID] rank_gap=..., track_gap=..., grid=(x,y)
- [CANVAS] bbox=(minx,miny,maxx,maxy) width=... height=...

### WARN
- [SLOT_COLLISION] slot ocupado → realocando track
- [BBOX_COLLISION] bbox intersect → ajustando track/rank
- [TEXT_WRAP] label quebrado em N linhas

### ERROR (abort)
- [UNRANKED_NODE] node sem rank
- [UNRESOLVED_COLLISION] colisão sem resolução após N tentativas
- [INVALID_LAYOUT_STATE] slot duplicado detectado no final

---

## Plano de Implementação (incremental)
### Etapa 1 — Slot-first (obrigatório)
- Implementar occupied_slots
- Garantir que nenhum slot repete

### Etapa 2 — GAP automático + Snap
- Ajustar rank_gap/track_gap baseado em shape max
- Aplicar snap e revalidar

### Etapa 3 — BBOX collision resolver
- Implementar bbox aproximado
- Resolver colisões pós-snap

### Etapa 4 — Auto-resize do SVG + uniformização das lanes
- Canvas baseado em bbox real
- Lanes uniformes por direction

---

## Como validar (Checklist rápido)
### Visual
- [ ] Fluxo progride corretamente (TB: topo→baixo / LR: esquerda→direita)
- [ ] Branches realmente vão para eixos laterais (track ±1, ±2…)
- [ ] Nenhum shape encosta em outro
- [ ] Nenhum texto sai parcialmente para fora (exceto regra de start/end e fallback de decision)
- [ ] Lanes do mesmo tamanho
- [ ] Canvas se ajusta ao conteúdo (sem “gigante vazio” e sem “corte”)

### Log
- [ ] Existem logs [SLOT_ASSIGN] para todos nodes
- [ ] Não existe slot duplicado
- [ ] Se houve realocação: aparece WARN [SLOT_COLLISION] ou [BBOX_COLLISION]
- [ ] [CANVAS] mostra width/height coerentes

### Casos de teste mínimos
- checkout_flow.sff (TB)
- test_lr_dag.sff (LR)
- um fluxo com 2 decisões em sequência (gera tracks ±2)
- um fluxo com labels longos (força wrap / texto fora)

---

## Fora de escopo (ainda não)
- Routing ortogonal (linhas)
- Minimização de cruzamentos
- PDF export
- CLI nativa
- Viewer web

---

## Critério de aceite (DoD)
- [ ] Slot-first funcionando (sem duplicidade de slot)
- [ ] Branches usam tracks laterais corretamente
- [ ] Snap não gera colisão
- [ ] Resolver de colisão bbox funciona (sem shapes sobrepostos)
- [ ] SVG auto-resize baseado em bbox real
- [ ] Lanes uniformes e alinhadas ao direction
- [ ] Logs completos (INFO/WARN/ERROR) para auditoria
