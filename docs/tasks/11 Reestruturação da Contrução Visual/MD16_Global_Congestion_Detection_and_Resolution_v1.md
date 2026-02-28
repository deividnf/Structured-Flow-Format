
# 📘 MD16 — Sistema de Detecção e Resolução de Congestionamento Global

## Sugestão de título:

`MD16_Global_Congestion_Detection_and_Resolution_v1.md`

---

# 1. Objetivo

O Sistema de Congestionamento Global é responsável por:

* Detectar padrões de saturação estrutural
* Antecipar gargalos antes do roteamento falhar
* Redistribuir espaço de forma matemática
* Garantir escalabilidade visual ilimitada

Ele atua acima do roteador (MD15) e abaixo do layout engine (MD13).

---

# 2. Definição Formal de Congestionamento

Congestionamento ocorre quando:

1. Ocupação de tracks ultrapassa limiar seguro
2. Concentração de edges em mesmo rank excede capacidade
3. Repetidas expansões locais não resolvem conflitos
4. Branches competem por mesmo corredor estrutural
5. Backbones atingem saturação

Congestionamento ≠ colisão.
É um estado estrutural de risco.

---

# 3. Métricas de Congestionamento

Para cada lane e para cada rank:

## 3.1 Track Utilization Ratio (TUR)

```text
TUR = tracks_ocupadas / tracks_total
```

Se TUR > 0.7 → alerta
Se TUR > 0.85 → congestionado

---

## 3.2 Rank Edge Density (RED)

```text
RED = edges_no_rank / largura_disponível
```

Mede quantas edges passam por um mesmo nível global.

---

## 3.3 Backbone Saturation (BS)

Percentual de ocupação do backbone principal.

Se BS > 0.75 → risco estrutural.

---

## 3.4 Branch Spread Index (BSI)

Mede dispersão lateral de branches.

Se BSI for baixo e branch_depth alto → tendência a congestionamento futuro.

---

# 4. Fases do Sistema de Congestionamento

---

## Fase 1 — Análise Pre-Roteamento

Antes de rotear qualquer edge:

* Analisar stats do CFF
* Calcular projeção de ocupação
* Identificar ranks críticos
* Identificar lanes críticas

Se risco alto:

→ Expandir lane antes do roteamento.

---

## Fase 2 — Monitoramento Durante Roteamento

Durante roteamento:

* Atualizar TUR
* Atualizar RED
* Atualizar BS

Se qualquer métrica cruzar limite crítico:

→ Interromper roteamento
→ Recalcular layout com expansão global

Nunca continuar roteando em sistema saturado.

---

## Fase 3 — Rebalanceamento Global

Se congestionamento persistir:

### Estratégias permitidas:

1. Aumentar rank_gap
2. Aumentar track_gap
3. Inserir rank buffer intermediário
4. Redistribuir branches lateralmente
5. Criar backbone secundário

Proibido:

* Compactar nodes
* Diminuir separação mínima
* Alterar rank.global

---

# 5. Algoritmo de Rebalanceamento

```text
detect_congestion():
  calcular TUR, RED, BS, BSI
  se crítico:
    aplicar expansão global
    reiniciar roteamento
```

Expansão global deve ser:

* Simétrica
* Determinística
* Reprodutível

---

# 6. Expansão Global vs Expansão Local

| Tipo   | Quando usar          | Impacto                 |
| ------ | -------------------- | ----------------------- |
| Local  | conflito isolado     | pequena expansão        |
| Global | saturação estrutural | reestruturação completa |

MD16 formaliza apenas expansão global.

---

# 7. Garantias

Após execução do sistema:

* Nenhuma lane saturada
* Nenhum rank crítico
* Nenhum backbone colapsado
* Layout escalável

---

# 8. Determinismo

Mesmo `.cff` → mesma decisão de expansão global.

Ordem de prioridade:

1. Expandir tracks
2. Expandir rank_gap
3. Criar backbone secundário
4. Inserir rank buffer

Sempre nessa ordem.

---

# 9. Limites

Se após N expansões globais ainda houver congestionamento:

```text
LAYOUT_UNSCALABLE_STRUCTURE
```

Erro estrutural.

---

# 10. Benefícios

Com MD16 o sistema passa a:

* Antecipar gargalos
* Escalar fluxos grandes
* Manter clareza visual
* Evitar “macarrão visual”
* Garantir previsibilidade

---

# Estado Atual da Arquitetura

* MD11 → CFF
* MD12 → Compilador
* MD13 → Engine
* MD14 → Tracks
* MD15 → Roteador
* MD16 → Controle estrutural global

Agora o sistema é arquiteturalmente robusto.

