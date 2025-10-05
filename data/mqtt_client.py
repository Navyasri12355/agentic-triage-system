import paho.mqtt.client as mqtt
import json
import threading
import os

# Default to HiveMQ public broker for global access
BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
PORT = int(os.getenv("MQTT_PORT", 1883))
TOPIC = os.getenv("MQTT_TOPIC", "triage/vitals")  # match Node-RED topic

def start_mqtt_listener(on_message_callback):
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ Connected to MQTT broker: {BROKER}:{PORT}")
            client.subscribe(TOPIC)
            print(f"📡 Subscribed to topic: {TOPIC}")
        else:
            print(f"⚠️ MQTT connection failed with code {rc}")

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            print(f"📩 Message received on {msg.topic}: {payload}")
            on_message_callback(payload)
        except Exception as e:
            print("⚠️ Error parsing message:", e)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    def run():
        try:
            client.connect(BROKER, PORT, 60)
            client.loop_forever()
        except Exception as e:
            print(f"🚫 MQTT connection error: {e}")

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
