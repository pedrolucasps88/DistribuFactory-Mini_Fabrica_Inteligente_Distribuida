from Maquinas.Maquina_base import Maquina_base
import json
import time
import threading
from queue import Queue

class Filler(Maquina_base):
    VOLUME_GARRAFA_L = 0.5          
    TEMPO_PREENCHIMENTO = 1.5      
    NIVEL_MINIMO_ALERTA = 10.0     

    def __init__(self, nome, broker, port, client_id,
                 capacidade_reservatorio_l=100.0, nivel_inicial_l=50.0,
                 status="ativo"):
        super().__init__(nome, broker, port, client_id, status)

        
        self.capacidade_reservatorio = float(capacidade_reservatorio_l)
        self.nivel_reservatorio = float(nivel_inicial_l)

        
        self.fila_garrafas = Queue()

        # Controle
        self.produzindo = False
        self.lock = threading.Lock()

        # Tópicos
        self.topico_receber_feeder = "factory/filler/in"  # recebe do feeder e mixer
        self.topico_enviar = "factory/packer/in"          # envia garrafas cheias
        self.topico_status = "factory/filler/status"      # publica nível do reservatório
        self.topico_alerta = "factory/controlador/in"

    def iniciar(self):
        self.conectar_broker()
        self.assinar_topico(self.topico_receber_feeder)
        self.log("🧪 Filler pronto — inscrito nos tópicos do feeder e mixer.")
        self._publicar_status_periodico()

    def operar(self):
        if self.produzindo:
            self.log("⚙️ Filler já operando.")
            return
        self.produzindo = True
        threading.Thread(target=self.preenchimento, daemon=True).start()
        threading.Thread(target=self._publicar_status_periodico, daemon=True).start()
        self.log("🟢 Filler iniciou operação de enchimento.")

    def parar_operacao(self):
        self.produzindo = False
        self.log("🔴 Filler parou operação.")

    def preenchimento(self):
        while self.produzindo:
            if self.status != "ativo":
                time.sleep(1)
                continue

            if self.fila_garrafas.empty():
                time.sleep(0.3)
                continue

            with self.lock:
                if self.nivel_reservatorio < self.VOLUME_GARRAFA_L:
                    self.log("⚠️ Reservatório vazio — aguardando reabastecimento.")
                    self.alertar_controlador("reservatorio_vazio")
                    time.sleep(2)
                    continue

                garrafa_id = self.fila_garrafas.get()
                self.nivel_reservatorio -= self.VOLUME_GARRAFA_L

            
            time.sleep(self.TEMPO_PREENCHIMENTO)

            msg = json.dumps({
                "origem": "Filler",
                "evento": "garrafa_cheia",
                "id": garrafa_id
            })
            self.publicar(self.topico_enviar, msg)
            self.log(f"🧴✅ Garrafa #{garrafa_id} cheia e enviada ao empacotador. Nível atual: {self.nivel_reservatorio:.2f} L")
            time.sleep(2)
            if self.nivel_reservatorio <= self.NIVEL_MINIMO_ALERTA:
                self.alertar_controlador("nivel_baixo", {"nivel": self.nivel_reservatorio})

            time.sleep(0.1)

    def _publicar_status_periodico(self):
        while self.produzindo:
            msg = json.dumps({
                "origem": "Filler",
                "evento": "reservatorio",
                "nivel_litros": round(self.nivel_reservatorio, 2)
            })
            self.publicar(self.topico_status, msg)
            time.sleep(3) 

    def processar_mensagem(self, mensagem):
        try:
            data = json.loads(mensagem)
        except Exception:
            self.log("❌ Mensagem inválida (não é JSON).")
            return

        origem = data.get("origem", "")
        evento = data.get("evento", "")

        if origem == "Feeder" and evento == "garrafa_pronta":
            garrafa_id = data.get("id")
            if garrafa_id is not None:
                self.fila_garrafas.put(garrafa_id)
                self.log(f"🧴 Garrafa #{garrafa_id} recebida para enchimento. Fila: {self.fila_garrafas.qsize()}")

        elif origem == "Mixer" and evento == "liquido_pronto":
            quantidade = float(data.get("quantidade_litros", 0))
            with self.lock:
                self.nivel_reservatorio += quantidade
                if self.nivel_reservatorio > self.capacidade_reservatorio:
                    self.nivel_reservatorio = self.capacidade_reservatorio
            self.log(f"💧✅ Recebido {quantidade} L do Mixer. Novo nível: {self.nivel_reservatorio:.2f} L")

        elif "command" in data:
            comando = str(data.get("command", "")).upper()
            match comando:
                case "OPERAR":
                    self.operar()
                case "PARAR":
                    self.parar_operacao()
                case _:
                    self.log(f"⚠️ Comando desconhecido: {comando}")


    def alertar_controlador(self, tipo_alerta, info=None):
        payload = {"origem": "Filler", "alerta": tipo_alerta, "nivel_reservatorio_l": self.nivel_reservatorio}
        if info:
            payload.update(info)
        self.publicar(self.topico_alerta, json.dumps(payload))
