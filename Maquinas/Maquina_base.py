
import random
from paho.mqtt import client as mqtt_client
from paho.mqtt.enums import CallbackAPIVersion


class Maquina_base:

    def __init__(self, nome, broker, port,client_id,status):
        self.nome = nome          
        self.broker = broker      
        self.port = port         
        self.client = None        
        self.client_id = client_id
        self.status = status

    def conectar_broker(self):
        def on_connect(client, userdata, flags, reason_code, properties):
            if reason_code == 0:
                print("Conectado ao MQTT Broker!")
            else:
                print(f"Falha ao conectar, razão:  {reason_code}")
        
        self.client = mqtt_client.Client(callback_api_version=CallbackAPIVersion.VERSION2,
                                client_id=self.client_id)
        self.client.on_connect = on_connect
        self.client.connect(self.broker, self.port)
        self.client.loop_start() 
        return self.client
        
    def desconectar(self):
        self.client.loop_stop()
        self.client.disconnect()

    def publicar(self, topico, mensagem):
        if self.client is None:
            print("⚠️ Cliente MQTT não conectado.")
            return
        info = self.client.publish(topico, mensagem, qos=0)
        try:
            info.wait_for_publish(timeout=1)
        except Exception:
            pass
        if info.is_published():
            print(f"[{self.client_id}] 📤 Enviou: `{mensagem}` ao tópico `{topico}`")
        else:
            print(f"[{self.client_id}] ⚠️ Falha ao publicar mensagem.")


    def assinar_topico(self, topico):
        self.client.subscribe(topico)
        print(f"[{self.client_id}] 🧭 Subscrito no tópico: {topico}")
        def on_message(client, userdata, msg):
            payload = msg.payload.decode()
            print(f"[{self.client_id}] 📥 Recebido de `{msg.topic}`: {payload}")
            self.processar_mensagem(payload)
            
        self.client.on_message = on_message
    
    def processar_mensagem(self, mensagem):
        print(f"[{self.client_id}] Mensagem genérica recebida: {mensagem}")

    def atualizar_status(self, novo_status):
        self.status = novo_status
    
    def obter_status(self):
        return self.status
    
    def log(self, mensagem):
        print(f"[LOG-{self.client_id}] {mensagem}")

    def operar(self):
        if self.status != "ativo":
            print(f"[{self.client_id}] ⚠️ Máquina {self.nome} inativa, não pode operar.")
            return
        print(f"[{self.client_id}] 🏭 Máquina {self.nome} em operação!")