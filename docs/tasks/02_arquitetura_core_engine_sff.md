
# Task 02 — Arquitetura do Core Engine (Compilador SFF)

## Status
🔄 Em definição

---

# 1. Objetivo da Task

Definir a arquitetura do **Core Engine do SFF**, responsável por:

- Ler arquivos `.sff`
- Validar JSON
- Validar estrutura obrigatória
- Validar regras lógicas
- Construir índices internos (`prev` / `next`)
- Gerar estrutura compilada
- Produzir logs claros e rastreáveis
- Permitir preview via terminal

Esta task define a arquitetura do motor.
Não define ainda renderização final.

---

# 2. Papel do Core Engine

O Core Engine é responsável por transformar:

Arquivo `.sff` (JSON declarativo)

→ Estrutura validada  
→ Grafo interno  
→ Estrutura compilada  
→ Base pronta para layout e renderização  

Conforme definido na especificação, o processo de leitura deve executar:

1. Validação JSON  
2. Validação estrutural  
3. Validação lógica  
4. Construção de índices  
5. Geração de estrutura compilada :contentReference[oaicite:4]{index=4}  

---

# 3. Pipeline Oficial do Engine

O pipeline será dividido em fases claras:

---

## 3.1 Fase 1 — Leitura

Entrada:
- Caminho para arquivo `.sff`

Passos:
- Abrir arquivo
- Interpretar como JSON
- Validar sintaxe

Falhas devem gerar:
- ERROR com linha e contexto
- Log persistido

---

## 3.2 Fase 2 — Validação Estrutural

Validar existência obrigatória de:

- `sff`
- `entry`
- `lanes`
- `nodes`
- `edges` :contentReference[oaicite:5]{index=5}  

Validar:

- `sff.version`
- `sff.id`
- `sff.title`
- `sff.direction`

Validar `entry`:
- `start` existe
- `ends` existe
- Tipos corretos :contentReference[oaicite:6]{index=6}  

Validar `lanes`
- IDs únicos
- `title` presente
- `order` presente :contentReference[oaicite:7]{index=7}  

Validar `nodes`
- IDs únicos
- `type`, `lane`, `label` obrigatórios :contentReference[oaicite:8]{index=8}  

Validar `edges`
- `from` e `to` existem
- Coerência com `decision.branches` :contentReference[oaicite:9]{index=9}  

---

## 3.3 Fase 3 — Validação Lógica

Regras obrigatórias:

- Exatamente 1 nó `start`
- Pelo menos 1 nó `end`
- `start` sem entradas
- `end` sem saídas :contentReference[oaicite:10]{index=10}  

Validar:

- Nenhum nó isolado
- Nenhum nó inalcançável
- Todas branches apontam para nós existentes
- Não há contradição entre branches e edges

---

## 3.4 Fase 4 — Construção de Índices

Gerar:

```json
"compiled": {
  "index": {
    "prev": {},
    "next": {}
  }
}
````

Baseado exclusivamente em `edges`.

Regras:

* `prev[node]` → lista de nós que apontam para ele
* `next[node]` → lista de nós que ele aponta

Esses índices não fazem parte do `.sff`, são gerados pelo engine.

---

## 3.5 Fase 5 — Estrutura Compilada

Gerar objeto final:

```json
"compiled": {
  "index": {...},
  "validation": {
    "errors": [],
    "warnings": []
  }
}
```

Se houver erro estrutural:

* Engine não prossegue para layout
* Erro é registrado em log

---

# 4. Arquitetura Interna do Core Engine

Estrutura sugerida:

```
core/
 ├── reader/
 ├── validator/
 ├── compiler/
 ├── layout/
 ├── logger/
 └── cli/
```

Separação de responsabilidades:

* reader → leitura do arquivo
* validator → regras estruturais
* compiler → índices internos
* layout → geração de ranks (Task 01)
* logger → persistência de logs
* cli → execução via terminal

---

# 5. Logging (Obrigatório)

Logs devem ser:

* Persistidos em arquivo
* Classificados como INFO/WARN/ERROR
* Claros e descritivos

Exemplo:

INFO  | Lendo arquivo exemplo.sff
INFO  | Validando estrutura raiz
ERROR | E_ENTRY_START_NOT_FOUND

Seguir padrão definido em `docs/context.md` 

---

# 6. CLI (Interface de Terminal)

O projeto deve permitir execução como:

```
sff validate arquivo.sff
sff compile arquivo.sff
sff preview arquivo.sff
```

Com saída clara:

* Estrutura validada
* Lista de erros
* Índices gerados
* Preview textual simples

---

# 7. Preview Inicial (Terminal)

Nesta fase, o preview pode ser:

* Lista hierárquica
* Representação textual simples
* Impressão de prev/next

Exemplo:

```
START → validate_payment
validate_payment → decision_check
decision_check (true) → success
decision_check (false) → fail
```

Objetivo:

* Confirmar coerência
* Confirmar determinismo
* Validar grafo antes do layout

---

# 8. Critérios de Aceite

A Task 02 estará concluída quando:

* [ ] Arquivo `.sff` pode ser lido via CLI
* [ ] JSON inválido gera erro claro
* [ ] Estrutura inválida gera erro claro
* [ ] Regras lógicas são validadas
* [ ] Índices prev/next são gerados
* [ ] Logs são persistidos
* [ ] Execução é reproduzível via terminal
* [ ] Documentação está atualizada

---

# 9. Fora de Escopo (Task 02)

* Renderização gráfica final
* Animação
* Layout avançado
* Otimização de performance
* Suporte a loops complexos
* Paralelismo

---

# 10. Como Validar

Após implementação:

1. Criar `.sff` mínimo válido
2. Rodar `sff validate`
3. Rodar `sff compile`
4. Conferir logs
5. Conferir índices prev/next
6. Rodar novamente e garantir mesmo resultado

Determinismo é obrigatório.

---

# 11. Resultado Esperado

Ao final da Task 02 teremos:

* Core Engine funcional
* Pipeline claro
* Validação robusta
* Base para layout automático (Task 01)
* Base para renderizadores futuros

Essa task transforma o SFF de especificação em sistema executável.
