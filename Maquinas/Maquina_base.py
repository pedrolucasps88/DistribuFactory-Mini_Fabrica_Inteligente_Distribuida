from paho.mqtt import client as mqtt_client
from paho.mqtt.enums import CallbackAPIVersion
class Maquina_base:

    def __init__(self, nome, broker, port,client_id,status):
        self.nome = nome          
        self.broker = "localhost"     
        self.port = 1883         
        self.client = None        
        self.client_id = client_id
        self.status = status

    def conectar_broker(self):
        def on_connect(client, userdata, flags, reason_code, properties):
            if reason_code == 0:
                print("✅ Conectado ao MQTT Broker!")
            else:
                print(f"⚠️ Falha na conexão ao MQTT Broker, código: {reason_code}")

        def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
            if reason_code != 0:
                print(f"⚠️ Conexão MQTT perdida! (código {reason_code}) — tentando reconectar...")

        self.client = mqtt_client.Client(callback_api_version=CallbackAPIVersion.VERSION2,client_id=self.client_id,clean_session=False)

        
        self.client.on_connect = on_connect
        self.client.on_disconnect = on_disconnect

        self.client.reconnect_delay_set(min_delay=1, max_delay=30)

        self.client.connect(self.broker, self.port)

        return self.client
            
    def desconectar(self):
        self.client.loop_stop()
        self.client.disconnect()

    def publicar(self, topico, mensagem):
        if self.client is None:
            print("⚠️ Cliente MQTT não inicializado.")
            return

        if not self.client.is_connected():
            print(f"[{self.client_id}] ⚠️ Cliente desconectado — publicação adiada.")
            return

        try:
            info = self.client.publish(topico, mensagem, qos=0)
            info.wait_for_publish(timeout=1)
            if info.is_published():
                print(f"[{self.client_id}] 📤 Enviou: `{mensagem}` ao tópico `{topico}`")
            else:
                print(f"[{self.client_id}] ⚠️ Falha ao publicar mensagem.")
        except Exception as e:
            print(f"[{self.client_id}] ❌ Erro ao publicar: {e}")


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