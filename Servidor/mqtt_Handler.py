import paho.mqtt.client as mqtt
import json

class MQTTHandler:
    def __init__(self, broker='localhost', port=1883, on_message_callback=None):
        self.client = mqtt.Client(client_id="servidor", clean_session=True)
        self.client.on_connect = self.on_connect
        self.client.on_message = on_message_callback
        self.broker = broker
        self.port = port

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("[MQTT] ✅ Conectado ao broker MQTT.")
            self.client.subscribe("factory/servidor/in" )
            print("[MQTT] Subscrito em factory/servidor/in")
        else:
            print(f"[MQTT] ❌ Falha ao conectar. Código: {rc}")

    def publish(self, topic, message):
        if isinstance(message, dict):
            message = json.dumps(message)
        self.client.publish(topic, message)

    def start(self):
        self.client.connect(self.broker, self.port)
        self.client.loop_start()
