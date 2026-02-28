
# Task 09 — Eixos Internos por Lane (Tracks) para Suporte a Branches e Paralelismo

## Status
🔄 Em implementação

---

# 1. Objetivo

Introduzir o conceito de **eixos internos (tracks)** dentro das lanes para permitir:

- Suporte organizado a decisões (branches)
- Suporte a múltiplos caminhos paralelos
- Posicionamento determinístico sem sobreposição
- Layout previsível e estável
- Expansão futura para routing ortogonal

Esta task resolve o problema de "nodes flutuando" e elimina desalinhamentos em fluxos com múltiplas escolhas.

---

# 2. Conceito Arquitetural

## 2.1 Separação de Eixos

O layout passa a ter dois eixos:

### Eixo Principal (Rank)
Define progressão do fluxo.

- direction = TB → rank controla Y
- direction = LR → rank controla X

### Eixo Secundário (Track)
Define deslocamento interno dentro da lane para suportar:

- Branches
- Paralelismo
- Anti-colisão

---

# 3. Estrutura de Dados Nova

Cada node passa a ter:

```json
{
  "id": "node_id",
  "lane": "lane_id",
  "rank": 3,
  "track": 0
}
````

Onde:

* rank = ordem topológica global
* track = deslocamento interno relativo ao eixo central

---

# 4. Regras de Atribuição de Track

## 4.1 Regra Base

Todo fluxo começa com:

```
track = 0
```

Track 0 representa o eixo central da lane.

---

## 4.2 Regras para Decision

Quando um node do tipo decision gerar branches:

### Branch primário:

* Herda track do decision

### Branch alternativo:

* Recebe track lateral

Ordem sugerida:

```
primeiro branch → +1
segundo branch → -1
terceiro branch → +2
quarto branch → -2
```

Sempre manter simetria.

---

## 4.3 Herança de Track

Nodes subsequentes dentro de um branch:

```
node.track = parent.track
```

Até convergir novamente no fluxo principal.

---

## 4.4 Convergência

Quando múltiplos branches convergirem:

* Novo node volta para `track = 0`
* Ou mantém track dominante (configurável no futuro)

Para esta fase, retornar para 0.

---

# 5. Cálculo de Coordenadas

## 5.1 direction = LR

```
x = LEFT_PADDING + (rank * RANK_GAP)

y = lane_center_y
    + (track * TRACK_GAP)
```

## 5.2 direction = TB

```
y = TOP_PADDING + (rank * RANK_GAP)

x = lane_center_x
    + (track * TRACK_GAP)
```

---

# 6. Parâmetros Recomendados

* RANK_GAP = 200 (LR)
* RANK_GAP = 120 (TB)
* TRACK_GAP = 90
* GRID_X = 40
* GRID_Y = 24

Aplicar snap-to-grid:

```
x = round(x / GRID_X) * GRID_X
y = round(y / GRID_Y) * GRID_Y
```

---

# 7. Anti-colisão Obrigatório

Se dois nodes tiverem:

```
mesmo rank
mesma lane
mesmo track
```

Aplicar realocação:

1. Testar track +1
2. Testar track -1
3. Testar +2
4. Testar -2

Registrar log WARN.

---

# 8. Expansão Dinâmica da Lane

A altura (LR) ou largura (TB) da lane deve expandir para acomodar:

```
max(abs(track)) * TRACK_GAP
```

Todas as lanes devem adotar o maior valor necessário (uniformização).

---

# 9. Logs Obrigatórios

## INFO

* direction
* rank e track por node
* lane_center_x/y
* TRACK_GAP aplicado

## WARN

* colisão detectada
* realocação de track

## ERROR

* node sem lane
* rank inválido
* track não resolvido após tentativa

---

# 10. Validação

## 10.1 Caso simples (sem decision)

Checklist:

* [ ] Todos nodes com track = 0
* [ ] Fluxo alinhado perfeitamente
* [ ] Sem deslocamento lateral

## 10.2 Caso com decision simples

Checklist:

* [ ] Decision no track central
* [ ] Branch lateral ocupa +1 ou -1
* [ ] Convergência retorna ao centro
* [ ] Sem sobreposição

## 10.3 Caso com múltiplas decisões

Checklist:

* [ ] Tracks simétricos
* [ ] Lanes expandem adequadamente
* [ ] Layout permanece legível

---

# 11. Fora de Escopo

* Routing ortogonal
* Minimização de cruzamentos
* Edge labels
* Export PDF
* CLI nativa

---

# 12. Critério de Aceite (DoD)

* [ ] Track implementado
* [ ] Branches posicionados corretamente
* [ ] Sem nodes sobrepostos
* [ ] Lanes ajustam tamanho automaticamente
* [ ] Layout determinístico
* [ ] Logs completos
* [ ] SVG íntegro

---

# 13. Próxima Task

Task 10 — Routing Ortogonal Inteligente baseado em Rank + Track
