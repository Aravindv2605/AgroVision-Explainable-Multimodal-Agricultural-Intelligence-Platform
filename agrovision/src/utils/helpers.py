import yaml
import json
from pathlib import Path


def load_config(config_path: str = "config/config.yaml") -> dict:
    """Load YAML configuration file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def save_json(data: dict, path: str):
    """Save a dictionary as a JSON file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def load_json(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def ensure_dir(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)
