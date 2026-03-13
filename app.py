from flask import Flask, render_template, request, jsonify
import requests
import VehicleDensity
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
# BACKGROUND YOLO DENSITY THREAD
# -----------------------------
def density_updater():
    global current_density, last_density_sent

    while True:
        try:
            current_density = VehicleDensity.get_density()

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

    density = current_density
    print("Current Density:", density)

    # -----------------------------
    # PRIORITY LOGIC
    # RF (ambulance route) overrides ML
    # -----------------------------
    if route:

        packet = "<" + ",".join(route) + "|" + SECRET_KEY + ">"
        mode = "RF"

        print("RF PRIORITY MODE")

    else:

        packet = "<D|" + density + "|" + SECRET_KEY + ">"
        mode = "ML"

        print("ML DENSITY MODE")

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
        "density": density
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
# START BACKGROUND THREAD
# -----------------------------
density_thread = threading.Thread(target=density_updater, daemon=True)
density_thread.start()


# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)