"""Application paths independent of the terminal working directory."""

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
