"""
core/layout/track_system.py
Sistema de tracks para o Layout Engine Determinístico (MD13/MD14)
Gerencia tracks, ocupação, expansão dinâmica e conflitos.
Versão: 1.0
"""

class TrackSystem:
    """Implementa o Sistema de Tracks e Grid Matemático (MD14).

    Cada lane mantém:
      - center_track
      - tracks_total
      - track_gap
      - occupancy_map (H/V)

    Nenhuma edge deve existir fora de uma track; conflitos são checados
    contra occupancy_map, usando min_separation = track_gap.
    """

    def __init__(self, lanes_data):
        self.lanes = {}
        for l_id, l_data in lanes_data.items():
            self.lanes[l_id] = {
                "center_track": l_data.get("center_track", 7),
                "tracks_total": l_data.get("tracks_total", 13),
                "track_gap": 20,  # pixels distance between tracks (MD14 5/7.1)
                "occupancy_map": {"H": {}, "V": {}},
                "expansion_factor": l_data.get("expansion_factor", 1.2),
                "lane_start_offset": 0  # Populado pelo Layout Engine (offset geométrico)
            }

    def expand_lane(self, lane_id):
        """Crescimento dinâmico de tracks (MD14 Seção 8).

        tracks_total += 2, mantendo center_track fixo; os novos tracks surgem
        simetricamente acima/abaixo do centro. Coordenadas derivadas via
        get_track_offset, não há compressão.
        """
        lane = self.lanes[lane_id]
        lane["tracks_total"] += 2
        return True

    def check_h_conflict(self, lane_id, track_index, x_start, x_end, min_sep=None):
        """Verifica conflito horizontal em uma track.

        min_separation padrão é track_gap (MD14 7.1).
        """
        lane = self.lanes[lane_id]
        if min_sep is None:
            min_sep = lane["track_gap"]
        if track_index not in lane["occupancy_map"]["H"]:
            return False
        
        # Check overlaps
        x_min, x_max = min(x_start, x_end), max(x_start, x_end)
        for (seg_start, seg_end, _) in lane["occupancy_map"]["H"][track_index]:
            s_min, s_max = min(seg_start, seg_end), max(seg_start, seg_end)
            # Extrema with min_separation
            if not (x_max + min_sep <= s_min or x_min - min_sep >= s_max):
                return True # Conflict
        return False

    def occupy_h_segment(self, lane_id, track_index, x_start, x_end, owner_id):
        lane = self.lanes[lane_id]
        if track_index not in lane["occupancy_map"]["H"]:
            lane["occupancy_map"]["H"][track_index] = []
        lane["occupancy_map"]["H"][track_index].append((x_start, x_end, owner_id))

    def check_v_conflict(self, lane_id, track_index, y_start, y_end, min_sep=None):
        """Verifica conflito vertical em uma track.

        min_separation padrão é track_gap (MD14 7.1).
        """
        lane = self.lanes[lane_id]
        if min_sep is None:
            min_sep = lane["track_gap"]
        if track_index not in lane["occupancy_map"]["V"]:
            return False
            
        y_min, y_max = min(y_start, y_end), max(y_start, y_end)
        for (seg_start, seg_end, _) in lane["occupancy_map"]["V"][track_index]:
            s_min, s_max = min(seg_start, seg_end), max(seg_start, seg_end)
            if not (y_max + min_sep <= s_min or y_min - min_sep >= s_max):
                return True # Conflict
        return False

    def occupy_v_segment(self, lane_id, track_index, y_start, y_end, owner_id):
        lane = self.lanes[lane_id]
        if track_index not in lane["occupancy_map"]["V"]:
            lane["occupancy_map"]["V"][track_index] = []
        lane["occupancy_map"]["V"][track_index].append((y_start, y_end, owner_id))

    def get_track_offset(self, lane_id, track_index):
        lane = self.lanes.get(lane_id)
        if not lane:
            return 0
        diff = track_index - lane["center_track"]
        return diff * lane["track_gap"]
