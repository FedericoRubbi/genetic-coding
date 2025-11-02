# tidal_gen/codegen/to_tidal.py
from ..tree.node import TreeNode
from ..grammar.function_type import FunctionType

def to_tidal(node: TreeNode) -> str:
    if node.is_leaf():
        if node.op == "sound":
            return f'sound "bd"'  # TODO: randomize sample
        if node.op == "silence":
            return "silence"
        return node.op

    kind = _get_kind(node.op)

    if kind == FunctionType.UNARY:
        return f"{node.op} ({to_tidal(node.children[0])})"
    if kind == FunctionType.BINARY:
        return f"{node.op} {node.value:.2f} $ ({to_tidal(node.children[-1])})"
    if kind == FunctionType.MODIFIER:
        left, right = node.children
        return f"{to_tidal(left)} # {node.op} ({to_tidal(right)})"
    if kind == FunctionType.N_ARY:
        return f"{node.op} [{', '.join(to_tidal(c) for c in node.children)}]"
    return node.op

def _get_kind(op_name: str) -> FunctionType:
    from ..grammar.registry import FUNCTIONS
    for f in FUNCTIONS:
        if f.name == op_name:
            return f.kind
    return FunctionType.UNARY