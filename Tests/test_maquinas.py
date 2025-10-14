# test_maquinas.py
import time
import threading
import json
import paho.mqtt.client as mqtt

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ajuste os imports para sua estrutura de pastas
from Maquinas.Feeder import Feeder
from Maquinas.Mixer import Mixer
from Maquinas.Filler import Filler
from Maquinas.Packer import Packer

BROKER = "broker.emqx.io"  # broker público
PORT = 1883

# Flag de parada global
estoque_acabou = threading.Event()

# --- Callback MQTT para escutar alerta do feeder ---
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        if payload.get("alerta") == "estoque_vazio":
            print("⚠️  Alerta recebido: estoque vazio — encerrando teste...")
            estoque_acabou.set()  # sinaliza para parar o loop principal
    except Exception as e:
        print("Erro ao processar mensagem:", e)

def main():
    print("🚀 Iniciando teste completo das máquinas...")

    # --- Instancia as máquinas ---
    feeder = Feeder("Feeder", BROKER, PORT, "feeder01", nivelEstoque=20)
    mixer = Mixer("Mixer", BROKER, PORT, "mixer01", capacidade_reservatorio_l=10.0, nivel_inicial_l=2.0)
    filler = Filler("Filler", BROKER, PORT, "filler01", capacidade_reservatorio_l=10.0, nivel_inicial_l=5.0)
    packer = Packer("Packer", BROKER, PORT, "packer01")

    # --- Cliente MQTT para escutar alertas ---
    listener = mqtt.Client(client_id="teste_listener")
    listener.on_message = on_message
    listener.connect(BROKER, PORT, 60)
    listener.subscribe("factory/controlador/in")
    listener.loop_start()

    # --- Conecta e inicia as máquinas ---
    feeder.conectar_broker()
    mixer.iniciar()
    filler.iniciar()
    packer.iniciar()

    feeder.operar()
    mixer.operar()
    filler.operar()
    packer.operar()

    # --- Espera até o alerta de estoque vazio ---
    print("🕒 Aguardando alerta de estoque vazio...")
    while not estoque_acabou.is_set():
        time.sleep(1)

    # --- Para todas as máquinas ---
    feeder.parar_operacao()
    mixer.parar_operacao()
    filler.parar_operacao()
    packer.parar_operacao()

    # --- Desconecta ---
    feeder.desconectar()
    mixer.desconectar()
    filler.desconectar()
    packer.desconectar()
    listener.loop_stop()
    listener.disconnect()

    print("✅ Teste concluído (estoque acabou).")

if __name__ == "__main__":
    main()
