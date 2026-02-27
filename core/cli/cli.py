"""
core/cli/cli.py
Interface de linha de comando para validação e leitura de arquivos SFF.
"""
import sys


import os
from core.reader.reader import read_sff_file
from core.validator.validator import validate_sff_structure
from core.compiler.compiler import compile_sff
from core.layout.layout import generate_layout
from core.logger.logger import Logger
from core.exporters.mermaid_exporter import export_mermaid
from core.exporters.dot_exporter import export_dot
from core.exporters.json_exporter import export_json

logger = Logger()

def main():
    if len(sys.argv) < 3:
        print("Uso: python -m core.cli.cli <validate|compile|preview|export> <arquivo.sff> [--format mermaid|dot|json]")
        sys.exit(1)
    command = sys.argv[1]
    filepath = sys.argv[2]
    export_format = None
    if command == "export":
        # Detecta --format
        if '--format' in sys.argv:
            idx = sys.argv.index('--format')
            if len(sys.argv) > idx + 1:
                export_format = sys.argv[idx + 1].lower()
        if not export_format:
            print("Formato de exportação obrigatório: --format mermaid|dot|json")
            sys.exit(1)
    if command == "validate":
        logger.info(f"Validando arquivo {filepath}")
        try:
            data = read_sff_file(filepath)
            errors = validate_sff_structure(data)
            if errors:
                for err in errors:
                    logger.error(err)
                print("Erros de validação encontrados:")
                for err in errors:
                    print(f"- {err}")
                sys.exit(2)
            else:
                logger.info("Validação estrutural OK")
                print("Validação estrutural OK")
        except Exception as e:
            logger.error(str(e))
            print(f"Erro: {e}")
            sys.exit(3)
    elif command == "compile":
        logger.info(f"Compilando arquivo {filepath}")
        try:
            data = read_sff_file(filepath)
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
            else:
                logger.info("Compilação OK")
                print("Compilação OK!")
                print("Índices prev/next:")
                print("prev:", compiled['index']['prev'])
                print("next:", compiled['index']['next'])
                if warnings:
                    print("Avisos:")
                    for w in warnings:
                        logger.warn(w)
                        print(f"- {w}")
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
        logger.info(f"Export iniciado: formato={export_format}, arquivo={filepath}")
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
            output = None
            if export_format == 'mermaid':
                output = export_mermaid(data, layout)
            elif export_format == 'dot':
                output = export_dot(data, layout)
            elif export_format == 'json':
                output = export_json(data, compiled, layout)
            elif export_format == 'svg':
                from core.exporters.svg_exporter import export_svg
                output = export_svg(data, layout)
                # Salvar arquivo SVG em export/
                input_name = os.path.splitext(os.path.basename(filepath))[0]
                out_path = os.path.join('export', f'{input_name}.svg')
                try:
                    with open(out_path, 'w', encoding='utf-8') as f:
                        f.write(output)
                    logger.info(f"[SVG Export] SVG salvo em {out_path}")
                except Exception as e:
                    logger.error(f"[SVG Export] Falha ao salvar SVG: {e}")
                    print(f"Erro ao salvar SVG: {e}")
                    sys.exit(2)
            else:
                logger.error(f"Formato de exportação inválido: {export_format}")
                print(f"Formato de exportação inválido: {export_format}")
                sys.exit(1)
            if export_format != 'svg':
                print(output)
            logger.info(f"Export gerado com sucesso: output={export_format}")
            sys.exit(0)
        except Exception as e:
            logger.error(str(e))
            print(f"Erro: {e}")
            sys.exit(3)
    else:
        print(f"Comando desconhecido: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
