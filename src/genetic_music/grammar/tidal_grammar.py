"""TidalCycles grammar definition."""

import random
from typing import Dict, List
from .function_type import FunctionType
from .function_signature import FunctionSignature

class TidalGrammar:
    """
    Grammar definition for TidalCycles pattern functions.
    Defines available functions and their signatures.
    """
    
    # Terminal sound samples (SuperDirt defaults)
    SOUNDS = [
        # Drums
        'bd', 'sn', 'cp', 'hh', 'oh', 'ch', 'cy', 'rim', 'tom',
        # Percussion
        'clap', 'click', 'cowbell', 'crash', 'hand', 'tabla',
        # Bass & Tonal
        'arpy', 'bass', 'bass0', 'bass1', 'bass2', 'bass3',
        # Synths
        'superpiano', 'supersaw', 'supermandolin', 'supersquare',
        # Breaks & Loops
        'breaks125', 'breaks152', 'breaks165', 'amencutup',
        # Industrial
        'industrial', 'insect', 'jazz', 'jungbass',
        # 808/909
        '808bd', '808sd', '808hh', '808oh', '808cy'
    ]
    
    # Function signatures organized by type
    FUNCTIONS: Dict[str, FunctionSignature] = {
        # === UNARY TRANSFORMERS (pattern -> pattern) ===
        'rev': FunctionSignature('rev', FunctionType.UNARY),
        'palindrome': FunctionSignature('palindrome', FunctionType.UNARY),
        'brak': FunctionSignature('brak', FunctionType.UNARY),
        'degrade': FunctionSignature('degrade', FunctionType.UNARY),
        'shuffle': FunctionSignature('shuffle', FunctionType.UNARY),
        'scramble': FunctionSignature('scramble', FunctionType.UNARY),
        
        # === BINARY NUMERIC (number, pattern -> pattern) ===
        'fast': FunctionSignature(
            'fast', 
            FunctionType.BINARY_NUMERIC,
            param_generator=lambda: random.uniform(0.5, 4.0)
        ),
        'slow': FunctionSignature(
            'slow',
            FunctionType.BINARY_NUMERIC,
            param_generator=lambda: random.uniform(0.5, 4.0)
        ),
        'density': FunctionSignature(
            'density',
            FunctionType.BINARY_NUMERIC,
            param_generator=lambda: random.uniform(0.5, 4.0)
        ),
        'sparsity': FunctionSignature(
            'sparsity',
            FunctionType.BINARY_NUMERIC,
            param_generator=lambda: random.uniform(0.5, 4.0)
        ),
        'hurry': FunctionSignature(
            'hurry',
            FunctionType.BINARY_NUMERIC,
            param_generator=lambda: random.uniform(0.5, 2.0)
        ),
        'ply': FunctionSignature(
            'ply',
            FunctionType.BINARY_INT,
            param_generator=lambda: random.randint(2, 4)
        ),
        'iter': FunctionSignature(
            'iter',
            FunctionType.BINARY_INT,
            param_generator=lambda: random.randint(2, 8)
        ),
        'chop': FunctionSignature(
            'chop',
            FunctionType.BINARY_INT,
            param_generator=lambda: random.randint(2, 16)
        ),
        'striate': FunctionSignature(
            'striate',
            FunctionType.BINARY_INT,
            param_generator=lambda: random.randint(2, 16)
        ),
        
        # === PROBABILISTIC (float, pattern -> pattern) ===
        'degradeBy': FunctionSignature(
            'degradeBy',
            FunctionType.PROBABILISTIC,
            param_generator=lambda: random.uniform(0.1, 0.7)
        ),
        'sometimesBy': FunctionSignature(
            'sometimesBy',
            FunctionType.PROBABILISTIC,
            param_generator=lambda: random.uniform(0.2, 0.8)
        ),
        
        # === N-ARY COMBINATORS (multiple patterns) ===
        'stack': FunctionSignature(
            'stack',
            FunctionType.N_ARY,
            min_children=2,
            max_children=4
        ),
        'cat': FunctionSignature(
            'cat',
            FunctionType.N_ARY,
            min_children=2,
            max_children=4
        ),
        'fastcat': FunctionSignature(
            'fastcat',
            FunctionType.N_ARY,
            min_children=2,
            max_children=4
        ),
        'slowcat': FunctionSignature(
            'slowcat',
            FunctionType.N_ARY,
            min_children=2,
            max_children=4
        ),
        'append': FunctionSignature(
            'append',
            FunctionType.N_ARY,
            min_children=2,
            max_children=2
        ),
        'overlay': FunctionSignature(
            'overlay',
            FunctionType.N_ARY,
            min_children=2,
            max_children=3
        ),
        
        # === CONDITIONAL (int, pattern, pattern -> pattern) ===
        'every': FunctionSignature(
            'every',
            FunctionType.CONDITIONAL,
            param_generator=lambda: random.randint(2, 8),
            min_children=2,
            max_children=2
        ),
        'whenmod': FunctionSignature(
            'whenmod',
            FunctionType.CONDITIONAL,
            param_generator=lambda: random.randint(3, 8),
            min_children=2,
            max_children=2
        ),
    }
    
    # Get lists of functions by type for easier selection
    @classmethod
    def get_functions_by_type(cls, func_type: FunctionType) -> List[FunctionSignature]:
        """Get all functions of a specific type."""
        return [sig for sig in cls.FUNCTIONS.values() if sig.func_type == func_type]
    
    @classmethod
    def get_all_functions(cls) -> List[FunctionSignature]:
        """Get all function signatures."""
        return list(cls.FUNCTIONS.values())