import json
from core.validator.validator import validate_sff_structure

class CFFCompiler:
    def __init__(self, sff_data):
        self.sff_source = sff_data
        
        self.cff = {
            "version": "1.0",
            "stats": {},
            "graph": {},
            "layout_context": {}
        }
        
        self.lanes = {}
        self.nodes = {}
        self.edges = {}

    def compile(self):
        # Step 1: Validate SFF
        self._validate_source()
        
        # Parse logic
        self._parse_base_structure()
        
        # Step 3: Base Graph (prev/next)
        self._build_base_graph()
        
        # Step 4-7: Rank & Depth via BFS
        self._calculate_ranks()
        
        # Step 9-10: Edge Classification & Priority
        self._classify_edges()
        
        # Step 8: Future Metrics
        self._calculate_future_metrics()
        
        # Step 12: General Stats
        self._finalize_stats()
        
        # End structure
        return {
            "sff_source": self.sff_source,
            "cff": self.cff,
            "lanes": self.lanes,
            "nodes": self.nodes,
            "edges": self.edges
        }
        
    def _validate_source(self):
        errors = validate_sff_structure(self.sff_source)
        if errors:
            raise ValueError(f"SFF Source Validation Failed: {errors}")

    def _parse_base_structure(self):
        # Lanes
        for l_id, l_data in self.sff_source.get("lanes", {}).items():
            self.lanes[l_id] = {
                "title": l_data.get("title", ""),
                "order": l_data.get("order", 0),
                "tracks_total": 13,   # Future MD13 integration default
                "center_track": 7,
                "expansion_factor": 1.2
            }
            
        # Nodes
        for n_id, n_data in self.sff_source.get("nodes", {}).items():
            self.nodes[n_id] = {
                "id": n_id,
                "type": n_data.get("type"),
                "lane": n_data.get("lane"),
                "label": n_data.get("label", ""),
                "rank": {
                    "global": 0,
                    "lane": 0,
                    "depth": 0,
                    "branch_depth": 0
                },
                "links": {
                    "prev_nodes": [],
                    "next_nodes": [],
                    "in_edges": [],
                    "out_edges": []
                },
                "future_metrics": {
                    "future_steps": 0,
                    "future_decisions": 0,
                    "cross_lane_ahead": 0,
                    "next_lane_target": ""
                },
                "layout_hints": {
                    "is_main_path": False,
                    "routing_priority": 0,
                    "preferred_exit_side": "",
                    "preferred_entry_side": ""
                }
            }
            
        # Edges
        edge_counter = 1
        for e in self.sff_source.get("edges", []):
            e_id = e.get("id", f"e{edge_counter}")
            edge_counter += 1
            
            self.edges[e_id] = {
                "id": e_id,
                "from": e["from"],
                "to": e["to"],
                "branch": e.get("branch"),
                "classification": {
                    "kind": "main_path",
                    "is_cross_lane": False,
                    "is_return": False,
                    "is_join": False
                },
                "priority": 0,
                "routing_constraints": {
                    "no_overlap": True,
                    "no_cross": True,
                    "min_separation": 16
                },
                "routing_hints": {
                    "backbone_lane": "",
                    "last_mile": True,
                    "preferred_channel": 0
                }
            }

    def _build_base_graph(self):
        for e_id, e in self.edges.items():
            src_id = e["from"]
            dst_id = e["to"]
            
            # Populate Links for Source
            if src_id in self.nodes:
                self.nodes[src_id]["links"]["out_edges"].append(e_id)
                self.nodes[src_id]["links"]["next_nodes"].append(dst_id)
                self.nodes[src_id]["links"]["next_nodes"] = list(set(self.nodes[src_id]["links"]["next_nodes"]))
                
            # Populate Links for Dest
            if dst_id in self.nodes:
                self.nodes[dst_id]["links"]["in_edges"].append(e_id)
                self.nodes[dst_id]["links"]["prev_nodes"].append(src_id)
                self.nodes[dst_id]["links"]["prev_nodes"] = list(set(self.nodes[dst_id]["links"]["prev_nodes"]))

    def _calculate_ranks(self):
        entry_start = self.sff_source.get("entry", {}).get("start")
        if not entry_start or entry_start not in self.nodes:
            return
            
        queue = [(entry_start, 0)]
        visited = {entry_start}
        max_d = 0
        
        while queue:
            curr_id, current_depth = queue.pop(0)
            
            node = self.nodes[curr_id]
            node["rank"]["depth"] = current_depth
            node["rank"]["global"] = current_depth + 1
            max_d = max(max_d, current_depth + 1)
            
            # Branches Depth update (if decision)
            is_decision = (node.get("type") == "decision")
            
            for next_id in node["links"]["next_nodes"]:
                if next_id not in visited:
                    visited.add(next_id)
                    
                    next_node = self.nodes[next_id]
                    if is_decision:
                        next_node["rank"]["branch_depth"] = node["rank"]["branch_depth"] + 1
                        next_node["branch_context"] = {
                            "root_decision": curr_id,
                            "branch_label": "", 
                            "terminates_soon": False
                        }
                    else:
                        next_node["rank"]["branch_depth"] = node["rank"]["branch_depth"]
                        if "branch_context" in node:
                            next_node["branch_context"] = dict(node["branch_context"])
                            
                    queue.append((next_id, current_depth + 1))
                    
        self.cff["stats"]["max_depth"] = max_d

        # Sort per lane
        lane_ordered = {}
        for nid, n_data in self.nodes.items():
            l = n_data.get("lane")
            if l not in lane_ordered:
                lane_ordered[l] = []
            lane_ordered[l].append(n_data)
            
        for l_id, n_list in lane_ordered.items():
            n_list.sort(key=lambda x: (x["rank"]["global"], x["id"]))
            
            for index, n in enumerate(n_list):
                self.nodes[n["id"]]["rank"]["lane"] = index + 1

    def _classify_edges(self):
        for e_id, e in self.edges.items():
            src_node = self.nodes.get(e["from"])
            dst_node = self.nodes.get(e["to"])
            
            if not src_node or not dst_node:
                continue
                
            kind = "main_path"
            priority = 100
            
            # Cross Lane?
            if src_node.get("lane") != dst_node.get("lane"):
                kind = "cross_lane"
                e["classification"]["is_cross_lane"] = True
                priority = 60
                
            # Branch?
            if e.get("branch"):
                kind = "branch"
                priority = 80
                
            # Return/Loop? (Depth of target <= Depth of source)
            if dst_node["rank"]["global"] <= src_node["rank"]["global"]:
                kind = "return"
                e["classification"]["is_return"] = True
                priority = 40
                
            # Join? (Target has multiple incoming)
            if len(dst_node["links"]["in_edges"]) > 1 and kind != "return":
                # We could label it join if it's strictly a convergence
                kind = "join"
                e["classification"]["is_join"] = True
                priority = 30
                
            e["classification"]["kind"] = kind
            e["priority"] = priority

    def _calculate_future_metrics(self):
        for nid, node in self.nodes.items():
            seen = set()
            queue = [nid]
            decisions = 0
            cross_lanes = 0
            
            while queue:
                curr = queue.pop(0)
                if curr != nid:
                    seen.add(curr)
                    if self.nodes[curr].get("type") == "decision":
                        decisions += 1
                
                for eid in self.nodes[curr]["links"]["out_edges"]:
                    edge = self.edges[eid]
                    # Ignore loops to avoid infinite counts (MD17)
                    if edge["classification"].get("is_return"):
                        continue
                        
                    if edge["classification"].get("is_cross_lane"):
                        cross_lanes += 1
                        
                    nxt = edge["to"]
                    if nxt not in seen and nxt not in queue:
                        queue.append(nxt)
                        
            node["future_metrics"]["future_steps"] = len(seen)
            node["future_metrics"]["future_decisions"] = decisions
            node["future_metrics"]["cross_lane_ahead"] = cross_lanes

    def _finalize_stats(self):
        stats = self.cff["stats"]
        stats["nodes_total"] = len(self.nodes)
        stats["edges_total"] = len(self.edges)
        stats["lanes_total"] = len(self.lanes)
        stats["decision_nodes"] = sum(1 for n in self.nodes.values() if n.get("type") == "decision")
        stats["branch_edges"] = sum(1 for e in self.edges.values() if e.get("classification", {}).get("kind") == "branch")
        stats["joins"] = sum(1 for e in self.edges.values() if e.get("classification", {}).get("kind") == "join")
        
        max_branch_depth = max((n["rank"]["branch_depth"] for n in self.nodes.values()), default=0)
        stats["max_branch_depth"] = max_branch_depth

