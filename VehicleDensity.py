"""
Legacy module – kept for backward compatibility and standalone visual preview.

For production use the `density` package directly:

    import density
    level = density.get_active_source().get_density()
"""

from density.base import density_level                        # noqa: F401  (re-exported)
from density.yolo import YoloDensitySource, _get_model, _get_cap, _get_lane3

_source = YoloDensitySource()


def get_density():
    """Run YOLO on one video frame and return a density level."""
    return _source.get_density()


def run_preview():
    """Optional: run a visual preview for debugging/demo (requires a display)."""

    import cv2

    model = _get_model()
    cap = _get_cap()
    lane3 = _get_lane3()

    frame_count = 0
    lane_counts = [0]

    while True:

        ret, frame = cap.read()

        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        cv2.polylines(frame, [lane3], True, (0, 255, 0), 2)

        frame_count += 1

        if frame_count % 10 == 0:

            results = model(frame)
            lane_counts = [0]

            for r in results:
                for box in r.boxes:

                    cls = int(box.cls)
                    label = model.names[cls]

                    if label not in ["car", "truck", "bus", "motorcycle"]:
                        continue

                    x1, y1, x2, y2 = box.xyxy[0]

                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)

                    cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)

                    if cv2.pointPolygonTest(lane3, (cx, cy), False) >= 0:
                        lane_counts[0] += 1

        count = lane_counts[0]
        level = density_level(count)

        cv2.putText(
            frame,
            f"Lane3: {count} ({level})",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

        cv2.imshow("Traffic", frame)

        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


# Run preview only if file is executed directly
if __name__ == "__main__":
    run_preview()