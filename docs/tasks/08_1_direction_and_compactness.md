
# Ajuste 1 — Lanes seguindo a mesma direção dos nodes

### O que mudar no motor

* O layout das lanes deve ser função direta de `direction`:

  * TB → offset no **Y** (stack vertical)
  * LR → offset no **X** (stack horizontal)

E o fluxo (nodes) também:

* TB → avanço no **Y**
* LR → avanço no **X**

Isso garante coerência mental e visual.

---

# Ajuste 2 — Distância exagerada (padding/gaps)

Hoje seu SVG está com “vazios” gigantes. Isso é tuning de parâmetros + regra de “conteúdo define tamanho”.

### Regra recomendada (MVP)

* `LANE_GAP`: **0** ou no máximo **8**
* `CANVAS_PADDING`: **16–24**
* `LANE_PADDING`: **16–24**
* `RANK_GAP` (distância entre passos do fluxo):

  * TB: **90–130**
  * LR: **160–220** (porque horizontal costuma precisar mais espaço pro texto)
* `NODE_GAP` (dentro da lane):

  * **40–70**

E principalmente:
✅ **Lane não deve ter tamanho fixo gigante**.
Ela deve ter tamanho mínimo + expansão baseada no bbox dos nodes (quando a fase já inclui nodes).

---

# Arquivo .md (Task 08.1 — “Direção Consistente + Compactação”)

Salva como: `docs/tasks/08_1_direction_and_compactness.md`

````md
# Task 08.1 — Direção Consistente (Nodes + Lanes) + Compactação de Espaços

## Status
🔄 Em implementação

---

# 1. Objetivo

Corrigir o comportamento de direção para que **lanes e nodes sigam a mesma orientação** e reduzir os espaços excessivos, tornando o diagrama compacto e legível.

---

# 2. Regra Única de Direção (Obrigatória)

## 2.1 direction = TB
- Nodes avançam de **cima para baixo** (Y aumenta).
- Lanes são **horizontais empilhadas** (offset no Y).
- Ordem das lanes respeita `lane.order`.

## 2.2 direction = LR
- Nodes avançam da **esquerda para a direita** (X aumenta).
- Lanes são **verticais lado a lado** (offset no X).
- Ordem das lanes respeita `lane.order`.

> Lanes e nodes DEVEM sempre obedecer a mesma direction.
> Proibido: TB com lanes em colunas ou LR com lanes empilhadas.

---

# 3. Compactação (reduzir “vazios”)

## 3.1 Parâmetros recomendados (MVP)
- CANVAS_PADDING: 16–24
- LANE_GAP: 0–8
- LANE_PADDING: 16–24
- TITLE_BAR: 48–56
- NODE_GAP: 40–70
- RANK_GAP:
  - TB: 90–130
  - LR: 160–220

## 3.2 Regra de tamanho das lanes
- Na fase com nodes:
  - calcular bbox dos nodes por lane
  - lane size = bbox + LANE_PADDING*2 + área do título (TITLE_BAR)
- Uniformização (se mantida):
  - todas as lanes adotam o maior tamanho necessário entre elas
  - mas sem inflar além do bbox real (evitar “tamanho fixo gigante”)

---

# 4. Validações Obrigatórias

## 4.1 TB (checkout_flow)
Comando:
```bash
python -m core.cli export import/checkout_flow.sff --format svg
````

Checklist:

* [ ] Lanes empilhadas (uma embaixo da outra)
* [ ] Nodes descendo em Y
* [ ] Espaços internos ok, sem vazios gigantes
* [ ] Sem corte no SVG (viewBox correto)

## 4.2 LR (exemplo)

Comando:

```bash
python -m core.cli export import/<arquivo_lr>.sff --format svg
```

Checklist:

* [ ] Lanes lado a lado (colunas)
* [ ] Nodes avançando em X
* [ ] Diagrama compacto

---

# 5. Logs Obrigatórios

INFO:

* direction
* lane stacking mode (TB=stackY / LR=stackX)
* parâmetros finais aplicados (gap/padding/rank_gap)
* bbox global

WARN:

* ajuste de compactação aplicado
* overflow evitado

ERROR:

* direction inválida
* lanes vazias

---

# 6. Critério de Aceite (DoD)

* [ ] TB: lanes empilhadas + nodes descendo
* [ ] LR: lanes lado a lado + nodes avançando
* [ ] Sem espaçamentos exagerados
* [ ] SVG sem corte e legível
* [ ] Logs claros

````

---

## Prompt curtinho pro agente executar a Task 08.1

```text
Corrigir direction para que lanes e nodes obedeçam a mesma orientação:

- direction=TB: lanes empilhadas (offset Y) + nodes avançam em Y
- direction=LR: lanes lado a lado (offset X) + nodes avançam em X

Depois, compactar espaços:
- reduzir LANE_GAP para 0–8
- reduzir LANE_PADDING para 16–24
- ajustar RANK_GAP (TB 90–130, LR 160–220)
- evitar lane size fixo gigante; usar bbox dos nodes + padding

Validar com checkout_flow TB e um exemplo LR. Garantir viewBox correto e logs INFO com direction e parâmetros.
