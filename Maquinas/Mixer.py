from Maquinas.Maquina_base import Maquina_base
import json
import time
import threading

class Mixer(Maquina_base):
    VOLUME_GARRAFA_L = 0.5             
    PRODUCTION_TIME_PER_BOTTLE = 0.5   
    MAX_BATCH_BOTTLES = 10             

    def __init__(self, nome, broker, port, client_id,
                 capacidade_reservatorio_l=100.0, nivel_inicial_l=0.0,
                 status="ativo"):
        super().__init__(nome, broker, port, client_id, status)

        
        self.capacidade_reservatorio = float(capacidade_reservatorio_l)  # L
        self.nivel_reservatorio = float(nivel_inicial_l)  # L
        self.feeder_estoque = 0         

        # controle e flags
        self.lock = threading.Lock()
        self.produzindo = False
        self.recebeu_feeder_status = False
        self.recebeu_filler_status = False

        # tópicos
        self.topico_feeder_status = "factory/feeder/status"   # espera JSON com {"origem":"Feeder","evento":"status","estoque_garrafas": N}
        self.topico_filler_status = "factory/filler/status"   # espera JSON com {"origem":"Filler","evento":"reservatorio","nivel_litros": X}
        self.topico_enviar = "factory/filler/in"              # envia {"origem":"Mixer","evento":"liquido_pronto","quantidade_litros": X, "bottles":n}
        self.topico_alerta = "factory/controlador/in"


    def iniciar(self):
        self.conectar_broker()
        self.assinar_topico(self.topico_feeder_status)
        self.assinar_topico(self.topico_filler_status)
        self.log("Mixer pronto — conectado e inscrito nos tópicos de status.")

    def operar(self):
        if self.produzindo:
            self.log("⚙️ Produção já em andamento.")
            return
        self.produzindo = True
        threading.Thread(target=self.producao, daemon=True).start()
        self.log("🟢 Loop de produção do Mixer iniciado.")

    def parar_operacao(self):
        self.produzindo = False
        self.log("🔴 Produção do Mixer parada.")

    def producao(self):
        while self.produzindo:
            if self.status != "ativo":
                time.sleep(1)
                continue

            if not self.recebeu_feeder_status:
                time.sleep(0.5)
                continue

            with self.lock:
                deficit_l = self.capacidade_reservatorio - self.nivel_reservatorio
                capacidade_feeder_l = self.feeder_estoque * self.VOLUME_GARRAFA_L
                bottles_to_produce = min(int(deficit_l / self.VOLUME_GARRAFA_L), int(self.feeder_estoque))
                if bottles_to_produce > self.MAX_BATCH_BOTTLES:
                    bottles_to_produce = self.MAX_BATCH_BOTTLES

            if bottles_to_produce <= 0:
                time.sleep(1)
                continue

            litros = bottles_to_produce * self.VOLUME_GARRAFA_L
            self.log(f"🌀 Mixer vai produzir {litros} L ({bottles_to_produce} garrafas simuladas).")

            
            time.sleep(4)

            with self.lock:
               
                self.nivel_reservatorio += litros
                if self.nivel_reservatorio > self.capacidade_reservatorio:
                    self.nivel_reservatorio = self.capacidade_reservatorio

            msg = json.dumps({
                "origem": "Mixer",
                "evento": "liquido_pronto",
                "quantidade_litros": litros,
                "bottles": bottles_to_produce,
                "nivel_reservatorio_l": round(self.nivel_reservatorio, 3)
            })
            self.publicar(self.topico_enviar, msg)
            self.log(f"🌀✅ Produção concluída e enviada ao Filler: {litros} L ({bottles_to_produce} garrafas).")

            time.sleep(0.2)


    def processar_mensagem(self, mensagem):
        try:
            data = json.loads(mensagem)
        except Exception:
            self.log("❌ Mensagem inválida (não é JSON).")
            return

        if "command" in data:
            cmd = str(data.get("command", "")).upper()
            if cmd == "OPERAR":
                self.operar()
                return
            elif cmd == "PARAR":
                self.parar_operacao()
                return

        origem = data.get("origem", "")

        if origem == "Feeder":
            estoque = data.get("nivelEstoque")
            if estoque is not None:
                with self.lock:
                    self.feeder_estoque = int(estoque)
                    self.recebeu_feeder_status = True
                self.log(f"📥 Atualizado estoque do Feeder: {self.feeder_estoque} garrafas.")

        elif origem == "Filler":
            nivel = data.get("nivel_litros")
            if nivel is not None:
                with self.lock:
                    self.nivel_reservatorio = float(nivel)
                    self.recebeu_filler_status = True
                self.log(f"📥 Atualizado nível do reservatório do Filler: {self.nivel_reservatorio:.3f} L.")

        else:
            self.log(f"Mensagem recebida (não processada): {data}")

    def alertar_controlador(self, tipo_alerta, info=None):
        payload = {"origem": "Mixer", "alerta": tipo_alerta, "nivel_reservatorio_l": self.nivel_reservatorio}
        if info:
            payload.update(info)
        self.publicar(self.topico_alerta, json.dumps(payload))
