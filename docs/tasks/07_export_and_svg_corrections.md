
# Task 07 — Correção do Export + SVG Responsivo + Encoding

## Status
🔄 Em implementação

---

# 1. Objetivo

Corrigir a lógica de exportação e geração de SVG para garantir:

- Salvamento automático correto na pasta `data/export/`
- Suporte a caminho personalizado via parâmetro
- SVG com viewBox correto (sem achatamento ou corte)
- Modo `--lanes-only` realmente renderizando apenas lanes
- Correção definitiva de encoding UTF-8
- Logs rastreáveis e consistentes

Esta task é estrutural e crítica para a estabilidade visual do projeto.

---

# 2. Problemas Identificados

## 2.1 Export não respeita pasta `data/export/`
Atualmente depende de redirect `>` no terminal.
Isso não é comportamento correto do sistema.

## 2.2 `--lanes-only` renderiza nodes indevidamente
O modo deveria renderizar apenas:
- Container
- Lanes
- Titles

## 2.3 SVG está achatado / cortado
Elementos estão sendo renderizados fora do viewBox.

## 2.4 Encoding quebrado
Textos aparecem como:
- `Usu├írio`
- `Dados v├ílidos?`

Problema clássico de encoding incorreto.

---

# 3. Nova Regra de Export (Obrigatória)

## 3.1 Flag `--out` (ou `--output`)

### Comportamento:

### Caso 1 — Usuário NÃO passa `--out`
Salvar automaticamente em:

```

data/export/<basename>.<ext>

```

Exemplo:
```

python -m core.cli export data/input/checkout_flow.sff --format svg

```

Resultado:
```

data/export/checkout_flow.svg

```

Se a pasta `data/export/` não existir:
- Criar automaticamente.

---

### Caso 2 — Usuário passa `--out` como diretório

```

--out data/export/

```

Salvar como:
```

data/export/<basename>.<ext>

```

---

### Caso 3 — Usuário passa `--out` como arquivo completo

```

--out C:\temp\meu.svg

```

Salvar exatamente nesse caminho.

---

## 3.2 CLI deve imprimir:

```

Export OK → data/export/checkout_flow.svg

```

E registrar log INFO com caminho final.

---

# 4. Correção do Modo `--lanes-only`

Se `--lanes-only` estiver ativo:

Renderizar somente:
- Container externo
- Lanes
- Titles

Não renderizar:
- Nodes
- Edges
- Routing
- Shapes internos

Validar via smoke test.

---

# 5. Correção do SVG Achatado

## 5.1 Problema

Elementos estão sendo desenhados fora do viewBox,
gerando corte ou proporção incorreta.

---

## 5.2 Implementação Obrigatória

Após desenhar todos os elementos:

1. Calcular bounding box real:
   - min_x
   - min_y
   - max_x
   - max_y

2. Aplicar padding global

3. Definir:

```

viewBox="min_x min_y width height"
width="width"
height="height"

```

Onde:
```

width  = max_x - min_x
height = max_y - min_y

```

Nenhum elemento pode ultrapassar o viewBox.

---

# 6. Correção de Encoding (UTF-8)

## 6.1 Leitura

Arquivos `.sff` devem ser lidos como UTF-8.

Se falhar:
- Log ERROR claro.

## 6.2 Escrita

SVG deve ser escrito como UTF-8.

Garantir que:
- “Usuário”
- “Válidos”
- “Conclusão”

apareçam corretamente.

---

# 7. Logs Obrigatórios

### INFO
- Caminho final do export
- Bounding box calculado
- width/height finais
- Modo lanes-only ativo ou não

### ERROR
- Path inválido
- Encoding inválido
- Falha ao salvar arquivo

---

# 8. Validação (Smoke Tests)

## 8.1 Export padrão

```

python -m core.cli export data/input/checkout_flow.sff --format svg

```

Checklist:
- [ ] Arquivo salvo em data/export/
- [ ] SVG abre sem cortes
- [ ] Texto com acentuação correta

---

## 8.2 Export custom path

```

python -m core.cli export data/input/checkout_flow.sff --format svg --out data/export/teste.svg

```

Checklist:
- [ ] Arquivo salvo no caminho informado
- [ ] Log informa caminho final

---

## 8.3 Lanes-only

```

python -m core.cli export data/input/checkout_flow.sff --format svg --lanes-only

```

Checklist:
- [ ] Apenas lanes desenhadas
- [ ] Nenhum node presente
- [ ] Container correto

---

# 9. Critério de Aceite (DoD)

- [ ] `--out` implementado corretamente
- [ ] export automático para `data/export/`
- [ ] Pasta criada se inexistente
- [ ] viewBox correto (sem corte)
- [ ] Sem achatamento
- [ ] Encoding corrigido
- [ ] `--lanes-only` respeitado
- [ ] Logs completos
- [ ] README atualizado

---

# 10. Observação Importante

Esta task é de estabilização estrutural.
Não adicionar novas features.
Não modificar layout logic.
Não alterar posicionamento de nodes.

Foco total: estabilidade e previsibilidade do export.
