
# SFF — Structured Flow Format

O **SFF (Structured Flow Format)** é um formato estruturado para definição de fluxos lógicos, processos e estruturas de decisão.

Um arquivo `.sff` deve ser interpretado como **JSON válido**, passando por um processo de:

1. Leitura
2. Validação estrutural
3. Validação lógica
4. Compilação para estrutura interna de grafo

O SFF é independente de linguagem e pode ser utilizado por qualquer runtime capaz de interpretar JSON.

---

# 1. Extensão Oficial

```

.sff

````

Embora utilize a extensão `.sff`, o conteúdo interno deve ser JSON válido.

O processo de leitura deve:

- Abrir o arquivo `.sff`
- Interpretar seu conteúdo como JSON
- Validar contra a especificação oficial
- Compilar para estrutura de execução ou renderização

---

# 2. Estrutura Base Obrigatória

Todo arquivo SFF deve conter os seguintes blocos raiz:

```json
{
  "sff": {},
  "entry": {},
  "lanes": {},
  "nodes": {},
  "edges": []
}
````

Todos os blocos acima são obrigatórios na versão 1.0.

---

# 3. Blocos Principais

## 3.1 `sff`

Contém metadados do fluxo.

Define:

* Versão da especificação
* Identificador único
* Título
* Direção de layout

---

## 3.2 `entry`

Define:

* Nó inicial obrigatório
* Nós finais obrigatórios

Responsável por determinar os pontos de entrada e término do fluxo.

---

## 3.3 `lanes`

Define agrupamentos lógicos.

Podem representar:

* Atores
* Sistemas
* Departamentos
* Camadas

Lanes não alteram a lógica do fluxo, apenas organização estrutural.

---

## 3.4 `nodes`

Define os elementos estruturais do fluxo.

Cada nó possui:

* Identificador único
* Tipo
* Lane associada
* Texto descritivo

Tipos de nó são definidos separadamente.

---

## 3.5 `edges`

Define conexões explícitas entre nós.

Responsável por:

* Sequenciamento
* Direcionamento
* Associação de branches

---

# 4. Processo de Leitura

O motor que consome SFF deve executar:

1. Validação de JSON
2. Validação estrutural dos blocos obrigatórios
3. Validação de coerência entre nodes e edges
4. Validação de regras específicas por tipo de nó
5. Construção de índices internos (`prev` e `next`)
6. Geração de estrutura compilada

---

# 5. Compilação

Após validação, o SFF deve ser transformado em uma estrutura interna que permita:

* Navegação determinística
* Geração de grafo
* Renderização visual
* Exportação para outros formatos
* Integração com motores externos

A estrutura compilada não faz parte do arquivo `.sff`, sendo gerada pelo motor.

---

# 6. Versionamento

O campo `sff.version` define a versão da especificação utilizada.

Alterações futuras devem respeitar versionamento semântico:

* Alterações incompatíveis → incremento major
* Extensões compatíveis → incremento minor

---

# 7. Modularização da Documentação

Cada bloco estrutural possui documentação própria:

* entry → `entry.md`
* lanes → `lanes.md`
* nodes → `nodes.md`
* edges → `edges.md`
* tipos de nodes → pasta `node_types/`

Este README define apenas a visão estrutural geral do formato.

---

# 8. Objetivo do SFF

O SFF foi projetado para:

* Representar fluxos estruturados
* Permitir validação formal
* Permitir compilação determinística
* Ser convertido para múltiplos renderizadores
* Ser independente de linguagem

O SFF é um formato estrutural, não apenas visual.
