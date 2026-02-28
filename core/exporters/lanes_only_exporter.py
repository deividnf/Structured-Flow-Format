"""
Exporta lanes e nodes em SVG, centralizando e adaptando tamanho conforme regras BPMN clássicas. Não desenha edges/routing avançado.
"""
import math
from core.logger.logger import Logger
logger = Logger()

# Parâmetros fixos
LANE_GAP = 0
PADDING = 24
TITLE_BAR = 56
FONT_TITLE = 20
NODE_W = 140
NODE_H = 44
START_END_R = 18
DECISION_W = 60
DECISION_H = 60
FONT_NODE = 13
COL_GAP = 180
ROW_GAP = 90
LANE_PADDING = 12
RANK_GAP = 90
LANE_BODY_W = 480
LANE_BODY_H = 180

def wrap_text(text, max_chars):
    words = text.split()
    lines = []
    line = ''
    for word in words:
        if len(line) + len(word) + 1 <= max_chars:
            line += (' ' if line else '') + word
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines if lines else ['']

def export_lanes_only(data, lanes_only=False):
    direction = data.get('sff', {}).get('direction', 'TB')
    lanes_dict = data.get('lanes', {})
    if not lanes_dict:
        logger.error('[LANES-ONLY] Nenhuma lane encontrada.')
        return '<svg><text x="10" y="20" fill="red">Erro: Nenhuma lane encontrada</text></svg>'

    # 1. Preparar lanes e nodes
    lanes = [{**props, 'id': lane_id} for lane_id, props in lanes_dict.items()]
    lanes_sorted = sorted(lanes, key=lambda l: l.get('order', 0))
    nodes = data.get('nodes', {})
    layout = data.get('layout', {})
    node_positions = layout.get('positions', {})

    # 2. Calcular dimensões dinâmicas das lanes
    # Cada lane deve ser grande o suficiente para conter seus nodes
    lane_content_size = {} # Para TB: (max_x_grid, max_y_grid), para LR: (max_x_grid, max_y_grid)
    
    for lane in lanes_sorted:
        lane_id = lane['id']
        lane_nodes = [nid for nid, n in nodes.items() if n.get('lane') == lane_id]
        
        max_col = 0
        max_row = 0
        
        if lane_nodes:
            for nid in lane_nodes:
                if nid in node_positions:
                    gx, gy = node_positions[nid]
                else:
                    gx = nodes[nid].get('col_index', 0)
                    gy = nodes[nid].get('rank_global', nodes[nid].get('row_index', 0))
                max_col = max(max_col, gx)
                max_row = max(max_row, gy)
        
        lane_content_size[lane_id] = (max_col, max_row)

    lane_widths = {}
    lane_heights = {}
    
    for lane in lanes_sorted:
        lane_id = lane['id']
        max_col, max_row = lane_content_size[lane_id]
        
        if direction == 'TB':
            # TB: Largura fixa (ou baseada em colunas), Altura dinâmica baseada em ranks
            lane_widths[lane_id] = TITLE_BAR + max(LANE_BODY_W, (max_col + 1) * COL_GAP + LANE_PADDING * 2)
            lane_heights[lane_id] = max(LANE_BODY_H, (max_row + 1) * RANK_GAP + LANE_PADDING * 2)
        else:
            # LR: Altura fixa (ou baseada em rows), Largura dinâmica baseada em ranks
            lane_widths[lane_id] = max(LANE_BODY_W, (max_col + 1) * RANK_GAP + LANE_PADDING * 2)
            lane_heights[lane_id] = TITLE_BAR + max(LANE_BODY_H, (max_row + 1) * ROW_GAP + LANE_PADDING * 2)

    # 3. Calcular offsets das lanes
    lane_offsets = {}
    current_offset = PADDING
    
    if direction == 'TB':
        for lane in lanes_sorted:
            lane_id = lane['id']
            lane_offsets[lane_id] = current_offset
            current_offset += lane_heights[lane_id]
    else:
        for lane in lanes_sorted:
            lane_id = lane['id']
            lane_offsets[lane_id] = current_offset
            current_offset += lane_widths[lane_id]

    # 4. Calcular Bounding Box para viewBox
    # Inclui lanes e nodes (se não for lanes_only)
    min_x, min_y = 0, 0
    if direction == 'TB':
        max_x = max(lane_widths.values()) + PADDING * 2
        max_y = current_offset + PADDING
    else:
        max_x = current_offset + PADDING
        max_y = max(lane_heights.values()) + PADDING * 2

    # SVG Header
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{max_x}" height="{max_y}" viewBox="0 0 {max_x} {max_y}">']
    svg.append(f'<rect x="0" y="0" width="{max_x}" height="{max_y}" fill="#ffffff" />')

    # 5. Desenhar Lanes
    for lane in lanes_sorted:
        lane_id = lane['id']
        title = lane.get('title', lane_id)
        
        if direction == 'TB':
            lx, ly = PADDING, lane_offsets[lane_id]
            lw, lh = lane_widths[lane_id], lane_heights[lane_id]
            
            # Corpo da lane
            svg.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" fill="#fcfcfc" stroke="#ccc" stroke-width="1" />')
            # Barra de título
            svg.append(f'<rect x="{lx}" y="{ly}" width="{TITLE_BAR}" height="{lh}" fill="#ececec" stroke="#ccc" stroke-width="1" />')
            # Texto rotacionado
            tx, ty = lx + TITLE_BAR // 2, ly + lh // 2
            svg.append(f'<text x="{tx}" y="{ty}" font-size="{FONT_TITLE}" font-weight="bold" fill="#333" text-anchor="middle" dominant-baseline="middle" transform="rotate(-90 {tx},{ty})">{title}</text>')
        else:
            lx, ly = lane_offsets[lane_id], PADDING
            lw, lh = lane_widths[lane_id], lane_heights[lane_id]
            
            # Corpo da lane
            svg.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" fill="#fcfcfc" stroke="#ccc" stroke-width="1" />')
            # Barra de título
            svg.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{TITLE_BAR}" fill="#ececec" stroke="#ccc" stroke-width="1" />')
            # Texto horizontal
            tx, ty = lx + lw // 2, ly + TITLE_BAR // 2
            svg.append(f'<text x="{tx}" y="{ty}" font-size="{FONT_TITLE}" font-weight="bold" fill="#333" text-anchor="middle" dominant-baseline="middle">{title}</text>')

    # 6. Desenhar Nodes (se não for lanes_only)
    if not lanes_only:
        for node_id, node in nodes.items():
            lane_id = node.get('lane')
            if lane_id not in lane_offsets: continue
            
            label = node.get('label', node_id)
            if node_id in node_positions:
                gx, gy = node_positions[node_id]
            else:
                gx = nodes[node_id].get('col_index', 0)
                gy = nodes[node_id].get('rank_global', nodes[node_id].get('row_index', 0))
            
            if direction == 'TB':
                # No modo TB: x depende da coluna, y depende do rank (global ou relativo à lane?)
                # Para simplificar e garantir consistência com o layout engine:
                # x = PADDING + TITLE_BAR + LANE_PADDING + gx * COL_GAP + NODE_W // 2
                # y = lane_offsets[lane_id] + LANE_PADDING + gy * RANK_GAP + NODE_H // 2 (Isso assumiria gy local à lane)
                # O layout engine atual gera positions (x, y) que parecem ser globais ou baseadas em grid.
                # Vamos usar gx e gy como coordenadas de grid.
                nx = PADDING + TITLE_BAR + LANE_PADDING + gx * COL_GAP + NODE_W // 2
                # Se gy for rank global, precisamos ver se faz sentido somar ao offset da lane ou se y já é absoluto.
                # Como calculamos lane_heights baseados em max_row, vamos usar gy local se possível.
                # Mas para ser seguro e seguir o visual atual:
                # Vamos assumir que gy é a posição vertical dentro da lane para TB.
                ny = lane_offsets[lane_id] + LANE_PADDING + gy * RANK_GAP + NODE_H // 2
            else:
                # No modo LR: x depende do rank, y depende da linha (row_index)
                nx = lane_offsets[lane_id] + LANE_PADDING + gx * RANK_GAP + NODE_W // 2
                ny = PADDING + TITLE_BAR + LANE_PADDING + gy * ROW_GAP + NODE_H // 2

            # Desenhar Shape
            shape_type = node.get('type', 'process')
            if shape_type == 'decision':
                p = f"{nx},{ny-DECISION_H//2} {nx+DECISION_W//2},{ny} {nx},{ny+DECISION_H//2} {nx-DECISION_W//2},{ny}"
                svg.append(f'<polygon points="{p}" fill="#fffde7" stroke="#fbc02d" stroke-width="2" />')
            elif shape_type == 'start':
                svg.append(f'<circle cx="{nx}" cy="{ny}" r="{START_END_R}" fill="#e0f7fa" stroke="#00796b" stroke-width="2" />')
            elif shape_type == 'end':
                svg.append(f'<circle cx="{nx}" cy="{ny}" r="{START_END_R}" fill="#ffe0e0" stroke="#c62828" stroke-width="2" />')
            else:
                svg.append(f'<rect x="{nx-NODE_W//2}" y="{ny-NODE_H//2}" width="{NODE_W}" height="{NODE_H}" rx="4" fill="#e3f2fd" stroke="#1565c0" stroke-width="2" />')
            
            # Texto
            lines = wrap_text(label, 16)
            y_text = ny - (len(lines) - 1) * (FONT_NODE + 2) // 2
            for i, line in enumerate(lines):
                svg.append(f'<text x="{nx}" y="{y_text + i*(FONT_NODE+2)}" font-size="{FONT_NODE}" fill="#333" text-anchor="middle" dominant-baseline="middle">{line}</text>')

    svg.append('</svg>')
    logger.info(f"[EXPORT] SVG gerado: {max_x}x{max_y}, lanes_only={lanes_only}")
    return '\n'.join(svg)
