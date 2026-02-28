
# Task 10.1 — Roteamento “Anti-Colisão” (Setas não podem ocupar o mesmo rumo)

> Objetivo: corrigir o problema atual onde **múltiplas edges seguem exatamente o mesmo caminho**, gerando sobreposição visual (linhas “em cima” uma da outra) e leitura confusa.
>
> Escopo desta task: **somente roteamento de edges** (sem mudar regras de lanes, ranks, tracks e sizing que já estão mais próximos do esperado).

---

## 1) Definições e Regras de Ouro

### 1.1 Regra principal
- **Duas edges diferentes NÃO podem compartilhar o mesmo “corredor” (canal) no mesmo trecho.**
- Se precisarem passar pela mesma região, devem:
  - **usar canais paralelos** (offsets), ou
  - **fazer detour (desvio)** por um corredor livre.

### 1.2 O que é “corredor/canal”
Chamaremos de **canal** uma faixa reservada para linhas dentro da lane (ou entre lanes), alinhada ao grid:

- Para direction `TB`:
  - A progressão principal é no **eixo Y** (rank).
  - As linhas (edges) usam:
    - **canais verticais** (descendo/subindo) e
    - **canais horizontais** (indo para esquerda/direita para trocar track ou trocar lane).

- Para direction `LR`:
  - A progressão principal é no **eixo X** (rank).
  - As edges usam:
    - **canais horizontais** (avançando) e
    - **canais verticais** (subindo/descendo para trocar track ou lane).

### 1.3 Portas (ports) dos nodes
Cada node deve ter pontos “de saída/entrada” para permitir múltiplas edges sem colisão:

- `start/end` (círculo): topo/baixo/esquerda/direita conforme direction
- `process` (retângulo): lados + topo/baixo
- `decision` (losango): preferir:
  - `true` sair por um lado (ex: direita)
  - `false` sair por outro (ex: esquerda)

**Regra:** duas edges saindo do mesmo nó devem usar **ports diferentes** OU o mesmo port com **offsets diferentes**.

---

## 2) Sintomas que esta task precisa eliminar

### 2.1 Sintoma A — Sobreposição total de duas setas
Ex.: `payment_approved -> end_success` e `payment_approved -> end_failure` saem juntas e seguem o mesmo caminho.

✅ esperado:
- saem do mesmo nó, mas **se separam cedo** (por lados/offset/canais).
- não ficam “uma em cima da outra”.

### 2.2 Sintoma B — Cruzamentos desnecessários
Uma edge cruza o centro de um node ou atravessa textos.

✅ esperado:
- edge nunca atravessa bbox de node (com margem).
- se precisar “passar perto”, usa detour.

### 2.3 Sintoma C — Labels (true/false) colidindo com linha
✅ esperado:
- label sempre fica “colado” ao segmento principal daquela edge (com offset e fundo opcional).

---

## 3) Estratégia de Implementação (recomendada)

> A sua engine já calcula: `rank_global`, `track`, bbox, e roteia com 4 pontos (Manhattan).
>
> Agora vamos evoluir para:
> 1) **roteamento por canais**
> 2) **reserva de ocupação**
> 3) **detour quando canal ocupado**

### 3.1 Modelo de Grid para Edge Routing

Criar um grid conceitual de roteamento (não é renderizado) com unidades do tipo:

- `CELL = grid_unit` (ex: 20px ou 24px)
- Toda rota deve cair em coordenadas múltiplas de `CELL`

**Sugestão de constantes:**
- `EDGE_CHANNEL_GAP = CELL` (separação mínima entre canais paralelos)
- `EDGE_NODE_CLEARANCE = 2 * CELL` (margem mínima do bbox do node)

### 3.2 Estrutura de “ocupação”
Manter um mapa de ocupação de segmentos:

- `occupied_h[(y, x1, x2)] -> count/edge_ids`
- `occupied_v[(x, y1, y2)] -> count/edge_ids`

Normalizar `x1<x2` e `y1<y2`.

**Regra:** um novo segmento só pode ser usado se:
- não existe ocupação no mesmo corredor **OU**
- existe, mas você escolher um **canal paralelo** (offset) diferente.

### 3.3 Canais paralelos (offsets) — o básico que resolve 80%
Quando detectar que um segmento proposto já está ocupado, aplicar offset:

- Para um segmento **vertical** em `x = X`:
  - tentar `x = X + k*EDGE_CHANNEL_GAP` e `x = X - k*EDGE_CHANNEL_GAP`
- Para um segmento **horizontal** em `y = Y`:
  - tentar `y = Y + k*EDGE_CHANNEL_GAP` e `y = Y - k*EDGE_CHANNEL_GAP`

Onde `k = 1..K_MAX` (ex: 6)

**Critério de escolha:**
- menor desvio total (distância Manhattan) + menor número de ocupações.

### 3.4 Ordem de roteamento (importante)
Roteie edges numa ordem previsível para estabilidade:

1) edges do “main path” (track=0) em ranks crescentes  
2) edges de branches (|track| maior)  
3) edges que “voltam” ou cruzam lanes (lane change)

