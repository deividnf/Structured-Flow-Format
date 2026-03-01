"""
core/cli/cli.py
Interface de linha de comando para validação e leitura de arquivos SFF.
"""
import sys


from core.reader.reader import read_sff_file
from core.validator.validator import validate_sff_structure
from core.compiler.compiler import compile_sff
from core.layout.layout import generate_layout
from core.logger.logger import Logger
from core.exporters.mermaid_exporter import export_mermaid
from core.exporters.dot_exporter import export_dot
from core.exporters.json_exporter import export_json
from core.exporters.lanes_only_exporter import export_lanes_only

logger = Logger()

def main():
    if len(sys.argv) < 3:
        print("Uso: python -m core.cli.cli <validate|compile|preview|export> <arquivo.sff> [--format mermaid|dot|json]")
        sys.exit(1)
    command = sys.argv[1]
    filepath = sys.argv[2]
    output_path = None
    out_flag = None
    if '--out' in sys.argv:
        out_flag = '--out'
    elif '--output' in sys.argv:
        out_flag = '--output'
    export_format = None
    lanes_only = False
    # Detecta --format e --lanes-only ANTES de usar export_format
    if command == "compile":
        import os
        from core.compiler.cff_compiler import CFFCompiler

        base_name = os.path.splitext(os.path.basename(filepath))[0]
        output_path = os.path.join('data', 'compiled', f"{base_name}.cpff")
        logger.info(f"Compilando arquivo {filepath}")
        try:
            data = read_sff_file(filepath)

            # Reutiliza compile_sff apenas para validação lógica
            compiled = compile_sff(data)
            errors = compiled['validation']['errors']
            warnings = compiled['validation']['warnings']
            if errors:
                for err in errors:
                    logger.error(err)
                print("Erros de validação lógica encontrados:")
                for err in errors:
                    print(f"- {err}")
                sys.exit(1)

            # Gera CFF formal conforme MD11/MD12/MD18/MD19
            cff_compiler = CFFCompiler(data)
            cff_data = cff_compiler.compile()

            import json
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(cff_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Compilação CFF OK! Salvo em: {output_path}")
            print(f"Compilação CFF OK! Salvo: {output_path}")
            sys.exit(0)
        except Exception as e:
            logger.error(str(e))
            print(f"Erro: {e}")
            sys.exit(3)
    elif command == "preview":
        logger.info(f"Preview do layout do arquivo {filepath}")
        try:
            data = read_sff_file(filepath)
            compiled = compile_sff(data)
            errors = compiled['validation']['errors']
            if errors:
                for err in errors:
                    logger.error(err)
                print("Erros de validação lógica encontrados:")
                for err in errors:
                    print(f"- {err}")
                sys.exit(1)
            layout = generate_layout(data, compiled)
            direction = data.get('sff', {}).get('direction', 'TB')
            print(f"direction: {direction}")
            print(f"lanes: {layout['lane_order']}")
            print("ranks:")
            # Agrupar por rank
            rank_nodes = {}
            for node_id, rank in layout['ranks'].items():
                rank_nodes.setdefault(rank, []).append(node_id)
            for r in sorted(rank_nodes):
                print(f"  Rank {r}: ", end='')
                print(", ".join(f"{n} ({data['nodes'][n]['lane']})" for n in rank_nodes[r]))
            print("edges:")
            for edge in data.get('edges', []):
                branch = edge.get('branch')
                label = edge.get('label')
                s = f"  {edge['from']} → {edge['to']}"
                if branch:
                    s += f" [branch={branch}]"
                if label:
                    s += f" [label={label}]"
                print(s)
            # Preview ASCII simples (opcional)
            print("\nPreview ASCII (simplificado):")
            grid = {}
            for node_id, (x, y) in layout['positions'].items():
                grid[(x, y)] = node_id
            max_x = max((x for x, y in grid), default=0)
            max_y = max((y for x, y in grid), default=0)
            for y in range(max_y + 1):
                row = []
                for x in range(max_x + 1):
                    node = grid.get((x, y), '.')
                    row.append(node.center(8) if node != '.' else '   .   ')
                print(' '.join(row))
            logger.info("Preview gerado com sucesso")
            sys.exit(0)
        except Exception as e:
            logger.error(str(e))
            print(f"Erro: {e}")
            sys.exit(3)
    elif command == "export":
        # Interpretar flags de formato e lanes-only para export
        if '--format' in sys.argv:
            idx = sys.argv.index('--format')
            if len(sys.argv) > idx + 1:
                export_format = sys.argv[idx + 1].lower()
        if '--lanes-only' in sys.argv:
            lanes_only = True
        if not export_format:
            print("Formato de exportação obrigatório: --format mermaid|dot|json|svg")
            sys.exit(1)

        logger.info(f"Export iniciado: formato={export_format}, arquivo={filepath}, lanes_only={lanes_only}")
        try:
            import os
            # 1. Definir caminho de saída (Regras Task 07)
            base_name = os.path.splitext(os.path.basename(filepath))[0]
            # Se export_format for json, usar .cpff como extensão
            ext = 'cpff' if export_format == 'json' else (export_format if export_format else 'txt')

            if out_flag:
                idx = sys.argv.index(out_flag)
                out_value = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else None
                
                if out_value:
                    if os.path.isdir(out_value):
                        # Caso 2: Usuário passa diretório
                        output_path = os.path.join(out_value, f"{base_name}.{ext}")
                    else:
                        # Caso 3: Usuário passa arquivo completo
                        # Se export_format for json e o usuário passar .json, troca para .cpff
                        if export_format == 'json' and out_value and out_value.endswith('.json'):
                            output_path = out_value[:-5] + '.cpff'
                        else:
                            output_path = out_value
                else:
                    # Fallback (não deveria ocorrer se CLI validado)
                    output_path = os.path.join('data', 'export', f"{base_name}.{ext}")
            else:
                # Caso 1: Usuário NÃO passa --out
                output_path = os.path.join('data', 'export', f"{base_name}.{ext}")

            # 2. Garantir que o diretório de saída existe
            out_dir = os.path.dirname(output_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)

            # 3. Ler e processar arquivo
            if filepath.endswith('.cpff'):
                import json
                from core.layout.cff_engine import CFFEngine
                with open(filepath, 'r', encoding='utf-8') as f:
                    cpff_data = json.load(f)
                # Log resumo do CFF antes do layout (MD19)
                stats = cpff_data.get("cpff", {}).get("stats", {})
                logger.info(
                    "[CFF-PIPELINE] cpff stats: N={nodes_total}, E={edges_total}, L={lanes_total}, "
                    "decisions={decision_nodes}, branches={branch_edges}, joins={joins}, "
                    "cycles={cycles_total}, max_cycle_depth={max_cycle_depth}, B_max={max_branches_per_rank}, "
                    "T_max={max_tracks_per_lane}".format(**{
                        **{
                            "nodes_total": stats.get("nodes_total", 0),
                            "edges_total": stats.get("edges_total", 0),
                            "lanes_total": stats.get("lanes_total", 0),
                            "decision_nodes": stats.get("decision_nodes", 0),
                            "branch_edges": stats.get("branch_edges", 0),
                            "joins": stats.get("joins", 0),
                            "cycles_total": stats.get("cycles_total", 0),
                            "max_cycle_depth": stats.get("max_cycle_depth", 0),
                            "max_branches_per_rank": stats.get("max_branches_per_rank", 0),
                            "max_tracks_per_lane": stats.get("max_tracks_per_lane", 0),
                        }
                    })
                )
                engine = CFFEngine(cpff_data)
                layout = engine.generate()
                # Layout_result contém bloco de complexidade MD19
                complexity = layout.get("complexity", {})
                if complexity:
                    logger.info(
                        "[CFF-PIPELINE] layout complexity: N={N}, E={E}, L={L}, D_max={D_max}, "
                        "T_max={T_max}, B_max={B_max}, cycles={cycles_total}, max_cycle_depth={max_cycle_depth}, "
                        "height≈{h}, width≈{w}".format(
                            N=complexity.get("N", 0),
                            E=complexity.get("E", 0),
                            L=complexity.get("L", 0),
                            D_max=complexity.get("D_max", 0),
                            T_max=complexity.get("T_max", 0),
                            B_max=complexity.get("B_max", 0),
                            cycles_total=complexity.get("cycles_total", 0),
                            max_cycle_depth=complexity.get("max_cycle_depth", 0),
                            h=int(complexity.get("estimated_height", 0)),
                            w=int(complexity.get("estimated_width", 0)),
                        )
                    )
                data = cpff_data["sff_source"] # mock original data for exporters
                compiled = {'validation': {'errors': [], 'warnings': []}} # mock for exporters
            else:
                data = read_sff_file(filepath)
                compiled = compile_sff(data)

                if compiled['validation']['errors']:
                    for err in compiled['validation']['errors']:
                        logger.error(err)
                    print("Erros de validação lógica encontrados:")
                    for err in compiled['validation']['errors']:
                        print(f"- {err}")
                    sys.exit(1)
                
                from core.layout.layout import generate_layout
                layout = generate_layout(data, compiled)
            
            if compiled['validation']['errors']:
                for err in compiled['validation']['errors']:
                    logger.error(err)
                print("Erros de validação lógica encontrados:")
                for err in compiled['validation']['errors']:
                    print(f"- {err}")
                sys.exit(1)

            # 4. Gerar saída conforme formato
            output = None
            if export_format == 'svg':
                if filepath.endswith('.cpff'):
                    from core.exporters.cff_svg_exporter import export_cff_svg
                    output = export_cff_svg(data, layout)
                else:
                    from core.exporters.svg_exporter import export_svg
                    if lanes_only:
                        output = export_lanes_only(data, lanes_only=True)
                    else:
                        output = export_svg(data, layout)
            elif export_format == 'mermaid':
                output = export_mermaid(data, layout)
            elif export_format == 'dot':
                output = export_dot(data, layout)
            elif export_format == 'json':
                output = export_json(data, compiled if not filepath.endswith('.cpff') else None, layout)
            else:
                logger.error(f"Formato de exportação inválido: {export_format}")
                print(f"Formato de exportação inválido: {export_format}")
                sys.exit(1)

            # 5. Salvar e reportar
            if output_path and output:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(output)
                print(f"Export OK → {output_path}")
                logger.info(f"Export OK → {output_path}")
                sys.exit(0)
            else:
                print(output)
                sys.exit(0)

        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(str(e))
            print(f"Erro: {e}")
            sys.exit(3)
    else:
        print(f"Comando desconhecido: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
