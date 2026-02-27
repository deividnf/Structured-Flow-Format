"""
core/compiler/compiler.py
Gera índices prev/next a partir de edges.
"""
from typing import Dict, Any
from core.validator.validator import validate_sff_logic

def compile_sff(data: Dict[str, Any]) -> Dict[str, Any]:
    """Compila o SFF: gera índices prev/next e validação lógica."""
    nodes = data.get('nodes', {})
    edges = data.get('edges', [])
    prev = {k: [] for k in nodes}
    next_ = {k: [] for k in nodes}
    for edge in edges:
        from_id = edge['from']
        to_id = edge['to']
        next_[from_id].append(to_id)
        prev[to_id].append(from_id)
    errors = validate_sff_logic(data)
    warnings = []
    # Exemplo: warning se não houver mainPath (pode ser expandido)
    if 'mainPath' not in data.get('sff', {}):
        warnings.append('Nenhum caminho principal (mainPath) definido.')
    compiled = {
        'index': {
            'prev': prev,
            'next': next_
        },
        'validation': {
            'errors': errors,
            'warnings': warnings
        }
    }
    return compiled
