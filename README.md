# README — Teste e Validação Inicial do SFF

Este projeto implementa o núcleo do Structured Flow Format (SFF) para leitura, validação e logging de arquivos .sff (JSON).

---

## Validação Terminal — Guia Completo

### 1. Comando de validação
Execute na raiz do projeto:
```
python -m core.cli validate <caminho_para_arquivo.sff>
```
Exemplo:
```
python -m core.cli validate exemplo/checkout_flow.sff
python -m core.cli validate exemplo/order_orchestration_flow.sff
```

### 2. Saída esperada
- Se o arquivo estiver correto: `Validação estrutural OK`
- Se houver erro estrutural: lista de erros exibida e registrada em log

### 3. Logs
- Todos os eventos são registrados em `logs/layout_engine.log`
- Exemplo de log:
   - `2026-02-27 16:19:29 | INFO  | Validando arquivo ./exemplo/checkout_flow.sff`
   - `2026-02-27 16:19:29 | INFO  | Validação estrutural OK`
- Mensagens de erro seguem o padrão:
   - `2026-02-27 16:16:48 | ERROR | Bloco obrigatório ausente: sff`

### 4. Evidências de execução
- Testes realizados com arquivos válidos e inválidos.
- Logs e saídas conferidos conforme esperado.

### 5. Como reproduzir
1. Crie ou copie um arquivo `.sff` válido para a pasta desejada.
2. Execute o comando de validação.
3. Verifique a saída no terminal e o conteúdo do log.
4. Para auditoria, mantenha os logs salvos.

---

## Estrutura do Core

---

## Como testar a validação

1. Certifique-se de ter Python 3.8+ instalado.
2. Navegue até a raiz do projeto:
   ```
   cd Structured Flow Format
   ```
3. Execute o comando de validação:
   ```
   python -m core.cli validate docs/model/example.sff.json
   ```

### Saída esperada
- "Validação estrutural OK" se o arquivo estiver correto.
- Em caso de erro, serão exibidas mensagens de erro e registradas em `logs/layout_engine.log`.

### Logs
- Os logs são persistidos em `logs/layout_engine.log`.
- Mensagens INFO, ERROR e WARN são registradas conforme execução.

## Estrutura de arquivos para teste
- Utilize o arquivo de exemplo: `docs/model/example.sff.json`

## Troubleshooting
- Se ocorrer erro de import, verifique se o diretório `core` possui os arquivos `__init__.py`.
- Se o log não for criado, verifique permissões da pasta `logs/`.

---

Qualquer dúvida ou erro, consulte os logs e reporte na documentação.
