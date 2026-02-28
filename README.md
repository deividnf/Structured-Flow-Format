## 🖼️ Como visualizar o SVG gerado (lanes-only)


Após rodar o comando:
```sh
python -m core.cli export data/example/checkout_flow.sff --format svg --lanes-only
```
O arquivo será salvo automaticamente em:
```
data/export/checkout_flow.svg
```
Abra o arquivo gerado no VS Code (basta clicar) ou arraste para o navegador. Você verá um bloco único dividido em faixas, com títulos na esquerda (TB) ou topo (LR).

Exemplo visual TB:
![lanes-only TB](docs/screenshots/lanes_only_tb.png)

Exemplo visual LR:
![lanes-only LR](docs/screenshots/lanes_only_lr.png)

Se preferir, use o comando `code data/export/checkout_flow.svg` para abrir direto no VS Code.

### Exportando para caminho customizado
```sh
python -m core.cli export data/example/checkout_flow.sff --format svg --lanes-only --out data/export/meu_arquivo.svg
```
O arquivo será salvo exatamente no caminho informado.

### Logs de exemplo (refino BPMN)
```
[LANES-ONLY] direction=TB, n_lanes=3
[LANES-ONLY] TB: container x=24, y=24, w=956, h=240
[LANES-ONLY] Lane user TB: x=24, y=24, w=956, h=240, title="Usuário"
[LANES-ONLY] Lane system TB: x=24, y=264, w=956, h=240, title="Sistema"
[LANES-ONLY] Lane gateway TB: x=24, y=504, w=956, h=240, title="Gateway"
[LANES-ONLY] TB: total_width=1004, total_height=768
Export OK → data/export/checkout_flow.svg
```
7. **Exportar apenas as lanes (boxes/baias) em SVG:**
    ```sh
    python -m core.cli export <caminho_para_arquivo.sff> --format svg --lanes-only
    ```
    - Saída esperada:
       - SVG com apenas as lanes desenhadas, sem nodes/edges/routing
       - direction=TB: lanes empilhadas, título vertical na esquerda
       - direction=LR: lanes lado a lado, título horizontal no topo
       - Lanes “grudadas” (gap pequeno), viewBox auto-ajustado
    - Logs:
       - INFO direction, n_lanes, dimensões finais, posição/tamanho de cada lane
       - INFO caminho final do arquivo
       - ERROR se direction inválida ou lanes vazias

## 🧪 Validação Visual Lanes-Only

### TB (empilhadas)
1. Use um .sff com 3 lanes (user/system/gateway)
2. Execute:
   ```sh
   python -m core.cli export data/example/checkout_flow.sff --format svg --lanes-only > data/export/lanes_only_tb.svg
   ```
3. Abra o SVG gerado (ex: VS Code, navegador)
4. Confirme:
   - Lanes empilhadas
   - Títulos na esquerda, rotacionados
   - Lanes grudadas
   - viewBox correto

### LR (lado a lado)
1. Use um .sff com direction=LR
2. Execute:
   ```sh
   python -m core.cli export data/example/checkout_flow_lr.sff --format svg --lanes-only > data/export/lanes_only_lr.svg
   ```
3. Abra o SVG gerado
4. Confirme:
   - Lanes lado a lado
   - Títulos no topo, horizontal
   - Lanes grudadas
   - viewBox correto

### Logs de exemplo
```
[LANES-ONLY] direction=TB, n_lanes=3
[LANES-ONLY] Lane user TB: x=24, y=24, w=956, h=240, title="Usuário"
[LANES-ONLY] Lane system TB: x=24, y=278, w=956, h=240, title="Sistema"
[LANES-ONLY] Lane gateway TB: x=24, y=532, w=956, h=240, title="Gateway"
```

## 📝 Logs detalhados de nodes e validação visual

Ao exportar para SVG, o sistema gera logs completos em `logs/layout_engine.log` para cada node, incluindo:
- Posição (x, y)
- Limites da lane
- Se o node está dentro da lane
- Distância para o próximo node

Exemplo de log:
```
[NODE] fill_data label='Preencher dados de pagamento' lane='user' x=106 y=174 dentro_lane=True lane_top=80 lane_bottom=204 dist_next=22
[NODE] validate_data label='Validar dados informados' lane='system' x=466 y=452 dentro_lane=True lane_top=260 lane_bottom=384 dist_next=24
```
Esses logs ajudam a auditar o layout, identificar nodes fora da faixa e ajustar o espaçamento.

## 🧪 Validação visual responsiva
- Todos os nodes devem aparecer dentro das faixas (lanes) no SVG.
- Se algum node sair da lane, verifique os logs para identificar o problema.
- Ajuste o modelo .sff ou os parâmetros de layout se necessário.

## 🛠️ Troubleshooting layout SVG
- Se nodes estiverem fora das lanes, confira os logs detalhados.
- Verifique se o arquivo .sff está correto e se os ranks/lanes estão bem definidos.
- Para auditoria, mantenha os logs salvos e compare com o visual do SVG.

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
    python -m core.cli preview data/example/checkout_flow.sff
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
   python -m core.cli validate data/example/checkout_flow.sff
   python -m core.cli validate data/example/order_orchestration_flow.sff
   ```
   - Saída esperada: `Validação estrutural OK` ou lista de erros estruturais.
3. **Compile e valide regras lógicas:**
   ```sh
   python -m core.cli compile <caminho_para_arquivo.sff>
   ```
   Exemplo:
   ```sh
   python -m core.cli compile data/example/checkout_flow.sff
   python -m core.cli compile data/example/invalid_logic.sff
   ```
   - Saída esperada: `Compilação OK!` e índices prev/next, ou lista de erros lógicos.
4. **Confira os logs:**
   - Todos os eventos são registrados em `logs/layout_engine.log`.
   - Exemplo:
     ```
     2026-02-27 17:00:00 | INFO  | Compilando arquivo data/example/checkout_flow.sff
     2026-02-27 17:00:00 | INFO  | Compilação OK
     2026-02-27 17:01:00 | INFO  | Compilando arquivo data/example/invalid_logic.sff
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
- `data/example/checkout_flow.sff` — fluxo correto, passa em todas as validações.

### Exemplo inválido lógico
- `data/example/invalid_logic.sff` — possui erro de lógica (end com saída, nó isolado).

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
