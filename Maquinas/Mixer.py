from Maquina_base import Maquina_base
import json
import time
import threading

class Mixer(Maquina_base):
    def __init__(self, nome, broker, port, client_id, status="ativo"):
        super().__init__(nome, broker, port, client_id, status)

        self.produzindo = False
        self.nivel_filler = 0.0
        self.limite_minimo_filler = 2.0      
        self.quantidade_envio = 10.0         
        self.tempo_producao = 4.0            
        self.feeder_estoque = 50             

        self.topico_filler_status = "factory/filler/status"
        self.topico_enviar = "factory/filler/in"
        self.topico_alerta = "factory/controlador/in"
        self.topico_comando = "factory/mixer/in"
        self.topico_servidor = "factory/servidor/in"

    def iniciar(self):
        self.conectar_broker()
        self.assinar_topico(self.topico_filler_status)
        self.assinar_topico(self.topico_comando)
        self.client.loop_start()
        
        for _ in range(10):
            if self.client.is_connected():
                break
            time.sleep(0.5)
        
        self.log("🧪 Mixer iniciado e aguardando status do Filler.")
        self.publicar(self.topico_servidor, "[MIXER]-> Iniciei e pronto para responder ao Filler.")

    def processar_mensagem(self, mensagem):
        try:
            data = json.loads(mensagem)
        except:
            self.log("❌ Mensagem inválida (não é JSON).")
            return

        origem = data.get("origem", "")
        evento = data.get("evento", "")

        if "command" in data:
            cmd = str(data["command"]).upper()
            if cmd == "OPERAR":
                self.produzindo = True
                self.log("🟢 Mixer em modo automático (responde ao Filler).")
            elif cmd == "PARAR":
                self.produzindo = False
                self.log("🔴 Mixer parado manualmente.")
            return

        if origem == "Filler" and evento == "reservatorio":
            nivel = float(data.get("nivel_litros", 0))
            self.nivel_filler = nivel
            self.log(f"📥 Status do Filler recebido: {nivel:.2f} L")

            if self.produzindo and nivel < self.limite_minimo_filler:
                threading.Thread(target=self.produzir_e_enviar, daemon=True).start()

    def produzir_e_enviar(self):
        self.log(f"🧪 Iniciando produção de {self.quantidade_envio} L para reabastecer o Filler...")
        time.sleep(self.tempo_producao)
        msg = json.dumps({
            "origem": "Mixer",
            "evento": "liquido_pronto",
            "quantidade_litros": self.quantidade_envio
        })
        self.publicar(self.topico_enviar, msg)
        self.publicar(self.topico_servidor, f"[MIXER]-> enviou {self.quantidade_envio} L ao Filler.")
        self.log(f"💧 {self.quantidade_envio} L enviados ao Filler.")

    def alertar_controlador(self, tipo_alerta):
        payload = {"origem": "Mixer", "alerta": tipo_alerta}
        self.publicar(self.topico_alerta, json.dumps(payload))


if __name__ == "__main__":
    mixer = Mixer("Mixer", "broker.emqx.io", 1883, "Mixer")
    mixer.iniciar()
    while True:
        time.sleep(1)
