# lanes.md — Bloco `lanes` (SFF v1.0)

## 1. O que é o bloco `lanes`

O bloco **`lanes`** define **agrupamentos lógicos** dentro de um fluxo SFF.

Ele NÃO altera a lógica do fluxo.
Ele NÃO influencia a execução.
Ele NÃO interfere na validação estrutural de branches.

Ele existe exclusivamente para:

* Organização estrutural
* Separação de responsabilidades
* Representação visual
* Clareza semântica

Em outras palavras:

> `lanes` define “onde” um nó pertence em termos organizacionais, não “como” ele se conecta.

---

## 2. Papel conceitual das Lanes

Lanes podem representar:

* Atores (Usuário, Sistema, API)
* Departamentos (Financeiro, Operações)
* Sistemas (Backend, Frontend, Banco de Dados)
* Camadas (Aplicação, Domínio, Infraestrutura)
* Fases (Pré-processamento, Validação, Execução)

Elas são equivalentes ao conceito de **Swimlanes** em diagramas BPMN.

---

## 3. Estrutura Formal

Estrutura obrigatória do bloco:

```json
"lanes": {
  "lane_id": {
    "title": "Nome da lane",
    "order": 1,
    "description": "Opcional"
  }
}
```

Definição oficial na especificação 

---

## 4. Campos da Lane

### 4.1 `lane_id`

* Tipo: `string`
* Obrigatório
* Deve ser único dentro do bloco `lanes`
* É a chave usada pelos nós (`nodes[node_id].lane`)

Exemplo:

```json
"user": { ... }
```

---

### 4.2 `title`

* Tipo: `string`
* Obrigatório
* Nome legível exibido em renderizações

Exemplo:

```json
"title": "Usuário"
```

---

### 4.3 `order`

* Tipo: `number`
* Obrigatório
* Define prioridade visual
* Determina a posição relativa da lane no layout

Exemplo:

```json
"order": 1
```

Se `direction = "TB"`:

* order menor → lane mais acima

Se `direction = "LR"`:

* order menor → lane mais à esquerda

---

### 4.4 `description` (opcional)

* Tipo: `string`
* Não interfere na lógica
* Pode ser usada para documentação

Exemplo:

```json
"description": "Responsável pelas ações humanas"
```

---

## 5. Regras Obrigatórias de Validação

### 5.1 Existência

* O bloco `lanes` é obrigatório na versão 1.0 
* Deve ser um objeto JSON
* Pode conter 1 ou mais lanes

---

### 5.2 Unicidade

* `lane_id` deve ser único
* `order` pode repetir?
  ➜ Recomendação: NÃO repetir
  ➜ Regra sugerida: `order` deve ser único (boa prática)

---

### 5.3 Referência por nós

Todo nó deve conter:

```json
"lane": "lane_id"
```

Regras:

* `nodes[*].lane` deve existir em `lanes`
* Não pode haver nó referenciando lane inexistente 

---

## 6. O que `lanes` NÃO faz

Importante para evitar confusão conceitual:

* Não cria isolamento lógico
* Não bloqueia conexões entre lanes
* Não define permissões
* Não altera execução
* Não interfere em `edges`
* Não altera `branches`
* Não define prioridade de fluxo

Ela é puramente estrutural e organizacional.

---

## 7. Relação com `nodes`

Cada nó DEVE declarar uma lane:

```json
"nodes": {
  "node_1": {
    "type": "process",
    "lane": "backend",
    "label": "Processar requisição"
  }
}
```

Validação obrigatória:

* `lane` deve existir em `lanes`
* `lane` não pode ser null
* `lane` não pode ser omitida

---

## 8. Relação com `edges`

`edges` ignora lanes.

Uma conexão pode ligar:

* Nó da lane A → nó da lane B
* Nó da lane Backend → nó da lane Usuário

Isso é permitido e comum.

---

## 9. Impacto na Renderização

Renderizadores devem:

* Agrupar nós por lane
* Ordenar lanes por `order`
* Exibir título da lane
* Delimitar visualmente cada lane

Exemplo de organização visual:

```
[Usuário]
  start → clicar botão

[Sistema]
  validar dados → processar → end
```

---

## 10. Exemplos

### 10.1 Exemplo mínimo válido

```json
"lanes": {
  "main": {
    "title": "Principal",
    "order": 1
  }
}
```

---

### 10.2 Exemplo com múltiplas lanes

```json
"lanes": {
  "user": {
    "title": "Usuário",
    "order": 1,
    "description": "Interações humanas"
  },
  "api": {
    "title": "API",
    "order": 2,
    "description": "Camada de backend"
  },
  "db": {
    "title": "Banco de Dados",
    "order": 3
  }
}
```

---

## 11. Validações que o Engine Deve Executar

Checklist:

* [ ] `lanes` existe
* [ ] `lanes` é objeto
* [ ] Pelo menos uma lane existe
* [ ] Todos os `lane_id` são únicos
* [ ] Todos possuem `title`
* [ ] Todos possuem `order`
* [ ] Nenhum `nodes[*].lane` aponta para lane inexistente

Erros sugeridos:

* `E_LANES_MISSING`
* `E_LANE_DUPLICATE_ID`
* `E_LANE_ORDER_DUPLICATE`
* `E_NODE_LANE_NOT_FOUND`
* `E_LANE_TITLE_MISSING`
* `E_LANE_ORDER_MISSING`

---

## 12. Boas Práticas

### 12.1 Use nomes semânticos

Exemplos bons:

* `frontend`
* `backend`
* `user`
* `system`
* `financeiro`

Evite:

* `lane1`
* `laneA`
* `x`

---

### 12.2 Mantenha poucas lanes

Fluxos muito fragmentados dificultam leitura.

Ideal:

* 1 a 5 lanes

---

### 12.3 Não use lane para substituir tipo

Errado:

* Criar lane "decisions"
* Criar lane "ends"

Tipos já definem isso.

Lane é responsabilidade organizacional, não estrutural.

---

## 13. Resumo Executivo

O bloco `lanes`:

* É obrigatório no SFF v1.0 
* Define agrupamentos organizacionais
* Não altera lógica do fluxo
* Deve ser referenciado por todos os nós
* Possui `title`, `order` e `description` opcional
* Impacta apenas renderização e organização