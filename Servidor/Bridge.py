from mqtt_Handler import MQTTHandler
from tcp_Handler import TCPHandler
import json

class Bridge:
    def __init__(self):
        self.mqtt = MQTTHandler(on_message_callback=self.on_mqtt_message)
        self.tcp = TCPHandler(on_data_callback=self.on_tcp_message)

    # Quando a máquina envia algo (via MQTT)
    def on_mqtt_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
        except json.JSONDecodeError:
            payload = msg.payload.decode()

        print(f"[Bridge] MQTT → {msg.topic}: {payload}")

        # Repassa para o Controlador via TCP
        data = {
            "topic": msg.topic,
            "payload": payload
        }
        self.tcp.send(data)

    # Quando o Controlador envia comando via TCP
    def on_tcp_message(self, message):
        print(f"[Bridge] TCP → comando do controlador: {message}")
        maquina = message.get("maquina")
        comando = message.get("comando").upper()

        if not maquina or not comando:
            print("[Bridge] ❌ Mensagem TCP incompleta.")
            return
        
        topic = f"factory/{maquina}/in"
        cmd_msg = {"command": comando}

        # Exemplo: se tiver quantidade para repor
        if comando == "REPOR" and "quantidade" in message:
            cmd_msg["quantidade"] = message["quantidade"]

        print(f"[Bridge] 📤 Enviando ao tópico {topic}: {cmd_msg}")
        self.mqtt.publish(topic, cmd_msg)
        

    def start(self):
        self.mqtt.start()
        self.tcp.start()
