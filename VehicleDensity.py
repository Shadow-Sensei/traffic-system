from ultralytics import YOLO
import cv2
import numpy as np

model = YOLO("yolov8n.pt")
cap = cv2.VideoCapture("traffic.mp4")

lane_capacity = 8

lane3 = np.array([
    [899,447],
    [431,118],
    [346,120],
    [663,483]
])


def density_level(count):

    if count <= 2:
        return "L"

    elif count <= 5:
        return "M"

    else:
        return "H"


def get_density():
    """
    Runs YOLO on one frame and returns density level
    """

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

            x1,y1,x2,y2 = box.xyxy[0]

            cx = int((x1+x2)/2)
            cy = int((y1+y2)/2)

            if cv2.pointPolygonTest(lane3,(cx,cy),False) >= 0:
                vehicle_count += 1

    density = density_level(vehicle_count)

    return density


def run_preview():
    """
    Optional: run visual preview for debugging/demo
    """

    frame_count = 0
    lane_counts = [0]

    while True:

        ret, frame = cap.read()

        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES,0)
            continue

        cv2.polylines(frame,[lane3],True,(0,255,0),2)

        frame_count += 1

        if frame_count % 10 == 0:

            results = model(frame)
            lane_counts = [0]

            for r in results:
                for box in r.boxes:

                    cls = int(box.cls)
                    label = model.names[cls]

                    if label not in ["car","truck","bus","motorcycle"]:
                        continue

                    x1,y1,x2,y2 = box.xyxy[0]

                    cx = int((x1+x2)/2)
                    cy = int((y1+y2)/2)

                    cv2.circle(frame,(cx,cy),4,(0,0,255),-1)

                    if cv2.pointPolygonTest(lane3,(cx,cy),False) >= 0:
                        lane_counts[0] += 1


        count = lane_counts[0]
        density = density_level(count)

        cv2.putText(
            frame,
            f"Lane3: {count} ({density})",
            (20,40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0,255,0),
            2
        )

        cv2.imshow("Traffic",frame)

        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


# Run preview only if file is executed directly
if __name__ == "__main__":
    run_preview()