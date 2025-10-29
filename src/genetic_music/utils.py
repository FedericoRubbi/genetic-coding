"""
Utility functions for the genetic music system.
"""

import json
import yaml
from pathlib import Path
from typing import Any, Dict


def save_config(config: Dict[str, Any], path: Path) -> None:
    """
    Save configuration to file.
    
    Args:
        config: Configuration dictionary
        path: Output file path (.json or .yaml)
    """
    path = Path(path)
    
    if path.suffix == '.json':
        with open(path, 'w') as f:
            json.dump(config, f, indent=2)
    elif path.suffix in ['.yaml', '.yml']:
        with open(path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")


def load_config(path: Path) -> Dict[str, Any]:
    """
    Load configuration from file.
    
    Args:
        path: Config file path (.json or .yaml)
    
    Returns:
        Configuration dictionary
    """
    path = Path(path)
    
    if path.suffix == '.json':
        with open(path, 'r') as f:
            return json.load(f)
    elif path.suffix in ['.yaml', '.yml']:
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")


def setup_logging(log_dir: Path, name: str = "genetic_music") -> None:
    """
    Setup logging configuration.
    
    Args:
        log_dir: Directory for log files
        name: Logger name
    """
    import logging
    from datetime import datetime
    
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{name}_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(name)
    logger.info(f"Logging initialized: {log_file}")

