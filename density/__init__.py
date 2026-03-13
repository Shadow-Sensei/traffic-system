"""
Density source registry for the Smart Traffic System.

Three sources are available:

  yolo        – YOLOv8 video detection (default)
  ultrasonic  – ESP32 ultrasonic sensor readings pushed to /density/ultrasonic
  manual      – Operator-set density via the web UI or POST /density/manual

Set the default source at startup with the DENSITY_SOURCE environment variable:

    DENSITY_SOURCE=manual python app.py

Usage inside app.py:

    import density
    level = density.get_active_source().get_density()   # "L", "M", or "H"
    density.set_active_source("manual")
"""

import os

from .yolo import YoloDensitySource
from .ultrasonic import UltrasonicDensitySource
from .manual import ManualDensitySource


# One persistent instance per source so state is preserved across switches.
_sources = {
    "yolo": YoloDensitySource(),
    "ultrasonic": UltrasonicDensitySource(),
    "manual": ManualDensitySource(),
}

_active_name = os.environ.get("DENSITY_SOURCE", "yolo").lower()

if _active_name not in _sources:
    _active_name = "yolo"


def get_active_source():
    """Return the currently active DensitySource instance."""
    return _sources[_active_name]


def set_active_source(name: str):
    """Switch the active density source by name."""
    global _active_name
    if name not in _sources:
        raise ValueError(
            f"Unknown density source '{name}'. Choose from: {source_names()}"
        )
    _active_name = name


def get_source(name: str):
    """Return a specific DensitySource instance by name."""
    if name not in _sources:
        raise ValueError(
            f"Unknown density source '{name}'. Choose from: {source_names()}"
        )
    return _sources[name]


def source_names():
    """Return a list of all available source names."""
    return list(_sources.keys())
