from core.layout.track_system import TrackSystem
from core.layout.cff_router import CFFRouter

class CFFEngine:
    def __init__(self, cpff_data):
        self.cpff = cpff_data
        self.nodes = self.cpff.get("nodes", {})
        self.edges = self.cpff.get("edges", {})
        self.lanes = self.cpff.get("lanes", {})
        
        self.sff_source = self.cpff.get("sff_source", {})
        self.direction = self.sff_source.get("sff", {}).get("direction", "TB")
        
        # Geometries
        self.RANK_GAP = 100
        self.LANE_WIDTH = 300
        
        # Components
        self.track_system = TrackSystem(self.lanes)
        
        # Results
        self.layout_nodes = {}
        self.layout_edges = {}
        self.layout_lanes = {}

    def generate(self):
        self._initialize_lanes()
        self._position_nodes()
        self._route_edges()
        
        return {
            "nodes": self.layout_nodes,
            "edges": self.layout_edges,
            "lanes": self.layout_lanes
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
        
        # MD13 Etapa 4: Ordenar (main_path, then priority descending)
        edges_list = list(self.edges.values())
        edges_list.sort(key=lambda e: (e.get("priority", 0), e.get("id")), reverse=True)
        
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
