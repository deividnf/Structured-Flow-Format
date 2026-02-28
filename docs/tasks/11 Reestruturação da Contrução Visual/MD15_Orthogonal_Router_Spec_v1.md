
# 📘 MD15 — Especificação Oficial do Roteador Ortogonal Definitivo

## Sugestão de título:

`MD15_Orthogonal_Router_Spec_v1.md`

---

# 1. Objetivo

Definir o algoritmo oficial que:

* Recebe um CFF válido
* Recebe o grid de tracks (MD14)
* Produz rotas ortogonais determinísticas
* Garante:

  * Zero sobreposição
  * Zero cruzamento
  * Zero paralelo colado
  * Zero invasão de bounding box

Sem heurística visual improvisada.

---

# 2. Modelo de Roteamento Permitido

A versão 1.0 suporta apenas:

### Layout TB

```
V → H → V
```

### Layout LR

```
H → V → H
```

Nenhuma outra forma permitida nesta versão.

---

# 3. Estrutura do Roteador

Para cada edge:

```text
route_edge(edge_id):
  1. Determinar portas de saída/entrada
  2. Determinar track de saída
  3. Determinar track intermediário
  4. Determinar track de chegada
  5. Validar conflito
  6. Reservar segmentos
  7. Retornar pontos
```

---

# 4. Portas do Nó

Cada nó possui 8 portas possíveis:

* Top
* Bottom
* Left
* Right
* 4 diagonais (fallback apenas)

Regra v1.0:

* Usar portas ortogonais primeiro
* Diagonais apenas se impossível

Uma porta só pode ser usada por uma edge por vez.

---

# 5. Escolha de Track

Ordem obrigatória:

1. Tentar center_track (se main_path)
2. Tentar tracks próximas ao centro
3. Expandir gradualmente para fora
4. Se esgotar → expandir lane

Ordenação sempre simétrica:

```
center
+1
-1
+2
-2
...
```

Determinismo absoluto.

---

# 6. Cálculo do Segmento

### TB

Dado:

```
(x1,y1) → (x2,y2)
```

Construir:

```
P1 = saída do nó origem
P2 = (x1, mid_y)
P3 = (x2, mid_y)
P4 = entrada do nó destino
```

mid_y deve:

* Estar dentro de track válida
* Não cruzar bounding box
* Não colidir com ocupação

---

# 7. Verificação de Conflito

Para cada segmento:

### 7.1 Sobreposição exata

Mesmo eixo e intervalo intersectando → proibido

### 7.2 Cruzamento ortogonal

Segmento H intersecta V → proibido

### 7.3 Bounding Box

Segmento dentro da caixa de nó ou label → proibido

### 7.4 Paralelo colado

Distância < min_separation → proibido

---

# 8. Sistema de Ocupação

Após validação:

Registrar no occupancy_map:

```
(H, y_track) → interval
(V, x_track) → interval
```

Nunca sobrescrever.

---

# 9. Fallback Strategy

Se nenhum track disponível:

1. Expandir lane
2. Recalcular posições
3. Reiniciar roteamento completo

Nunca forçar rota inválida.

---

# 10. Ordem de Execução Global

Edges devem ser roteadas segundo prioridade (MD12):

1. main_path
2. branch longa
3. branch curta
4. cross_lane
5. return
6. join

Empate → ordenar por ID.

---

# 11. Determinismo

Proibido:

* Uso de random
* Dependência de estado externo
* Uso de hash não ordenado

Mesma entrada → mesma saída.

---

# 12. Garantias

Após execução:

* Todas as edges possuem exatamente 4 pontos
* Nenhuma colisão
* Nenhuma interseção
* Nenhuma violação de separação

Se impossível:

```
ROUTING_IMPOSSIBLE
```

---

# 13. Extensões Futuras (Não nesta versão)

* Roteamento com mais de 2 curvas
* Suporte a loops
* Curvas diagonais reais
* A*

---

# Conclusão

O MD15 transforma o layout em um sistema:

* Matemático
* Formal
* Determinístico
* Totalmente previsível

Ele é o coração geométrico do sistema.

---

Agora temos a arquitetura completa:

* MD11 → CFF
* MD12 → Compilador
* MD13 → Engine
* MD14 → Tracks
* MD15 → Roteador
