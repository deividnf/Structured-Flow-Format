"""
core/layout/cff_router.py
Roteador ortogonal para o Layout Engine Determinístico (MD13/MD15/MD17/MD21).

Implementa o modelo formal do MD15 v1.0:
    - TB: V → H → V
    - LR: H → V → H

E incorpora partes de MD20/MD21 para Flow-Only:
    - Channel Allocator por faixa de ranks e tipo de edge
    - Bridge corridors simplificado para edges cross_lane em TB

Sem uso de heurísticas visuais aleatórias, apenas:
    - Portas ortogonais (top/bottom/left/right)
    - Escolha determinística de track (center, +1, -1, +2, -2, ...)
    - Verificação básica de conflito via TrackSystem
    - Verificação de bounding box para o segmento intermediário
"""


class CFFRouter:
    def __init__(self, track_system, direction="TB", layout_nodes=None, layout_lanes=None):
        self.ts = track_system
        self.direction = direction
        # Layout completo dos nós para checar bounding boxes (MD15/MD17)
        self.layout_nodes = layout_nodes or {}
        self.layout_lanes = layout_lanes or {}
        from core.logger.logger import Logger
        self._logger = Logger()
        # MD21: parâmetros básicos de canais e bridge corridors (Flow-Only)
        self.RANK_BAND_SIZE = 2
        # MD21 fala em K0/K_MAX para offsets adaptativos; aqui usamos _iter_tracks
        # com ordem 0,+1,-1,+2,-2,... o que corresponde conceitualmente.
        # Bridge corridors (TB): offsets opcionais
        self.BRIDGE_SPINE_OFFSET = 0

        # Channel Allocator por (lane, banda de ranks, kind, role, direction)
        # Garante canais estáveis por tipo de edge dentro de uma banda de ranks.
        # Estrutura: {(lane_id, band_idx, kind, role, direction): track_index}
        self._channel_map = {}

        # Ocupação simples de bridge corridors para debug (MD21/MD22)
        # Lista de dicts com spine, lanes e edges que usaram o corredor
        self.bridge_segments = []

        # Índice de lanes em X para bridge corridors (TB)
        self._lane_order = []
        self._lane_index = {}
        if self.layout_lanes:
            ordered = sorted(self.layout_lanes.items(), key=lambda kv: kv[1].get("x_start", 0))
            self._lane_order = [lid for lid, _ in ordered]
            self._lane_index = {lid: i for i, lid in enumerate(self._lane_order)}

    # --- API pública -----------------------------------------------------
    def route_edge(self, edge, src_node, dst_node, orig_src, orig_dst):
        """Roteia uma edge seguindo o padrão MD15/MD17.

        - Edges normais seguem V-H-V (TB) ou H-V-H (LR)
        - Edges de loop (`kind=return`) usam backbone externo dedicado (MD17),
          com rota expandida fora das lanes principais.
        - Edges cross_lane em TB usam bridge corridor simplificado (MD21)
        """
        kind = edge.get("classification", {}).get("kind")

        # Loops externos (MD17)
        if kind == "return":
            if self.direction == "TB":
                return self._route_tb_return(edge, src_node, dst_node, orig_src, orig_dst)
            return self._route_lr_return(edge, src_node, dst_node, orig_src, orig_dst)

        # Cross-lane com bridge corridor (MD21) — apenas TB por enquanto
        if kind == "cross_lane" and self.direction == "TB":
            return self._route_tb_cross_lane_bridge(edge, src_node, dst_node, orig_src, orig_dst)

        if self.direction == "TB":
            return self._route_tb(edge, src_node, dst_node, orig_src, orig_dst)
        return self._route_lr(edge, src_node, dst_node, orig_src, orig_dst)

    # --- Helpers geométricos --------------------------------------------
    def _node_bbox(self, node):
        x = node["x"]
        y = node["y"]
        w = node["width"]
        h = node["height"]
        return (
            x - w / 2.0,
            x + w / 2.0,
            y - h / 2.0,
            y + h / 2.0,
        )

    def _horizontal_hits_node(self, y, x_start, x_end, ignore_ids=None):
        """Verifica se um segmento horizontal intersecta bounding box de algum nó.

        Considera apenas nós cujo intervalo em X intersecta [x_start, x_end]
        e que contêm a coordenada Y do segmento.
        """
        ignore_ids = ignore_ids or set()
        x_min, x_max = min(x_start, x_end), max(x_start, x_end)
        for n_id, node in self.layout_nodes.items():
            if n_id in ignore_ids:
                continue
            nx_min, nx_max, ny_min, ny_max = self._node_bbox(node)
            if ny_min <= y <= ny_max:
                if not (x_max <= nx_min or x_min >= nx_max):
                    return True
        return False

    def _vertical_hits_node(self, x, y_start, y_end, ignore_ids=None):
        """Verifica se um segmento vertical intersecta bounding box de algum nó."""
        ignore_ids = ignore_ids or set()
        y_min, y_max = min(y_start, y_end), max(y_start, y_end)
        for n_id, node in self.layout_nodes.items():
            if n_id in ignore_ids:
                continue
            nx_min, nx_max, ny_min, ny_max = self._node_bbox(node)
            if nx_min <= x <= nx_max:
                if not (y_max <= ny_min or y_min >= ny_max):
                    return True
        return False

    def _iter_tracks(self, lane_id):
        """Gera índices de track em ordem simétrica em torno do centro.

        center, center+1, center-1, center+2, center-2, ...
        """
        lane = self.ts.lanes[lane_id]
        center = lane["center_track"]
        total = lane["tracks_total"]
        # tracks numeradas de 1..total (ou conforme já vierem do CFF)
        visited = set()
        yield center
        visited.add(center)
        offset = 1
        while len(visited) < total:
            cand_plus = center + offset
            cand_minus = center - offset
            if cand_plus not in visited and 1 <= cand_plus <= total:
                visited.add(cand_plus)
                yield cand_plus
            if cand_minus not in visited and 1 <= cand_minus <= total:
                visited.add(cand_minus)
                yield cand_minus
            offset += 1

    # --- Helpers de canais / bandas --------------------------------------
    def _rank_band_index(self, rank_global: int) -> int:
        if rank_global is None:
            return 0
        if rank_global < 0:
            return 0
        return rank_global // self.RANK_BAND_SIZE

    def _edge_role(self, edge_kind: str) -> str:
        # Papel da edge para o Channel Allocator (MD21 3.2)
        if edge_kind == "branch":
            return "branch"
        if edge_kind == "join":
            return "join"
        return "mid"

    def _make_channel_key(self, lane_id, edge, orig_src, orig_dst, direction: str) -> tuple:
        edge_kind = edge.get("classification", {}).get("kind", "normal")
        role = self._edge_role(edge_kind)
        rank_from = (orig_src.get("rank") or {}).get("global")
        rank_to = (orig_dst.get("rank") or {}).get("global")
        base_rank = None
        if rank_from is not None and rank_to is not None:
            base_rank = min(rank_from, rank_to)
        elif rank_from is not None:
            base_rank = rank_from
        elif rank_to is not None:
            base_rank = rank_to
        band_idx = self._rank_band_index(base_rank if base_rank is not None else 0)
        return (lane_id, band_idx, edge_kind, role, direction)

    def _outer_bounds(self):
        """Retorna limites externos do layout em X e Y.

        Usado para posicionar backbone externo de loops (MD17 5/6).
        """
        if not self.layout_lanes:
            return 0, 0, 0, 0
        xs = [l["x_start"] for l in self.layout_lanes.values()]
        xe = [l["x_end"] for l in self.layout_lanes.values()]
        # Para Y usamos bounding box dos nós existentes
        if self.layout_nodes:
            ys = []
            ye = []
            for n in self.layout_nodes.values():
                _, _, ny_min, ny_max = self._node_bbox(n)
                ys.append(ny_min)
                ye.append(ny_max)
            return min(xs), max(xe), min(ys), max(ye)
        return min(xs), max(xe), 0, 0

    # --- Bridge corridors (TB) -------------------------------------------
    def _bridge_spine_x(self, lane_a_id, lane_b_id):
        """Calcula o X do corredor vertical fixo entre duas lanes (MD21 4.2).

        Usa x_end da lane mais à esquerda e x_start da lane mais à direita.
        """
        if not self.layout_lanes:
            return None
        if lane_a_id not in self.layout_lanes or lane_b_id not in self.layout_lanes:
            return None
        la = self.layout_lanes[lane_a_id]
        lb = self.layout_lanes[lane_b_id]
        # Ordena por posição em X
        if la["x_start"] <= lb["x_start"]:
            left, right = la, lb
        else:
            left, right = lb, la
        left_edge = left["x_end"]
        right_edge = right["x_start"]
        return (left_edge + right_edge) / 2.0 + self.BRIDGE_SPINE_OFFSET

    # --- Roteamento TB: V-H-V -------------------------------------------
    def _route_tb(self, edge, src_node, dst_node, orig_src, orig_dst):
        lane_src = orig_src.get("lane")
        if lane_src not in self.ts.lanes:
            # Fallback minimalista se lane inválida
            return self._fallback_tb(edge, src_node, dst_node)

        # Portas ortogonais: saída em bottom/top, entrada em top/bottom
        src_y_center = src_node["y"]
        dst_y_center = dst_node["y"]
        src_half_h = src_node["height"] / 2.0
        dst_half_h = dst_node["height"] / 2.0

        going_down = dst_y_center >= src_y_center

        if going_down:
            # P1: bottom do nó origem
            x1 = src_node["x"]
            y1 = src_y_center + src_half_h
            # P4: top do nó destino
            x4 = dst_node["x"]
            y4 = dst_y_center - dst_half_h
        else:
            # retorno / fluxo para cima
            x1 = src_node["x"]
            y1 = src_y_center - src_half_h
            x4 = dst_node["x"]
            y4 = dst_y_center + dst_half_h

        if y1 == y4:
            # Caso degenerado: nós alinhados, usa fallback simples
            return self._fallback_tb(edge, src_node, dst_node)

        # Base do mid_y: meio do corredor entre saída e entrada
        base_mid_y = (y1 + y4) / 2.0
        lane = self.ts.lanes[lane_src]
        track_gap = lane["track_gap"]
        min_clear = track_gap  # clearance mínima em relação às bordas dos nós

        x_start = x1
        x_end = x4
        ignore_nodes = {orig_src.get("id"), orig_dst.get("id")}

        chosen_track = None
        chosen_mid_y = None

        # MD21: Channel Allocator por banda de ranks/role
        channel_key = self._make_channel_key(lane_src, edge, orig_src, orig_dst, "TB")
        _, band_idx, edge_kind, _, _ = channel_key

        # 1) Se já houver canal reservado para esta combinação, tentar primeiro
        preset_track = self._channel_map.get(channel_key)
        tested_tracks = set()
        if preset_track is not None and lane["center_track"] <= lane["tracks_total"]:
            tested_tracks.add(preset_track)
            dy = (preset_track - lane["center_track"]) * track_gap
            mid_y = base_mid_y + dy

            lower, upper = (y1, y4) if y1 < y4 else (y4, y1)
            if (lower + min_clear <= mid_y <= upper - min_clear) and \
               (not self._horizontal_hits_node(mid_y, x_start, x_end, ignore_ids=ignore_nodes)) and \
               (not self.ts.check_h_conflict(lane_src, preset_track, x_start, x_end)):
                chosen_track = preset_track
                chosen_mid_y = mid_y

        # 2) Se não deu para usar o canal pré-reservado, procurar novo track

        # Procura determinística de track (MD15 Seção 5 / MD20 B1)
        if chosen_track is None:
            for track_idx in self._iter_tracks(lane_src):
                if track_idx in tested_tracks:
                    continue

                dy = (track_idx - lane["center_track"]) * track_gap
                mid_y = base_mid_y + dy

                # mid_y precisa estar entre y1 e y4 com uma margem mínima
                lower, upper = (y1, y4) if y1 < y4 else (y4, y1)
                if not (lower + min_clear <= mid_y <= upper - min_clear):
                    continue

                # Bounding box (MD15 7.3): não pode atravessar nenhum nó
                if self._horizontal_hits_node(mid_y, x_start, x_end, ignore_ids=ignore_nodes):
                    continue

                # Conflito de track intermediário (sobreposição / paralelo colado básico)
                if self.ts.check_h_conflict(lane_src, track_idx, x_start, x_end):
                    continue

                chosen_track = track_idx
                chosen_mid_y = mid_y
                # Registra canal estável para futuras edges na mesma banda
                self._channel_map[channel_key] = track_idx
                break

        # Log de canal escolhido (MD21/MD22)
        if self._logger and chosen_track is not None:
            reused = preset_track is not None and preset_track == chosen_track
            self._logger.info(
                f"[CHANNEL] TB lane={lane_src} band={band_idx} kind={edge_kind} "
                f"track={chosen_track} reused={reused}"
            )

        if chosen_track is None:
            # Não encontrou track possível para o segmento H
            if self._logger:
                self._logger.warn(
                    f"[CHANNEL_FAIL] edge={edge.get('id')} key={channel_key} "
                    f"reason=NO_TRACK_AVAILABLE tried={sorted(tested_tracks)}"
                )
            raise ValueError("ROUTING_IMPOSSIBLE: no horizontal track available (TB)")

        # Reserva o segmento intermediário horizontal
        self.ts.occupy_h_segment(lane_src, chosen_track, x_start, x_end, edge.get("id"))

        # Segmentos verticais P1→P2 e P3→P4
        # Aqui ainda não fazemos checagem completa H×V, apenas bounding box
        if self._vertical_hits_node(x1, y1, chosen_mid_y, ignore_ids=ignore_nodes):
            # Em casos extremos, recusar rota
            raise ValueError("ROUTING_IMPOSSIBLE: vertical from source hits node (TB)")
        if self._vertical_hits_node(x4, chosen_mid_y, y4, ignore_ids=ignore_nodes):
            raise ValueError("ROUTING_IMPOSSIBLE: vertical to target hits node (TB)")

        p1 = (x1, y1)
        p2 = (x1, chosen_mid_y)
        p3 = (x4, chosen_mid_y)
        p4 = (x4, y4)
        return [p1, p2, p3, p4]

    def _route_tb_cross_lane_bridge(self, edge, src_node, dst_node, orig_src, orig_dst):
        """Roteia edges cross_lane em TB usando um bridge corridor vertical (MD21 4.4).

        Padrão: P1 (exit) → P2 (até spine_x) → P3 (ao longo do spine até o rank do destino)
                 → P4 (entry no destino).
        """
        lane_src = orig_src.get("lane")
        lane_dst = orig_dst.get("lane")
        if not lane_src or not lane_dst or lane_src == lane_dst:
            # Se informação de lane estiver inconsistente, cai no roteamento TB normal
            return self._route_tb(edge, src_node, dst_node, orig_src, orig_dst)

        spine_x = self._bridge_spine_x(lane_src, lane_dst)
        if spine_x is None:
            return self._route_tb(edge, src_node, dst_node, orig_src, orig_dst)

        # Portas ortogonais iguais ao TB normal
        src_y_center = src_node["y"]
        dst_y_center = dst_node["y"]
        src_half_h = src_node["height"] / 2.0
        dst_half_h = dst_node["height"] / 2.0

        going_down = dst_y_center >= src_y_center

        if going_down:
            x1 = src_node["x"]
            y1 = src_y_center + src_half_h
            x4 = dst_node["x"]
            y4 = dst_y_center - dst_half_h
        else:
            x1 = src_node["x"]
            y1 = src_y_center - src_half_h
            x4 = dst_node["x"]
            y4 = dst_y_center + dst_half_h

        # P2: H inicial até o corredor
        x2, y2 = spine_x, y1
        # P3: V ao longo do corredor até o rank do destino
        x3, y3 = spine_x, y4
        # P4: entrada no nó destino
        x4, y4 = x4, y4

        if self._logger:
            self._logger.info(
                f"[BRIDGE] TB lanes=({lane_src},{lane_dst}) spine_x={spine_x} edge={edge.get('id')}"
            )
        # Registrar uso de bridge para dumps de debug (MD22)
        self.bridge_segments.append(
            {
                "edge": edge.get("id"),
                "lane_src": lane_src,
                "lane_dst": lane_dst,
                "spine_x": spine_x,
            }
        )

        p1 = (x1, y1)
        p2 = (x2, y2)
        p3 = (x3, y3)
        p4 = (x4, y4)
        return [p1, p2, p3, p4]

    def _fallback_tb(self, edge, src_node, dst_node):
        """Fallback mínimo para casos degenerados em TB.

        Mantém ainda o padrão V-H-V, mas sem uso de tracks.
        """
        x1 = src_node["x"]
        y1 = src_node["y"] + src_node["height"] / 2.0
        x4 = dst_node["x"]
        y4 = dst_node["y"] - dst_node["height"] / 2.0
        mid_y = (y1 + y4) / 2.0
        p1 = (x1, y1)
        p2 = (x1, mid_y)
        p3 = (x4, mid_y)
        p4 = (x4, y4)
        return [p1, p2, p3, p4]

    # --- Roteamento LR: H-V-H -------------------------------------------
    def _route_lr(self, edge, src_node, dst_node, orig_src, orig_dst):
        lane_src = orig_src.get("lane")
        if lane_src not in self.ts.lanes:
            return self._fallback_lr(edge, src_node, dst_node)

        src_x_center = src_node["x"]
        dst_x_center = dst_node["x"]
        src_half_w = src_node["width"] / 2.0
        dst_half_w = dst_node["width"] / 2.0

        going_right = dst_x_center >= src_x_center

        if going_right:
            # saída pela direita, entrada pela esquerda
            x1 = src_x_center + src_half_w
            y1 = src_node["y"]
            x4 = dst_x_center - dst_half_w
            y4 = dst_node["y"]
        else:
            x1 = src_x_center - src_half_w
            y1 = src_node["y"]
            x4 = dst_x_center + dst_half_w
            y4 = dst_node["y"]

        if x1 == x4:
            return self._fallback_lr(edge, src_node, dst_node)

        base_mid_x = (x1 + x4) / 2.0
        lane = self.ts.lanes[lane_src]
        track_gap = lane["track_gap"]
        min_clear = track_gap

        y_start = y1
        y_end = y4
        ignore_nodes = {orig_src.get("id"), orig_dst.get("id")}

        chosen_track = None
        chosen_mid_x = None

        # MD21: Channel Allocator para LR com mesma chave
        channel_key = self._make_channel_key(lane_src, edge, orig_src, orig_dst, "LR")
        _, band_idx, edge_kind, _, _ = channel_key

        preset_track = self._channel_map.get(channel_key)
        tested_tracks = set()
        if preset_track is not None and lane["center_track"] <= lane["tracks_total"]:
            tested_tracks.add(preset_track)
            dx = (preset_track - lane["center_track"]) * track_gap
            mid_x = base_mid_x + dx

            left, right = (x1, x4) if x1 < x4 else (x4, x1)
            if (left + min_clear <= mid_x <= right - min_clear) and \
               (not self._vertical_hits_node(mid_x, y_start, y_end, ignore_ids=ignore_nodes)) and \
               (not self.ts.check_v_conflict(lane_src, preset_track, y_start, y_end)):
                chosen_track = preset_track
                chosen_mid_x = mid_x

        if chosen_track is None:
            for track_idx in self._iter_tracks(lane_src):
                if track_idx in tested_tracks:
                    continue
                dx = (track_idx - lane["center_track"]) * track_gap
                mid_x = base_mid_x + dx

                left, right = (x1, x4) if x1 < x4 else (x4, x1)
                if not (left + min_clear <= mid_x <= right - min_clear):
                    continue

                if self._vertical_hits_node(mid_x, y_start, y_end, ignore_ids=ignore_nodes):
                    continue

                if self.ts.check_v_conflict(lane_src, track_idx, y_start, y_end):
                    continue

                chosen_track = track_idx
                chosen_mid_x = mid_x
                # Registra canal estável para futuras edges na mesma banda
                self._channel_map[channel_key] = track_idx
                break

        # Log de canal escolhido (MD21/MD22)
        if self._logger and chosen_track is not None:
            reused = preset_track is not None and preset_track == chosen_track
            self._logger.info(
                f"[CHANNEL] LR lane={lane_src} band={band_idx} kind={edge_kind} "
                f"track={chosen_track} reused={reused}"
            )

        if chosen_track is None:
            if self._logger:
                self._logger.warn(
                    f"[CHANNEL_FAIL] edge={edge.get('id')} key={channel_key} "
                    f"reason=NO_TRACK_AVAILABLE tried={sorted(tested_tracks)}"
                )
            raise ValueError("ROUTING_IMPOSSIBLE: no vertical track available (LR)")

        self.ts.occupy_v_segment(lane_src, chosen_track, y_start, y_end, edge.get("id"))

        if self._horizontal_hits_node(x1, y1, chosen_mid_x, ignore_ids=ignore_nodes):
            raise ValueError("ROUTING_IMPOSSIBLE: horizontal from source hits node (LR)")
        if self._horizontal_hits_node(x4, y4, chosen_mid_x, ignore_ids=ignore_nodes):
            raise ValueError("ROUTING_IMPOSSIBLE: horizontal to target hits node (LR)")

        p1 = (x1, y1)
        p2 = (chosen_mid_x, y1)
        p3 = (chosen_mid_x, y4)
        p4 = (x4, y4)
        return [p1, p2, p3, p4]

    def _fallback_lr(self, edge, src_node, dst_node):
        x1 = src_node["x"] + src_node["width"] / 2.0
        y1 = src_node["y"]
        x4 = dst_node["x"] - dst_node["width"] / 2.0
        y4 = dst_node["y"]
        mid_x = (x1 + x4) / 2.0
        p1 = (x1, y1)
        p2 = (mid_x, y1)
        p3 = (mid_x, y4)
        p4 = (x4, y4)
        return [p1, p2, p3, p4]

    # --- Loops / Returns externos (MD17) -------------------------------
    def _route_tb_return(self, edge, src_node, dst_node, orig_src, orig_dst):
        """Roteia loops em layout TB usando backbone lateral externo.

                Modelo aproximado de MD17 6:
                    V (sai do nó origem)
                    H (vai até backbone lateral externo)
                    V (sobe/desce externamente)
                    H (entra no nó destino)

                Gera 5 pontos (4 segmentos), permitindo a exceção de loops em
                relação à regra geral de 4 pontos.
        """
        min_x, max_x, min_y, max_y = self._outer_bounds()

        # Offset externo baseado no nível de ciclo (MD18 7)
        base_offset = 80
        loop_spacing = 80
        cycle_level = max(
            orig_src.get("rank", {}).get("cycle_depth", 0),
            orig_dst.get("rank", {}).get("cycle_depth", 0),
        ) or 1
        corridor_x = max_x + base_offset + (cycle_level - 1) * loop_spacing

        # Saída pela direita do nó origem
        src_x_center = src_node["x"]
        src_y_center = src_node["y"]
        src_half_w = src_node["width"] / 2.0
        x1 = src_x_center + src_half_w
        y1 = src_y_center

        dst_x_center = dst_node["x"]
        dst_y_center = dst_node["y"]
        dst_half_w = dst_node["width"] / 2.0
        x5 = dst_x_center + dst_half_w
        y5 = dst_y_center

        # V: pequeno deslocamento vertical inicial, mantendo dentro do "corredor" do nó
        # Usa direção do loop (subindo ou descendo) apenas para evitar choque com o próprio nó
        going_down = dst_y_center >= src_y_center
        v_offset = src_node["height"]
        if going_down:
            y2 = y1 + v_offset
        else:
            y2 = y1 - v_offset

        # H: até backbone externo
        x2 = x1
        x3 = corridor_x
        y3 = y2

        # V externo: até altura próxima ao destino, fora das lanes
        y4 = dst_y_center
        x4 = corridor_x

        # H final: até lateral do nó destino
        # Entrando também pela direita, mantendo loop sempre fora das lanes
        # Sequência de pontos: P1(x1,y1) -> P2(x2,y2) -> P3(x3,y3) -> P4(x4,y4) -> P5(x5,y5)
        if self._logger:
            self._logger.info(
                f"[LOOP-ROUTE] TB return edge={edge.get('id')} cycle_level={cycle_level} corridor_x={corridor_x}"
            )

        p1 = (x1, y1)
        p2 = (x2, y2)
        p3 = (x3, y3)
        p4 = (x4, y4)
        p5 = (x5, y5)
        return [p1, p2, p3, p4, p5]

    def _route_lr_return(self, edge, src_node, dst_node, orig_src, orig_dst):
        """Roteia loops em layout LR usando backbone superior externo.

        Análogo ao TB, mas movendo pelo topo (y externo) ao invés de
        lateral em X, conforme MD17 5 para LR.
        """
        min_x, max_x, min_y, max_y = self._outer_bounds()

        base_offset = 80
        loop_spacing = 80
        cycle_level = max(
            orig_src.get("rank", {}).get("cycle_depth", 0),
            orig_dst.get("rank", {}).get("cycle_depth", 0),
        ) or 1
        corridor_y = min_y - (base_offset + (cycle_level - 1) * loop_spacing)

        src_x_center = src_node["x"]
        src_y_center = src_node["y"]
        src_half_h = src_node["height"] / 2.0

        # Saída pelo topo do nó origem
        x1 = src_x_center
        y1 = src_y_center - src_half_h

        dst_x_center = dst_node["x"]
        dst_y_center = dst_node["y"]
        dst_half_h = dst_node["height"] / 2.0

        # Entrada pelo topo do nó destino
        x5 = dst_x_center
        y5 = dst_y_center - dst_half_h

        # H inicial: afasta para fora
        h_offset = src_node["width"]
        x2 = x1 + h_offset
        y2 = y1

        # V externo: sobe até corredor superior
        x3 = x2
        y3 = corridor_y

        # H externo: até alinhamento com destino
        x4 = x5
        y4 = corridor_y

        # H final: desce até topo do destino (na verdade segmento V)
        if self._logger:
            self._logger.info(
                f"[LOOP-ROUTE] LR return edge={edge.get('id')} cycle_level={cycle_level} corridor_y={corridor_y}"
            )

        p1 = (x1, y1)
        p2 = (x2, y2)
        p3 = (x3, y3)
        p4 = (x4, y4)
        p5 = (x5, y5)
        return [p1, p2, p3, p4, p5]
