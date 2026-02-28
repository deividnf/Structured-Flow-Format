def export_cff_svg(data, layout):
    """
    Export based exclusively on deterministically computed coordinates by CFFEngine.
    layout = { 'nodes': {}, 'edges': {}, 'lanes': {} }
    """
    
    direction = data.get("sff", {}).get("direction", "TB")
    nodes = layout["nodes"]
    edges = layout["edges"]
    lanes = layout["lanes"]
    
    # Calculate bounds
    min_x = min([n["x"] - n["width"]/2 for n in nodes.values()] + [0], default=0)
    min_y = min([n["y"] - n["height"]/2 for n in nodes.values()] + [0], default=0)
    max_x = max([n["x"] + n["width"]/2 for n in nodes.values()] + [800], default=800)
    max_y = max([n["y"] + n["height"]/2 for n in nodes.values()] + [600], default=600)
    
    # Expand slightly
    min_x -= 100
    min_y -= 100
    max_x += 100
    max_y += 100
    
    w = max_x - min_x
    h = max_y - min_y
    
    svg = []
    svg.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{min_x} {min_y} {w} {h}">')
    svg.append('  <style>')
    svg.append('    .lane { fill: #f8f9fa; stroke: #dee2e6; stroke-width: 2; }')
    svg.append('    .node { fill: #ffffff; stroke: #333333; stroke-width: 2; }')
    svg.append('    .label { font-family: sans-serif; font-size: 14px; text-anchor: middle; fill: #333; }')
    svg.append('    .edge { fill: none; stroke: #666; stroke-width: 2; }')
    svg.append('    path { marker-end: url(#arrow); }')
    svg.append('  </style>')
    svg.append('  <defs><marker id="arrow" viewBox="0 -5 10 10" refX="8" refY="0" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,-5L10,0L0,5" fill="#666"/></marker></defs>')
    
    # Draw Lanes
    # Since TB and LR differ
    if direction == "TB":
        for l_id, l_data in lanes.items():
            lx = l_data["start"]
            lw = l_data["end"] - l_data["start"]
            svg.append(f'  <rect class="lane" x="{lx}" y="{min_y}" width="{lw}" height="{h}" />')
            svg.append(f'  <text class="label" x="{lx + lw/2}" y="{min_y + 30}">{l_id}</text>')
    else:
        for l_id, l_data in lanes.items():
            ly = l_data["start"]
            lh = l_data["end"] - l_data["start"]
            svg.append(f'  <rect class="lane" x="{min_x}" y="{ly}" width="{w}" height="{lh}" />')
            svg.append(f'  <text class="label" x="{min_x + 30}" y="{ly + lh/2}" transform="rotate(-90 {min_x+30},{ly+lh/2})">{l_id}</text>')

    # Draw Edges
    for e_id, e in edges.items():
        pts = e["points"]
        if not pts:
            continue
        d = f"M {pts[0][0]},{pts[0][1]}"
        for p in pts[1:]:
            d += f" L {p[0]},{p[1]}"
        svg.append(f'  <path class="edge" d="{d}" />')
        
    # Draw Nodes
    for n_id, n in nodes.items():
        w, h_node = n["width"], n["height"]
        cx, cy = n["x"], n["y"]
        x = cx - w/2
        y = cy - h_node/2
        
        orig_node = data["nodes"].get(n_id, {})
        ntype = orig_node.get("type", "process")
        label = orig_node.get("label", n_id)
        
        if ntype in ["start", "end"]:
            r = min(w, h_node)/2
            svg.append(f'  <circle class="node" cx="{cx}" cy="{cy}" r="{r}" />')
            if ntype == "end":
                svg.append(f'  <circle cx="{cx}" cy="{cy}" r="{r-4}" fill="none" stroke="#333" stroke-width="2"/>')
            svg.append(f'  <text class="label" x="{cx}" y="{cy + r + 20}">{label}</text>')
        elif ntype == "decision":
            pts = f"{cx},{cy-h_node/2} {cx+w/2},{cy} {cx},{cy+h_node/2} {cx-w/2},{cy}"
            svg.append(f'  <polygon class="node" points="{pts}" />')
            svg.append(f'  <text class="label" x="{cx}" y="{cy + h_node/2 + 20}">{label}</text>')
        else:
            svg.append(f'  <rect class="node" x="{x}" y="{y}" width="{w}" height="{h_node}" rx="8" />')
            svg.append(f'  <text class="label" x="{cx}" y="{cy + 5}">{label}</text>')
            
    svg.append('</svg>')
    return "\n".join(svg)
