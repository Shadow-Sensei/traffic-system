from .base import DensitySource, density_level


# ---------------------------------------------------------------------------
# Module-level lazy globals – all heavy dependencies (numpy, cv2, ultralytics)
# are imported on first use so that the `density` package itself can be
# imported even when these optional packages are not installed.
# ---------------------------------------------------------------------------

_model = None
_cap = None
_lane3 = None


def _get_lane3():
    global _lane3
    if _lane3 is None:
        import numpy as np
        _lane3 = np.array([
            [899, 447],
            [431, 118],
            [346, 120],
            [663, 483],
        ])
    return _lane3


def _get_model():
    global _model
    if _model is None:
        from ultralytics import YOLO   # lazy – only needed for YOLO source
        _model = YOLO("yolov8n.pt")
    return _model


def _get_cap():
    global _cap
    if _cap is None:
        import cv2
        _cap = cv2.VideoCapture("traffic.mp4")
    return _cap


class YoloDensitySource(DensitySource):
    """Detect vehicle density from video using YOLOv8."""

    @property
    def name(self):
        return "yolo"

    def get_density(self) -> str:
        """Run YOLO on one video frame and return a density level."""

        import cv2

        cap = _get_cap()
        model = _get_model()
        lane3 = _get_lane3()

        ret, frame = cap.read()

        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()

        results = model(frame)

        vehicle_count = 0

        for r in results:
            for box in r.boxes:

                cls = int(box.cls)
                label = model.names[cls]

                if label not in ["car", "truck", "bus", "motorcycle"]:
                    continue

                x1, y1, x2, y2 = box.xyxy[0]

                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)

                if cv2.pointPolygonTest(lane3, (cx, cy), False) >= 0:
                    vehicle_count += 1

        return density_level(vehicle_count)
