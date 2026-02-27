
# Structured Flow Format (SFF) — Guia Visual e Prático

> **Automatize, valide e audite fluxos estruturados com SFF.**

---

## 🚀 O que é este projeto?
Este repositório implementa o núcleo do SFF: um formato declarativo para modelar, validar e compilar fluxogramas de processos de forma determinística, auditável e automatizável.

---

## 🧭 Fluxo de uso — do zero ao log

6. **Exporte o fluxo para outros formatos:**
    ```sh
    python -m core.cli export <caminho_para_arquivo.sff> --format mermaid
    python -m core.cli export <caminho_para_arquivo.sff> --format dot
    python -m core.cli export <caminho_para_arquivo.sff> --format json
    ```
    - Saída esperada:
       - Mermaid: flowchart TB/LR, lanes agrupadas, decisões com labels Sim/Não
       - DOT: arquivo DOT com rankdir, clusters por lane, labels
       - JSON: objeto compilado + layout

5. **Visualize o layout do fluxo (preview):**
    ```sh
    python -m core.cli preview <caminho_para_arquivo.sff>
    ```
    Exemplo:
    ```sh
    python -m core.cli preview exemplo/checkout_flow.sff
    ```
    - Saída esperada:
       ```
       direction: TB
       lanes: ['user', 'pc']
       ranks:
          Rank 0: start (user)
          Rank 1: press_power (user)
          ...
       edges:
          start → press_power
          ...
       Preview ASCII (simplificado):
       start    .
       press_power   .
       ...
       ```

1. **Crie ou edite um arquivo `.sff` (JSON) representando seu fluxo.**
2. **Valide a estrutura:**
   ```sh
   python -m core.cli validate <caminho_para_arquivo.sff>
   ```
   Exemplo:
   ```sh
   python -m core.cli validate exemplo/checkout_flow.sff
   python -m core.cli validate exemplo/order_orchestration_flow.sff
   ```
   - Saída esperada: `Validação estrutural OK` ou lista de erros estruturais.
3. **Compile e valide regras lógicas:**
   ```sh
   python -m core.cli compile <caminho_para_arquivo.sff>
   ```
   Exemplo:
   ```sh
   python -m core.cli compile exemplo/checkout_flow.sff
   python -m core.cli compile exemplo/invalid_logic.sff
   ```
   - Saída esperada: `Compilação OK!` e índices prev/next, ou lista de erros lógicos.
4. **Confira os logs:**
   - Todos os eventos são registrados em `logs/layout_engine.log`.
   - Exemplo:
     ```
     2026-02-27 17:00:00 | INFO  | Compilando arquivo exemplo/checkout_flow.sff
     2026-02-27 17:00:00 | INFO  | Compilação OK
     2026-02-27 17:01:00 | INFO  | Compilando arquivo exemplo/invalid_logic.sff
     2026-02-27 17:01:00 | ERROR | Nó 'end1' não pode ter edges de saída.
     ```

---

## 🧪 Exemplos práticos

### Export CLI — exemplos de saída

#### Mermaid
```
flowchart TB
subgraph user
      start[Início]
      press_power[Pressionar o botão]
end
subgraph pc
      wait_boot[Aguardar]
end
start --> press_power
press_power -->|Sim| wait_boot
```

#### DOT
```
digraph G {
   rankdir=TB;
   subgraph cluster_user {
      label="user";
      start [label="Início"]
      press_power [label="Pressionar o botão"]
   }
   subgraph cluster_pc {
      label="pc";
      wait_boot [label="Aguardar"]
   }
   start -> press_power
   press_power -> wait_boot [label="Sim"]
}
```

#### JSON
```
{
   "sff": { ... },
   "compiled": { ... },
   "layout": { ... },
   "export_version": "1.0"
}
```

### Preview CLI — exemplos de saída

#### Fluxo simples
```
direction: TB
lanes: ['user', 'pc']
ranks:
   Rank 0: start (user)
   Rank 1: press_power (user)
   Rank 2: wait_boot (pc)
edges:
   start → press_power
   press_power → wait_boot
Preview ASCII (simplificado):
start    .
press_power   .
    .   wait_boot
```

#### Fluxo com decision boolean
```
direction: TB
lanes: ['user']
ranks:
   Rank 0: start (user)
   Rank 1: decision1 (user)
   Rank 2: end_true (user), end_false (user)
edges:
   start → decision1
   decision1 → end_true [branch=true]
   decision1 → end_false [branch=false]
Preview ASCII (simplificado):
start
decision1
end_true   end_false
```

#### Fluxo com múltiplas lanes
```
direction: TB
lanes: ['user', 'system']
ranks:
   Rank 0: start (user)
   Rank 1: process1 (system)
   Rank 2: end1 (user)
edges:
   start → process1
   process1 → end1
Preview ASCII (simplificado):
start   .
    .   process1
end1    .
```

### Exemplo válido
- `exemplo/checkout_flow.sff` — fluxo correto, passa em todas as validações.

### Exemplo inválido lógico
- `exemplo/invalid_logic.sff` — possui erro de lógica (end com saída, nó isolado).

---

## 📋 O que é validado?

- Estrutura mínima (blocos obrigatórios: sff, entry, lanes, nodes, edges)
- Regras lógicas:
  - Exatamente 1 nó start, coerente com entry.start
  - Pelo menos 1 end, todos em entry.ends
  - Start sem entrada, end sem saída
  - Todos os nós alcançáveis a partir do start
  - Não permite nós isolados
  - Decision boolean: branches true/false obrigatórios, next existente, edges coerentes

---

## 🛠️ Troubleshooting

- Se ocorrer erro de import, verifique se o diretório `core` possui os arquivos `__init__.py`.
- Se o log não for criado, verifique permissões da pasta `logs/`.
- Para auditoria, mantenha os logs salvos.

---

## 📚 Estrutura do Core

- `core/reader/reader.py`: Leitura de arquivos .sff
- `core/validator/validator.py`: Validação estrutural e lógica
- `core/compiler/compiler.py`: Geração de índices prev/next e validação
- `core/logger/logger.py`: Logging persistente
- `core/cli/cli.py`: Interface de linha de comando

---

## 🤝 Contribua ou evolua

Sugestões, dúvidas ou melhorias? Consulte a documentação, abra uma issue ou contribua diretamente!
