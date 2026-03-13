from .base import DensitySource, density_level


# Distance thresholds for the ultrasonic sensor (centimetres).
# A shorter obstacle distance implies more vehicles blocking the road.
_DIST_LOW = 200   # > 200 cm  → Low traffic
_DIST_MED = 100   # 101–200 cm → Medium traffic
                  # ≤ 100 cm  → High traffic


class UltrasonicDensitySource(DensitySource):
    """
    Density sourced from ultrasonic sensors attached to an ESP32.

    The ESP32 pushes readings to POST /density/ultrasonic.
    Two payload formats are accepted:

      {"count": N}         – direct vehicle count from sensor polling
      {"distance_cm": D}   – nearest-obstacle distance in centimetres
                             (shorter distance → higher density)
    """

    def __init__(self):
        self._density = "L"

    @property
    def name(self):
        return "ultrasonic"

    def update(self, payload: dict):
        """
        Update the stored density from a sensor payload dict.
        Called by the /density/ultrasonic Flask route.
        """

        if "count" in payload:
            self._density = density_level(int(payload["count"]))

        elif "distance_cm" in payload:
            d = float(payload["distance_cm"])

            if d > _DIST_LOW:
                self._density = "L"
            elif d > _DIST_MED:
                self._density = "M"
            else:
                self._density = "H"

        else:
            raise ValueError("Payload must contain 'count' or 'distance_cm'")

    def get_density(self) -> str:
        return self._density
