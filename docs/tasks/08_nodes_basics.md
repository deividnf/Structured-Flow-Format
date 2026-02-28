
# Task 08 — Nodes Básicos nas Lanes (Sem Sobreposição) + Texto Assertivo + Lanes Uniformes

## Status
🔄 Em implementação

---

# 1. Objetivo

Evoluir a renderização para incluir **nodes dentro das lanes** com qualidade mínima de leitura, garantindo:

- Lanes uniformes (todas do mesmo tamanho)
- Posicionamento básico dos nodes (fluxo linear + decisões) sem sobreposição
- Textos sempre legíveis e “dentro da forma” quando aplicável
- Regra de texto externo apenas para start/end quando necessário
- SVG auto-size correto (sem cortes)

> Nesta task ainda NÃO é necessário implementar routing ortogonal completo.
> Linhas podem ser ignoradas nesta fase.

---

# 2. Pré-requisitos

- Task 07 concluída (export salva em data/export/ por padrão, viewBox correto, UTF-8 OK, lanes-only funciona)
- Lanes renderizadas sem gap e com bordas retas (BPMN-like)

---

# 3. Regras Obrigatórias

## 3.1 Lanes Uniformes (todas do mesmo tamanho)

Independente de direção, **todas as lanes devem ter o mesmo tamanho** dentro do diagrama.

### direction=TB (lanes empilhadas)
- Todas devem ter a **mesma largura total**
- Todas devem ter a **mesma altura total**
- A altura final da lane = a MAIOR altura necessária entre todas

### direction=LR (lanes lado a lado)
- Todas devem ter a **mesma altura total**
- Todas devem ter a **mesma largura total**
- A largura final da lane = a MAIOR largura necessária entre todas

> Em outras palavras: se 1 lane “crescer” para caber nodes, todas crescem junto para manter padronização visual.

---

## 3.2 Posicionamento Básico de Nodes (sem edges)

### Regra base
- Nodes devem avançar na sequência do fluxo:
  - TB: avançar da **esquerda para a direita** dentro da lane (por enquanto)
  - LR: avançar de **cima para baixo** dentro da lane (por enquanto)

> Observação: nesta task, a prioridade é evitar sobreposição e garantir leitura.
> O mapeamento perfeito de ranks globais entra na próxima task.

### Espaçamento mínimo
- Deve existir um `NODE_GAP` fixo entre nodes (ex.: 60px).
- Nenhum node pode ocupar o mesmo `x,y` de outro.

---

## 3.3 Regra Anti-sobreposição (obrigatória)

### 3.3.1 Nenhum node pode ter posição idêntica
- Ao calcular posição, validar:
  - Se `(x,y)` já foi usado → deslocar para o próximo slot disponível.

### 3.3.2 Regras especiais para Decision
- Node tipo decision nunca pode ficar no mesmo ponto de outro node.
- Se ocorrer colisão:
  - deslocar horizontalmente (TB) ou verticalmente (LR) até ficar livre.
- Branches (true/false) devem ocupar slots diferentes do decision.

---

## 3.4 Texto Assertivo (dentro das formas)

### 3.4.1 Regra geral (process/decision/delay)
- Texto deve estar **dentro da forma**.
- Implementar wrap com `tspan`.
- Centralizar o bloco de texto.

### 3.4.2 Start/End — exceção de texto externo
Se o texto for grande:
- Não “estourar” o círculo/pill.
- Colocar label **fora da forma**, mas seguindo esta regra:

**Posição do texto externo (start/end):**
- Por padrão: acima (`top`)
- Se houver colisão com outro elemento: abaixo (`bottom`)

> Não colocar o texto externo na esquerda/direita por enquanto.
> Apenas “superior ou inferior” para padronizar.

---

# 4. Tamanhos Mínimos (MVP)

- NODE_W = 220
- NODE_H = 64
- START_END_R = 26
- DECISION_SIZE = 90
- NODE_GAP = 60
- LANE_PADDING = 24
- TITLE_BAR = 56
- CANVAS_PADDING = 24

---

# 5. Adaptação de Tamanho das Lanes (uniformização)

1) Calcular a área necessária para os nodes dentro de cada lane:
   - min/max X/Y dos nodes
2) Calcular o tamanho mínimo da lane para conter seus nodes + padding
3) Encontrar:
   - max_lane_width (entre todas as lanes)
   - max_lane_height (entre todas as lanes)
4) Aplicar para todas as lanes:
   - lane_width = max_lane_width
   - lane_height = max_lane_height

---

# 6. Validações Obrigatórias

## 6.1 TB — checkout_flow
Gerar SVG:

```bash
python -m core.cli export data/input/checkout_flow.sff --format svg
````

Checklist:

* [ ] Lanes têm o mesmo tamanho (todas iguais)
* [ ] Nodes não se sobrepõem
* [ ] Decisions não colidem com outros nodes
* [ ] Texto dentro das formas (exceto start/end com label externo top/bottom)
* [ ] Nada cortado (viewBox OK)

---

## 6.2 LR — exemplo simples

Criar 1 arquivo LR e repetir checklist.

---

# 7. Logs Obrigatórios

### INFO

* direction
* lane size final aplicada (width/height)
* posição final dos nodes (id → x,y)
* bbox global

### WARN

* colisão detectada e resolvida (id A vs id B)
* texto movido para fora (start/end)

### ERROR

* node sem lane
* falha em encontrar slot livre (deve ser muito raro)

---

# 8. Critério de Aceite (DoD)

* [ ] Lanes uniformes em TB e LR
* [ ] Nodes sem sobreposição
* [ ] Decision nunca colide
* [ ] Texto assertivo dentro das formas
* [ ] Start/end com label externo top/bottom quando necessário
* [ ] Export gera SVG íntegro (viewBox correto)
* [ ] Logs completos e úteis

---

# 9. Fora de Escopo (não fazer nesta task)

* Routing ortogonal avançado
* Minimização de cruzamentos
* Export PDF
* Batch export
* CLI nativa
