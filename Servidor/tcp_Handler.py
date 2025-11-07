import socket
import threading
import json

class TCPHandler:
    def __init__(self, host='127.0.0.1', port=9000, on_data_callback=None):
        self.host = host
        self.port = port
        self.on_data_callback = on_data_callback
        self.client_conn = None

    def start(self):
        threading.Thread(target=self._listen, daemon=True).start()

    def _listen(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen(1)
            print(f"[TCP] 🔌 Aguardando conexão do controlador em {self.port}...")
            self.client_conn, addr = s.accept()
            print(f"[TCP] ✅ Controlador conectado de {addr}")

            with self.client_conn:
                while True:
                    data = self.client_conn.recv(1024)
                    if not data:
                        break
                    try:
                        msg = json.loads(data.decode())
                        if self.on_data_callback:
                            self.on_data_callback(msg)
                    except json.JSONDecodeError:
                        print("[TCP] ❌ Erro ao decodificar mensagem recebida.")

    def send(self, data):
        if self.client_conn:
            self.client_conn.sendall(json.dumps(data).encode())
