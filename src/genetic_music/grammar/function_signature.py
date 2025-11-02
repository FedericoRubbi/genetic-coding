"""Function signature definition and helper utilities."""

from dataclasses import dataclass
from typing import Any, Callable, Optional
from .function_type import FunctionType
from .tidal_type import TidalType
from typing import List

@dataclass
class FunctionSignature:
    name: str
    kind: FunctionType
    arg_types: List[TidalType]
    return_type: TidalType
    param_generator: Optional[Callable[[], float]] = None

    def generate_param(self):
        return self.param_generator() if self.param_generator else None
