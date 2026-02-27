"""
core/validator/validator.py
Valida estrutura obrigatória e regras do SFF.
"""
from typing import Dict, Any, List

REQUIRED_BLOCKS = ["sff", "entry", "lanes", "nodes", "edges"]

class ValidationError(Exception):
    pass

def validate_sff_structure(data: Dict[str, Any]) -> List[str]:
    """Valida a presença dos blocos obrigatórios e retorna lista de erros."""
    errors = []
    for block in REQUIRED_BLOCKS:
        if block not in data:
            errors.append(f"Bloco obrigatório ausente: {block}")
    # Validações adicionais podem ser implementadas aqui
    return errors
