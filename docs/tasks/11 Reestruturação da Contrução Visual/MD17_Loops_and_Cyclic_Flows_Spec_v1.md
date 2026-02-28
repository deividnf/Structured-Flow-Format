
# 📘 MD17 — Especificação Formal de Loops e Fluxos Cíclicos

## Sugestão de título:

`MD17_Loops_and_Cyclic_Flows_Spec_v1.md`

---

# 1. Objetivo

Formalizar como o sistema suporta **loops e fluxos cíclicos** sem quebrar:

* Determinismo
* Rank global
* Sistema de tracks
* Roteamento ortogonal
* Cálculo de métricas futuras
* Garantias do CFF

Este documento altera principalmente:

* MD12 (Compilador)
* MD13 (Layout Engine)
* MD15 (Roteador)

Sem afetar o SFF base estrutural .

---

# 2. Definição Formal de Loop

Um loop é uma edge tal que:

```
depth(to) ≤ depth(from)
```

Ou seja, a edge aponta para um nó já visitado no fluxo principal.

Classificação automática no compilador:

```
edge.kind = return
```

---

# 3. Tipos de Loops Permitidos (v1.0)

## 3.1 Retry Loop (reprocessamento simples)

Exemplo:

* Validação falha → volta para preenchimento
* Pagamento falha → volta para dados

Características:

* Retorna para depth menor
* Permanece na mesma lane (preferencialmente)

Permitido.

---

## 3.2 Loop Cross-Lane

Exemplo:

* Sistema detecta erro → retorna para usuário

Permitido, mas classificado como:

```
kind = return + cross_lane
```

---

## 3.3 Self-loop (mesmo nó)

```
from == to
```

❌ Proibido na v1.0.

---

# 4. Impacto no Compilador (MD12)

## 4.1 Cálculo de Depth

Depth continua sendo calculado via BFS a partir do start.

Loops não alteram depth já definido.

Depth é definido apenas na primeira visita.

---

## 4.2 Future Metrics com Loop

Para evitar contagem infinita:

Regra:

* Ignorar edges classificadas como `return` ao calcular future_steps
* Ignorar ciclos no cálculo de reachability futura

Future analysis deve considerar apenas grafo acíclico derivado (DAG temporário).

---

## 4.3 Classificação

Se:

```
rank.global(to) < rank.global(from)
```

Então:

```
kind = return
priority = 40
```

---

# 5. Impacto no Sistema de Tracks (MD14)

Loops não utilizam tracks internas normais.

Eles devem usar:

## 5.1 Backbone Externo Obrigatório

Layout TB:

* Loops sobem pelo backbone lateral externo
* Nunca passam pelo interior do diagrama

Layout LR:

* Loops retornam pelo topo ou base externa

Regra:

Loops sempre ocupam trilhas externas dedicadas.

---

# 6. Impacto no Roteador (MD15)

Modelo para TB:

```
V (sai)
H (vai para backbone lateral)
V (sobe/ desce externamente)
H (entra no nó destino)
```

Ou seja, loops têm 4 curvas (exceção à regra V-H-V).

Isso é permitido apenas para `kind = return`.

---

# 7. Regras Absolutas para Loops

Proibido:

* Loop cruzar fluxo principal
* Loop passar entre tracks internas
* Loop usar center_track
* Loop usar trilha de branch ativa

Obrigatório:

* Usar corredor externo dedicado
* Manter min_separation
* Respeitar bounding boxes

---

# 8. Expansão Automática

Se não houver espaço lateral suficiente para loop:

1. Expandir lane horizontalmente
2. Criar nova trilha externa
3. Recalcular roteamento

Nunca compactar fluxo.

---

# 9. Limitação Estrutural

Se houver loop aninhado dentro de loop:

```
LOOP_NESTING_NOT_SUPPORTED_V1
```

Versão 1 suporta apenas loops simples (não recursivos).

---

# 10. Determinismo

Mesmo `.cff` com loops → mesmo layout.

Ordem de roteamento:

1. main_path
2. branches
3. joins
4. returns (loops sempre por último)

---

# 11. Garantias

Após roteamento com loops:

* Nenhuma interseção
* Nenhum cruzamento
* Loop sempre externo
* Layout permanece legível
* Main path nunca é afetado estruturalmente

---

# 12. Atualização na Classificação de Edges (MD12)

Tabela atualizada:

| kind       | priority |
| ---------- | -------- |
| main_path  | 100      |
| branch     | 80       |
| cross_lane | 60       |
| return     | 40       |
| join       | 30       |

Loops usam `return`.

---

# 13. Impacto Arquitetural

Com MD17:

O sistema deixa de ser estritamente DAG-only
e passa a suportar fluxos reais com retry e fallback.

Sem comprometer:

* Compilação determinística
* Roteamento formal
* Sistema de tracks
* Controle de congestionamento

---

# 14. Próximo nível possível

Depois de MD17, os caminhos naturais são:

* MD18 — Formalização de Merges Complexos
* MD19 — Prova de Escalabilidade e Limites Matemáticos
* MD20 — Subflows e Modularização de Fluxos
