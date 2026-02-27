"""
core/layout/layout.py
Estrutura base para futura implementação do cálculo de ranks, posições e roteamento.
"""
from typing import Dict, Any, List, Tuple
import collections

def generate_layout(data: Dict[str, Any], compiled: Dict[str, Any]) -> Dict[str, Any]:
    """Gera ranks, positions (grid) e routing ortogonal determinístico."""
    nodes = data.get("nodes", {})
    edges = data.get("edges", [])
    lanes = data.get("lanes", {})
    entry = data.get("entry", {})
    direction = data.get("sff", {}).get("direction", "TB")
    prev = compiled["index"]["prev"]
    # 1. Calcular ranks (BFS)
    ranks = {}
    queue = collections.deque()
    start = entry.get("start")
    if start is None:
        return {"ranks": {}, "positions": {}, "routing": {}}
    ranks[start] = 0
    queue.append(start)
    while queue:
        node = queue.popleft()
        for e in edges:
            if e["from"] == node:
                to = e["to"]
                if to not in ranks or ranks[to] > ranks[node] + 1:
                    ranks[to] = ranks[node] + 1
                    queue.append(to)
    # 2. Ordenar lanes
    lane_order = sorted(lanes, key=lambda l: lanes[l].get("order", 0))
    lane_offsets = {lane: i for i, lane in enumerate(lane_order)}
    # 3. Calcular posições (grid)
    positions = {}
    # Agrupar por rank e lane
    rank_lane_nodes = collections.defaultdict(lambda: collections.defaultdict(list))
    for node_id, node in nodes.items():
        r = ranks.get(node_id, 0)
        lane = node.get("lane")
        rank_lane_nodes[r][lane].append(node_id)
    for r in sorted(rank_lane_nodes):
        for lane in lane_order:
            nodes_in_cell = rank_lane_nodes[r].get(lane, [])
            for idx, node_id in enumerate(nodes_in_cell):
                if direction == "TB":
                    x = lane_offsets[lane]
                    y = r
                else:
                    x = r
                    y = lane_offsets[lane]
                positions[node_id] = (x, y)
    # 4. Routing ortogonal (mínimo viável)
    routing = {}
    occupied = set(positions.values())
    for edge in edges:
        src = edge["from"]
        dst = edge["to"]
        src_pos = positions.get(src)
        dst_pos = positions.get(dst)
        if not src_pos or not dst_pos:
            routing[(src, dst)] = []
            continue
        path = []
        # Caminho ortogonal: src → (x_dst, y_src) → dst
        if direction == "TB":
            mid = (dst_pos[0], src_pos[1])
            if mid != src_pos:
                path.append((src_pos, mid))
            if mid != dst_pos:
                path.append((mid, dst_pos))
        else:
            mid = (src_pos[0], dst_pos[1])
            if mid != src_pos:
                path.append((src_pos, mid))
            if mid != dst_pos:
                path.append((mid, dst_pos))
        routing[(src, dst)] = path
    return {
        "ranks": ranks,
        "positions": positions,
        "lane_order": lane_order,
        "routing": routing
    }
