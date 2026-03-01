import json
from core.validator.validator import validate_sff_structure
from core.logger.logger import Logger


_logger = Logger()


class CFFCompiler:
    """Compilador cpff conforme MD11/MD12.

    Transforma um SFF válido em um cpff totalmente expandido, determinístico
    e pronto para consumo por engines de layout/export.
    """

    def __init__(self, sff_data):
        self.sff_source = sff_data

        # Bloco raiz "cpff" conforme MD11/MD12
        self.cpff = {
            "version": "1.0",
            "stats": {},           # Preenchido em _finalize_stats
            "graph": {},           # Índices globais prev/next
            "layout_context": {},  # Metadados mínimos para layout (ex.: direção)
            "subflows": {}         # Reservado para MD18 (subflows estruturais)
        }

        self.lanes = {}
        self.nodes = {}
        self.edges = {}

        # Conjunto determinístico de nós/edges pertencentes ao main path
        self._main_path_nodes = set()
        self._main_path_edges = set()

    def compile(self):
        # Step 1: Validate SFF
        self._validate_source()
        
        # Parse logic
        self._parse_base_structure()
        
        # Step 3: Base Graph (prev/next)
        self._build_base_graph()
        
        # Step 4-7: Rank & Depth via BFS
        self._calculate_ranks()

        # MD18 — Detecção de ciclos/SCC e ciclo_context
        self._detect_cycles_and_cycle_context()

        # Etapa 5 (MD12) — Identificação do Main Path
        self._compute_main_path()
        
        # Step 9-10: Edge Classification & Priority
        self._classify_edges()
        
        # Step 8: Future Metrics
        self._calculate_future_metrics()
        
        # Step 12: General Stats
        self._finalize_stats()
        
        # Log resumido de stats (MD19) para auditoria
        stats = self.cpff.get("stats", {})
        _logger.info(
            "[CFF-COMPILER] N={nodes_total}, E={edges_total}, L={lanes_total}, "
            "decisions={decision_nodes}, branches={branch_edges}, joins={joins}, "
            "cycles={cycles_total}, max_cycle_depth={max_cycle_depth}, "
            "max_branch_depth={max_branch_depth}, B_max={max_branches_per_rank}, "
            "T_max={max_tracks_per_lane}".format(**{
                **{
                    "nodes_total": stats.get("nodes_total", 0),
                    "edges_total": stats.get("edges_total", 0),
                    "lanes_total": stats.get("lanes_total", 0),
                    "decision_nodes": stats.get("decision_nodes", 0),
                    "branch_edges": stats.get("branch_edges", 0),
                    "joins": stats.get("joins", 0),
                    "max_branch_depth": stats.get("max_branch_depth", 0),
                    "cycles_total": stats.get("cycles_total", 0),
                    "max_cycle_depth": stats.get("max_cycle_depth", 0),
                    "max_branches_per_rank": stats.get("max_branches_per_rank", 0),
                    "max_tracks_per_lane": stats.get("max_tracks_per_lane", 0),
                }
            })
        )

        # End structure
        return {
            "sff_source": self.sff_source,
            "cpff": self.cpff,
            "lanes": self.lanes,
            "nodes": self.nodes,
            "edges": self.edges
        }
        
    def _validate_source(self):
        errors = validate_sff_structure(self.sff_source)
        if errors:
            raise ValueError(f"SFF Source Validation Failed: {errors}")

    def _parse_base_structure(self):
        # Lanes (expansão mínima conforme MD11)
        for l_id, l_data in self.sff_source.get("lanes", {}).items():
            self.lanes[l_id] = {
                "title": l_data.get("title", ""),
                "order": l_data.get("order", 0),
                "tracks_total": 13,   # Future MD13 integration default
                "center_track": 7,
                "expansion_factor": 1.2
            }
            
        # Nodes (expansão obrigatória conforme MD11)
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
                    "branch_depth": 0,
                    "cycle_depth": 0  # MD18: nível de aninhamento de ciclo
                },
                "links": {
                    "prev_nodes": [],
                    "next_nodes": [],
                    "in_edges": [],
                    "out_edges": []
                },
                # Para compatibilizar com CFFEngine, inicializamos sempre branch_context;
                # nós que não estiverem em branch permanecem com root_decision vazio.
                "branch_context": {
                    "root_decision": "",
                    "branch_label": "",
                    "terminates_soon": False
                },
                "future_metrics": {
                    "future_steps": 0,
                    "future_decisions": 0,
                    "cross_lane_ahead": 0,
                    "next_lane_target": ""
                },
                # Contexto de ciclo (MD18)
                "cycle_context": {
                    "cycle_id": "",
                    "cycle_level": 0,
                    "cycle_root": "",
                    "cycle_exit_nodes": []
                },
                "layout_hints": {
                    "is_main_path": False,
                    "routing_priority": 0,
                    "preferred_exit_side": "",
                    "preferred_entry_side": ""
                },
                # Conveniência interna (MD12 Etapa 3)
                "in_degree": 0,
                "out_degree": 0
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
        """Popula links prev/next, graus e resumo em cpff.graph (MD12 Etapa 3)."""
        prev_index = {nid: [] for nid in self.nodes.keys()}
        next_index = {nid: [] for nid in self.nodes.keys()}

        for e_id, e in self.edges.items():
            src_id = e["from"]
            dst_id = e["to"]

            # Populate Links for Source
            if src_id in self.nodes:
                self.nodes[src_id]["links"]["out_edges"].append(e_id)
                self.nodes[src_id]["links"]["next_nodes"].append(dst_id)
                next_index[src_id].append(dst_id)

            # Populate Links for Dest
            if dst_id in self.nodes:
                self.nodes[dst_id]["links"]["in_edges"].append(e_id)
                self.nodes[dst_id]["links"]["prev_nodes"].append(src_id)
                prev_index[dst_id].append(src_id)

        # Remover duplicados e ordenar para garantir determinismo
        for nid, node in self.nodes.items():
            links = node["links"]
            links["prev_nodes"] = sorted(set(links["prev_nodes"]))
            links["next_nodes"] = sorted(set(links["next_nodes"]))
            links["in_edges"] = sorted(set(links["in_edges"]))
            links["out_edges"] = sorted(set(links["out_edges"]))

            node["in_degree"] = len(links["in_edges"])
            node["out_degree"] = len(links["out_edges"])

        for nid in prev_index:
            prev_index[nid] = sorted(set(prev_index[nid]))
        for nid in next_index:
            next_index[nid] = sorted(set(next_index[nid]))

        self.cpff["graph"] = {
            "prev": prev_index,
            "next": next_index
        }

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

            # Percorrer próximos nós em ordem determinística
            for next_id in sorted(node["links"]["next_nodes"]):
                if next_id not in visited:
                    visited.add(next_id)
                    
                    next_node = self.nodes[next_id]
                    if is_decision:
                        # Nós abaixo de uma decisão ganham branch_depth>0
                        next_node["rank"]["branch_depth"] = node["rank"]["branch_depth"] + 1
                        next_node["branch_context"] = {
                            "root_decision": curr_id,
                            # O rótulo exato do branch é conhecido na edge;
                            # aqui mantemos vazio e deixamos export/layout decidir exibição.
                            "branch_label": "",
                            "terminates_soon": False
                        }
                    else:
                        next_node["rank"]["branch_depth"] = node["rank"]["branch_depth"]
                        # Propaga contexto de branch se existir
                        if node.get("branch_context"):
                            next_node["branch_context"] = dict(node["branch_context"])
                            
                    queue.append((next_id, current_depth + 1))
                    
        # max_depth obrigatório em stats (MD11/MD12)
        self.cpff["stats"]["max_depth"] = max_d

        # Sort per lane (MD12 Etapa 7)
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

    def _detect_cycles_and_cycle_context(self):
        """MD18: Detecta componentes fortemente conectados (SCC) e ciclo_context.

        - Usa algoritmo de Tarjan para identificar SCCs.
        - SCCs com mais de 1 nó são considerados ciclos estruturais.
        - Atribui a cada nó em ciclo:
            - cycle_id (cycle_1, cycle_2, ...)
            - cycle_level (nível de aninhamento)
            - cycle_root (nó com menor rank.global dentro do ciclo)
            - cycle_exit_nodes (nós que saem do ciclo)
        - Detecta ciclos sem saída externa e lança CYCLE_WITHOUT_EXIT.
        """
        if not self.nodes:
            return

        # Grafo baseado em links next_nodes
        graph = {nid: list(n["links"]["next_nodes"]) for nid, n in self.nodes.items()}

        index = 0
        stack = []
        on_stack = set()
        indices = {}
        lowlinks = {}
        scc_list = []

        def strongconnect(v):
            nonlocal index
            indices[v] = index
            lowlinks[v] = index
            index += 1
            stack.append(v)
            on_stack.add(v)

            for w in graph.get(v, []):
                if w not in indices:
                    strongconnect(w)
                    lowlinks[v] = min(lowlinks[v], lowlinks[w])
                elif w in on_stack:
                    lowlinks[v] = min(lowlinks[v], indices[w])

            if lowlinks[v] == indices[v]:
                # Raiz de uma SCC
                scc = []
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    scc.append(w)
                    if w == v:
                        break
                scc_list.append(scc)

        for v in self.nodes.keys():
            if v not in indices:
                strongconnect(v)

        # Mapear SCCs e identificar quais são ciclos (|SCC| > 1)
        node_to_scc = {}
        cyclic_scc_ids = []
        for idx, comp in enumerate(scc_list):
            for nid in comp:
                node_to_scc[nid] = idx
            if len(comp) > 1:
                cyclic_scc_ids.append(idx)

        if not cyclic_scc_ids:
            return

        # Construir DAG condensado entre SCCs
        scc_edges = {i: set() for i in range(len(scc_list))}
        for e in self.edges.values():
            src = e["from"]
            dst = e["to"]
            if src in node_to_scc and dst in node_to_scc:
                c_src = node_to_scc[src]
                c_dst = node_to_scc[dst]
                if c_src != c_dst:
                    scc_edges[c_src].add(c_dst)

        # Detectar ciclos sem saída (MD18 8)
        for cid in cyclic_scc_ids:
            has_exit = False
            for nid in scc_list[cid]:
                for nxt in graph.get(nid, []):
                    if node_to_scc.get(nxt) != cid:
                        has_exit = True
                        break
                if has_exit:
                    break
            if not has_exit:
                raise ValueError("CYCLE_WITHOUT_EXIT")

        # Construir lista de SCCs cíclicas com ordem determinística por menor id
        cyclic_scc_ids_sorted = sorted(
            cyclic_scc_ids,
            key=lambda cid: min(scc_list[cid])
        )
        scc_to_cycle_id = {
            cid: f"cycle_{i+1}" for i, cid in enumerate(cyclic_scc_ids_sorted)
        }

        # Construir grafo reverso de SCCs para calcular cycle_level
        rev_edges = {i: set() for i in range(len(scc_list))}
        for src_c, dsts in scc_edges.items():
            for d in dsts:
                rev_edges[d].add(src_c)

        from functools import lru_cache

        @lru_cache(maxsize=None)
        def scc_level(cid):
            if cid not in cyclic_scc_ids:
                return 0
            preds = [p for p in rev_edges[cid] if p in cyclic_scc_ids]
            if not preds:
                return 1
            return 1 + max(scc_level(p) for p in preds)

        # Preencher cycle_context e cycle_depth nos nós
        for cid in cyclic_scc_ids:
            comp_nodes = scc_list[cid]
            # Root: menor rank.global e, em empate, menor id
            root = min(
                comp_nodes,
                key=lambda nid: (
                    self.nodes[nid]["rank"].get("global", 0),
                    nid,
                ),
            )
            exits = set()
            for nid in comp_nodes:
                for nxt in graph.get(nid, []):
                    if node_to_scc.get(nxt) != cid:
                        exits.add(nid)

            level = scc_level(cid)
            cycle_id = scc_to_cycle_id[cid]

            for nid in comp_nodes:
                node = self.nodes[nid]
                node["rank"]["cycle_depth"] = level
                node["cycle_context"] = {
                    "cycle_id": cycle_id,
                    "cycle_level": level,
                    "cycle_root": root,
                    "cycle_exit_nodes": sorted(exits),
                }

    def _compute_main_path(self):
        """Identifica o main path (MD12 Etapa 5) de forma determinística."""
        entry_start = self.sff_source.get("entry", {}).get("start")
        if not entry_start or entry_start not in self.nodes:
            return

        curr = entry_start
        visited = set()

        def edge_sort_key(edge):
            # Ordena por id para empate determinístico
            return edge["id"]

        while curr and curr not in visited:
            visited.add(curr)
            self._main_path_nodes.add(curr)
            node = self.nodes[curr]
            out_edges_ids = node["links"]["out_edges"]
            if not out_edges_ids:
                break

            # Selecionar edge principal conforme regras:
            edges = [self.edges[eid] for eid in out_edges_ids]
            edges.sort(key=edge_sort_key)

            chosen = None
            ntype = node.get("type")

            if ntype == "decision":
                # 1) Branch "true" / equivalentes
                true_labels = {"true", "yes", "sim"}
                true_edges = [e for e in edges if str(e.get("branch", "")).lower() in true_labels]
                # 2) Caso contrário, primeira branch declarada
                branch_edges = [e for e in edges if e.get("branch")]
                if true_edges:
                    chosen = true_edges[0]
                elif branch_edges:
                    chosen = branch_edges[0]
                else:
                    # Fallback: fluxo linear
                    chosen = edges[0]
            else:
                # Não-decision: prioriza edges sem branch
                linear_edges = [e for e in edges if not e.get("branch")]
                if linear_edges:
                    chosen = linear_edges[0]
                else:
                    chosen = edges[0]

            if not chosen:
                break

            eid = chosen["id"]
            self._main_path_edges.add(eid)
            curr = chosen["to"]

    def _classify_edges(self):
        for e_id, e in self.edges.items():
            src_node = self.nodes.get(e["from"])
            dst_node = self.nodes.get(e["to"])
            
            if not src_node or not dst_node:
                continue
            
            # Loops v1.0: self-loop proibido (MD17 3.3)
            if e["from"] == e["to"]:
                raise ValueError("SELF_LOOP_NOT_SUPPORTED_V1")

            kind = None
            priority = None

            # Return/Loop? (Depth of target < ou = Depth de origem) — MD17 2/3.1
            if dst_node["rank"]["global"] <= src_node["rank"]["global"]:
                kind = "return"
                e["classification"]["is_return"] = True
                # Loop cross-lane (MD17 3.2): return + cross_lane
                if src_node.get("lane") != dst_node.get("lane"):
                    e["classification"]["is_cross_lane"] = True
                priority = 40

            # Join? (Target tem múltiplas entradas e não é return)
            if kind is None and len(dst_node["links"]["in_edges"]) > 1:
                kind = "join"
                e["classification"]["is_join"] = True
                priority = 30

            # Main path? (conecta nós consecutivos do main path)
            if kind is None and e_id in self._main_path_edges:
                kind = "main_path"
                priority = 100

            # Branch?
            if kind is None and e.get("branch"):
                kind = "branch"
                priority = 80

            # Cross Lane?
            if kind is None and src_node.get("lane") != dst_node.get("lane"):
                kind = "cross_lane"
                e["classification"]["is_cross_lane"] = True
                priority = 60

            # Fallback determinístico
            if kind is None:
                kind = "main_path"
                priority = 100

            e["classification"]["kind"] = kind
            e["priority"] = priority

            # Hints básicos para roteamento conforme MD11
            src_lane = src_node.get("lane") if src_node else ""
            e["routing_hints"]["backbone_lane"] = src_lane or ""

        # Atualizar layout_hints em nós com base no main path identificado
        for nid, node in self.nodes.items():
            is_main = nid in self._main_path_nodes
            node["layout_hints"]["is_main_path"] = is_main
            node["layout_hints"]["routing_priority"] = 100 if is_main else 60

            # Preferências simples de entrada/saída por direção do fluxo
            direction = self.sff_source.get("sff", {}).get("direction", "TB")
            if direction == "TB":
                node["layout_hints"]["preferred_entry_side"] = "top"
                node["layout_hints"]["preferred_exit_side"] = "bottom"
            else:
                node["layout_hints"]["preferred_entry_side"] = "left"
                node["layout_hints"]["preferred_exit_side"] = "right"

    def _calculate_future_metrics(self):
        for nid, node in self.nodes.items():
            seen = set()
            queue = [nid]
            decisions = 0
            cross_lanes = 0
            origin_lane = node.get("lane")
            next_lane_target = ""
            lane_window_counts = {}
            origin_depth = node["rank"].get("depth", 0)
            
            while queue:
                curr = queue.pop(0)
                if curr != nid:
                    seen.add(curr)
                    if self.nodes[curr].get("type") == "decision":
                        decisions += 1
                
                for eid in self.nodes[curr]["links"]["out_edges"]:
                    edge = self.edges[eid]
                    nxt = edge["to"]

                    # Ignore loops to evitar contagens infinitas (MD17)
                    if edge["classification"].get("is_return"):
                        continue

                    if edge["classification"].get("is_cross_lane"):
                        cross_lanes += 1

                    if nxt not in seen and nxt not in queue:
                        queue.append(nxt)

                    # Janela de 2 níveis à frente para next_lane_target
                    target_node = self.nodes.get(nxt)
                    if target_node:
                        t_lane = target_node.get("lane")
                        depth_diff = target_node["rank"].get("depth", 0) - origin_depth
                        if t_lane and t_lane != origin_lane and 1 <= depth_diff <= 2:
                            lane_window_counts[t_lane] = lane_window_counts.get(t_lane, 0) + 1
                        
            node["future_metrics"]["future_steps"] = len(seen)
            node["future_metrics"]["future_decisions"] = decisions
            node["future_metrics"]["cross_lane_ahead"] = cross_lanes

            if lane_window_counts:
                # Lane predominante; em caso de empate, menor id lexicográfico
                best_lane = sorted(lane_window_counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
                next_lane_target = best_lane
            node["future_metrics"]["next_lane_target"] = next_lane_target or ""

    def _finalize_stats(self):
        stats = self.cpff["stats"]
        stats["nodes_total"] = len(self.nodes)
        stats["edges_total"] = len(self.edges)
        stats["lanes_total"] = len(self.lanes)
        stats["decision_nodes"] = sum(1 for n in self.nodes.values() if n.get("type") == "decision")
        stats["branch_edges"] = sum(1 for e in self.edges.values() if e.get("classification", {}).get("kind") == "branch")
        stats["joins"] = sum(1 for e in self.edges.values() if e.get("classification", {}).get("kind") == "join")
        
        max_branch_depth = max((n["rank"]["branch_depth"] for n in self.nodes.values()), default=0)
        stats["max_branch_depth"] = max_branch_depth

        # MD18/MD19 — Estatísticas de ciclos e branches simultâneos
        cycle_ids = set()
        max_cycle_depth = 0
        for n in self.nodes.values():
            cc = n.get("cycle_context", {})
            cid = cc.get("cycle_id")
            if cid:
                cycle_ids.add(cid)
            max_cycle_depth = max(max_cycle_depth, n["rank"].get("cycle_depth", 0))
        stats["cycles_total"] = len(cycle_ids)
        stats["max_cycle_depth"] = max_cycle_depth

        # B (MD19): máximo de branches simultâneas em um mesmo rank.global
        branches_per_rank = {}
        for e in self.edges.values():
            if e.get("classification", {}).get("kind") == "branch":
                src = self.nodes.get(e["from"])
                if not src:
                    continue
                r = src["rank"].get("global", 0)
                branches_per_rank[r] = branches_per_rank.get(r, 0) + 1
        stats["max_branches_per_rank"] = max(branches_per_rank.values(), default=0)

        # T (MD19): máximo de tracks configuradas por lane (antes de expansões em runtime)
        stats["max_tracks_per_lane"] = max(
            (lane.get("tracks_total", 0) for lane in self.lanes.values()),
            default=0,
        )

        # layout_context mínimo: direção do fluxo herdada do SFF
        self.cpff["layout_context"] = {
            "direction": self.sff_source.get("sff", {}).get("direction", "TB")
        }

        # Normalizar branch_depth/branch_context pós-join (Etapa 6 MD12)
        for nid, node in self.nodes.items():
            parents = node["links"]["prev_nodes"]
            if parents:
                min_bd = min(self.nodes[p]["rank"].get("branch_depth", 0) for p in parents)
                node["rank"]["branch_depth"] = min_bd

            # Se branch_depth final for 0, resetar contexto de branch
            if node["rank"].get("branch_depth", 0) == 0:
                node["branch_context"] = {
                    "root_decision": "",
                    "branch_label": "",
                    "terminates_soon": False
                }

