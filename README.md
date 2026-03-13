# Smart Traffic System

A smart emergency traffic management system that uses YOLOv8 to detect vehicle density from a live video feed and coordinates traffic signals via an ESP32 device over Wi-Fi.

## How It Works

1. **Traffic density detection** – `VehicleDensity.py` reads frames from `traffic.mp4`, runs YOLOv8 to count vehicles (cars, trucks, buses, motorcycles) inside a defined lane polygon, and classifies the result as:
   - `L` – Low  (≤ 2 vehicles)
   - `M` – Medium (3–5 vehicles)
   - `H` – High  (> 5 vehicles)

2. **Packet generation** – The Flask server (`app.py`) encodes the current state into a compact packet and POSTs it to the ESP32 at `http://192.168.4.1/packet`.

3. **Ambulance priority** – A web UI lets operators draw an ambulance route on the map. That route overrides the ML density mode and sends an RF-priority packet to clear the path.

## Packet Format

| Mode | Format | Example |
|------|--------|---------|
| ML density | `<D\|<level>\|<key>>` | `<D\|M\|4>` |
| RF route  | `<<signals>\|<key>>` | `<1,6\|4>` |

- `<level>` is `L`, `M`, or `H`
- `<signals>` is a comma-separated list of signal IDs along the ambulance route
- `<key>` is the shared secret (`4` by default, see `SECRET_KEY` in `app.py`)

## Project Structure

```
traffic-system/
├── app.py              # Flask web server & background YOLO thread
├── VehicleDensity.py   # YOLOv8 density detection logic
├── requirements.txt    # Python dependencies
├── traffic.mp4         # Input video for density detection
├── yolov8n.pt          # YOLOv8n model weights
├── templates/
│   ├── index.html      # Emergency traffic map UI
│   ├── received.html       # Live packet log viewer
│   └── send_message.html # Manual packet transmitter
└── static/
    ├── RealMap.png     # Intersection map image
    ├── map.js          # Interactive map & route logic
    └── random          # ESP32 Arduino sketch (receiver)
```

## Installation

```bash
pip install -r requirements.txt
```

> **Note:** `opencv-python-headless` is used instead of `opencv-python` so the server runs in headless environments (no display required).

## Running

```bash
python app.py
```

Open `http://localhost:5000` in a browser.

- Click traffic signals on the map to build an ambulance route, then press **Send Route**.
- The background thread continuously reads video frames and sends density updates to the ESP32 every 3 seconds.
- Visit `/received` to monitor the last 5 sent packets in real time.

## ESP32 Setup

Flash `static/random` (Arduino sketch) onto an ESP32. It creates a Wi-Fi access point `AmbulanceSystem` (password `12345678`) and listens for HTTP POST requests on port 80 at `/packet`.
