from Maquina_base import Maquina_base
import json
import time
import threading
import queue

class Packer(Maquina_base):
    def __init__(self, nome, broker, port, client_id,status="ativo"):
        super().__init__(nome, broker, port, client_id, status)

        self.fila_garrafas = queue.Queue()
        self.garrafas_por_caixa = 5
        self.caixas_empacotadas = 0
        self.produzindo = False

        self.topico_receber_filler = "factory/packer/in" 
        self.topico_alerta = "factory/controlador/in"
        self.topico_servidor = "factory/servidor/in"



    def iniciar(self):
        self.conectar_broker()

        if hasattr(self, "client"):
            self.client._keepalive = 30 
            self.client.reconnect_delay_set(min_delay=1, max_delay=10)
        else:
            self.log("❌ Erro: client MQTT não inicializado pela Maquina_base.")
            return

        self.assinar_topico(self.topico_receber_filler)
        self.client.loop_start()

        for _ in range(10):
            if self.client.is_connected():
                break
            time.sleep(0.5)
        self.log("🧪 Packer conectado e monitorando filler.")
        self.publicar(self.topico_servidor, "[PACKER]-> INICIEI!")

        threading.Thread(target=self.manter_vivo, daemon=True).start()

    def manter_vivo(self):
        while True:
            try:
                self.publicar(self.topico_servidor, "[PACKER]-> Esperando")
            except:
                pass
            time.sleep(20)

    def operar(self):
        if self.produzindo:
            self.log("⚙️ Packer já operando.")
            return
        self.produzindo = True
        threading.Thread(target=self.empacotando, daemon=True).start()
        self.log("🟢 Packer iniciou operação de empacotamento")

    def parar_operacao(self):
        self.produzindo = False
        self.log("🔴 Packer parou operação.")

    def receber_garrafa(self, garrafa):
        self.fila_garrafas.put(garrafa)
        self.log(f"📦 Garrafa #{garrafa['id']} recebida para empacotamento. Fila atual: {self.fila_garrafas.qsize()}")

    def empacotando(self):
        while self.produzindo:
            if self.status != "ativo":
                time.sleep(1)
                continue

            if self.fila_garrafas.qsize() >= self.garrafas_por_caixa:
                garrafas = []
                for _ in range(self.garrafas_por_caixa):
                    garrafas.append(self.fila_garrafas.get())
                
                self.caixas_empacotadas += 1
                self.log(f"📦✅ Caixa #{self.caixas_empacotadas} empacotada com {len(garrafas)} garrafas.")
                self.publicar(self.topico_servidor, f"[Packer]-> 📦✅ Caixa #{self.caixas_empacotadas} empacotada com {len(garrafas)} garrafas. ")
                
                time.sleep(2)

                msg = json.dumps({
                    "origem": "Packer",
                    "evento": "caixa_empacotada",
                    "caixas_totais": self.caixas_empacotadas,
                })
                self.publicar(self.topico_alerta, msg)
            else:
                time.sleep(0.5)

    def processar_mensagem(self, mensagem):
        try:
            data = json.loads(mensagem)
        except json.JSONDecodeError:
            self.log("❌ Mensagem inválida (não é JSON).")
            return
        
        evento = data.get("evento")
        if evento == "garrafa_cheia":
            self.receber_garrafa(data)
        elif data.get("command", "").upper() == "PARAR":
            self.parar_operacao()
        elif data.get("command", "").upper() == "OPERAR":
            self.operar()
        else:
            self.log(f"⚠️ Mensagem desconhecida: {mensagem}")
    
    def alertar_controlador(self, tipo_alerta):
        payload = {"origem": "Packer", "alerta": tipo_alerta}
        self.publicar(self.topico_alerta, json.dumps(payload))

if __name__ == "__main__":
    packer = Packer("Packer","broker.emqx.io",1883,"Packer")
    packer.iniciar()

    while True:
        time.sleep(1)