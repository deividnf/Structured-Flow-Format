"""
Gera flowchart Mermaid determinístico a partir do fluxo SFF.
"""
def export_mermaid(data, layout):
    direction = data.get('sff', {}).get('direction', 'TB')
    lanes = layout['lane_order']
    nodes = data['nodes']
    edges = data['edges']
    lane_nodes = {lane: [] for lane in lanes}
    for node_id, node in nodes.items():
        lane_nodes[node['lane']].append(node_id)
    lines = [f"flowchart {direction}"]
    # Lanes como subgraph
    for lane in lanes:
        lines.append(f"subgraph {lane}")
        for node_id in lane_nodes[lane]:
            label = nodes[node_id].get('label', node_id)
            lines.append(f"    {node_id}[{label}]")
        lines.append("end")
    # Edges
    for edge in edges:
        src = edge['from']
        dst = edge['to']
        branch = edge.get('branch')
        label = edge.get('label', '')
        edge_label = label
        if branch:
            if branch == 'true': edge_label = 'Sim'
            elif branch == 'false': edge_label = 'Não'
            elif label: edge_label = label
        if edge_label:
            lines.append(f"{src} -->|{edge_label}| {dst}")
        else:
            lines.append(f"{src} --> {dst}")
    return '\n'.join(lines)
