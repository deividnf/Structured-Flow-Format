
# Structured Flow Format (SFF) — Guia Visual e Prático

> **Automatize, valide e audite fluxos estruturados com SFF.**

---

## 🚀 O que é este projeto?
Este repositório implementa o núcleo do SFF: um formato declarativo para modelar, validar e compilar fluxogramas de processos de forma determinística, auditável e automatizável.

---

## 🧭 Fluxo de uso — do zero ao log

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
