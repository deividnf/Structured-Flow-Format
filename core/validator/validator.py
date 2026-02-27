"""
core/validator/validator.py
Valida estrutura obrigatória e regras do SFF.
"""
from typing import Dict, Any, List, Set

REQUIRED_BLOCKS = ["sff", "entry", "lanes", "nodes", "edges"]

class ValidationError(Exception):
    pass

def validate_sff_structure(data: Dict[str, Any]) -> List[str]:
    """Valida a presença dos blocos obrigatórios e retorna lista de erros."""
    errors = []
    for block in REQUIRED_BLOCKS:
        if block not in data:
            errors.append(f"Bloco obrigatório ausente: {block}")
    return errors

def validate_sff_logic(data: Dict[str, Any]) -> List[str]:
    """Valida regras lógicas do SFF."""
    errors = []
    nodes = data.get("nodes", {})
    edges = data.get("edges", [])
    entry = data.get("entry", {})
    # 1. Exatamente 1 nó type=start e deve ser entry.start
    start_nodes = [k for k, v in nodes.items() if v.get("type") == "start"]
    if len(start_nodes) != 1:
        errors.append("Deve existir exatamente 1 nó do tipo 'start'.")
    else:
        if entry.get("start") != start_nodes[0]:
            errors.append(f"O entry.start ('{entry.get('start')}') deve ser o nó do tipo 'start' ('{start_nodes[0]}').")
    # 2. Pelo menos 1 nó type=end e todos devem estar em entry.ends
    end_nodes = [k for k, v in nodes.items() if v.get("type") == "end"]
    if not end_nodes:
        errors.append("Deve existir pelo menos 1 nó do tipo 'end'.")
    else:
        entry_ends = set(entry.get("ends", []))
        for eid in end_nodes:
            if eid not in entry_ends:
                errors.append(f"Nó 'end' ('{eid}') não está listado em entry.ends.")
    # 3. start não pode ter edges de entrada
    if start_nodes:
        incoming = [e for e in edges if e.get("to") == start_nodes[0]]
        if incoming:
            errors.append(f"Nó 'start' ('{start_nodes[0]}') não pode ter edges de entrada.")
    # 4. end não pode ter edges de saída
    for eid in end_nodes:
        outgoing = [e for e in edges if e.get("from") == eid]
        if outgoing:
            errors.append(f"Nó 'end' ('{eid}') não pode ter edges de saída.")
    # 5. Todos os nós devem ser alcançáveis a partir de entry.start
    if start_nodes:
        reachable = set()
        def dfs(node_id):
            if node_id in reachable:
                return
            reachable.add(node_id)
            for e in edges:
                if e.get("from") == node_id:
                    dfs(e.get("to"))
        dfs(entry.get("start"))
        for node_id in nodes:
            if node_id not in reachable:
                errors.append(f"Nó '{node_id}' não é alcançável a partir do start.")
    # 6. Não permitir nós isolados (sem prev e sem next)
    prev = {k: [] for k in nodes}
    next_ = {k: [] for k in nodes}
    for e in edges:
        prev[e["to"]].append(e["from"])
        next_[e["from"]].append(e["to"])
    for node_id in nodes:
        if not prev[node_id] and not next_[node_id]:
            errors.append(f"Nó '{node_id}' está isolado (sem entrada e sem saída).")
    # 7. Para decision boolean: branches.true/false obrigatórios, next deve existir, edges coerentes
    for node_id, node in nodes.items():
        if node.get("type") == "decision":
            branches = node.get("branches", {})
            if "true" not in branches or "false" not in branches:
                errors.append(f"Decision '{node_id}' deve ter branches 'true' e 'false'.")
            for branch_key in ["true", "false"]:
                if branch_key in branches:
                    next_id = branches[branch_key].get("next")
                    if next_id not in nodes:
                        errors.append(f"Decision '{node_id}' branch '{branch_key}' aponta para nó inexistente '{next_id}'.")
                    # Edge coerente
                    found = False
                    for e in edges:
                        if e.get("from") == node_id and e.get("to") == next_id and e.get("branch") == branch_key:
                            found = True
                    if not found:
                        errors.append(f"Decision '{node_id}' branch '{branch_key}' não possui edge coerente para '{next_id}'.")
    return errors
