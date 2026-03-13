from .base import DensitySource


VALID_LEVELS = {"L", "M", "H"}


class ManualDensitySource(DensitySource):
    """
    Density set by a human operator via the web UI or API.

    POST /density/manual  {"density": "M"}

    Calling set_density() also automatically switches the active source to
    'manual' when invoked through the Flask route.
    """

    def __init__(self, initial: str = "L"):
        if initial not in VALID_LEVELS:
            raise ValueError(f"Density must be one of {sorted(VALID_LEVELS)}")
        self._density = initial

    @property
    def name(self):
        return "manual"

    def set_density(self, level: str):
        if level not in VALID_LEVELS:
            raise ValueError(f"Density must be one of {sorted(VALID_LEVELS)}")
        self._density = level

    def get_density(self) -> str:
        return self._density
