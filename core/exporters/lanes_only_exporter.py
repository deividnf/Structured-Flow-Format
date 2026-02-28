"""
Exporta lanes e nodes em SVG, centralizando e adaptando tamanho conforme regras BPMN clássicas. Não desenha edges/routing avançado.
"""
import math
from core.logger.logger import Logger
logger = Logger()

# Parâmetros Espaçosos (Task 08.3)
LANE_GAP = 8
PADDING = 40
CANVAS_PADDING = 40
TITLE_BAR = 50
FONT_TITLE = 18
NODE_W = 220
NODE_H = 60
NODE_GAP = 50
START_END_R = 26
DECISION_SIZE = 80
DECISION_W = DECISION_SIZE
DECISION_H = DECISION_SIZE
FONT_NODE = 13
# Gaps entre slots
COL_GAP = NODE_W + NODE_GAP
ROW_GAP = NODE_H + 80 # Mais espaço vertical
LANE_PADDING = 40
RANK_GAP_TB = 130 # Mais espaço
RANK_GAP_LR = 180
LANE_MIN_W = 400
LANE_MIN_H = 150

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

    # 2. Calcular dimensões das lanes por conteúdo e centralização (Task 08.4)
    lane_content_size = {} # lane -> (max_col, max_row)
    lane_content_pixels = {} # lane -> (content_w, content_h)
    
    global_max_col = 0
    global_max_row = 0

    for lane in lanes_sorted:
        lane_id = lane['id']
        lane_nodes = [nid for nid, n in nodes.items() if n.get('lane') == lane_id]
        max_col, max_row = 0, 0
        if lane_nodes:
            for nid in lane_nodes:
                if nid in node_positions: gx, gy = node_positions[nid]
                else:
                    gx = nodes[nid].get('col_index', 0)
                    gy = nodes[nid].get('rank_global', nodes[nid].get('row_index', 0))
                max_col, max_row = max(max_col, gx), max(max_row, gy)
        
        lane_content_size[lane_id] = (max_col, max_row)
        global_max_col, global_max_row = max(global_max_col, max_col), max(global_max_row, max_row)
        
        # Pixels reais do conteúdo nesta lane
        if direction == 'TB':
            lane_content_pixels[lane_id] = (max_col * COL_GAP + NODE_W, max_row * RANK_GAP_TB + NODE_H)
        else:
            lane_content_pixels[lane_id] = (max_col * RANK_GAP_LR + NODE_W, max_row * ROW_GAP + NODE_H)

    # UNIFORMIZAÇÃO Inteligente (Task 08.4)
    # A dimensão paralela ao fluxo é UNIFORME (para alinhar ranks).
    # A dimensão perpendicular ao fluxo é DINÂMICA (conforme conteúdo e título).
    global_max_content_h = global_max_row * RANK_GAP_TB + NODE_H
    global_max_content_w = global_max_col * RANK_GAP_LR + NODE_W

    lane_widths, lane_heights = {}, {}
    for lane in lanes_sorted:
        lid = lane['id']
        title = lane.get('title', lid)
        cw, ch = lane_content_pixels[lid]
        
        # Estimar tamanho do texto (simples)
        title_len = len(title) * 10 

        if direction == 'TB':
            # TB: Colunas Verticais. Altura é compartilhada. Largura é dinâmica.
            lane_widths[lid] = max(LANE_MIN_W, cw + LANE_PADDING * 2, title_len + LANE_PADDING * 2)
            lane_heights[lid] = TITLE_BAR + max(LANE_MIN_H, global_max_content_h + LANE_PADDING * 2)
        else:
            # LR: Linhas Horizontais. Largura é compartilhada. Altura é dinâmica.
            lane_widths[lid] = TITLE_BAR + max(LANE_MIN_W, global_max_content_w + LANE_PADDING * 2)
            lane_heights[lid] = max(LANE_MIN_H, ch + LANE_PADDING * 2, title_len + LANE_PADDING * 2)

    # 3. Calcular offsets das lanes e de centralização interna
    lane_offsets = {}
    content_centering_offsets = {} # lane -> (off_x, off_y)
    current_offset = CANVAS_PADDING
    
    for lane in lanes_sorted:
        lane_id = lane['id']
        lane_offsets[lane_id] = current_offset
        cw, ch = lane_content_pixels[lane_id]
        
        if direction == 'TB':
            # Centralizar horizontalmente dentro da PRÓPRIA largura da lane
            off_x = (lane_widths[lane_id] - cw) / 2
            # Centralizar bloco verticalmente na altura compartilhada (descontando o TITLE_BAR)
            off_y = TITLE_BAR + (lane_heights[lane_id] - TITLE_BAR - (global_max_row * RANK_GAP_TB + NODE_H)) / 2
            content_centering_offsets[lane_id] = (off_x, off_y)
            current_offset += lane_widths[lane_id] + LANE_GAP
        else:
            # Centralizar verticalmente dentro da PRÓPRIA altura da lane
            off_y = (lane_heights[lane_id] - ch) / 2
            # Centralizar bloco horizontalmente na largura compartilhada (descontando o TITLE_BAR)
            off_x = TITLE_BAR + (lane_widths[lane_id] - TITLE_BAR - (global_max_col * RANK_GAP_LR + NODE_W)) / 2
            content_centering_offsets[lane_id] = (off_x, off_y)
            current_offset += lane_heights[lane_id] + LANE_GAP

    # 4. Bounding Box Global
    if direction == 'TB':
        max_x, max_y = current_offset + CANVAS_PADDING - LANE_GAP, max(lane_heights.values()) + CANVAS_PADDING * 2
    else:
        max_x, max_y = max(lane_widths.values()) + CANVAS_PADDING * 2, current_offset + CANVAS_PADDING - LANE_GAP

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{max_x}" height="{max_y}" viewBox="0 0 {max_x} {max_y}">']
    svg.append(f'<rect x="0" y="0" width="{max_x}" height="{max_y}" fill="#ffffff" />')

    # 5. Desenhar Lanes
    for lane in lanes_sorted:
        lane_id = lane['id']
        title = lane.get('title', lane_id)
        # lx, ly dependem se empilhamos em X (TB) ou Y (LR)
        lx, ly = (lane_offsets[lane_id], CANVAS_PADDING) if direction == 'TB' else (CANVAS_PADDING, lane_offsets[lane_id])
        lw, lh = lane_widths[lane_id], lane_heights[lane_id]
        
        # Lane Body
        svg.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" fill="#fff" stroke="#444" stroke-width="1.5" />')
        
        # Lane Title Area
        if direction == 'TB':
            # Título no topo (Horizontal)
            svg.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{TITLE_BAR}" fill="#eee" stroke="#444" stroke-width="1.5" />')
            tx, ty = lx + lw // 2, ly + TITLE_BAR // 2
            svg.append(f'<text x="{tx}" y="{ty}" font-family="sans-serif" font-size="{FONT_TITLE}" font-weight="bold" fill="#333" text-anchor="middle" dominant-baseline="middle">{title}</text>')
        else:
            # Título na esquerda (Vertical rotacionado)
            svg.append(f'<rect x="{lx}" y="{ly}" width="{TITLE_BAR}" height="{lh}" fill="#eee" stroke="#444" stroke-width="1.5" />')
            tx, ty = lx + TITLE_BAR // 2, ly + lh // 2
            svg.append(f'<text x="{tx}" y="{ty}" font-family="sans-serif" font-size="{FONT_TITLE}" font-weight="bold" fill="#333" text-anchor="middle" dominant-baseline="middle" transform="rotate(-90 {tx},{ty})">{title}</text>')

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

            off_x, off_y = content_centering_offsets[lane_id]
            lx, ly = (lane_offsets[lane_id], CANVAS_PADDING) if direction == 'TB' else (CANVAS_PADDING, lane_offsets[lane_id])

            if direction == 'TB':
                nx = lx + off_x + gx * COL_GAP + NODE_W // 2
                ny = ly + off_y + gy * RANK_GAP_TB + NODE_H // 2
            else:
                nx = lx + off_x + gx * RANK_GAP_LR + NODE_W // 2
                ny = ly + off_y + gy * ROW_GAP + NODE_H // 2

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
