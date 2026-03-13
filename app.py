from flask import Flask, render_template, request, jsonify
import requests
import density
import threading
import time

app = Flask(__name__)

last_density_sent = None

SECRET_KEY = "4"
# Store received packets
received_packets = []

ESP32_URL = "http://192.168.4.1/packet"

# Shared density value (updated in background)
current_density = "L"


# -----------------------------
# BACKGROUND DENSITY THREAD
# -----------------------------
def density_updater():
    global current_density, last_density_sent

    while True:
        try:
            current_density = density.get_active_source().get_density()

            packet = "<D|" + current_density + "|" + SECRET_KEY + ">"

            # Only send if density changed
            if packet != last_density_sent:

                print("Density Packet:", packet)

                received_packets.append(packet)

                if len(received_packets) > 5:
                    received_packets.pop(0)

                try:
                    response = requests.post(ESP32_URL, data=packet, timeout=2)
                    print("Density forwarded:", response.status_code)
                except Exception as e:
                    print("ESP32 not reachable:", e)

                last_density_sent = packet

        except Exception as e:
            print("Density error:", e)

        time.sleep(3)


# -----------------------------
# HOME PAGE
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# RECEIVE ROUTE FROM MAP
# -----------------------------
@app.route("/send_path", methods=["POST"])
def receive_path():

    global current_density

    data = request.get_json()
    route = data.get("route", [])

    # convert numbers to string
    route = [str(x) for x in route]

    density_val = current_density
    print("Current Density:", density_val)

    # -----------------------------
    # PRIORITY LOGIC
    # RF (ambulance route) overrides density mode
    # -----------------------------
    if route:

        packet = "<" + ",".join(route) + "|" + SECRET_KEY + ">"
        mode = "RF"

        print("RF PRIORITY MODE")

    else:

        packet = "<D|" + density_val + "|" + SECRET_KEY + ">"
        mode = density.get_active_source().name.upper()

        print(f"{mode} DENSITY MODE")

    print("Generated Packet:", packet)

    # Store packet
    received_packets.append(packet)

    # Send packet to ESP32
    try:
        response = requests.post(ESP32_URL, data=packet, timeout=2)
        print("Packet forwarded to ESP32:", response.status_code)
    except Exception as e:
        print("ESP32 not reachable:", e)

    return jsonify({
        "status": "ok",
        "mode": mode,
        "packet": packet,
        "density": density_val
    })


# -----------------------------
# SHOW RECEIVED PACKETS
# -----------------------------
@app.route("/received")
def received():
    return render_template("received.html", packets=received_packets)


# -----------------------------
# MANUAL SEND PAGE
# -----------------------------
@app.route("/send")
def send():
    return render_template("send_message.html")


# -----------------------------
# DENSITY SOURCE MANAGEMENT
# -----------------------------

@app.route("/density/source", methods=["GET"])
def get_density_source():
    """Return the currently active density source and all available sources."""
    return jsonify({
        "source": density.get_active_source().name,
        "available": density.source_names(),
    })


@app.route("/density/source", methods=["POST"])
def set_density_source():
    """Switch the active density source.  Body: {"source": "yolo"|"ultrasonic"|"manual"}"""
    data = request.get_json(silent=True) or {}
    source = data.get("source", "")
    try:
        density.set_active_source(source)
        return jsonify({"status": "ok", "source": source})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/density/manual", methods=["POST"])
def set_manual_density():
    """
    Set the manual density level and switch to manual mode.
    Body: {"density": "L"|"M"|"H"}
    """
    data = request.get_json(silent=True) or {}
    level = data.get("density", "")
    try:
        src = density.get_source("manual")
        src.set_density(level)
        density.set_active_source("manual")
        return jsonify({"status": "ok", "density": level})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/density/ultrasonic", methods=["POST"])
def update_ultrasonic_density():
    """
    Receive a sensor reading from an ESP32 ultrasonic sensor.
    Body: {"count": N}  or  {"distance_cm": D}
    """
    data = request.get_json(silent=True) or {}
    try:
        src = density.get_source("ultrasonic")
        src.update(data)
        return jsonify({"status": "ok", "density": src.get_density()})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/density/current", methods=["GET"])
def get_current_density():
    """Return the current density level and active source (used by the UI)."""
    return jsonify({
        "density": current_density,
        "source": density.get_active_source().name,
    })


# -----------------------------
# START BACKGROUND THREAD
# -----------------------------
density_thread = threading.Thread(target=density_updater, daemon=True)
density_thread.start()


# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)