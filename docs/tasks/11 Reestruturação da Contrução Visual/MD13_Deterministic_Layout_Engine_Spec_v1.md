# 📘 MD13 — Especificação Oficial do Engine de Layout Determinístico

## Sugestão de título do arquivo:

`MD13_Deterministic_Layout_Engine_Spec_v1.md`

---

# Deterministic Layout Engine — Especificação Formal v1.0

---

# 1. Objetivo

O **Layout Engine Determinístico** é responsável por transformar um `.cff` válido em uma estrutura geométrica pronta para renderização.

Ele:

* Não interpreta regras de negócio.
* Não calcula métricas estruturais.
* Não recompila grafo.
* Não toma decisões baseadas em heurística ambígua.

Ele apenas:

> Converte estrutura matemática explícita (CFF) em geometria visual determinística.

---

# 2. Princípios Fundamentais

1. Zero sobreposição
2. Zero cruzamento
3. Zero paralelo colado
4. Expansão dinâmica de espaço
5. Determinismo absoluto
6. Clareza > Compactação

Mesmo `.cff` → Mesmo layout geométrico.

---

# 3. Entrada Oficial

Entrada única:

```
.cff
```

Campos obrigatórios utilizados:

* nodes[].rank
* nodes[].links
* nodes[].branch_context
* nodes[].future_metrics
* nodes[].layout_hints
* edges[].classification
* edges[].priority
* lanes[].tracks_total
* lanes[].center_track

Se qualquer campo obrigatório estiver ausente → erro fatal.

---

# 4. Pipeline Oficial do Layout Engine

---

## Etapa 1 — Inicialização da Grade

Para cada lane:

Criar:

* Eixo central
* Tracks invisíveis (mínimo 13 por padrão)
* Espaçamento base fixo

### Modelo inicial:

* track_gap = constante
* center_track = definido no CFF
* track_index ∈ [1..tracks_total]

Nenhuma compressão automática permitida.

---

## Etapa 2 — Posicionamento Base dos Nós

Regras:

* rank.global define progressão principal (vertical ou horizontal)
* rank.lane define posição dentro da lane
* main_path ocupa center_track

Para cada node:

```
x = lane_offset + track_offset
y = rank.global * rank_gap
```

Sem exceções.

---

## Etapa 3 — Reserva de Corredores (Backbone Allocation)

Antes de desenhar qualquer edge:

Criar estrutura:

```
occupancy_map:
  - H segments
  - V segments
```

Cada segmento registrado com:

* coordenada fixa
* intervalo variável
* owner_edge_id

---

## Etapa 4 — Ordem de Roteamento

Edges devem ser roteadas nesta ordem:

1. main_path
2. branch com maior future_steps
3. branch com menor future_steps
4. cross_lane
5. return
6. join

Se houver empate → ordenar por ID.

---

## Etapa 5 — Modelo de Roteamento Ortogonal

Formato padrão:

### TB (top-bottom)

```
V → H → V
```

### LR (left-right)

```
H → V → H
```

Nenhum outro padrão permitido na v1.0.

---

## Etapa 6 — Sistema de Tracks

Cada edge deve ocupar:

* Um track de saída
* Um corredor intermediário
* Um track de chegada

Tracks são exclusivos.

Se conflito:

→ tentar próximo track livre
→ se todos ocupados → expandir lane

Nunca reduzir espaçamento.

---

## Etapa 7 — Regras Absolutas de Conflito

Proibido:

* Segmento H sobre outro H no mesmo y
* Segmento V sobre outro V no mesmo x
* Cruzamento H-V
* Segmento dentro de bounding box de node
* Segmento dentro de bounding box de label
* Distância menor que min_separation

Se ocorrer conflito:

→ tentar novo track
→ se falhar → expandir lane
→ recalcular

---

## Etapa 8 — Expansão Dinâmica de Lane

Quando expansão for necessária:

* tracks_total += 2 (um acima e um abaixo)
* recalcular posições
* reiniciar roteamento

Sem limite fixo.

---

## Etapa 9 — Branch Direction Intelligence

Branch direction deve considerar:

* future_steps
* cross_lane_ahead
* branch_depth

Regra base:

* Branch longa tende ao lado interno
* Branch curta tende ao lado externo
* Branch que muda de lane tende ao lado mais próximo da lane destino

Nunca usar regra fixa de “true direita / false esquerda”.

---

## Etapa 10 — Last Mile Strategy

Edges longas:

1. Entram em backbone (corredor)
2. Percorrem backbone
3. Aproximam-se do nó apenas no trecho final

Evitar múltiplas curvas intermediárias.

---

## Etapa 11 — Determinismo

O layout engine deve:

* Ordenar sempre por prioridade e ID
* Nunca usar random
* Nunca usar estado global externo
* Produzir mesmo layout para mesma entrada

---

# 5. Estrutura de Saída

Output do engine:

```
layout_result = {
  nodes: {
    id: {
      x,
      y,
      width,
      height
    }
  },
  edges: {
    id: {
      points: [(x1,y1),(x2,y2),(x3,y3),(x4,y4)]
    }
  },
  lanes: {
    id: {
      x_start,
      x_end,
      tracks_total
    }
  }
}
```

Sem lógica adicional.

---

# 6. O que NÃO pertence ao Layout Engine

* Cálculo de main_path
* Cálculo de future_steps
* Classificação de edge.kind
* Regras de negócio
* Validação estrutural

Tudo isso já pertence ao compilador (MD12).

---

# 7. Garantias Formais

Após execução:

* Nenhuma linha se sobrepõe
* Nenhuma linha cruza
* Nenhuma linha toca bounding box
* Todos os nós possuem posição
* Todas as edges possuem rota válida

Se não for possível → erro explícito:

```
LAYOUT_IMPOSSIBLE_WITH_CURRENT_GRID
```

---

# 8. Complexidade Adaptativa

O layout deve:

* Expandir quando necessário
* Nunca compactar automaticamente
* Priorizar legibilidade sobre tamanho

---

# 9. Versão

Qualquer alteração estrutural no algoritmo:

→ Incrementar versão
→ Registrar breaking changes

---

# 10. Conclusão

O Layout Engine Determinístico é:

* Mecânico
* Formal
* Matemático
* Previsível
* Escalável

Ele transforma CFF em geometria clara, sem heurística improvisada.
