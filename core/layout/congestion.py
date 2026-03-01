"""
core/layout/congestion.py

Sistema de Detecção e Resolução de Congestionamento Global (MD16 v1.0).

Atua entre o Layout Engine (MD13) e o Roteador Ortogonal (MD15), com foco em:
  - Detectar saturação estrutural de lanes/tracks
  - Monitorar utilização de tracks e densidade por rank
  - Decidir expansões globais de forma determinística

Escopo da versão 1.0 (implementação inicial):
  - Métricas implementadas: TUR (Track Utilization Ratio), RED aproximado, BS
  - Suporte a expansão global de tracks_total e rank_gap
  - Máximo de N expansões globais antes de LAYOUT_UNSCALABLE_STRUCTURE

Esta implementação é conservadora: prefere manter thresholds altos para
não interferir em fluxos pequenos, servindo como base para futuras
otimizações.
"""


class GlobalCongestionManager:
    """Gerencia métricas de congestionamento global (MD16).

    Conectado a uma instância de CFFEngine, acompanha:
      - Utilização de tracks por lane (TUR)
      - Densidade de edges por rank (RED aproximado)
      - Saturação do backbone principal (BS)

    Quando qualquer métrica passa de um limiar crítico, sinaliza
    congestão e permite ao engine aplicar expansão global e reiniciar
    o roteamento.
    """

    # Thresholds MD16 (valores conservadores para v1.0)
    TUR_WARN = 0.70
    TUR_CRITICAL = 0.85
    BS_CRITICAL = 0.75
    # RED aproximado: edges por pixel de largura (lane_width)
    RED_CRITICAL = 0.04

    # Configuração de capacidade: quantas edges "seguras" por track
    EDGES_PER_TRACK_SAFE = 4

    def __init__(self, engine):
        self.engine = engine
        self.max_global_expansions = 3
        self.global_expansion_count = 0
        self.congested = False
        # Estado dinâmico por lane/rank
        self.edges_per_rank = {}  # chave: (lane_id, rank_global) -> count

    # ------------------------------------------------------------------
    # Fase 1 — Análise pré-roteamento
    # ------------------------------------------------------------------
    def analyze_prerouting(self):
        """Analisa o CFF antes de rotear qualquer edge (MD16 Fase 1).

        Estratégia simples:
          - Para cada lane, estima ocupação projetada a partir do número
            total de edges que passam por ela (origem ou destino na lane).
          - Se TUR projetado > TUR_CRITICAL, aplica uma expansão global
            inicial de tracks em todas as lanes.
        """
        lanes = self.engine.lanes
        nodes = self.engine.nodes
        edges = self.engine.edges

        need_expand = False
        for lane_id in lanes.keys():
            edges_in_lane = 0
            for e in edges.values():
                src_lane = nodes.get(e["from"], {}).get("lane")
                dst_lane = nodes.get(e["to"], {}).get("lane")
                if src_lane == lane_id or dst_lane == lane_id:
                    edges_in_lane += 1
            tracks_total = lanes[lane_id].get("tracks_total", 1)
            safe_capacity = max(1, tracks_total * self.EDGES_PER_TRACK_SAFE)
            tur_proj = edges_in_lane / safe_capacity
            if tur_proj > self.TUR_CRITICAL:
                need_expand = True

        if need_expand and self.global_expansion_count < self.max_global_expansions:
            self.global_expansion_count += 1
            if getattr(self.engine, "_logger", None):
                self.engine._logger.info(
                    f"[CONGESTION] Pré-roteamento indica alta projeção de ocupação; expansão global inicial #{self.global_expansion_count}"
                )
            self.apply_global_expansion(self.global_expansion_count)

    # ------------------------------------------------------------------
    # Fase 2 — Monitoramento durante roteamento
    # ------------------------------------------------------------------
    def reset_runtime_state(self):
        self.congested = False
        self.edges_per_rank.clear()

    def update_after_edge(self, edge):
        """Atualiza métricas de congestionamento após rotear uma edge.

        - TUR: baseado em occupancy_map do TrackSystem
        - RED: contagem de edges por rank.global (aproximado)
        - BS: saturação de tracks pelo backbone principal

        Se alguma métrica cruza o limite crítico, marca self.congested
        e lança ValueError para que o engine possa reagir.
        """
        if self.engine.track_system is None:
            return
        ts = self.engine.track_system
        nodes = self.engine.nodes
        lanes = ts.lanes

        src_id = edge["from"]
        dst_id = edge["to"]
        src_node = nodes.get(src_id, {})
        dst_node = nodes.get(dst_id, {})
        lane_id = src_node.get("lane")
        if lane_id not in lanes:
            return

        lane_state = lanes[lane_id]
        tracks_total = lane_state.get("tracks_total", 1)

        # TUR: quantas tracks estão efetivamente ocupadas nesta lane
        used_tracks = set(lane_state["occupancy_map"]["H"].keys()) | set(
            lane_state["occupancy_map"]["V"].keys()
        )
        tur = len(used_tracks) / tracks_total if tracks_total > 0 else 1.0

        # RED aproximado: edges por rank.global e largura da lane
        rank_src = src_node.get("rank", {}).get("global", 1)
        lane_width = self.engine.LANE_WIDTH
        key = (lane_id, rank_src)
        self.edges_per_rank[key] = self.edges_per_rank.get(key, 0) + 1
        red = self.edges_per_rank[key] / max(1, lane_width)

        # BS: ocupação do backbone por tracks (edges main_path)
        bs = 0.0
        if edge.get("classification", {}).get("kind") == "main_path":
            # Descobre em qual track esta edge foi reservada (se houver)
            backbone_tracks = set()
            edge_id = edge.get("id")
            # Apenas horizontal em TB e vertical em LR são considerados
            if self.engine.direction == "TB":
                for t_idx, segments in lane_state["occupancy_map"]["H"].items():
                    for _, _, owner in segments:
                        if owner == edge_id:
                            backbone_tracks.add(t_idx)
            else:
                for t_idx, segments in lane_state["occupancy_map"]["V"].items():
                    for _, _, owner in segments:
                        if owner == edge_id:
                            backbone_tracks.add(t_idx)
            if backbone_tracks:
                bs = len(backbone_tracks) / tracks_total

        # Verificações de limiar crítico
        if tur > self.TUR_CRITICAL or red > self.RED_CRITICAL or bs > self.BS_CRITICAL:
            self.congested = True
            if getattr(self.engine, "_logger", None):
                self.engine._logger.warn(
                    "[CONGESTION] Limite crítico atingido: "
                    f"TUR={tur:.2f}, RED={red:.4f}, BS={bs:.2f} na lane={lane_id}"
                )
            raise ValueError(
                "CONGESTION_DETECTED: TUR={:.2f}, RED={:.4f}, BS={:.2f}".format(
                    tur, red, bs
                )
            )

    # ------------------------------------------------------------------
    # Fase 3 — Expansão global
    # ------------------------------------------------------------------
    def is_congested(self):
        return self.congested

    def apply_global_expansion(self, step_index: int):
        """Aplica expansão global determinística (MD16 Seção 5/8).

        Ordem de prioridade (sempre):
          1. Expandir tracks_total em todas as lanes
          2. Expandir rank_gap (a partir do passo 2)

        Outros itens (backbone secundário, rank buffer) não são
        implementados nesta versão.
        """
        # 1. Expandir tracks_total em todas as lanes (global, simétrico)
        for lane_id, lane in self.engine.lanes.items():
            # Cada passo global aumenta 2 tracks, mantendo center_track
            lane["tracks_total"] = lane.get("tracks_total", 1) + 2

        # 2. Expandir rank_gap a partir do segundo passo
        if step_index >= 2:
            base_gap = getattr(self.engine, "_base_rank_gap", self.engine.RANK_GAP)
            # Mantém determinismo: rank_gap = base + step*40
            self.engine.RANK_GAP = base_gap + step_index * 40

    # ------------------------------------------------------------------
    # Fase 4 — Limites globais
    # ------------------------------------------------------------------
    def check_final_limits_or_raise(self):
        """Lança erro estrutural se já excedeu o limite de expansões.

        Corresponde ao LAYOUT_UNSCALABLE_STRUCTURE do MD16.
        """
        if self.global_expansion_count >= self.max_global_expansions:
            if getattr(self.engine, "_logger", None):
                self.engine._logger.error(
                    "[CONGESTION] LAYOUT_UNSCALABLE_STRUCTURE: limite de expansões globais excedido"
                )
            raise ValueError("LAYOUT_UNSCALABLE_STRUCTURE")
