# Contexto de Trabalho — Agentes (docs/context.md)

Este documento define **como os agentes devem trabalhar** neste repositório: como **ler a estrutura**, **validar fluxo**, **executar testes**, **registrar logs**, **organizar pastas** e **documentar mudanças**.

> Objetivo: garantir **reprodutibilidade**, **clareza**, **rastreabilidade** e **arquitetura escalável** — sem “mexer aleatoriamente” no projeto.

---

## 1) Leitura obrigatória do repositório

### 1.1 Ordem de leitura (sempre que iniciar uma task)
1. **`model/`** → leia a árvore de pastas e arquivos para entender a estrutura existente.
2. **`docs/`** → procure guias, decisões e padrões.
3. **`docs/context/`** → verifique documentação operacional e de arquitetura (fonte de verdade para o “como trabalhar”).
4. **Arquivos raiz** (se existirem) → `README`, `CONTRIBUTING`, `CHANGELOG`, `Makefile`, `pyproject`, `package.json`, etc.

### 1.2 Regra de ouro
Antes de criar algo novo, o agente DEVE:
- **Procurar se já existe** uma pasta/arquivo com a função desejada.
- **Reutilizar e estender** a estrutura existente quando fizer sentido.
- **Evitar duplicação** de padrões, nomenclaturas e caminhos.

---

## 2) Fluxo padrão de execução (como trabalhar em qualquer task)

### 2.1 Passo a passo mínimo
1. **Entender o problema**: o que deve mudar e por quê.
2. **Mapear impacto**: quais arquivos/pastas serão afetados.
3. **Planejar execução**: quais etapas e validações serão usadas.
4. **Implementar com incrementos pequenos**.
5. **Validar via terminal** (sempre).
6. **Registrar logs e evidências** (sempre).
7. **Atualizar documentação** (sempre que houver mudança estrutural/arquitetural).
8. **Revisar consistência** (padrões, pastas, testes, logs, mensagens).

### 2.2 Regra de “não quebrar o fluxo”
Nenhuma alteração é considerada “pronta” se:
- Não for possível **reproduzir localmente via terminal**.
- Não existir **log claro** de sucesso/erro.
- Não estiver **documentado** onde o agente mexeu e como validar.

---

## 3) Validação obrigatória via terminal

O agente DEVE sempre conseguir:
- Executar o projeto (ou parte afetada) via terminal.
- Rodar testes (quando existirem).
- Exibir resultados claros para:
  - Ele próprio (debug),
  - A equipe,
  - Um usuário futuro.

### 3.1 Requisitos mínimos de validação
- Deve existir um caminho reproduzível para:
  - **Build/Run** (executar),
  - **Test** (testar),
  - **Lint/Format** (se houver),
  - **Logs** (ver evidências).

### 3.2 Quando não houver testes
Se o projeto não tiver suíte de testes ainda:
- Crie **um “smoke test” mínimo** (mesmo que seja um script simples).
- Garanta um comando reprodutível no terminal.
- Documente a validação no `docs/context/`.

---

## 4) Testes e reprodutibilidade

### 4.1 Princípios de testes
- Testes devem ser:
  - **Determinísticos** (mesmo input → mesmo output),
  - **Automatizáveis** (rodar por comando),
  - **Fáceis de entender** (nomes claros),
  - **Fáceis de executar** (sem passos manuais confusos).

### 4.2 Regras de ouro
- Não criar “teste” que depende de estado manual invisível.
- Se precisar de variáveis de ambiente:
  - Documentar claramente quais são,
  - Fornecer exemplo (ex.: `.env.example`),
  - Falhar com mensagem clara se estiver faltando.

---

## 5) Logs: obrigatório, claro e rastreável

Logs são essenciais para:
- Diagnóstico de falhas,
- Confirmação de sucesso,
- Auditoria e rastreio de comportamento,
- Suporte e manutenção.

### 5.1 Regras de logs (obrigatórias)
- Toda operação crítica deve registrar:
  - **início** (o que vai fazer),
  - **resultado** (sucesso/erro),
  - **contexto mínimo** (id, arquivo, etapa, etc. sem expor segredos).
- Mensagens devem ser:
  - **Humanas e claras**,
  - **Sem ambiguidades**,
  - **Úteis para usuário e time técnico**.

### 5.2 Onde registrar logs
O projeto deve ter uma pasta/padrão definido para logs. Regra:
- Não espalhar logs “em qualquer lugar”.
- Se ainda não existir um padrão, criar e documentar em `docs/context/architecture.md` (ou arquivo equivalente).

### 5.3 Padrão de mensagem (recomendado)
- `INFO` para passos normais.
- `WARN` para comportamento inesperado mas recuperável.
- `ERROR` para falha com contexto e ação sugerida.

Exemplos de conteúdo mínimo:
- O que falhou,
- Onde falhou,
- Por que falhou (se conhecido),
- O que o usuário pode fazer (ação sugerida).

---

## 6) Governança de pastas e arquitetura (não criar “qualquer pasta”)

### 6.1 Regras para criar pastas/arquivos
Antes de criar uma nova pasta:
1. Verifique se já existe uma pasta adequada.
2. Se existir, **use a existente**.
3. Se não existir, justifique:
   - Por que é necessária,
   - Por que não se encaixa nas atuais,
   - Qual padrão de nome será usado.

