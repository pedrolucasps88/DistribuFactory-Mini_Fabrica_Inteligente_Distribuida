import socket
import json
import threading
import time

class ControladorTCP:
    def __init__(self, host='127.0.0.1', port=9000):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def conectar(self):
        self.socket.connect((self.host, self.port))
        print(f"[Controlador] ✅ Conectado ao servidor TCP ({self.host}:{self.port})")

        threading.Thread(target=self._ouvir, daemon=True).start()

    def _ouvir(self):
        while True:
            data = self.socket.recv(2048)
            if not data:
                break
            try:
                msg = json.loads(data.decode())
                print(f"[Controlador] 📥 Recebido do servidor: {json.dumps(msg, indent=2)}")
            except json.JSONDecodeError:
                print("[Controlador] ❌ Mensagem inválida recebida.")

    def enviar_comando(self, maquina, comando, quantidade=None):
        msg = {"maquina": maquina, "comando": comando}
        if quantidade is not None:
            msg["quantidade"] = quantidade

        self.socket.sendall(json.dumps(msg).encode())
        print(f"[Controlador] 📤 Enviado: {msg}")

if __name__ == "__main__":
    controlador = ControladorTCP()
    controlador.conectar()

    while True:
        print("\n--- MENU ---")
        print("1 - Operar feeder")
        print("2 - Parar Feeder")
        print("3 - Repor Feeder")
        print("4 - Operar Mixer")
        print("5 - Operar Filler")
        print("6 - operar packer")
        print("7 - Operar tudo")
        print("8 - Sair")
        opc = input("Escolha: ")

        if opc == "1":
            controlador.enviar_comando("feeder", "OPERAR")
        elif opc == "2":
            controlador.enviar_comando("feeder", "PARAR")
        elif opc == "3":
            qtd = int(input("Quantidade a repor: "))
            controlador.enviar_comando("feeder", "REPOR", quantidade=qtd)
        elif opc == "4":
            controlador.enviar_comando("mixer", "OPERAR")
        elif opc == "5":
            controlador.enviar_comando("filler", "OPERAR")
        elif opc == "6":
            controlador.enviar_comando("packer", "OPERAR")
        elif opc == "7":
            controlador.enviar_comando("filler", "OPERAR")
            time.sleep(1)
            controlador.enviar_comando("mixer", "OPERAR")
            time.sleep(1)
            controlador.enviar_comando("feeder", "OPERAR")
            time.sleep(1)
            controlador.enviar_comando("packer", "OPERAR")
        elif opc == "8":
            break

