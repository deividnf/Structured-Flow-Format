# Task 01 — Arquitetura do Modelo Visual de Fluxogramas

## Status
🔄 Em definição

---

# 1. Objetivo da Task

Definir a **arquitetura lógica do layout visual** dos fluxogramas SFF, garantindo que:

- O fluxograma possa ser gerado automaticamente
- Não exista necessidade de desenhar setas manualmente
- As conexões sejam sempre ortogonais (curvas quadradas 90°)
- O layout funcione tanto em direção TB (Top-Bottom) quanto LR (Left-Right)
- O modelo seja escalável
- O renderizador seja determinístico
- O layout respeite `lanes`, `nodes`, `edges` e `entry`

Essa task NÃO implementa renderização.
Ela define o modelo lógico que tornará a renderização automática possível.

---

# 2. Princípios Fundamentais

O layout visual deve obedecer aos princípios do SFF:

- Estrutural
- Determinístico
- Validável
- Independente de runtime
- Não ambíguo
- Compilável

A estrutura raiz obrigatória do SFF deve ser respeitada:
`sff`, `entry`, `lanes`, `nodes`, `edges` :contentReference[oaicite:5]{index=5}

---

# 3. Camadas da Arquitetura Visual

A arquitetura será dividida em 3 camadas lógicas:

---

## 3.1 Camada Estrutural (Grafo)

Fonte de verdade:
- nodes
- edges
- decision.branches
- entry

Regras:

- O fluxo começa em `entry.start`
- O fluxo termina em `entry.ends`
- `edges` definem conexões explícitas
- `branches` são a fonte oficial de ramificação
- `edges` devem ser coerentes com branches :contentReference[oaicite:6]{index=6}

Saída esperada:
- Índice prev/next compilado
- Grafo acíclico validado (MVP sem loops complexos)

---

## 3.2 Camada de Layout (Posicionamento)

Objetivo: posicionar nós automaticamente.

### 3.2.1 Direção

Baseada em:

```json
"sff": {
  "direction": "TB | LR"
}
````

Se TB:

* Fluxo principal vertical
* Lanes empilhadas horizontalmente

Se LR:

* Fluxo principal horizontal
* Lanes empilhadas verticalmente

---

### 3.2.2 Ranks (Níveis)

Cada nó receberá um "rank" calculado por:

* Distância do start
* Profundidade no grafo

Regra:

* Nós no mesmo nível estrutural compartilham rank
* Rank define coluna (LR) ou linha (TB)

Isso elimina posicionamento manual.

---

### 3.2.3 Ordenação Interna

Dentro do mesmo rank:

* Minimizar cruzamento de arestas
* Priorizar proximidade de dependência
* Agrupar por lane

---

## 3.3 Camada de Roteamento de Arestas

As linhas devem ser:

* 100% ortogonais
* Segmentadas
* Com ângulos de 90°
* Sem curvas suaves

Regras:

* Conexões sempre saem de portas fixas
* Não cruzar nós
* Desviar por "corredores invisíveis"
* Utilizar canais paralelos quando necessário

---

# 4. Regras de Portas de Conexão

Para evitar ambiguidade:

Se direction = TB:

* Entrada principal: topo
* Saída principal: base
* Desvios: laterais

Se direction = LR:

* Entrada principal: esquerda
* Saída principal: direita
* Desvios: topo/base

Decision:

* true → lado direito (LR) ou inferior direito (TB)
* false → lado esquerdo (LR) ou inferior esquerdo (TB)
* join → convergência central

---

# 5. Integração com Lanes

Lanes NÃO alteram lógica 

Mas alteram organização visual:

* Cada lane é uma faixa (swimlane)
* Nós são posicionados dentro da lane correspondente
* A ordem visual segue `lane.order` 

Regras:

* Nunca misturar nodes fora da sua lane
* Edges podem cruzar lanes
* Layout deve respeitar agrupamento

---

# 6. Modelo Interno de Layout (a ser gerado pelo engine)

O compilador deverá gerar uma estrutura auxiliar:

```json
"layout": {
  "ranks": {},
  "positions": {},
  "routing": {}
}
```

Onde:

* ranks[node_id] → nível estrutural
* positions[node_id] → coordenada lógica (grid)
* routing[edge_id] → lista de segmentos ortogonais

---

# 7. Regras para Decisões (Visual)

Decision deve:

* Gerar dois ramos visíveis
* Nunca sobrepor arestas
* Ter merge visual coerente se houver `join`

Se `join` existir:

* Deve convergir para o nó declarado
* Merge deve ser centralizado

---

# 8. Critérios de Aceite

A task será considerada concluída quando:

* [ ] Existe definição clara de ranks
* [ ] Existe regra formal de portas
* [ ] Existe regra formal de roteamento ortogonal
* [ ] Lanes são respeitadas visualmente
* [ ] Não há necessidade de posicionamento manual
* [ ] Layout funciona para TB e LR
* [ ] Documentação está atualizada
* [ ] É possível gerar preview via terminal (mesmo que simples)

---

# 9. Fora de Escopo (Task 01)

* Renderização final SVG/Canvas
* Animações
* Interação
* Loops complexos
* Paralelismo avançado

---

# 10. Como Validar (obrigatório)

Após implementação futura:

1. Gerar fluxo simples
2. Gerar fluxo com decision
3. Gerar fluxo com múltiplas lanes
4. Validar que:

   * Não há linhas curvas suaves
   * Não há sobreposição
   * Layout é determinístico
   * Rodando duas vezes → mesma estrutura

---

# 11. Resultado Esperado

Ao final desta task teremos:

* Arquitetura formal do layout
* Base lógica para renderizadores
* Modelo previsível
* Fundamento para o Core Engine

Essa task é a fundação visual do projeto.
