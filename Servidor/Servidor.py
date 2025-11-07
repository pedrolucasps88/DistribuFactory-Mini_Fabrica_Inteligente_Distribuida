from Bridge import Bridge
import time

if __name__ == "__main__":
    bridge = Bridge()
    bridge.start()

    print("[Servidor] 🧠 Rodando e aguardando mensagens...")
    while True:
        time.sleep(1)
