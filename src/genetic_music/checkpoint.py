"""Checkpointing utilities for genetic evolution."""

import os
import pickle
import random
import sys
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

from genetic_music.genome.genome import Genome


def save_checkpoint(
    filepath: Union[str, Path],
    generation: int,
    population: List[Genome],
    extra_data: Optional[dict] = None,
) -> None:
    """Save the current evolution state to a pickle file.

    Args
    ----
    filepath:
        Path to save the checkpoint.
    generation:
        Current generation number.
    population:
        Current population list.
    extra_data:
        Optional dictionary for other metadata.
    """

    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Create a temporary file first to avoid corruption if interrupted
    temp_path = filepath.with_suffix(".tmp")

    data = {
        "generation": generation,
        "population": population,
        "rng_state": random.getstate(),
        "extra_data": extra_data or {},
    }

    with open(temp_path, "wb") as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

    # Atomic rename
    os.replace(temp_path, filepath)
    print(f"[Checkpoint] Saved generation {generation} to {filepath}")


def load_checkpoint(filepath: Union[str, Path]) -> Tuple[int, List[Genome], Any]:
    """Load evolution state from a pickle file.

    Returns
    -------
    Tuple[int, List[Genome], Any]
        Tuple of (generation, population, extra_data).

    Notes
    -----
    - Pattern trees can be fairly deep, so unpickling may require a higher
      recursion limit than the Python default (~1000). We temporarily raise
      the limit to a safer value before loading.
    """

    filepath = Path(filepath)

    # Bump recursion limit to safely unpickle deep pattern trees
    old_limit = sys.getrecursionlimit()
    if old_limit < 10_000:
        sys.setrecursionlimit(10_000)

    with open(filepath, "rb") as f:
        data = pickle.load(f)

    if "rng_state" in data:
        random.setstate(data["rng_state"])

    return data["generation"], data["population"], data.get("extra_data", {})
