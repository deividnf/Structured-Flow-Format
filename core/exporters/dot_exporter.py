"""
Gera arquivo DOT/Graphviz a partir do fluxo SFF.
"""
def export_dot(data, layout):
    direction = data.get('sff', {}).get('direction', 'TB')
    lanes = layout['lane_order']
    nodes = data['nodes']
    edges = data['edges']
    lane_nodes = {lane: [] for lane in lanes}
    for node_id, node in nodes.items():
        lane_nodes[node['lane']].append(node_id)
    rankdir = 'TB' if direction == 'TB' else 'LR'
    lines = [f'digraph G {{', f'  rankdir={rankdir};']
    # Clusters por lane
    for lane in lanes:
        lines.append(f'  subgraph cluster_{lane} {{')
        lines.append(f'    label="{lane}";')
        for node_id in lane_nodes[lane]:
            label = nodes[node_id].get('label', node_id)
            lines.append(f'    {node_id} [label="{label}"]')
        lines.append('  }')
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
            lines.append(f'  {src} -> {dst} [label="{edge_label}"]')
        else:
            lines.append(f'  {src} -> {dst}')
    lines.append('}')
    return '\n'.join(lines)