### 6.2 Padrões de organização
- Nomeação clara e consistente.
- Separar por responsabilidade (ex.: core, infra, adapters, docs, scripts, tests).
- Evitar pastas genéricas como `tmp/`, `new/`, `misc/` sem necessidade real.
- Evitar duplicar estruturas (ex.: `services/` e `service/`).

### 6.3 “Fonte de verdade” da arquitetura
A arquitetura do projeto deve estar descrita em um arquivo dentro de `docs/context/` (ex.: `docs/context/architecture.md`).

Sempre que o agente:
- criar um novo módulo,
- mover arquivos,
- introduzir um novo padrão,
- alterar fluxo de execução,
- adicionar uma dependência relevante,
ele DEVE:
- atualizar o documento de arquitetura,
- registrar “o que mudou” e “como validar”.

---

## 7) Documentação mínima por mudança

### 7.1 O que documentar (obrigatório)
Para qualquer mudança relevante, registrar:
- **O que foi feito**
- **Por que foi feito**
- **Onde foi feito** (caminhos)
- **Como validar** (comandos de terminal)
- **Evidências** (logs esperados, exemplos de saída)

### 7.2 Onde documentar
- Mudanças operacionais e de execução: `docs/context/`
- Mudanças de arquitetura/estrutura: `docs/context/architecture.md`
- Mudanças de fluxo/padrão de trabalho: este `docs/context.md` (se necessário)

---

## 8) Padrão de commit/entrega (para agentes)

### 8.1 “Definição de pronto” (DoD)
Uma task só está pronta quando:
- [ ] Foi implementada com impacto mapeado,
- [ ] Foi validada via terminal,
- [ ] Os testes rodam (ou existe smoke test),
- [ ] Os logs estão claros e registráveis,
- [ ] A documentação foi atualizada,
- [ ] Nenhuma pasta foi criada “sem justificativa”,
- [ ] Existe um caminho de reprodução simples.

### 8.2 O que evitar (proibido)
- “Achar” que funciona sem validar no terminal.
- Alterar estrutura de pastas sem consultar o modelo existente.
- Criar pastas duplicadas ou paralelas sem necessidade.
- Adicionar dependências sem justificar e documentar.
- Mensagens de erro genéricas (“deu ruim”, “falhou”) sem contexto.

---

## 9) O que perguntar antes de fazer (quando houver ambiguidade)

Se a task estiver ambígua, o agente deve perguntar **antes de codar**:
- Qual é o **resultado esperado** (ex.: saída, formato, comportamento).
- Qual é o **limite do escopo** (o que não deve ser feito).
- Quais são os **comandos esperados** para validar.
- Onde devem ficar:
  - logs,
  - arquivos novos,
  - documentação.

**Regra:** se a decisão impacta arquitetura ou pastas, pergunte primeiro (ou siga o documento de arquitetura se já estiver definido).

---

## 10) Checklist operacional rápido (copiar e usar)

- [ ] Li `model/` e entendi a estrutura antes de alterar.
- [ ] Procurei pastas/arquivos existentes antes de criar novos.
- [ ] Planejei validação via terminal.
- [ ] Rodei comandos de execução e validação.
- [ ] Garanti logs claros (sucesso e erro).
- [ ] Registrei evidências (saídas esperadas).
- [ ] Atualizei `docs/context/architecture.md` quando necessário.
- [ ] Documentei “o que foi feito” + “como validar”.

---

## 11) Padrão recomendado para “Como validar” na documentação

Sempre incluir uma seção como:

### Como validar
1. Comando A (explicar o que deve acontecer)
2. Comando B (explicar o que deve acontecer)
3. Onde ver logs
4. Como reproduzir erro comum (se relevante)

> A validação deve ser executável por qualquer pessoa do time sem conhecimento prévio do histórico.

---
## Evidências e Instruções Finais (2026-02-27)
- Testes realizados com arquivos válidos: `exemplo/checkout_flow.sff`, `exemplo/order_orchestration_flow.sff`
- Comando utilizado:
  - `python -m core.cli validate exemplo/checkout_flow.sff`
  - `python -m core.cli validate exemplo/order_orchestration_flow.sff`
- Saída esperada: `Validação estrutural OK`
- Logs registrados em `logs/layout_engine.log`:
  - `2026-02-27 16:19:29 | INFO  | Validando arquivo ./exemplo/checkout_flow.sff`
  - `2026-02-27 16:19:29 | INFO  | Validação estrutural OK`
  - `2026-02-27 16:22:02 | INFO  | Validando arquivo ./exemplo/order_orchestration_flow.sff`
  - `2026-02-27 16:22:02 | INFO  | Validação estrutural OK`

---
## Checklist Final de Entrega
- [x] Documentação e arquitetura atualizadas
- [x] Validação terminal reproduzível
- [x] Logs e evidências registradas
- [x] README e instruções de uso claros

---

## 12) Encerramento

Este `docs/context.md` é o **manual operacional** do projeto para agentes.
Ele existe para garantir que o desenvolvimento seja:
- escalável,
- organizado,
- reproduzível,
- auditável,
- fácil de manter.

Sempre que o projeto evoluir em arquitetura e processos, este documento deve ser ajustado para refletir o “modo certo” de trabalhar.