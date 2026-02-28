class CFFRouter:
    def __init__(self, track_system, direction="TB"):
        self.ts = track_system
        self.direction = direction

    def route_edge(self, edge, src_node, dst_node):
        # Implement MD15 (V-H-V or H-V-H)
        points = []
        lane_src = src_node.get("lane")
        lane_dst = dst_node.get("lane")

        if self.direction == "TB":
            # Output from bottom of source
            x1 = src_node["x"]
            y1 = src_node["y"] + (src_node["height"] / 2)
            
            # Input to top of dest
            x4 = dst_node["x"]
            y4 = dst_node["y"] - (dst_node["height"] / 2)
            
            # intermediate H track logic
            track_idx = self.ts.lanes[lane_src]["center_track"] # Basic fallback
            mid_y = y1 + 50 # Fallback midpoint rank
            
            if edge["classification"]["is_return"]:
                # return edges go around
                x1 = src_node["x"] + (src_node["width"] / 2)
                x4 = dst_node["x"] + (dst_node["width"] / 2)
                y1 = src_node["y"]
                y4 = dst_node["y"]
                # 4 bends minimum, but let's stick to simple polyline
                p1 = (x1, y1)
                p2 = (x1 + 100, y1)
                p3 = (x4 + 100, y4)
                p4 = (x4, y4)
                points = [p1, p2, p3, p4]
            else:
                # V-H-V
                p1 = (x1, y1)
                p2 = (x1, mid_y)
                p3 = (x4, mid_y)
                p4 = (x4, y4)
                points = [p1, p2, p3, p4]
                
        else: # LR
            # Output from right of source
            x1 = src_node["x"] + (src_node["width"] / 2)
            y1 = src_node["y"]
            
            # Input to left of dest
            x4 = dst_node["x"] - (dst_node["width"] / 2)
            y4 = dst_node["y"]
            
            mid_x = x1 + 50

            p1 = (x1, y1)
            p2 = (mid_x, y1)
            p3 = (mid_x, y4)
            p4 = (x4, y4)
            points = [p1, p2, p3, p4]

        return points
