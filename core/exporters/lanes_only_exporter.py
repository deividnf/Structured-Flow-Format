"""
Exporta apenas as lanes (boxes/baias) em SVG, sem nodes/edges/routing.
"""
import math
from core.logger.logger import Logger
logger = Logger()

# Parâmetros fixos
LANE_GAP = 0
PADDING = 24
TITLE_BAR = 56
LANE_BODY_W = 900
LANE_BODY_H = 240
FONT_TITLE = 20


def export_lanes_only(data):
    direction = data.get('sff', {}).get('direction', 'TB')
    lanes = list(data.get('lanes', {}).values())
    if not lanes:
        logger.error('[LANES-ONLY] Nenhuma lane encontrada.')
        return '<svg><text x="10" y="20" fill="red">Erro: Nenhuma lane encontrada</text></svg>'
    lanes_sorted = sorted(lanes, key=lambda l: l.get('order', 0))
    n_lanes = len(lanes_sorted)
    svg = []
    if direction == 'TB':
        lane_width = TITLE_BAR + LANE_BODY_W
        lane_height = LANE_BODY_H
        total_height = n_lanes * lane_height + 2*PADDING
        total_width = lane_width + 2*PADDING
        # Container externo
        svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="{total_height}" viewBox="0 0 {total_width} {total_height}">')
        svg.append(f'<rect x="{PADDING}" y="{PADDING}" width="{lane_width}" height="{n_lanes*lane_height}" fill="#fff" stroke="#bbb" stroke-width="1" />')
        logger.info(f'[LANES-ONLY] TB: container x={PADDING}, y={PADDING}, w={lane_width}, h={n_lanes*lane_height}')
        for i, lane in enumerate(lanes_sorted):
            y = PADDING + i * lane_height
            # Box da lane (sem rx/ry)
            svg.append(f'<rect x="{PADDING}" y="{y}" width="{lane_width}" height="{lane_height}" fill="#f5f5f5" stroke="#bbb" stroke-width="1" />')
            # Barra do título (sem rx/ry)
            svg.append(f'<rect x="{PADDING}" y="{y}" width="{TITLE_BAR}" height="{lane_height}" fill="#e0e0e0" stroke="#bbb" stroke-width="1" />')
            # Título rotacionado
            title = lane.get('title', lane.get('id', ''))
            tx = PADDING + TITLE_BAR//2
            ty = y + lane_height//2
            svg.append(f'<text x="{tx}" y="{ty}" font-size="{FONT_TITLE}" font-weight="bold" fill="#333" text-anchor="middle" dominant-baseline="middle" transform="rotate(-90 {tx},{ty})">{title}</text>')
            logger.info(f'[LANES-ONLY] Lane {lane.get("id")} TB: x={PADDING}, y={y}, w={lane_width}, h={lane_height}, title="{title}"')
        svg.append('</svg>')
        logger.info(f'[LANES-ONLY] TB: total_width={total_width}, total_height={total_height}')
    elif direction == 'LR':
        lane_width = LANE_BODY_W
        lane_height = TITLE_BAR + LANE_BODY_H
        total_width = n_lanes * lane_width + 2*PADDING
        total_height = lane_height + 2*PADDING
        # Container externo
        svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="{total_height}" viewBox="0 0 {total_width} {total_height}">')
        svg.append(f'<rect x="{PADDING}" y="{PADDING}" width="{n_lanes*lane_width}" height="{lane_height}" fill="#fff" stroke="#bbb" stroke-width="1" />')
        logger.info(f'[LANES-ONLY] LR: container x={PADDING}, y={PADDING}, w={n_lanes*lane_width}, h={lane_height}')
        for i, lane in enumerate(lanes_sorted):
            x = PADDING + i * lane_width
            # Box da lane (sem rx/ry)
            svg.append(f'<rect x="{x}" y="{PADDING}" width="{lane_width}" height="{lane_height}" fill="#f5f5f5" stroke="#bbb" stroke-width="1" />')
            # Barra do título (sem rx/ry)
            svg.append(f'<rect x="{x}" y="{PADDING}" width="{lane_width}" height="{TITLE_BAR}" fill="#e0e0e0" stroke="#bbb" stroke-width="1" />')
            # Título horizontal
            title = lane.get('title', lane.get('id', ''))
            tx = x + lane_width//2
            ty = PADDING + TITLE_BAR//2
            svg.append(f'<text x="{tx}" y="{ty}" font-size="{FONT_TITLE}" font-weight="bold" fill="#333" text-anchor="middle" dominant-baseline="middle">{title}</text>')
            logger.info(f'[LANES-ONLY] Lane {lane.get("id")} LR: x={x}, y={PADDING}, w={lane_width}, h={lane_height}, title="{title}"')
        svg.append('</svg>')
        logger.info(f'[LANES-ONLY] LR: total_width={total_width}, total_height={total_height}')
    else:
        logger.error(f'[LANES-ONLY] direction inválida: {direction}')
        return '<svg><text x="10" y="20" fill="red">Erro: direction inválida</text></svg>'
    return '\n'.join(svg)
