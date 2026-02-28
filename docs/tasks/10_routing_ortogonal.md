# Task 10 — Routing Ortogonal (Linhas) por Grid + Portas (v1)

## Objetivo
Desenhar as conexões (edges) entre nodes no SVG usando **linhas ortogonais** (apenas segmentos retos + curvas em 90°), respeitando:

- Direction do fluxo (`TB` ou `LR`)
- Rank e Track já calculados
- Lanes e seus limites (manter as linhas “dentro” da lane quando possível)
- Evitar atravessar shapes (no mínimo: não passar por dentro do bbox dos nodes)
- Labels de branches (true/false) posicionados no primeiro segmento horizontal/vertical

**Importante:** v1 não precisa otimizar cruzamentos ao máximo. Precisa ser **determinístico e legível**.

---

## Pré-requisitos (obrigatórios antes do routing)
1) Cada node já tem:
   - `lane_id`
   - `rank_global`
   - `track`
   - `x, y` (centro do node) e `bbox` (xmin,ymin,xmax,ymax)

2) Lanes já têm:
   - bbox (xmin,ymin,xmax,ymax)
   - header bbox (para evitar linhas passando por cima do título)

3) Grid configurado:
   - `GRID_X`, `GRID_Y`
   - `RANK_GAP`, `TRACK_GAP`

---

## Conceitos chave

### 1) Portas (anchors)
Cada node possui portas de entrada/saída (pontos onde linhas conectam).

Para TB:
- saída padrão: `BOTTOM_CENTER`
- entrada padrão: `TOP_CENTER`

Para LR:
- saída padrão: `RIGHT_CENTER`
- entrada padrão: `LEFT_CENTER`

Nodes “end” só têm entrada.
Nodes “start” só têm saída.

### 2) Waypoints (pontos intermediários)
Cada edge vira uma sequência de pontos:
`(x1,y1) -> (x2,y2) -> ... -> (xn,yn)`
Todos os segmentos devem ser ortogonais.

### 3) Snap obrigatório
Cada waypoint deve ser snapado ao grid:
- x múltiplo de GRID_X
- y múltiplo de GRID_Y

---

## Regras de roteamento (v1)

## Regra A — Edge dentro da mesma lane (mais simples)
### A1) TB (top->bottom)
source bottom -> target top:

1) p1 = saída do source (BOTTOM_CENTER)
2) p2 = (p1.x, mid_y)
3) p3 = (p_target.x, mid_y)
4) p4 = entrada do target (TOP_CENTER)

Onde `mid_y` deve ser:
- pelo menos `max(p1.y, p_target.y) - (RANK_GAP/2)` se o target estiver abaixo
- ou `p1.y + (RANK_GAP/2)` garantindo espaço

### A2) LR (left->right)
source right -> target left:

1) p1 = saída (RIGHT_CENTER)
2) p2 = (mid_x, p1.y)
3) p3 = (mid_x, p_target.y)
4) p4 = entrada (LEFT_CENTER)

Onde `mid_x` deve ser:
- `p1.x + (RANK_GAP/2)` no mínimo

---

## Regra B — Edge entre lanes diferentes
A linha precisa sair da lane do source e entrar na lane do target com um “corredor” neutro.

### B1) TB
- Saia pelo BOTTOM_CENTER do source
- Vá até uma “faixa de transição” em y (transit_y) que esteja:
  - abaixo do source bbox
  - acima do target bbox (se target abaixo)
- Cruze horizontalmente para x do target
- Desça até o TOP_CENTER do target

### B2) LR
- Saia pelo RIGHT_CENTER
- Vá até transit_x (à direita do source bbox)
- Cruze verticalmente para y do target
- Vá para LEFT_CENTER do target

---

## Regra C — Branches de Decision
Decision (losango) precisa distribuir saídas em direções diferentes, usando track.

### C1) TB
Decision normalmente aponta para baixo.
Se tiver branches `true/false`:

- Branch principal (ex: true) vai para `track +1` (direita)
- Branch secundário (false) vai para `track -1` (esquerda)

Routing recomendado:
1) sair do BOTTOM_CENTER do decision
2) descer um pouco até `y = decision.bottom + PAD`
3) ir horizontalmente até o x do target (que já foi definido por track)
4) descer até target TOP_CENTER

### C2) LR
Decision aponta para direita.
Branches dividem em Y:

1) sair do RIGHT_CENTER
2) ir até `x = decision.right + PAD`
3) mover verticalmente até y do target
4) ir até target LEFT_CENTER

---

## Anti-colisão (v1)
### Objetivo mínimo:
Linhas não podem passar dentro do bbox dos nodes.

### Estratégia v1:
Antes de aceitar um segmento (ponto A -> ponto B):

1) construir bbox do segmento (retângulo fino)
2) verificar interseção com bbox de qualquer node (exceto source/target)
3) se colidir:
   - desviar usando um offset de track (corredor lateral)

#### Desvio TB
Se segmento horizontal colide:
- aumentar `mid_y` em +GRID_Y*2 (ou -GRID_Y*2 se possível)

Se segmento vertical colide:
- deslocar `x` para `x + GRID_X*2` (ou -)

#### Desvio LR
Se segmento vertical colide:
- aumentar `mid_x` em +GRID_X*2
Se segmento horizontal colide:
- deslocar `y` em +GRID_Y*2

**Limite:** até 10 tentativas. Depois: ERROR + abort.

---

## Ordenação de desenho (reduz poluição visual)
1) Desenhar lanes
2) Desenhar edges (linhas)
3) Desenhar nodes (por cima das linhas)
4) Desenhar labels (por cima)

Assim as linhas ficam atrás dos nodes.

---

## Labels de edges (true/false)
Se edge tem label:

- TB: renderizar label perto do primeiro segmento horizontal (p2->p3)
- LR: renderizar label perto do primeiro segmento vertical (p2->p3)

Regras:
- offset de 6~10px do segmento
- nunca dentro de bbox do node
- snap em grid opcional (não obrigatório)

---

## Logs obrigatórios
### INFO
- [ROUTE_EDGE] edge_id=..., from=..., to=..., pts=N

### WARN
- [ROUTE_DETOUR] edge_id=..., reason=bbox_collision, tries=k

### ERROR
- [ROUTE_FAIL] edge_id=..., reason=unresolvable_collision

---

## Como validar (smoke tests)
### Caso 1 — checkout_flow (TB)
- linhas descendo do start -> process -> decision
- branches indo para lados diferentes (true/false)
- nenhuma linha atravessando nodes

### Caso 2 — test_lr_dag (LR)
- linhas indo esquerda->direita
- branch vertical em Y se existir decision

### Caso 3 — collision stress
- 2 decisões próximas, 3 branches cada
- garante que o detour acontece e fica legível

---

## Critério de Aceite (DoD)
- [ ] Linhas ortogonais (90°) para todos edges
- [ ] Respeita TB/LR para lanes e nodes
- [ ] Usa portas corretas (top/bottom ou left/right)
- [ ] Sem linhas passando dentro de nodes
- [ ] Labels de true/false visíveis e fora das formas
- [ ] Logs de roteamento por edge
- [ ] Pipeline determinístico: mesmo input → mesmo SVG

---

## Fora de escopo (por enquanto)
- Minimização avançada de cruzamentos
- Bundling de linhas
- Roteamento “por canal” (edge channels por track)
- PDF export