Isso reduz bagunça, porque o caminho principal ocupa o corredor central primeiro, e os outros desviam.

---

## 4) Detour inteligente (quando offsets não bastam)

Se após tentar offsets a rota ainda colide (com node bbox ou com muitos segmentos ocupados), aplicar detour por “corredores de rank”.

### 4.1 Corredores fixos por rank (TB)
Para `TB`, defina “ruas horizontais” entre ranks:

- `street_y = y_rank + (rank_gap/2)`

E “avenidas verticais” por track:

- `avenue_x = x_track_center`

A edge deve preferir caminhar:
- do node A até a rua do rank
- seguir pela rua até a avenida do track/lane alvo
- descer/subir até o node B

Isso cria roteamento limpo e repetível.

### 4.2 Corredores fixos por rank (LR)
Para `LR`, análogo:
- `street_x = x_rank + (rank_gap/2)`
- `avenue_y = y_track_center`

### 4.3 Seleção de rota por custo (sem virar um labirinto)
Definir custo:

- `cost = length_manhattan`
- `+ 100 * collisions_with_nodes`
- `+ 10 * overlaps_with_edges`
- `+ 2 * number_of_bends`

Escolher rota com menor custo dentre candidatos:
- rota padrão (4 pontos)
- rota com offsets (até K_MAX)
- rota com detour via rua/avenida (2 ou 3 variações)

---

## 5) Regras específicas para Decision (true/false)

### 5.1 Port mapping obrigatório
Quando node.type = `decision` e branches boolean:

- branch `true`:
  - preferir sair pelo **lado direito** (TB: primeiro segmento horizontal para direita; LR: primeiro segmento vertical para cima/baixo conforme padrão do projeto)
- branch `false`:
  - preferir sair pelo **lado esquerdo**

### 5.2 Separação mínima entre branches
A partir do ponto de saída do decision, garantir:
- **pelo menos 1 canal de distância** entre as duas edges
- ou seja, elas nunca podem compartilhar o primeiro segmento

---

## 6) Logs obrigatórios (para depurar sem “olhar no SVG”)

Adicionar logs em `layout_engine.log` (nível INFO/WARN):

### 6.1 Proposta e seleção
- `[ROUTE_TRY] edge_id=..., variant=base|offset|detour, cost=..., bends=..., overlaps=..., node_hits=...`
- `[ROUTE_PICK] edge_id=..., chosen=..., cost=...`

### 6.2 Ocupação
- `[OCCUPY] edge_id=..., segment=H|V, from=(x1,y1), to=(x2,y2), channel_offset=...`

### 6.3 Detour
- `[ROUTE_DETOUR] edge_id=..., reason=edge_overlap|node_collision, tries=N`

---

## 7) Critérios de Aceite (DoD)

### 7.1 Visual
- ✅ Nenhuma seta fica “colada” exatamente em outra seta por todo o percurso.
- ✅ Branches (true/false) se separam logo após o decision.
- ✅ Nenhuma edge atravessa bbox de node (com `EDGE_NODE_CLEARANCE`).
- ✅ Em `TB`, o fluxo principal parece “descer” de forma natural.
- ✅ Em `LR`, o fluxo principal parece “avançar” de forma natural.

### 7.2 Estrutural
- ✅ Roteamento é determinístico (mesmo input → mesma rota).
- ✅ `occupied_*` impede reutilização do mesmo corredor sem offset.
- ✅ Logs mostram tentativas e escolha.

---

## 8) Como Validar (passo a passo)

### 8.1 Arquivos alvo
1) `exemplo/checkout_flow.sff` (TB)  
2) `import/test_lr_dag.sff` (LR)

### 8.2 Rodar export
```bash
python -m core.cli export exemplo/checkout_flow.sff --format svg
python -m core.cli export import/test_lr_dag.sff --format svg
````

### 8.3 Conferir logs

Abrir `logs/layout_engine.log` e validar:

* Cada edge tem `[ROUTE_PICK]`
* Para edges que antes sobrepunham:

  * aparece `[ROUTE_DETOUR]` ou seleção com `variant=offset`
* Existência de múltiplos `[OCCUPY]` com offsets diferentes

### 8.4 Checklist visual rápido (sem zoom extremo)

* As duas edges do decision aparecem separadas.
* As edges do gateway não se sobrepõem.
* Não há linhas atravessando caixas.

---

## 9) Notas importantes (para não regredir)

1. **Não “randomizar” offsets.** Sempre escolha pelo menor custo.
2. **Evitar offsets grandes** (isso volta a “espalhar demais” o layout).
3. **Priorizar corredor central** para o caminho principal.
4. Se um arquivo tem loops, o roteamento pode explodir — manter bloqueio já existente para ciclos (por enquanto).

---

## 10) Próxima evolução (não faz parte desta task)

* “Edge bundling” opcional (agrupar linhas até certo ponto e depois separar).
* Suporte a loops com roteamento dedicado (canal externo).
* PDF export real (converter SVG→PDF mantendo viewBox e escala).
