from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional

import json

import numpy as np
import pandas as pd


@dataclass
class RunLoggerConfig:
    """Configuration for a logging run.

    This is intentionally minimal; extend it if needed.
    """

    run_name: str
    output_dir: Path
    timestamp: str

    @property
    def base_filename(self) -> str:
        return f"{self.run_name}_{self.timestamp}"

    @property
    def csv_path(self) -> Path:
        return self.output_dir / f"{self.base_filename}.csv"

    @property
    def metadata_path(self) -> Path:
        return self.output_dir / f"{self.base_filename}.metadata.json"


class RunLogger:
    """Minimal helper to log GA run statistics to CSV.

    Usage
    -----
    >>> logger = RunLogger(run_name="long_run", metadata={"population_size": 128})
    >>> for gen in range(num_generations):
    ...     # after computing fitness_scores and best_expression_str
    ...     logger.log_generation(gen, fitness_scores, best_expression_str)
    >>> logger.close()
    """

    def __init__(
        self,
        run_name: str,
        output_dir: str | Path = "logs",
        overwrite: bool = False,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        self._closed = False

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.config = RunLoggerConfig(
            run_name=run_name,
            output_dir=output_dir,
            timestamp=timestamp,
        )

        if not overwrite:
            # Make sure we don't accidentally overwrite an existing run.
            if self.config.csv_path.exists() or self.config.metadata_path.exists():
                raise FileExistsError(
                    f"Log files already exist for base name '{self.config.base_filename}'. "
                    "Use overwrite=True or change run_name."
                )

        # Prepare CSV with header but no rows yet.
        self._init_csv()

        # Write metadata once at the start of the run.
        self._write_metadata(metadata or {})

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def log_generation(
        self,
        generation: int,
        fitness_scores: Iterable[float],
        best_expression: str,
    ) -> None:
        """Append statistics for a single generation to the CSV.

        Parameters
        ----------
        generation:
            Zero-based generation index.
        fitness_scores:
            Iterable of fitness scores for the whole population.
        best_expression:
            String representation of the best individual (e.g. pretty-printed tree
            or Tidal code). It will be stored as-is and quoted by pandas.
        """

        if self._closed:
            raise RuntimeError("Cannot log_generation on a closed RunLogger.")

        scores_array = np.fromiter(fitness_scores, dtype=float)
        if scores_array.size == 0:
            raise ValueError("fitness_scores is empty; cannot compute statistics.")

        min_f = float(scores_array.min())
        max_f = float(scores_array.max())
        mean_f = float(scores_array.mean())

        row = {
            "generation": int(generation),
            "min_fitness": min_f,
            "max_fitness": max_f,
            "mean_fitness": mean_f,
            "best_fitness": max_f,  # explicit, even if redundant
            "population_size": int(scores_array.size),
            "best_expression": best_expression,
        }

        df = pd.DataFrame([row])

        # Append without header (header is written once in _init_csv)
        df.to_csv(
            self.config.csv_path,
            mode="a",
            header=False,
            index=False,
        )

    def close(self) -> None:
        """Mark the logger as closed.

        There are no persistent open file handles (pandas handles I/O per call),
        but this is here for symmetry and future-proofing.
        """

        self._closed = True

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------
    def __enter__(self) -> "RunLogger":  # type: ignore[override]
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _make_json_safe(obj: Any) -> Any:
        """Recursively convert objects to JSON-serialisable forms.

        Currently this mainly ensures :class:`pathlib.Path` instances are
        represented as strings but can be extended if needed.
        """

        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, dict):
            return {k: RunLogger._make_json_safe(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple, set)):
            return [RunLogger._make_json_safe(v) for v in obj]
        return obj

    def _init_csv(self) -> None:
        """Create the CSV file with header only (no rows)."""

        columns = [
            "generation",
            "min_fitness",
            "max_fitness",
            "mean_fitness",
            "best_fitness",
            "population_size",
            "best_expression",
        ]

        df = pd.DataFrame(columns=columns)
        df.to_csv(self.config.csv_path, index=False)

    def _write_metadata(self, metadata: dict[str, Any]) -> None:
        """Write a JSON sidecar file with run metadata.

        The file includes the logger configuration and any user-provided
        metadata (e.g. config dict, random seed, notes).
        """

        raw_payload: dict[str, Any] = {
            "logger_config": asdict(self.config),
            "user_metadata": metadata,
        }

        # Ensure everything is JSON-serialisable (e.g. Path -> str).
        payload = RunLogger._make_json_safe(raw_payload)

        with self.config.metadata_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
