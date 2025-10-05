# data/mqtt_client.py
import paho.mqtt.client as mqtt
import json
import threading
import os

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", 1883))
TOPIC = os.getenv("MQTT_TOPIC", "vitals/stream")

def start_mqtt_listener(on_message_callback):
    def on_connect(client, userdata, flags, rc):
        print("✅ MQTT connected with result code", rc)
        client.subscribe(TOPIC)
        print(f"📡 Subscribed to topic: {TOPIC}")

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            on_message_callback(payload)
        except Exception as e:
            print("⚠️ Error parsing message:", e)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    def run():
        client.connect(BROKER, PORT, 60)
        client.loop_forever()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
