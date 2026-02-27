"""
core/reader/reader.py
Responsável por ler arquivos .sff (JSON) e retornar o dicionário bruto ou erro de leitura.
"""
import json
from typing import Any, Dict

def read_sff_file(filepath: str) -> Dict[str, Any]:
    """Lê um arquivo .sff (JSON) e retorna o dicionário correspondente."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise RuntimeError(f"Erro ao ler arquivo {filepath}: {e}")
