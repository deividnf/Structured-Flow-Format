# README — Teste e Validação Inicial do SFF

Este projeto implementa o núcleo do Structured Flow Format (SFF) para leitura, validação e logging de arquivos .sff (JSON).

## Estrutura do Core
- `core/reader/reader.py`: Leitura de arquivos .sff
- `core/validator/validator.py`: Validação estrutural
- `core/compiler/compiler.py`: Geração de índices prev/next
- `core/layout/layout.py`: Estrutura base para layout
- `core/logger/logger.py`: Logging persistente
- `core/cli/cli.py`: Interface de linha de comando

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
