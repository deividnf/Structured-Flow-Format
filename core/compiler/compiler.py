"""
core/compiler/compiler.py
Gera índices prev/next a partir de edges.
"""
from typing import Dict, Any

def compile_indices(data: Dict[str, Any]) -> Dict[str, Dict[str, list]]:
    """Gera índices prev/next para os nodes do fluxo."""
    prev = {k: [] for k in data.get('nodes', {})}
    next_ = {k: [] for k in data.get('nodes', {})}
    for edge in data.get('edges', []):
        from_id = edge['from']
        to_id = edge['to']
        next_[from_id].append(to_id)
        prev[to_id].append(from_id)
    return {'prev': prev, 'next': next_}
