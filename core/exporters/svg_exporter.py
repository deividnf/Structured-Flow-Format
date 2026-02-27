"""
core/exporters/svg_exporter.py
Exporta o diagrama SFF para SVG visual real, auto-size, lanes, nodes, edges ortogonais.
"""
import os
from core.logger.logger import Logger

logger = Logger()

SVG_PADDING = 24

NODE_STYLES = {
    'start': {'shape': 'circle', 'fill': '#e0f7fa', 'stroke': '#00796b'},
    'end':   {'shape': 'circle', 'fill': '#ffe0e0', 'stroke': '#c62828'},
    'process': {'shape': 'rect', 'fill': '#e3f2fd', 'stroke': '#1565c0'},
    'decision': {'shape': 'diamond', 'fill': '#fffde7', 'stroke': '#fbc02d'},
    'delay': {'shape': 'rect', 'fill': '#f3e5f5', 'stroke': '#6a1b9a', 'icon': True},
}

LANE_COLORS = ['#f5f5f5', '#e0e0e0', '#eeeeee', '#fafafa']

# Tamanhos padrão dos nós
NODE_WIDTH = 96
NODE_HEIGHT = 48
DIAMOND_SIZE = 64
CIRCLE_RADIUS = 28

ARROW_SIZE = 12
FONT_SIZE = 16
LABEL_MARGIN = 8
LANE_TITLE_HEIGHT = 32


def export_svg(data, layout):
    try:
        logger.info(f"[SVG Export] Iniciando exportação SVG para {data.get('filename', '<output>')}")
        # ...existing code...
        svg.append('</svg>')
        return '\n'.join(svg)
    except Exception as e:
        logger.error(f"[SVG Export] Falha ao gerar SVG: {e}")
        return f'<svg><text x="10" y="20" fill="red">Erro ao gerar SVG: {e}</text></svg>'
