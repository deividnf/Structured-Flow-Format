# Structured Flow Format (SFF)
## Especificação Oficial — Versão 1.0 (Draft)

Este documento define as regras formais de leitura, validação, interpretação e compilação de arquivos no padrão **SFF (Structured Flow Format)**.

Este documento deve orientar:

- SFF Core Engine
- Parsers
- Validadores
- Compiladores
- Renderizadores
- Agentes de IA que consumirem arquivos `.sff`

O SFF é um formato estruturado para modelagem de fluxos, baseado semanticamente em JSON.

---

# 1. Visão Geral

SFF (Structured Flow Format) é um formato estruturado para representar fluxos lógicos, processos, decisões e estruturas de controle.

O SFF:

- É independente de linguagem
- É estruturado como JSON
- É determinístico
- É validável
- É compilável
- É extensível

O SFF NÃO é limitado a Python.

---

# 2. Extensão do Arquivo

Extensão oficial:

```

.sff

````

Importante:

Embora o arquivo tenha extensão `.sff`, ele deve conter estrutura JSON válida.

O processo de leitura deve:

1. Ler o conteúdo bruto do `.sff`
2. Interpretar o conteúdo como JSON
3. Validar contra a especificação SFF
4. Compilar para estrutura interna de grafo

---

# 3. Estrutura Raiz Obrigatória

Todo arquivo `.sff` deve conter:

```json
{
  "sff": {},
  "entry": {},
  "lanes": {},
  "nodes": {},
  "edges": []
}
````

Todos os blocos acima são obrigatórios, salvo indicação explícita em versões futuras.

---

# 4. Bloco `sff`

Metadados do fluxo.

Estrutura obrigatória:

```json
"sff": {
  "version": "1.0",
  "id": "identificador_unico",
  "title": "Título do fluxo",
  "direction": "TB | LR"
}
```

Campos:

| Campo     | Tipo   | Obrigatório | Descrição                    |
| --------- | ------ | ----------- | ---------------------------- |
| version   | string | sim         | Versão da especificação      |
| id        | string | sim         | Identificador único do fluxo |
| title     | string | sim         | Nome legível do fluxo        |
| direction | string | sim         | Direção do layout (TB ou LR) |

---

# 5. Bloco `entry`

Define o ponto inicial e os pontos finais.

Estrutura:

```json
"entry": {
  "start": "node_id",
  "ends": ["node_id"]
}
```

Regras obrigatórias:

* `start` deve existir em `nodes`
* `ends` deve conter pelo menos um nó válido
* O nó `start` deve ser do tipo `start`
* Todos os nós listados em `ends` devem ser do tipo `end`
* O nó `start` não pode possuir entradas
* Nós do tipo `end` não podem possuir saídas

---

# 6. Bloco `lanes`

Define agrupamentos lógicos (atores, sistemas ou divisões).

Estrutura:

```json
"lanes": {
  "lane_id": {
    "title": "Nome da lane",
    "order": 1,
    "description": "Opcional"
  }
}
```

Regras:

* `lane_id` deve ser único
* Todo nó deve referenciar uma lane válida
* `order` define prioridade visual
* Lanes não alteram lógica, apenas agrupamento

---

# 7. Bloco `nodes`

Dicionário indexado por ID.

Estrutura:

```json
"nodes": {
  "node_id": {
    "type": "tipo_do_no",
    "lane": "lane_id",
    "label": "Texto exibido"
  }
}
```

Regras obrigatórias:

* IDs devem ser únicos
* Cada nó deve conter:

  * type
  * lane
  * label
* Cada `lane` deve existir no bloco `lanes`

---

# 8. Tipos de Nó (v1.0)

Tipos permitidos:

* start
* end
* process
* decision
* delay

---

## 8.1 start

Representa início do fluxo.

Regras:

* Deve existir exatamente um nó do tipo `start`
* Deve corresponder ao `entry.start`

---

## 8.2 end

Representa término do fluxo.

Regras:

* Deve existir pelo menos um
* Não pode possuir saídas

---

## 8.3 process

Representa ação simples.

Campos opcionais:

```json
"note": "Descrição adicional"
```

---

## 8.4 delay

Representa espera temporal.

Estrutura adicional:

```json
"delay": {
  "min_seconds": number,
  "max_seconds": number
}
```

---

## 8.5 decision

Representa ramificação lógica.

Estrutura obrigatória:

```json
"decision": {
  "kind": "boolean"
}
```

Estrutura obrigatória de ramificações:

```json
"branches": {
  "true": {
    "label": "Sim",
    "next": "node_id"
  },
  "false": {
    "label": "Não",
    "next": "node_id"
  }
}
```

Regras:

* Toda decisão deve possuir `branches`
* Para `kind: boolean`, deve existir:

  * branch `true`
  * branch `false`
* Cada `next` deve existir em `nodes`
* Opcionalmente pode existir:

```json
"join": {
  "type": "merge",
  "node": "node_id"
}
```

O `join` indica ponto de reencontro lógico.

---

# 9. Bloco `edges`

Define conexões explícitas.

Estrutura:

```json
{
  "from": "node_id",
  "to": "node_id",
  "label": "Texto opcional",
  "branch": "true | false | join"
}
```

Regras:

* `from` e `to` devem existir
* `branch` deve corresponder a uma branch válida caso o nó de origem seja decision
* Não pode existir edge que contradiga a definição de `branches`

Observação:

`branches` é a fonte oficial de ramificação.
`edges` são conexões estruturais.

---

# 10. Processo de Leitura (Engine)

Ao ler um arquivo `.sff`, o motor deve:

1. Validar JSON
2. Validar estrutura raiz
3. Validar tipos de nós
4. Validar coerência de branches
5. Construir índice interno:

```
prev[node_id] = [...]
next[node_id] = [...]
```

6. Garantir:

   * Um único start
   * Pelo menos um end
   * Nenhum nó isolado
   * Nenhuma referência inexistente

---

# 11. Regras de Validação Obrigatórias

* Deve existir exatamente 1 nó do tipo `start`
* Deve existir ao menos 1 nó do tipo `end`
* Todo `branch.next` deve existir
* Toda `edge.from` e `edge.to` deve existir
* `start` não pode ter entradas
* `end` não pode ter saídas
* Decisões booleanas devem conter `true` e `false`
* Não pode haver ciclos infinitos não controlados (versão futura pode permitir loops)

---

# 12. Compilação

O processo de compilação deve gerar:

* Índice de adjacência
* Índice reverso
* Validação consolidada
* Estrutura pronta para renderização

Estrutura compilada sugerida:

```json
"compiled": {
  "index": {
    "prev": {},
    "next": {}
  },
  "validation": {
    "errors": [],
    "warnings": []
  }
}
```

---

# 13. Extensibilidade

Versões futuras podem adicionar:

* switch cases
* loops
* paralelismo
* eventos
* integrações externas
* metadata avançada
* permissões

Toda extensão deve respeitar versionamento semântico.

---

# 14. Versionamento

Formato:

```
MAJOR.MINOR
```

* MAJOR: quebra de compatibilidade
* MINOR: extensão compatível

---

# 15. Princípios do SFF

O SFF deve ser:

* Explícito
* Determinístico
* Validável
* Independente de runtime
* Conversível para múltiplos renderizadores
* Simples na leitura
* Estruturalmente consistente

---

# Fim da Especificação SFF v1.0 (Draft)

