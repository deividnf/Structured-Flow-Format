# 📘 MD12 — Especificação Oficial do Compilador cpff

## Sugestão de título do arquivo:

`MD12_cpff_Compiler_Spec_v1.md`

---

# cpff Compiler — Especificação Formal v1.0

---

# 1. Objetivo

Este documento define formalmente o **Comportamento Oficial do Compilador cpff**.

O compilador é responsável por transformar um arquivo `.sff` válido em um `.cpff` totalmente expandido, determinístico e pronto para consumo por qualquer engine de layout, exportador ou integração externa.

O compilador:

* Não desenha.
* Não calcula coordenadas.
* Não executa heurística visual.
* Não depende de engine gráfica.

Ele apenas transforma estrutura declarativa em estrutura explícita.

---

# 2. Princípios Fundamentais

1. Determinismo absoluto
2. Nenhuma inferência no export
3. Nenhum campo implícito no cpff
4. Zero ambiguidade estrutural
5. Reprodutibilidade total

Mesmo `.sff` → Mesmo `.cpff` (sempre)

---

# 3. Pipeline Oficial do Compilador

## Etapa 1 — Leitura

* Abrir arquivo `.sff`
* Validar JSON
* Validar blocos obrigatórios:

  * sff
  * entry
  * lanes
  * nodes
  * edges

Se falhar → erro fatal.

---

## Etapa 2 — Validação Estrutural

Executar:

* Verificar existência de todos os nodes referenciados nas edges
* Verificar unicidade de IDs
* Verificar existência do entry.start
* Verificar pelo menos um entry.end
* Verificar que start não possui incoming edges
* Verificar que end não possui outgoing edges
* Verificar coerência de decision.branches
* Verificar que todos os nós são alcançáveis

Se qualquer regra falhar → abortar compilação.

---

## Etapa 3 — Construção do Grafo Base

Para cada node:

Criar:

```
prev_nodes[]
next_nodes[]
in_edges[]
out_edges[]
in_degree
out_degree
```

Esses dados passam a ser considerados **fonte oficial de navegação**.

---

## Etapa 4 — Cálculo de Depth Global

Depth é definido como:

```
depth(node) = distância mínima do entry.start até o node
```

Algoritmo:

* BFS a partir do start
* Armazenar nível de cada node

Resultado:

```
rank.global = depth + 1
```

---

## Etapa 5 — Identificação do Main Path

Main path é definido como:

* Caminho que parte do start
* Prioriza edges sem branch
* Em decision:

  * Se existir branch "true", assume como continuidade padrão
  * Caso contrário, primeira branch declarada

O caminho é percorrido até atingir um end.

Todos os nodes neste caminho recebem:

```
layout_hints.is_main_path = true
```

---

## Etapa 6 — Cálculo de Branch Depth

Para cada decision:

* Ao entrar em branch (true/false):

  * branch_depth = parent.branch_depth + 1
* Ao chegar em join:

  * branch_depth retorna ao nível anterior

Armazenar:

```
rank.branch_depth
```

---

## Etapa 7 — Cálculo de Rank por Lane

Para cada lane:

* Ordenar nodes pela ordem de depth
* Enumerar sequencialmente

```
rank.lane = posição incremental dentro da lane
```

---

## Etapa 8 — Métricas Futuras (Future Analysis)

Para cada node:

Calcular:

### future_steps

Quantidade de nodes alcançáveis a partir dele.

### future_decisions

Quantidade de decision nodes à frente.

### cross_lane_ahead

Quantidade de edges cujo destino esteja em outra lane.

### next_lane_target

Lane predominante nos próximos 2 níveis.

---

## Etapa 9 — Classificação de Edges

Para cada edge:

### Determinar kind:

Se edge conecta nodes consecutivos do main path:

```
kind = main_path
```

Se edge pertence a branch:

```
kind = branch
```

Se edge conecta lanes diferentes:

```
kind = cross_lane
```

Se edge retorna para depth menor:

```
kind = return
```

Se edge conecta branches convergindo:

```
kind = join
```

---

## Etapa 10 — Definição de Priority

Tabela padrão:

| Tipo       | Priority |
| ---------- | -------- |
| main_path  | 100      |
| branch     | 80       |
| cross_lane | 60       |
| return     | 40       |
| join       | 30       |

Priority é obrigatória e determinística.

---

## Etapa 11 — Layout Hints

Para cada node:

Calcular:

```
preferred_exit_side
preferred_entry_side
routing_priority
```

Regras:

* Main path prefere continuar na direção predominante do fluxo.
* Branch com menor future_steps tende a sair para lado externo.
* Branch com maior continuidade tende ao lado interno.

---

## Etapa 12 — Estatísticas Globais

Gerar:

```
nodes_total
edges_total
decision_nodes
branch_edges
joins
lanes_total
max_depth
max_branch_depth
```

---

# 4. Regras de Erro do Compilador

Compilação deve falhar se:

* Nó inalcançável
* Edge contraditória com decision.branches
* Join implícito não declarado
* Loop detectado (caso loops não suportados)
* Rank não determinístico

---

# 5. O que o Compilador NÃO faz

* Não calcula coordenadas X/Y
* Não calcula trilhas (tracks)
* Não calcula grid final
* Não escolhe backbone
* Não executa roteamento

Essas etapas pertencem ao Layout Engine (MD13+).

---

# 6. Garantias do cpff Gerado

Após compilação:

* Todos os nodes possuem:

  * rank
  * links completos
  * branch_context
  * future_metrics
  * layout_hints

* Todas as edges possuem:

  * classification.kind
  * priority
  * routing_constraints

Nenhum campo é opcional.

---

# 7. Determinismo

O compilador deve:

* Ordenar sempre por ID quando houver empate
* Nunca depender de ordem de inserção do JSON
* Nunca depender de hash não ordenado
* Produzir saída idêntica para mesma entrada

---

# 8. Compatibilidade

Se a estrutura do cpff mudar:

* Incrementar version
* Manter backward compatibility quando possível
* Registrar breaking changes

---

# 9. Conclusão

O Compilador cpff é o cérebro estrutural do sistema.

Ele transforma:

* Fluxo narrativo → Estrutura matemática
* Edges implícitas → Relações explícitas
* Caminhos possíveis → Caminho classificado
* Ambiguidade → Determinismo

Sem MD12, o sistema depende de heurística visual.

Com MD12, o sistema se torna formal, testável e escalável.
