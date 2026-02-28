"""
Exporta lanes e nodes em SVG, centralizando e adaptando tamanho conforme regras BPMN clássicas. Não desenha edges/routing avançado.
"""
import math
from core.logger.logger import Logger
logger = Logger()

# Parâmetros Espaçosos (Task 09)
LANE_GAP = 12
PADDING = 40
CANVAS_PADDING = 40
TITLE_BAR = 50
FONT_TITLE = 18
NODE_W = 220
NODE_H = 60
NODE_GAP = 50
START_END_R = 26
DECISION_SIZE = 80
FONT_NODE = 13
# Gaps Automáticos (Parte C) serão calculados na hora do export
GRID_X = 40
GRID_Y = 24
LANE_PADDING = 40
LANE_PADDING = 40
LANE_MIN_W = 400
LANE_MIN_H = 150

def wrap_text(text, max_chars):
    if not text: return [""]
    words = text.split()
    lines, current = [], []
    for w in words:
        if sum(len(x)+1 for x in current) + len(w) <= max_chars:
            current.append(w)
        else:
            lines.append(" ".join(current))
            current = [w]
    if current: lines.append(" ".join(current))
    return lines

def assign_tracks(nodes, edges):
    """Atribui eixos internos (tracks) para suporte a branches (Task 09)"""
    node_tracks = {} # nid -> track
    
    # Encontrar entrada
    start_nodes = [nid for nid, n in nodes.items() if n.get('type') == 'start']
    queue = []
    for s in start_nodes:
        node_tracks[s] = 0
        queue.append(s)
    
    visited = set()
    while queue:
        curr = queue.pop(0)
        if curr in visited: continue
        visited.add(curr)
        
        curr_track = node_tracks.get(curr, 0)
        curr_edges = [e for e in edges if e['from'] == curr]
        
        if not curr_edges: continue
        
        # Se for decisão, espalhar em tracks diferentes
        if nodes[curr].get('type') == 'decision' and len(curr_edges) > 1:
            # Branch primário (True ou primeiro) mantém track
            # Demais espalham: +1, -1, +2, -2...
            offsets = [0, 1, -1, 2, -2, 3, -3]
            for i, edge in enumerate(curr_edges):
                target = edge['to']
                if target not in node_tracks:
                    off = offsets[i] if i < len(offsets) else i
                    node_tracks[target] = curr_track + off
                    queue.append(target)
        else:
            # Fluxo linear ou convergência
            for edge in curr_edges:
                target = edge['to']
                if target not in node_tracks:
                    # Se múltiplos pais chegam aqui (convergência), volta pro track 0
                    parents = [e for e in edges if e['to'] == target]
                    if len(parents) > 1:
                        node_tracks[target] = 0
                    else:
                        node_tracks[target] = curr_track
                    queue.append(target)
    
    # Garantir que todos tenham um track
    for nid in nodes:
        if nid not in node_tracks: node_tracks[nid] = 0
            
    return node_tracks

