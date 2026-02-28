
# 📘 MD18 — Especificação Formal de Loops Avançados e Subflows

## Sugestão de título:

`MD18_Advanced_Loops_and_Subflows_v1.md`

---

# 1️⃣ Objetivo

Expandir o suporte de loops para permitir:

* Loops aninhados
* Loops com múltiplas entradas
* Subflows reutilizáveis
* Blocos repetitivos estruturais
* Ciclos com join explícito
* Reentrada controlada

Sem comprometer:

* Determinismo
* Rank global
* Cálculo de future_metrics
* Sistema de tracks
* Layout ortogonal

---

# 2️⃣ Nova Classificação de Ciclos

## 2.1 Loop Simples (já definido no MD17)

Edge que retorna para depth menor.

```
A → B → C
     ↑   ↓
     └───┘
```

---

## 2.2 Loop Aninhado

Loop dentro de um branch que já está dentro de outro loop.

```
Start
  ↓
A → B → C
     ↑   ↓
     └───┘
  ↓
D
```

Agora temos dois ciclos ativos em diferentes níveis estruturais.

---

## 2.3 Subflow Reentrante

Subflow é um conjunto de nós com:

* Entrada única
* Saída única
* Pode ser invocado múltiplas vezes
* Pode conter loops internos

Representação conceitual:

```
Main → [Subflow X] → Continue
           ↑
           └── loop interno
```

---

# 3️⃣ Atualização no Compilador (MD12)

## 3.1 Detecção de Componentes Fortemente Conectados (SCC)

Agora o compilador deve executar:

> Algoritmo de Tarjan ou Kosaraju

Para identificar:

```
Strongly Connected Components
```

Cada SCC com mais de 1 nó → ciclo estrutural.

---

## 3.2 Novo Campo no CFF

Em nodes:

```json
"cycle_context": {
  "cycle_id": "cycle_1",
  "cycle_level": 2,
  "cycle_root": "validate_data",
  "cycle_exit_nodes": ["process_payment"]
}
```

---

## 3.3 Rank em presença de ciclos

Rank.global continua sendo baseado no primeiro encontro via BFS.

Mas agora adicionamos:

```json
"rank": {
  "global": 4,
  "lane": 2,
  "depth": 3,
  "cycle_depth": 1
}
```

cycle_depth representa nível de aninhamento.

---

# 4️⃣ Future Metrics com Ciclos Complexos

Para evitar recursão infinita:

## Regra:

Ao calcular métricas futuras:

* Ignorar edges dentro do mesmo cycle_id após primeira visita
* Considerar apenas transições que saem do ciclo

Ou seja:

O compilador cria um **grafo condensado (DAG de ciclos)** e calcula métricas sobre ele.

---

# 5️⃣ Subflows (Nova Entidade Estrutural)

## 5.1 Definição

Subflow é um agrupamento lógico de nós com:

* 1 entry interno
* 1 exit interno
* Pode conter loops

No CFF:

```json
"subflows": {
  "sub_1": {
    "entry": "node_x",
    "exit": "node_y",
    "nodes": [...]
  }
}
```

---

## 5.2 Benefícios

* Permite reutilização futura
* Permite blueprint modular
* Permite colapsar visualmente subflow

---

# 6️⃣ Layout para Loops Aninhados

Regra geral:

* Cada nível de ciclo recebe um backbone externo próprio
* Nível 1 → corredor externo primário
* Nível 2 → corredor ainda mais externo
* Nível N → expandir lateralmente progressivamente

Ou seja:

```
[Loop level 1]
   [Loop level 2]
```

Nunca permitir sobreposição de corredores de ciclos.

---

# 7️⃣ Roteamento Atualizado (MD15 Impacto)

Para `kind = return` com cycle_level:

```
spine_offset = base_offset + (cycle_level * loop_spacing)
```

Ou seja:

Cada nível empurra o loop mais para fora.

---

# 8️⃣ Novos Erros Estruturais

Se detectar:

* Ciclo sem saída externa
* Ciclo completamente fechado (infinito)
* Loop recursivo sem escape

→

```
CYCLE_WITHOUT_EXIT
```

---

# 9️⃣ Determinismo Garantido

Mesmo com:

* Loops aninhados
* Subflows múltiplos
* Ciclos cruzando lanes

O algoritmo deve:

1. Identificar SCC
2. Condensar em grafo acíclico
3. Calcular ranks
4. Aplicar layout

Sempre mesma ordem por ID em empate.

---

# 🔟 Impacto Arquitetural

Agora o sistema suporta:

* Retry simples
* Retry múltiplo
* Loops aninhados
* Subflows reutilizáveis
* Ciclos complexos reais de negócio

Sem virar caos visual.

---

# 📌 Próximo nível possível

Se quisermos elevar ainda mais:

* MD19 — Modelo Formal de Complexidade e Limites Matemáticos
* MD20 — Modo Modular (Subflows colapsáveis)
* MD21 — Engine de Otimização Global (minimização de área total)
