class TrackSystem:
    def __init__(self, lanes_data):
        self.lanes = {}
        for l_id, l_data in lanes_data.items():
            self.lanes[l_id] = {
                "center_track": l_data.get("center_track", 7),
                "tracks_total": l_data.get("tracks_total", 13),
                "track_gap": 20, # pixels distance between tracks
                "occupancy_map": {"H": {}, "V": {}},
                "expansion_factor": l_data.get("expansion_factor", 1.2),
                "lane_start_offset": 0 # Will be populated by layout engine
            }

    def expand_lane(self, lane_id):
        # Step 8 (MD13), Step 8 (MD14)
        # Expansion: +2 tracks total, keep center track index, effectively adding +1 above and +1 below.
        lane = self.lanes[lane_id]
        lane["tracks_total"] += 2
        # Center track doesn't move index, the negative tracks go further.

    def occupy_h_segment(self, lane_id, track_index, x_start, x_end, owner_id):
        pass # Full conflict resolution will happen here

    def occupy_v_segment(self, lane_id, track_index, y_start, y_end, owner_id):
        pass

    def get_track_offset(self, lane_id, track_index):
        lane = self.lanes.get(lane_id)
        if not lane:
            return 0
        
        diff = track_index - lane["center_track"]
        return diff * lane["track_gap"]
