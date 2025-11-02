"""PatternTree implementation for TidalCycles."""

# tidal_gen/tree/pattern_tree.py
import random
from .node import TreeNode
from ..grammar.registry import FUNCTIONS
from ..grammar.tidal_type import TidalType, unify
from ..grammar.function_type import FunctionType

class PatternTree(TreeNode):
    @classmethod
    def random(cls, target_type=TidalType.CONTROL, max_depth=4):
        if max_depth <= 1:
            return cls._terminal_of_type(target_type)
        matching_funcs = [f for f in FUNCTIONS if unify(f.return_type, target_type)]
        assert len(matching_funcs) > 0, f"No functions found that return type {target_type}"
        func = random.choice(matching_funcs)
        children = [cls.random(t, max_depth-1) for t in func.arg_types]
        return cls(func.name, children, func.generate_param(), func.return_type)

    @classmethod
    def _terminal_of_type(cls, target_type):
        matching_functions = [f for f in FUNCTIONS if unify(f.return_type, target_type) and f.kind == FunctionType.TERMINAL]
        assert len(matching_functions) > 0, f"No terminal functions found that return type {target_type}"
        f = random.choice(matching_functions)
        return cls(f.name, [], None, f.return_type)