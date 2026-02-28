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
    from core.logger.logger import Logger
    logger = Logger()
    
    # 1. Calcular ranks (Kahn's Topological Sort - Task 09.2)
    start_node = entry.get("start")
    if not start_node or start_node not in nodes:
        logger.error(f"ENTRY START inválido: {start_node}")
        raise ValueError("Pipeline abortado: Entry start inválido.")

    # Achar nós alcançáveis a partir do start
    reachable = set()
    q = collections.deque([start_node])
    reachable.add(start_node)
    
    full_adj = collections.defaultdict(list)
    for e in edges:
        full_adj[e["from"]].append(e["to"])
        
    while q:
        curr = q.popleft()
        for nxt in full_adj[curr]:
            if nxt not in reachable:
                reachable.add(nxt)
                q.append(nxt)

    # Construir indegree e adj apenas para o subgrafo alcançável
    adj = collections.defaultdict(list)
    in_degree = collections.defaultdict(int)
    
    for e in edges:
        u, v = e["from"], e["to"]
        if u in reachable and v in reachable:
            adj[u].append(v)
            in_degree[v] += 1
            if u not in in_degree:
                in_degree[u] = 0

    in_degree[start_node] = 0
    queue = collections.deque([start_node])
    ranks = {start_node: 0}
    topo_order = []

    while queue:
        u = queue.popleft()
        topo_order.append(u)
        for v in adj[u]:
            in_degree[v] -= 1
            ranks[v] = max(ranks.get(v, 0), ranks[u] + 1)
            if in_degree[v] == 0:
                queue.append(v)

    if len(topo_order) != len(reachable):
        logger.error("Cyclic dependency detected during rank assignment.")
        raise ValueError("Pipeline abortado: Cíclo detectado (o fluxo não é um DAG).")

    if len(ranks) != len(nodes):
        for nid in nodes:
            if nid not in ranks:
                logger.error(f"Node {nid} is unreachable or unranked.")
        raise ValueError("Pipeline abortado: Existem nodes inalcançáveis a partir do start.")

    for nid, r in ranks.items():
        nodes[nid]['rank_global'] = r
        logger.info(f"[RANK_ASSIGN] node_id={nid}, rank={r}")
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
        key = f"{src}->{dst}"
        if not src_pos or not dst_pos:
            routing[key] = []
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
        routing[key] = path
    return {
        "ranks": ranks,
        "positions": positions,
        "lane_order": lane_order,
        "routing": routing
    }
