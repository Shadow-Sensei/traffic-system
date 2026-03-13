# Smart Traffic System

A smart emergency traffic management system that uses YOLOv8 to detect vehicle density from a live video feed and coordinates traffic signals via an ESP32 device over Wi-Fi.

## How It Works

1. **Traffic density detection** – A pluggable density source reads the current traffic level and classifies it as:
   - `L` – Low  (≤ 2 vehicles)
   - `M` – Medium (3–5 vehicles)
   - `H` – High  (> 5 vehicles)

2. **Packet generation** – The Flask server (`app.py`) encodes the current state into a compact packet and POSTs it to the ESP32 at `http://192.168.4.1/packet`.

3. **Ambulance priority** – A web UI lets operators draw an ambulance route on the map. That route overrides the density mode and sends an RF-priority packet to clear the path.

## Density Sources

The system supports three interchangeable density sources, selectable at runtime through the web UI or API:

| Source | Key | Description |
|--------|-----|-------------|
| YOLO video detection | `yolo` | YOLOv8 analyses frames from `traffic.mp4` to count vehicles in a defined lane polygon *(default)* |
| ESP32 ultrasonic sensors | `ultrasonic` | The ESP32 pushes sensor readings to `POST /density/ultrasonic` |
| Manual simulation | `manual` | An operator sets the density level directly via the web UI or `POST /density/manual` |

Set the default source at startup with the `DENSITY_SOURCE` environment variable:

```bash
DENSITY_SOURCE=manual python app.py
```

## Packet Format

| Mode | Format | Example |
|------|--------|---------|
| Density update | `<D\|<level>\|<key>>` | `<D\|M\|4>` |
| RF route  | `<<signals>\|<key>>` | `<1,6\|4>` |

- `<level>` is `L`, `M`, or `H`
- `<signals>` is a comma-separated list of signal IDs along the ambulance route
- `<key>` is the shared secret (`4` by default, see `SECRET_KEY` in `app.py`)

## API Endpoints

### Density source management

| Method | Path | Body / Response |
|--------|------|-----------------|
| `GET` | `/density/source` | `{"source": "yolo", "available": [...]}` |
| `POST` | `/density/source` | `{"source": "manual"}` → switches active source |
| `POST` | `/density/manual` | `{"density": "M"}` → sets level, switches to manual |
| `POST` | `/density/ultrasonic` | `{"count": 4}` or `{"distance_cm": 80}` → ESP32 push |
| `GET` | `/density/current` | `{"density": "L", "source": "yolo"}` → UI polling |

### Ultrasonic payload formats

The ESP32 may send either:
- `{"count": N}` – number of vehicles detected by sensor polling
- `{"distance_cm": D}` – distance to nearest obstacle (≤ 100 cm = High, 101–200 cm = Medium, > 200 cm = Low)

## Project Structure

```
traffic-system/
├── app.py                  # Flask web server & background density thread
├── VehicleDensity.py       # Backward-compat wrapper + run_preview() utility
├── density/                # Modular density source package
│   ├── __init__.py         # Source registry (get_active_source, set_active_source)
│   ├── base.py             # DensitySource ABC + density_level() helper
│   ├── yolo.py             # YoloDensitySource  – YOLOv8 video detection
│   ├── ultrasonic.py       # UltrasonicDensitySource – ESP32 sensor push
│   └── manual.py           # ManualDensitySource – operator-set level
├── requirements.txt        # Python dependencies
├── traffic.mp4             # Input video for YOLO density detection
├── yolov8n.pt              # YOLOv8n model weights
├── templates/
│   ├── index.html          # Emergency traffic map UI (includes density panel)
│   ├── received.html       # Live packet log viewer
│   └── send_message.html   # Manual packet transmitter
└── static/
    ├── RealMap.png         # Intersection map image
    ├── map.js              # Interactive map & route logic
    └── random              # ESP32 Arduino sketch (receiver)
```

## Installation

```bash
pip install -r requirements.txt
```

> **Note:** `opencv-python-headless` is used instead of `opencv-python` so the server runs in headless environments (no display required).

## Running

```bash
# Default: YOLO source
python app.py

# Start with manual simulation (no video/YOLO needed)
DENSITY_SOURCE=manual python app.py
```

Open `http://localhost:5000` in a browser.

- Use the **Density Source Control** panel to switch between YOLO, ultrasonic, and manual modes.
- In **manual** mode, click the Low / Medium / High buttons to set the density instantly.
- Click traffic signals on the map to build an ambulance route, then press **Send Route**.
- The background thread continuously polls the active source and sends density updates to the ESP32 every 3 seconds.
- Visit `/received` to monitor the last 5 sent packets in real time.

## ESP32 Setup

Flash `static/random` (Arduino sketch) onto an ESP32. It creates a Wi-Fi access point `AmbulanceSystem` (password `12345678`) and listens for HTTP POST requests on port 80 at `/packet`.

For ultrasonic sensing, add code to the sketch to POST to `/density/ultrasonic` on the Flask server with `{"count": N}` or `{"distance_cm": D}`.
