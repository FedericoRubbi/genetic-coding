"""Function signature definition and helper utilities."""

from dataclasses import dataclass
from typing import Any, Callable, Optional
from .function_type import FunctionType
import random


@dataclass
class FunctionSignature:
    """
    Defines the signature and parameter generation for a TidalCycles function.
    
    Attributes:
        name: Function name
        func_type: Type of function signature
        param_generator: Optional function to generate numeric/int parameters
        min_children: Minimum number of pattern children
        max_children: Maximum number of pattern children
    """
    name: str
    func_type: FunctionType
    param_generator: Optional[Callable[[], Any]] = None
    min_children: int = 1
    max_children: int = 1
    
    def generate_param(self) -> Any:
        """Generate a parameter value if needed."""
        if self.param_generator:
            return self.param_generator()
        return None
    
    def get_num_children(self) -> int:
        """Get number of children to generate."""
        if self.min_children == self.max_children:
            return self.min_children
        return random.randint(self.min_children, self.max_children)