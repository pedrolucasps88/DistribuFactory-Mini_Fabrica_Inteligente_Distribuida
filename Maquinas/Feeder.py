from Maquinas.Maquina_base import Maquina_base
import json
import time
import threading

class Feeder(Maquina_base):

    def __init__(self,nome,broker,port,client_id,nivelEstoque,status="ativo"):
        super().__init__(nome, broker, port,client_id,status)
        self.velocidade = 2 
        self.nivelEstoque = nivelEstoque
        self.estoqueMinimo = 3
        self.garrafas_produzidas = 0
        self.produzindo = False

        self.topico_comando = "factory/feeder/in"
        self.topico_estoque_status = "factory/feeder/status" 
        self.topico_enviar = "factory/mixer/in"
        self.topico_filler = "factory/filler/in"
        self.topico_alerta = "factory/controlador/in"

    def iniciar(self):
        self.conectar_broker()
        self.assinar_topico(self.topico_comando)
        self.log("🧪 Feeder pronto — inscrito no tópico de comandos.")

    def operar(self):
        
        if self.produzindo:
            self.log("⚙️ Produção já em andamento.")
            return

        if self.nivelEstoque <= 0:
            self.log("🚫 Sem garrafas no estoque! Reponha antes de iniciar.")
            return
        
        self.produzindo = True
        self.log("🟢 Iniciando produção de garrafas.")
        threading.Thread(target=self.producao, daemon=True).start()


    def parar_operacao(self):
        self.produzindo = False
        self.log("🔴 Produção parada.")

    def producao(self):
        while self.produzindo:
            if self.status != "ativo":
                time.sleep(1)
                continue

            if self.nivelEstoque <= 0:
                self.log("⚠️ Estoque de garrafas vazio, parando produção.")
                self.alertar_controlador("estoque_vazio")
                self.produzindo = False
                break

            self.nivelEstoque -= 1
            self.garrafas_produzidas += 1
            msg = json.dumps({
                "origem": "Feeder",
                "evento": "garrafa_pronta",
                "id": self.garrafas_produzidas
            })
             
            status_msg = json.dumps( {
                "origem": "Feeder",
                "evento": "status_estoque",
                "nivelEstoque": self.nivelEstoque
            })

            self.publicar(self.topico_filler, msg)
            self.publicar(self.topico_estoque_status, status_msg)

            self.log(f"🧃✅ Garrafa #{self.garrafas_produzidas} enviada. Estoque restante: {self.nivelEstoque}")
            time.sleep(3)

            if self.nivelEstoque <= self.estoqueMinimo:
                self.alertar_controlador("estoque_baixo")

            time.sleep(self.velocidade)

    def repor_estoque(self,valor=10):
        self.nivelEstoque += valor
        self.log(f"🧃✅ Estoque reposto em +{valor}. Total: {self.nivelEstoque}")
    
    def estoque_atual(self):
        return self.nivelEstoque
    
    def processar_mensagem(self, mensagem):
        try:
            data = json.loads(mensagem)
            comando = data.get("command", "").upper()
        except json.JSONDecodeError:
            self.log("❌ Mensagem inválida (não é JSON).")
            return
        
        match comando:
            case "OPERAR":
                self.operar()
            case "PARAR":
                self.parar_operacao()               
            case "REPOR":
                qtd = int(data.get("quantidade", 0))
                self.repor_estoque(qtd)
            case _:
                self.log(f"⚠️ Comando desconhecido: {comando}")


    def alertar_controlador(self, tipo_alerta):
        msg = json.dumps({
            "origem": "Feeder",
            "alerta": tipo_alerta,
            "estoque": self.nivelEstoque
        })
        self.publicar(self.topico_alerta, msg)
                
