"""Configuration management for genetic_music package.

Loads settings from a config.yaml file in the project root, with fallback
to environment variables and sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional

import yaml


class Config:
    """Configuration singleton for the genetic_music package."""

    _instance: Optional["Config"] = None
    _config_data: dict = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """Load configuration from config.yaml or environment variables."""
        # Try to find config.yaml in the project root
        config_paths = [
            Path.cwd() / "config.yaml",
            Path(__file__).parent.parent.parent / "config.yaml",
        ]

        config_file = None
        for path in config_paths:
            if path.exists():
                config_file = path
                break

        if config_file:
            with open(config_file, "r") as f:
                self._config_data = yaml.safe_load(f) or {}
        else:
            self._config_data = {}

    def get(self, key: str, default=None):
        """Get a configuration value by key.

        First checks the config file, then environment variables, then returns default.

        Args:
            key: Configuration key (can use dot notation for nested keys, e.g., 'tidal.boot_file_path')
            default: Default value if key is not found

        Returns:
            Configuration value or default
        """
        # Handle nested keys (e.g., 'tidal.boot_file_path')
        keys = key.split(".")
        value = self._config_data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                # Key not found in config file, try environment variable
                env_key = "_".join(keys).upper()
                env_value = os.environ.get(env_key)
                if env_value:
                    return env_value
                return default

        return value

    @property
    def boot_tidal_path(self) -> Optional[str]:
        """Get the BootTidal.hs file path.

        Returns:
            Path to BootTidal.hs file, or None if not configured
        """
        path = self.get("tidal.boot_file_path")
        if path:
            # Expand user home directory if needed
            return os.path.expanduser(path)
        return None

    def reload(self) -> None:
        """Reload configuration from file."""
        self._load_config()


# Singleton instance
config = Config()


def get_boot_tidal_path() -> Optional[str]:
    """Convenience function to get the BootTidal.hs path.

    Returns:
        Path to BootTidal.hs file, or None if not configured

    Raises:
        FileNotFoundError: If path is configured but file doesn't exist
    """
    path = config.boot_tidal_path
    if path and not os.path.exists(path):
        raise FileNotFoundError(
            f"BootTidal.hs not found at configured path: {path}\n"
            f"Please check your config.yaml file or set the TIDAL_BOOT_FILE_PATH environment variable."
        )
    return path
