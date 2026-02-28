"""
Exporta lanes e nodes em SVG, centralizando e adaptando tamanho conforme regras BPMN clássicas. Não desenha edges/routing avançado.
"""
import math
from core.logger.logger import Logger
logger = Logger()

# Parâmetros fixos (Task 08)
LANE_GAP = 0
PADDING = 24
CANVAS_PADDING = 24
TITLE_BAR = 56
FONT_TITLE = 20
NODE_W = 220
NODE_H = 64
START_END_R = 26
DECISION_SIZE = 90
DECISION_W = DECISION_SIZE
DECISION_H = DECISION_SIZE
FONT_NODE = 13
COL_GAP = 280  # NODE_W + NODE_GAP
ROW_GAP = 124  # NODE_H + NODE_GAP
LANE_PADDING = 24
RANK_GAP = 160 # Ajustado para acomodar nodes + gap
LANE_BODY_W = 400
LANE_BODY_H = 150

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

    # 2. Calcular dimensões das lanes (Primeiro por conteúdo)
    lane_content_size = {} 
    
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
                    # Task 08 pede linear sequence, mas se houver layout usamos gy
                    gy = nodes[nid].get('rank_global', nodes[nid].get('row_index', 0))
                max_col = max(max_col, gx)
                max_row = max(max_row, gy)
        
        lane_content_size[lane_id] = (max_col, max_row)

    # Encontrar dimensão máxima para UNIFORMIZAÇÃO (Task 08)
    max_w_needed = LANE_BODY_W
    max_h_needed = LANE_BODY_H

    for lane_id, (max_col, max_row) in lane_content_size.items():
        if direction == 'TB':
            w = (max_col + 1) * COL_GAP + LANE_PADDING * 2
            h = (max_row + 1) * RANK_GAP + LANE_PADDING * 2
        else:
            w = (max_col + 1) * RANK_GAP + LANE_PADDING * 2
            h = (max_row + 1) * ROW_GAP + LANE_PADDING * 2
        
        max_w_needed = max(max_w_needed, w)
        max_h_needed = max(max_h_needed, h)

    lane_widths = {}
    lane_heights = {}
    
    for lane in lanes_sorted:
        lane_id = lane['id']
        if direction == 'TB':
            lane_widths[lane_id] = TITLE_BAR + max_w_needed
            lane_heights[lane_id] = max_h_needed
        else:
            lane_widths[lane_id] = max_w_needed
            lane_heights[lane_id] = TITLE_BAR + max_h_needed

    # 3. Calcular offsets das lanes
    lane_offsets = {}
    current_offset = PADDING
    
    for lane in lanes_sorted:
        lane_id = lane['id']
        lane_offsets[lane_id] = current_offset
        if direction == 'TB':
            current_offset += lane_heights[lane_id]
        else:
            current_offset += lane_widths[lane_id]

    # 4. Bounding Box Global
    if direction == 'TB':
        max_x = max(lane_widths.values()) + PADDING * 2
        max_y = current_offset + PADDING
    else:
        max_x = current_offset + PADDING
        max_y = max(lane_heights.values()) + PADDING * 2

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{max_x}" height="{max_y}" viewBox="0 0 {max_x} {max_y}">']
    svg.append(f'<rect x="0" y="0" width="{max_x}" height="{max_y}" fill="#ffffff" />')

    # 5. Desenhar Lanes
    for lane in lanes_sorted:
        lane_id = lane['id']
        title = lane.get('title', lane_id)
        lx, ly = (PADDING, lane_offsets[lane_id]) if direction == 'TB' else (lane_offsets[lane_id], PADDING)
        lw, lh = lane_widths[lane_id], lane_heights[lane_id]
        
        svg.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" fill="#fdfdfd" stroke="#666" stroke-width="2" />')
        
        if direction == 'TB':
            svg.append(f'<rect x="{lx}" y="{ly}" width="{TITLE_BAR}" height="{lh}" fill="#eee" stroke="#666" stroke-width="2" />')
            tx, ty = lx + TITLE_BAR // 2, ly + lh // 2
            svg.append(f'<text x="{tx}" y="{ty}" font-size="{FONT_TITLE}" font-weight="bold" fill="#333" text-anchor="middle" dominant-baseline="middle" transform="rotate(-90 {tx},{ty})">{title}</text>')
        else:
            svg.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{TITLE_BAR}" fill="#eee" stroke="#666" stroke-width="2" />')
            tx, ty = lx + lw // 2, ly + TITLE_BAR // 2
            svg.append(f'<text x="{tx}" y="{ty}" font-size="{FONT_TITLE}" font-weight="bold" fill="#333" text-anchor="middle" dominant-baseline="middle">{title}</text>')

    # 6. Desenhar Nodes (se não for lanes_only)
    if not lanes_only:
        occupied_slots = {} # (x, y) -> node_id to detect collisions
        
        for node_id, node in nodes.items():
            lane_id = node.get('lane')
            if lane_id not in lane_offsets: continue
            
            label = node.get('label', node_id)
            if node_id in node_positions:
                gx, gy = node_positions[node_id]
            else:
                gx = nodes[node_id].get('col_index', 0)
                gy = nodes[node_id].get('rank_global', nodes[node_id].get('row_index', 0))
            
            # Anti-sobreposição básica: se slot ocupado, desloca
            while (gx, gy, lane_id) in occupied_slots:
                logger.warn(f"[COLLISION] Node {node_id} colide em ({gx}, {gy}) na lane {lane_id}. Deslocando...")
                if direction == 'TB': gx += 1
                else: gy += 1
            occupied_slots[(gx, gy, lane_id)] = node_id

            if direction == 'TB':
                nx = PADDING + TITLE_BAR + LANE_PADDING + gx * COL_GAP + NODE_W // 2
                ny = lane_offsets[lane_id] + LANE_PADDING + gy * RANK_GAP + NODE_H // 2
            else:
                nx = lane_offsets[lane_id] + LANE_PADDING + gx * RANK_GAP + NODE_W // 2
                ny = PADDING + TITLE_BAR + LANE_PADDING + gy * ROW_GAP + NODE_H // 2

            # Desenhar Shape
            shape_type = node.get('type', 'process')
            if shape_type == 'decision':
                p = f"{nx},{ny-DECISION_H//2} {nx+DECISION_W//2},{ny} {nx},{ny+DECISION_H//2} {nx-DECISION_W//2},{ny}"
                svg.append(f'<polygon points="{p}" fill="#fffde7" stroke="#fbc02d" stroke-width="2" />')
            elif shape_type == 'start':
                svg.append(f'<circle cx="{nx}" cy="{ny}" r="{START_END_R}" fill="#e8f5e9" stroke="#2e7d32" stroke-width="2" />')
            elif shape_type == 'end':
                svg.append(f'<circle cx="{nx}" cy="{ny}" r="{START_END_R}" fill="#ffebee" stroke="#c62828" stroke-width="2" />')
            else:
                svg.append(f'<rect x="{nx-NODE_W//2}" y="{ny-NODE_H//2}" width="{NODE_W}" height="{NODE_H}" rx="8" fill="#e3f2fd" stroke="#1565c0" stroke-width="2" />')
            
            # Texto Assertivo
            is_start_end = shape_type in ['start', 'end']
            if is_start_end and len(label) > 10:
                # Label externo para start/end longos
                svg.append(f'<text x="{nx}" y="{ny - START_END_R - 10}" font-size="{FONT_NODE}" fill="#333" text-anchor="middle" font-weight="bold">{label}</text>')
            else:
                lines = wrap_text(label, 20 if shape_type != 'decision' else 12)
                y_text = ny - (len(lines) - 1) * (FONT_NODE + 2) // 2
                for i, line in enumerate(lines):
                    svg.append(f'<text x="{nx}" y="{y_text + i*(FONT_NODE+2)}" font-size="{FONT_NODE}" fill="#333" text-anchor="middle" dominant-baseline="middle">{line}</text>')

    svg.append('</svg>')
    logger.info(f"[EXPORT] SVG gerado: {max_x}x{max_y}, lanes_only={lanes_only}")
    return '\n'.join(svg)
