"""
core/layout/cff_engine.py
Engine de Layout Determinístico — MD13
Transforma .cff válido em layout_result geométrico, sem heurística ou regras de negócio.
Pipeline:
    1. Inicialização da grade/tracks
    2. Posicionamento base dos nós
    3. Reserva de corredores (backbone)
    4. Roteamento ortogonal das edges
    5. Expansão dinâmica de lanes/tracks
    6. Saída formal layout_result
    7. Erro explícito se impossível
Versão: 1.0
"""
from core.layout.track_system import TrackSystem
from core.layout.cff_router import CFFRouter

class CFFEngine:
    def __init__(self, cpff_data):
        """
        CFFEngine v1.0 — Deterministic Layout Engine (MD13)
        Valida campos obrigatórios do .cff e inicializa pipeline determinístico.
        """
        self.cpff = cpff_data
        # Validação de campos obrigatórios
        required_node_fields = ["rank", "links", "branch_context", "future_metrics", "layout_hints"]
        required_edge_fields = ["classification", "priority"]
        required_lane_fields = ["tracks_total", "center_track"]
        if not self.cpff.get("nodes") or not self.cpff.get("edges") or not self.cpff.get("lanes"):
            raise ValueError("LAYOUT_IMPOSSIBLE_WITH_CURRENT_GRID: CFF incompleto (nodes, edges, lanes obrigatórios)")
        for n_id, node in self.cpff["nodes"].items():
            for f in required_node_fields:
                if f not in node:
                    raise ValueError(f"LAYOUT_IMPOSSIBLE_WITH_CURRENT_GRID: Node {n_id} sem campo obrigatório '{f}'")
        for e_id, edge in self.cpff["edges"].items():
            for f in required_edge_fields:
                if f not in edge:
                    raise ValueError(f"LAYOUT_IMPOSSIBLE_WITH_CURRENT_GRID: Edge {e_id} sem campo obrigatório '{f}'")
        for l_id, lane in self.cpff["lanes"].items():
            for f in required_lane_fields:
                if f not in lane:
                    raise ValueError(f"LAYOUT_IMPOSSIBLE_WITH_CURRENT_GRID: Lane {l_id} sem campo obrigatório '{f}'")

        self.nodes = self.cpff["nodes"]
        self.edges = self.cpff["edges"]
        self.lanes = self.cpff["lanes"]
        self.sff_source = self.cpff.get("sff_source", {})
        self.direction = self.sff_source.get("sff", {}).get("direction", "TB")
        # Geometria
        self.RANK_GAP = 100
        self.LANE_WIDTH = 300
        # Componentes
        self.track_system = TrackSystem(self.lanes)
        # Resultados
        self.layout_nodes = {}
        self.layout_edges = {}
        self.layout_lanes = {}
        # Versão
        self.engine_version = "1.0"

    def generate(self):
        """
        Executa pipeline determinístico do layout engine conforme MD13.
        """
        self._initialize_lanes()
        self._position_nodes()
        try:
            self._route_edges()
        except Exception as e:
            raise ValueError(f"LAYOUT_IMPOSSIBLE_WITH_CURRENT_GRID: {str(e)}")
        return {
            "nodes": self.layout_nodes,
            "edges": self.layout_edges,
            "lanes": self.layout_lanes,
            "engine_version": self.engine_version
        }

    def _initialize_lanes(self):
        # MD13 Etapa 1
        # Order lanes
        ordered_lanes = sorted(self.lanes.items(), key=lambda x: x[1].get("order", 0))
        
        current_offset = 0
        for l_id, l_data in ordered_lanes:
            width = self.LANE_WIDTH
            self.track_system.lanes[l_id]["lane_start_offset"] = current_offset + (width / 2) # Center of lane
            self.layout_lanes[l_id] = {
                "x_start": current_offset,
                "x_end": current_offset + width,
                "tracks_total": self.track_system.lanes[l_id]["tracks_total"]
            }
            # Keep an internal hidden center for nodes
            self.layout_lanes[l_id]["_center"] = current_offset + (width / 2)
            current_offset += width

    def _position_nodes(self):
        # MD13 Etapa 2
        for n_id, node in self.nodes.items():
            lane_id = node.get("lane")
            rank = node.get("rank", {})
            r_global = rank.get("global", 1)
            
            lane_center = self.layout_lanes[lane_id]["_center"]
            track_diff = self.track_system.get_track_offset(lane_id, self.track_system.lanes[lane_id]["center_track"])
            # Assuming main path takes center_track (0 diff)
            base_primary = lane_center + track_diff
            base_secondary = r_global * self.RANK_GAP
            
            if self.direction == "TB":
                x = base_primary
                y = base_secondary
            else:
                x = base_secondary
                y = base_primary
                
            # MD13 Etapa 2 Size config
            w, h = 180, 50 # Process default
            ntype = node.get("type")
            if ntype == "decision":
                w, h = 60, 60
            elif ntype in ["start", "end"]:
                w, h = 40, 40

            self.layout_nodes[n_id] = {
                "x": x,
                "y": y,
                "width": w,
                "height": h
            }

    def _route_edges(self):
        router = CFFRouter(self.track_system, self.direction)
        
        # MD13 Etapa 4 — Ordem de roteamento determinística
        def edge_group(edge):
            kind = edge.get("classification", {}).get("kind", "")
            # 1 main_path, 2 branch, 3 cross_lane, 4 return, 5 join
            order = {
                "main_path": 0,
                "branch": 1,
                "cross_lane": 3,
                "return": 4,
                "join": 5,
            }.get(kind, 6)
            return order

        edges_list = list(self.edges.values())

        def sort_key(e):
            g = edge_group(e)
            # Para branch, considerar future_steps do nó de origem (maior primeiro)
            if e.get("classification", {}).get("kind") == "branch":
                src = self.nodes.get(e["from"], {})
                fs = src.get("future_metrics", {}).get("future_steps", 0)
                return (g, -fs, e.get("id"))
            return (g, -e.get("priority", 0), e.get("id"))

        edges_list.sort(key=sort_key)

        for e in edges_list:
            e_id = e["id"]
            src_node = self.layout_nodes[e["from"]]
            dst_node = self.layout_nodes[e["to"]]
            orig_src = self.nodes.get(e["from"], {})
            orig_dst = self.nodes.get(e["to"], {})
            points = router.route_edge(e, src_node, dst_node, orig_src, orig_dst)
            self.layout_edges[e_id] = {
                "points": points
            }