def export_lanes_only(data, lanes_only=False):
    sff = data.get('sff', {})
    direction = sff.get('direction', 'TB')
    lanes = data.get('lanes', {})
    nodes = data.get('nodes', {})
    edges = data.get('edges', [])
    layout = data.get('layout', {})
    node_positions = layout.get('positions', {})

    # Parte C: Gaps automáticos de segurança
    base_max_h = max(NODE_H, DECISION_SIZE, START_END_R * 2)
    base_max_w = max(NODE_W, DECISION_SIZE, START_END_R * 2)
    
    RANK_GAP_TB = base_max_h + 80
    RANK_GAP_LR = base_max_w + 80
    TRACK_GAP_TB = base_max_w + 60
    TRACK_GAP_LR = base_max_h + 60

    TRACK_GAP = TRACK_GAP_TB if direction == 'TB' else TRACK_GAP_LR
    RANK_GAP = RANK_GAP_TB if direction == 'TB' else RANK_GAP_LR
    
    logger.info(f"[GRID] rank_gap={RANK_GAP}, track_gap={TRACK_GAP}, grid=({GRID_X},{GRID_Y})")

    # 1. Atribuir Tracks Iniciais
    node_tracks = assign_tracks(nodes, edges)

    # 1.5 Resolver colisões de Slot (Parte A)
    occupied = {} # (lane_id, rank, track) -> node_id
    nodes_sorted_for_layout = sorted(nodes.items(), key=lambda x: (x[1].get('rank_global', 0), x[0]))
    
    for node_id, node in nodes_sorted_for_layout:
        lane_id = node.get('lane')
        if not lane_id: continue
        rank = node.get('rank_global', 0)
        base_track = node_tracks.get(node_id, 0)
        
        final_track = base_track
        if (lane_id, rank, final_track) in occupied:
            logger.warn(f"[SLOT_COLLISION] slot ocupado -> realocando track para {node_id}")
            offsets = [1, -1, 2, -2, 3, -3, 4, -4, 5, -5]
            for off in offsets:
                test_track = base_track + off
                if (lane_id, rank, test_track) not in occupied:
                    final_track = test_track
                    break
                    
        node_tracks[node_id] = final_track
        occupied[(lane_id, rank, final_track)] = node_id
        logger.info(f"[SLOT_ASSIGN] node_id={node_id}, lane={lane_id}, rank={rank}, track={final_track}")

    # Processo Iterativo de BBOX (Parte D) - Preparando coords
    # Para o BBOX precisamos do offset provisorio das lanes, entao vamos calcular os meta-dados e posições baseadas nos tracks finais.

    # Ordenar lanes por ordem
    lanes_sorted = sorted([{'id': k, **v} for k, v in lanes.items()], key=lambda x: x.get('order', 0))

    # 2. Calcular dimensões das lanes por conteúdo e tracks (Task 09)
    lane_content_meta = {} # lane_id -> {max_rank, min_track, max_track, content_w, content_h}
    
    global_max_rank = 0

    for lane in lanes_sorted:
        lid = lane['id']
        lane_nodes = [nid for nid, n in nodes.items() if n.get('lane') == lid]
        
        max_rank = 0
        min_tr, max_tr = 0, 0
        
        if lane_nodes:
            for nid in lane_nodes:
                rank = nodes[nid].get('rank_global', 0)
                track = node_tracks.get(nid, 0)
                max_rank = max(max_rank, rank)
                min_tr = min(min_tr, track)
                max_tr = max(max_tr, track)
        
        global_max_rank = max(global_max_rank, max_rank)
        
        # Dimensão PERPENDICULAR ao fluxo (baseada em tracks)
        track_span = (max_tr - min_tr) * TRACK_GAP + NODE_W
        # Dimensão PARALELA ao fluxo (baseada em ranks)
        rank_span = max_rank * RANK_GAP + (NODE_H if direction == 'TB' else NODE_W)
        
        if direction == 'TB':
            cw, ch = track_span, rank_span
        else:
            cw, ch = rank_span, track_span
            
        lane_content_meta[lid] = {
            'max_rank': max_rank,
            'min_track': min_tr,
            'max_track': max_tr,
            'cw': cw, 'ch': ch
        }

    # UNIFORMIZAÇÃO Inteligente (Parte E)
    # Ranks (Fluxo) são uniformes. Tracks (Interno) são dinâmicos.
    global_flow_h = global_max_rank * RANK_GAP + NODE_H if direction == 'TB' else 0
    global_flow_w = global_max_rank * RANK_GAP + NODE_W if direction == 'LR' else 0

    lane_widths, lane_heights = {}, {}
    for lane in lanes_sorted:
        lid = lane['id']
        meta = lane_content_meta[lid]
        title_len = len(lane.get('title', lid)) * 11

        if direction == 'TB':
            lane_widths[lid] = max(LANE_MIN_W, meta['cw'] + LANE_PADDING * 2, title_len + LANE_PADDING * 2)
            lane_heights[lid] = TITLE_BAR + max(LANE_MIN_H, global_flow_h + LANE_PADDING * 2)
        else:
            lane_widths[lid] = TITLE_BAR + max(LANE_MIN_W, global_flow_w + LANE_PADDING * 2)
            lane_heights[lid] = max(LANE_MIN_H, meta['ch'] + LANE_PADDING * 2, title_len + LANE_PADDING * 2)

    # 3. Offsets e Centralização
    lane_offsets = {}
    content_centering_offsets = {}
    current_offset = CANVAS_PADDING
    
    for lane in lanes_sorted:
        lid = lane['id']
        lane_offsets[lid] = current_offset
        meta = lane_content_meta[lid]
        
        if direction == 'TB':
            # off_x deve considerar que min_track pode ser negativo
            # O centro teórico é track=0.
            # cw_total = (max_tr - min_tr) * TRACK_GAP + NODE_W
            off_x = (lane_widths[lid] - meta['cw']) / 2
            off_y = TITLE_BAR + (lane_heights[lid] - TITLE_BAR - global_flow_h) / 2
            content_centering_offsets[lid] = (off_x, off_y)
            current_offset += lane_widths[lid] + LANE_GAP
        else:
            off_y = (lane_heights[lid] - meta['ch']) / 2
            off_x = TITLE_BAR + (lane_widths[lid] - TITLE_BAR - global_flow_w) / 2
            content_centering_offsets[lid] = (off_x, off_y)
            current_offset += lane_heights[lid] + LANE_GAP

    # 4. PRE-PASS: Iterative BBOX Collision Resolver & Geometry Calc (Part D)
    node_geometry = {} # node_id -> {'nx': nx, 'ny': ny, 'shape_type': type, 'label': label}
    bboxes = [] # (node_id, x1, y1, x2, y2)

    for node_id, node in nodes.items():
        lane_id = node.get('lane')
        if lane_id not in lane_offsets: continue
        
        label = node.get('label', node_id)
        rank = node.get('rank_global', 0)
        track = node_tracks.get(node_id, 0)
        shape_type = node.get('type', 'process')
        
        meta = lane_content_meta[lane_id]
        off_x, off_y = content_centering_offsets[lane_id]
        lx, ly = (lane_offsets[lane_id], CANVAS_PADDING) if direction == 'TB' else (CANVAS_PADDING, lane_offsets[lane_id])

        resolved = False
        for attempt in range(10):
            if direction == 'TB':
                nx = lx + off_x + (track - meta['min_track']) * TRACK_GAP + NODE_W // 2
                ny = ly + off_y + rank * RANK_GAP + NODE_H // 2
            else:
                nx = lx + off_x + rank * RANK_GAP + NODE_W // 2
                ny = ly + off_y + (track - meta['min_track']) * TRACK_GAP + NODE_H // 2

            # Snap to grid (Parte B)
            nx = round(nx / GRID_X) * GRID_X
            ny = round(ny / GRID_Y) * GRID_Y

            # Bounding Box approx
            if shape_type == 'decision':
                x1, y1 = nx - DECISION_SIZE//2, ny - DECISION_SIZE//2
                x2, y2 = nx + DECISION_SIZE//2, ny + DECISION_SIZE//2
            elif shape_type in ['start', 'end']:
                x1, y1 = nx - START_END_R, ny - START_END_R
                x2, y2 = nx + START_END_R, ny + START_END_R
            else:
                x1, y1 = nx - NODE_W//2, ny - NODE_H//2
                x2, y2 = nx + NODE_W//2, ny + NODE_H//2

            # Expand bbox for text
            is_start_end = shape_type in ['start', 'end']
            if is_start_end and len(label) > 10:
                y1 = min(y1, ny - START_END_R - 20)
                x1 = min(x1, nx - (len(label) * FONT_NODE * 0.6) / 2)
                x2 = max(x2, nx + (len(label) * FONT_NODE * 0.6) / 2)
            else:
                text_bbox_w = min(20, len(label)) * FONT_NODE * 0.6
                lines = wrap_text(label, 20 if shape_type != 'decision' else 12)
                if len(lines) > 1 and attempt == 0:
                    logger.warn(f"[TEXT_WRAP] Node {node_id} quebrado em {len(lines)} linhas")
                text_bbox_h = len(lines) * (FONT_NODE + 2)
                
                if shape_type == 'decision':
                    x1 = min(x1, nx - text_bbox_w/2)
                    x2 = max(x2, nx + text_bbox_w/2)
                    y1 = min(y1, ny - text_bbox_h/2)
                    y2 = max(y2, ny + text_bbox_h/2)

            collision = False
            for other_id, ox1, oy1, ox2, oy2 in bboxes:
                # Add gap geometry
                GAP = 10
                if not (x2 + GAP <= ox1 or x1 - GAP >= ox2 or y2 + GAP <= oy1 or y1 - GAP >= oy2):
                    collision = True
                    logger.warn(f"[BBOX_COLLISION] Node {node_id} sobrepoe {other_id} (attempt {attempt}). Ajustando track.")
                    break
            
            if not collision:
                bboxes.append((node_id, x1, y1, x2, y2))
                node_positions[node_id] = (nx, ny)
                node_geometry[node_id] = {'nx': nx, 'ny': ny, 'shape_type': shape_type, 'label': label, 'bbox': (x1, y1, x2, y2), 'lines': lines if 'lines' in locals() else [label]}
                resolved = True
                break
            else:
                track += 1 # Try pushing track

        if not resolved:
            logger.error(f"[UNRESOLVED_COLLISION] Node {node_id} colidindo apos 10 tentativas.")
            raise ValueError(f"Pipeline abortado: [UNRESOLVED_COLLISION] Node {node_id}")

    # 5. Global Bounding Box Calculation (Parte E - Auto-Resize)
    gmin_x, gmin_y, gmax_x, gmax_y = float('inf'), float('inf'), float('-inf'), float('-inf')

    # Lane Headers
    for lane in lanes_sorted:
        lane_id = lane['id']
        lx, ly = (lane_offsets[lane_id], CANVAS_PADDING) if direction == 'TB' else (CANVAS_PADDING, lane_offsets[lane_id])
        lw, lh = lane_widths[lane_id], lane_heights[lane_id]
        gmin_x, gmin_y = min(gmin_x, lx), min(gmin_y, ly)
        gmax_x, gmax_y = max(gmax_x, lx + lw), max(gmax_y, ly + lh)

    # Node BBOXes
    for _, x1, y1, x2, y2 in bboxes:
        gmin_x, gmin_y = min(gmin_x, x1), min(gmin_y, y1)
        gmax_x, gmax_y = max(gmax_x, x2), max(gmax_y, y2)

    PAD = 80
    final_w = (gmax_x - gmin_x) + PAD * 2
    final_h = (gmax_y - gmin_y) + PAD * 2
    vb_x = gmin_x - PAD
    vb_y = gmin_y - PAD

    if math.isinf(final_w): final_w = CANVAS_PADDING * 2
    if math.isinf(final_h): final_h = CANVAS_PADDING * 2
    if math.isinf(vb_x): vb_x = 0
    if math.isinf(vb_y): vb_y = 0

    logger.info(f"[CANVAS] bbox=({gmin_x},{gmin_y},{gmax_x},{gmax_y}) width={final_w} height={final_h}")

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{final_w}" height="{final_h}" viewBox="{vb_x} {vb_y} {final_w} {final_h}">']
    svg.append(f'<rect x="{vb_x}" y="{vb_y}" width="{final_w}" height="{final_h}" fill="#ffffff" />')

    # 5. Desenhar Lanes
    for lane in lanes_sorted:
        lane_id = lane['id']
        title = lane.get('title', lane_id)
        lx, ly = (lane_offsets[lane_id], CANVAS_PADDING) if direction == 'TB' else (CANVAS_PADDING, lane_offsets[lane_id])
        lw, lh = lane_widths[lane_id], lane_heights[lane_id]
        
        svg.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" fill="#fff" stroke="#444" stroke-width="1.5" />')
        
        if direction == 'TB':
            svg.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{TITLE_BAR}" fill="#eee" stroke="#444" stroke-width="1.5" />')
            tx, ty = lx + lw // 2, ly + TITLE_BAR // 2
            svg.append(f'<text x="{tx}" y="{ty}" font-family="sans-serif" font-size="{FONT_TITLE}" font-weight="bold" fill="#333" text-anchor="middle" dominant-baseline="middle">{title}</text>')
        else:
            svg.append(f'<rect x="{lx}" y="{ly}" width="{TITLE_BAR}" height="{lh}" fill="#eee" stroke="#444" stroke-width="1.5" />')
            tx, ty = lx + TITLE_BAR // 2, ly + lh // 2
            svg.append(f'<text x="{tx}" y="{ty}" font-family="sans-serif" font-size="{FONT_TITLE}" font-weight="bold" fill="#333" text-anchor="middle" dominant-baseline="middle" transform="rotate(-90 {tx},{ty})">{title}</text>')

    # 6. Desenhar Nodes (se não for lanes_only) e Textos
    if not lanes_only:
        svg_processes = []
        svg_decisions = []
        svg_start_end = []
        svg_texts = []

        for node_id, geom in node_geometry.items():
            nx, ny = geom['nx'], geom['ny']
            shape_type = geom['shape_type']
            label = geom['label']
            lines = geom['lines']
            
            # Formas
            if shape_type == 'decision':
                p = f"{nx},{ny-DECISION_SIZE//2} {nx+DECISION_SIZE//2},{ny} {nx},{ny+DECISION_SIZE//2} {nx-DECISION_SIZE//2},{ny}"
                svg_decisions.append(f'<polygon points="{p}" fill="#fffde7" stroke="#fbc02d" stroke-width="2" />')
            elif shape_type == 'start':
                svg_start_end.append(f'<circle cx="{nx}" cy="{ny}" r="{START_END_R}" fill="#e8f5e9" stroke="#2e7d32" stroke-width="2" />')
            elif shape_type == 'end':
                svg_start_end.append(f'<circle cx="{nx}" cy="{ny}" r="{START_END_R}" fill="#ffebee" stroke="#c62828" stroke-width="2" />')
            else:
                svg_processes.append(f'<rect x="{nx-NODE_W//2}" y="{ny-NODE_H//2}" width="{NODE_W}" height="{NODE_H}" rx="8" fill="#e3f2fd" stroke="#1565c0" stroke-width="2" />')
            
            # Textos
            is_start_end = shape_type in ['start', 'end']
            if is_start_end and len(label) > 10:
                svg_texts.append(f'<text x="{nx}" y="{ny - START_END_R - 10}" font-size="{FONT_NODE}" fill="#333" text-anchor="middle" font-weight="bold">{label}</text>')
            else:
                y_text = ny - (len(lines) - 1) * (FONT_NODE + 2) // 2
                for i, line in enumerate(lines):
                    svg_texts.append(f'<text x="{nx}" y="{y_text + i*(FONT_NODE+2)}" font-size="{FONT_NODE}" font-family="sans-serif" fill="#333" text-anchor="middle" dominant-baseline="middle">{line}</text>')

        svg.extend(svg_processes)
        svg.extend(svg_decisions)
        svg.extend(svg_start_end)
        svg.extend(svg_texts)

    svg.append('</svg>')
    logger.info(f"[EXPORT] SVG gerado: view_box={vb_x},{vb_y},{final_w},{final_h}")
    return '\n'.join(svg)
