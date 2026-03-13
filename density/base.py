from abc import ABC, abstractmethod


def density_level(count):
    """Convert a vehicle count to a density level string."""

    if count <= 2:
        return "L"

    elif count <= 5:
        return "M"

    else:
        return "H"


class DensitySource(ABC):
    """Abstract base class for all traffic density sources."""

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def get_density(self) -> str:
        """Return the current density level: 'L', 'M', or 'H'."""
        ...
