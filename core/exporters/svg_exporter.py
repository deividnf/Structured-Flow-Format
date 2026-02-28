"""
Exporta lanes e nodes em SVG completo, incluindo container, lanes, títulos, nodes e edges.
"""
from core.exporters.lanes_only_exporter import export_lanes_only

def export_svg(data, layout=None):
    # Se layout for fornecido, injeta no data para o lanes_only_exporter usar as posições
    if layout:
        data = dict(data)  # cópia rasa
        data['layout'] = layout
    return export_lanes_only(data, lanes_only=False)
