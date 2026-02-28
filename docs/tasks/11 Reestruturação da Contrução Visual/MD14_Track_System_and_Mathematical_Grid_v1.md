# 📘 MD14 — Especificação Oficial do Sistema de Tracks e Grid Matemático

## Sugestão de título do arquivo:

`MD14_Track_System_and_Mathematical_Grid_v1.md`

---

# Track System & Mathematical Grid — Especificação Formal v1.0

---

# 1. Objetivo

O **Sistema Oficial de Tracks e Grid Matemático** define a base geométrica sobre a qual o Layout Engine opera.

Ele formaliza:

* Como lanes são estruturadas internamente
* Como tracks são distribuídas
* Como ocorre expansão dinâmica
* Como corredores são reservados
* Como manter separação absoluta entre edges

Este documento é a base matemática do layout determinístico definido no MD13.

---

# 2. Princípio Estrutural Fundamental

Cada lane é um sistema fechado com:

* Um eixo central
* Trilhas paralelas numeradas
* Espaçamento constante
* Crescimento simétrico

Nenhuma linha pode existir fora de uma track.

---

# 3. Estrutura Base da Lane

Cada lane contém:

```text
center_track
tracks_total
track_gap
track_index ∈ [1..tracks_total]
```

---

# 4. Modelo Inicial Oficial

### 4.1 Tracks iniciais

Por padrão:

```text
tracks_total = 13
center_track = 7
```

Distribuição:

* 6 tracks acima do centro
* 6 tracks abaixo do centro

---

# 5. Sistema de Coordenadas

Para layout TB (top-bottom):

```text
y = rank.global * rank_gap
x = lane_start + (track_index - center_track) * track_gap
```

Para layout LR (left-right):

```text
x = rank.global * rank_gap
y = lane_start + (track_index - center_track) * track_gap
```

---

# 6. Reservas de Tracks

Cada segmento ortogonal ocupa:

* 1 track fixa (H ou V)
* 1 intervalo variável

O occupancy_map armazena:

```text
(H, y_track) → intervalos ocupados
(V, x_track) → intervalos ocupados
```

Nenhuma sobreposição permitida.

---

# 7. Regras de Separação

### 7.1 min_separation

Distância mínima entre segmentos paralelos:

```text
min_separation = track_gap
```

Nunca menor.

---

# 8. Crescimento Dinâmico

Se todos os tracks estiverem ocupados:

1. tracks_total += 2
2. center_track permanece fixo
3. Expandir simetricamente:

   * +1 acima
   * +1 abaixo

Recalcular posições.

Sem limite máximo definido na v1.0.

---

# 9. Canalização de Edge

Cada edge possui:

```text
exit_track
intermediate_track
entry_track
```

Main path:

```text
exit_track = center_track
entry_track = center_track
```

Branches:

```text
exit_track = center ± offset
```

Offset determinado pelo Layout Engine (MD13).

---

# 10. Backbone System

Backbones são corredores dedicados:

* Superior externo
* Inferior externo
* Central principal

Edges longas devem utilizar backbone antes do last-mile.

---

# 11. Interação com Expansão

Ao expandir tracks:

* Nenhum node muda de rank
* Apenas deslocamento horizontal (ou vertical no LR)
* Reprocessar roteamento

---

# 12. Determinismo

O sistema deve:

* Garantir mesma posição para mesmo CFF
* Nunca depender de ordem aleatória
* Ordenar sempre por ID quando empate

---

# 13. Proibições Absolutas

* Compressão automática
* Remoção de track existente
* Reindexação dinâmica durante roteamento
* Uso de coordenadas livres fora da grade

---

# 14. Estrutura de Dados Interna Recomendada

```text
lane_grid = {
  lane_id: {
    center_track,
    tracks_total,
    track_gap,
    occupancy_map
  }
}
```

---

# 15. Complexidade Adaptativa

Fluxos simples:

* Usam poucas tracks

Fluxos complexos:

* Expandem dinamicamente

Nunca reduzir espaço.

---

# 16. Garantias do Sistema

Após layout:

* Todas edges estão sobre tracks válidas
* Nenhum conflito de ocupação
* Separação visual garantida
* Escalabilidade ilimitada

---

# 17. Conclusão

O Sistema de Tracks é o esqueleto matemático do layout.

Ele garante:

* Organização
* Separação
* Crescimento previsível
* Controle absoluto do espaço
