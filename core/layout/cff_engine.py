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
import os
import json
from core.layout.track_system import TrackSystem
from core.layout.cff_router import CFFRouter
from core.layout.congestion import GlobalCongestionManager
from core.logger.logger import Logger

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
        self._base_rank_gap = self.RANK_GAP
        self.LANE_WIDTH = 300
        # Componentes
        self.track_system = None  # Instanciado a cada tentativa de layout
        self.congestion_manager = GlobalCongestionManager(self)
        # Resultados
        self.layout_nodes = {}
        self.layout_edges = {}
        self.layout_lanes = {}
        # Versão
        self.engine_version = "1.0"
        # Logger
        self._logger = Logger()
        # MD22: coletores de debug por execução
        self._routing_failures = []
        self._bridge_dump = []

    def generate(self):
        """
        Executa pipeline determinístico do layout engine conforme MD13.
        """
        # Reset de estruturas de debug (MD22) a cada geração
        self._routing_failures = []
        self._bridge_dump = []
        # Fase 1 — Análise pré-roteamento (MD16)
        self._logger.info("[CFF-ENGINE] Iniciando layout determinístico (MD13+MD15+MD16+MD18+MD19)")
        self.congestion_manager.analyze_prerouting()

        attempt = self.congestion_manager.global_expansion_count

        # Fase 2/3 — Roteamento com monitoramento e expansões globais
        while attempt < self.congestion_manager.max_global_expansions:
            # Reset dos artefatos de cada tentativa
            self.track_system = TrackSystem(self.lanes)
            self.layout_nodes = {}
            self.layout_edges = {}
            self.layout_lanes = {}
            self.congestion_manager.reset_runtime_state()

            self._initialize_lanes()
            self._position_nodes()
            try:
                self._route_edges()
            except Exception as e:
                msg = str(e)
                # Se falha for de roteamento ou congestionamento, tentar expansão global
                if "ROUTING_IMPOSSIBLE" in msg or "CONGESTION_DETECTED" in msg:
                    # Registrar falha de roteamento/canal para routing_failures.json (MD22)
                    self._routing_failures.append(
                        {
                            "attempt": attempt + 1,
                            "error": msg,
                            "global_expansions_before": self.congestion_manager.global_expansion_count,
                        }
                    )
                    self._logger.warn(f"[CFF-ENGINE] Tentativa {attempt+1} falhou: {msg}")
                    attempt += 1
                    self.congestion_manager.global_expansion_count = attempt
                    try:
                        self.congestion_manager.check_final_limits_or_raise()
                    except ValueError as final_err:
                        # Propaga erro estrutural
                        raise ValueError(str(final_err))
                    # Aplica expansão global e reinicia loop
                    self._logger.info(f"[CFF-ENGINE] Aplicando expansão global #{attempt} (MD16)")
                    self.congestion_manager.apply_global_expansion(attempt)
                    continue
                # Outros erros são propagados diretamente
                raise ValueError(f"LAYOUT_IMPOSSIBLE_WITH_CURRENT_GRID: {msg}")

            # Se roteou mas métricas indicaram congestionamento crítico
            if self.congestion_manager.is_congested():
                attempt += 1
                self.congestion_manager.global_expansion_count = attempt
                try:
                    self.congestion_manager.check_final_limits_or_raise()
                except ValueError as final_err:
                    raise ValueError(str(final_err))
                self._logger.info(f"[CFF-ENGINE] Métricas de congestionamento indicaram saturação; expansão global #{attempt} (MD16)")
                self.congestion_manager.apply_global_expansion(attempt)
                continue

            # Sucesso sem congestionamento crítico
            self._logger.info(f"[CFF-ENGINE] Layout convergiu em {attempt+1} tentativa(s)")
            break

        # MD19 — métricas formais aproximadas de complexidade/escala visual
        stats = self.cpff.get("cpff", {}).get("stats", {})
        n_nodes = len(self.nodes)
        n_edges = len(self.edges)
        n_lanes = len(self.lanes)
        max_depth = stats.get("max_depth", 0)
        max_tracks = max(
            (lane.get("tracks_total", 0) for lane in self.lanes.values()),
            default=0,
        )
        # track_gap assumido constante entre lanes no TrackSystem
        track_gap = 0
        if self.track_system and self.track_system.lanes:
            any_lane = next(iter(self.track_system.lanes.values()))
            track_gap = any_lane.get("track_gap", 0)

        estimated_height = max_depth * self.RANK_GAP
        estimated_width = n_lanes * self.LANE_WIDTH + (max_tracks / 2.0) * track_gap

        complexity = {
            "N": n_nodes,
            "E": n_edges,
            "L": n_lanes,
            "T_max": max_tracks,
            "D_max": max_depth,
            "B_max": stats.get("max_branches_per_rank", 0),
            "cycles_total": stats.get("cycles_total", 0),
            "max_cycle_depth": stats.get("max_cycle_depth", 0),
            "estimated_height": estimated_height,
            "estimated_width": estimated_width,
            # Classes de complexidade teóricas (MD19, documentais)
            "compiler_complexity": "O(N+E)",
            "layout_complexity": "O(E log E)",
        }

        self._logger.info(
            "[CFF-ENGINE] Complexity: N={N}, E={E}, L={L}, D_max={D_max}, "
            "T_max={T_max}, B_max={B_max}, cycles={cycles_total}, max_cycle_depth={max_cycle_depth}, "
            "height≈{h}, width≈{w}, expansions={exp}".format(
                N=complexity["N"],
                E=complexity["E"],
                L=complexity["L"],
                D_max=complexity["D_max"],
                T_max=complexity["T_max"],
                B_max=complexity["B_max"],
                cycles_total=complexity["cycles_total"],
                max_cycle_depth=complexity["max_cycle_depth"],
                h=int(complexity["estimated_height"]),
                w=int(complexity["estimated_width"]),
                exp=self.congestion_manager.global_expansion_count,
            )
        )

        # MD22 — dumps de debug para validação offline
        self._write_debug_dumps(complexity, stats)

        return {
            "nodes": self.layout_nodes,
            "edges": self.layout_edges,
            "lanes": self.layout_lanes,
            "engine_version": self.engine_version,
            "complexity": complexity,
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
        # Router MD15/MD17 recebe TrackSystem, direção, nós e lanes em layout
        router = CFFRouter(
            self.track_system,
            self.direction,
            layout_nodes=self.layout_nodes,
            layout_lanes=self.layout_lanes,
        )
        
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
            # Atualiza métricas de congestionamento para esta edge (MD16 Fase 2)
            if self.congestion_manager:
                self.congestion_manager.update_after_edge(e)

        # Após roteamento bem-sucedido, capturar uso de bridge corridors (MD22)
        if getattr(router, "bridge_segments", None):
            self._bridge_dump = list(router.bridge_segments)

    def _write_debug_dumps(self, complexity, stats):
        """Gera arquivos de debug conforme checklist do MD22.

        - layout_dump.json: nós, edges, lanes, stats e complexidade
        - occupancy_dump.json: ocupação H/V por lane/track
        - bridge_dump.json: uso de bridge corridors
        - routing_failures.json: falhas intermediárias de roteamento/canal
        """
        try:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs"))
            os.makedirs(base_dir, exist_ok=True)

            layout_dump = {
                "nodes": self.layout_nodes,
                "edges": self.layout_edges,
                "lanes": self.layout_lanes,
                "cpff_stats": stats,
                "complexity": complexity,
            }

            occupancy_dump = {}
            if self.track_system is not None:
                for lane_id, lane in self.track_system.lanes.items():
                    occupancy_dump[lane_id] = {
                        "center_track": lane.get("center_track"),
                        "tracks_total": lane.get("tracks_total"),
                        "track_gap": lane.get("track_gap"),
                        "H": lane.get("occupancy_map", {}).get("H", {}),
                        "V": lane.get("occupancy_map", {}).get("V", {}),
                    }

            bridge_dump = list(self._bridge_dump or [])
            routing_failures = list(self._routing_failures or [])

            with open(os.path.join(base_dir, "layout_dump.json"), "w", encoding="utf-8") as f:
                json.dump(layout_dump, f, ensure_ascii=False, indent=2)
            with open(os.path.join(base_dir, "occupancy_dump.json"), "w", encoding="utf-8") as f:
                json.dump(occupancy_dump, f, ensure_ascii=False, indent=2)
            with open(os.path.join(base_dir, "bridge_dump.json"), "w", encoding="utf-8") as f:
                json.dump(bridge_dump, f, ensure_ascii=False, indent=2)
            with open(os.path.join(base_dir, "routing_failures.json"), "w", encoding="utf-8") as f:
                json.dump(routing_failures, f, ensure_ascii=False, indent=2)

            self._logger.info(
                "[CFF-ENGINE] Debug dumps escritos em logs/: layout_dump.json, occupancy_dump.json, "
                "bridge_dump.json, routing_failures.json"
            )
        except Exception as e:
            # Não quebra o layout se debug falhar; apenas loga erro.
            self._logger.error(f"[CFF-ENGINE] Falha ao escrever dumps de debug MD22: {e}")
