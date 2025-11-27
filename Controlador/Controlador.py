import socket
import json
import threading
from tkinter import *
from tkinter import ttk
from queue import Queue, Empty
from PIL import Image, ImageTk


class ControladorTCP:
    def __init__(self, gui_callback, host='127.0.0.1', port=9000):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.gui_callback = gui_callback
        self.conectado = False

    def conectar(self):
        try:
            self.socket.connect((self.host, self.port))
            self.conectado = True
            print(f"[Controlador] ✅ Conectado ao servidor TCP ({self.host}:{self.port})")
            threading.Thread(target=self._ouvir, daemon=True).start()
        except Exception as e:
            print(f"[Controlador] ❌ Erro ao conectar: {e}")

    def _ouvir(self):
        while self.conectado:
            try:
                data = self.socket.recv(2048)
                if not data:
                    break
                msg = json.loads(data.decode())
                print(f"[Controlador] 📥 Recebido: {msg}")
                self.gui_callback(msg)
            except:
                pass

    def enviar_comando(self, maquina, comando, quantidade=None):
        if not self.conectado:
            return
        msg = {"maquina": maquina, "comando": comando}
        if quantidade is not None:
            msg["quantidade"] = quantidade
        try:
            self.socket.sendall(json.dumps(msg).encode())
            print(f"[Controlador] 📤 Enviado: {msg}")
        except:
            print("[C1''ontrolador] ⚠️ Falha ao enviar comando.")


class InterfaceControlador:
    def __init__(self, root):
        self.root = root
        self.root.title("Painel do Controlador - DistribuFactory")
        self.root.geometry("1100x700")
        self.root.configure(bg="#0d1117")

        self.queue_event = Queue()
        self.garrafas = []
        self.para_Empacotar = []
        self.caixas = []
        self.caixa_img = PhotoImage(file="assets/pacote.png")
        self.gotas = []
        self.Contador = {"garrafas_totais": 0, "pacotes_totais": 0 , "emergencias_totais":0, "Mixer_enviou":0}
        self.ta_emergencia = False
        self.garrafa_imagens = {
            "empty": PhotoImage(file="assets\garrafa_vazia.png"),
            "full": PhotoImage(file="assets\garrafa_cheia.png"),
        }
        self.maquinas_imagens = {
            "feeder": self.carregar_imagem_redimensionada("assets/Feeder_img.png"),
            "mixer": self.carregar_imagem_redimensionada("assets/Mixer_img.png"),
            "filler": self.carregar_imagem_redimensionada("assets/Filler_img.png"),
            "packer": self.carregar_imagem_redimensionada("assets/Packer_img.png"),
        }
        self.alarme_imagem = PhotoImage(file="assets\\alarm.png")
        self.alarme_widget = None
        self.estado_alarme_piscando = False
        self._build_ui()
        self.controlador = ControladorTCP(self.ouvir_Mensagens_servidor)
        threading.Thread(target=self.controlador.conectar, daemon=True).start()

        self._loop_atualizar()

    def _build_ui(self):
        main = Frame(self.root, bg="#0d1117")
        main.pack(fill=BOTH, expand=True)

        self.canvas = Canvas(main, bg="#111827", highlightthickness=0)
        self.canvas.pack(side=TOP, fill=BOTH, expand=True, pady=(10, 0))
        
        bottom_frame = Frame(self.root, bg="#121212", height=200) 
        bottom_frame.pack(side=BOTTOM, fill=X)
        
        ctrl_frame = Frame(bottom_frame, bg="#121212")
        ctrl_frame.pack(side=LEFT, padx=80, pady=10)

        Label(ctrl_frame, text="Controles", bg="#121212", fg="#e6edf3",
            font=("Segoe UI", 14, "bold")).pack(anchor="w")

        ttk.Style().configure("TButton", padding=6, font=("Segoe UI", 10, "bold"))
        ttk.Style().map("TButton", background=[("active", "#1f6feb")])

        Button(ctrl_frame, text="🔹 Ligar Feeder", command=lambda: self._cmd("feeder", "OPERAR")).pack(fill=X, pady=2)
        Button(ctrl_frame, text="🔹 Repor Feeder", command=self._repor_feeder).pack(fill=X, pady=2)
        Button(ctrl_frame, text="⚡ Ligar Tudo", command=self._ligar_tudo).pack(fill=X, pady=2)
        Button(ctrl_frame, text="🆘 Emergência", bg="#b91c1c", fg="white", command=self._emergencia).pack(fill=X, pady=2)

        status_frame = Frame(bottom_frame, bg="#121212")
        status_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=20, pady=10)

        logs_status_frame = Frame(status_frame, bg="#121212")
        logs_status_frame.pack(fill=X)


        log_frame = Frame(logs_status_frame, bg="#121212", width=750)
        log_frame.pack(side=LEFT, fill=Y)
        
        log_frame.pack_propagate(False)

        self.log_text = Text(log_frame, bg="#1e1e1e", fg="#a3a3a3", height=8,
                            relief=FLAT, wrap=WORD)
        self.log_text.pack(fill=BOTH, expand=True, pady=(10, 0))
        self.log_text.insert(END, "🔌 Aguardando conexão...\n")

        status_info_frame = Frame(logs_status_frame, bg="#121212", width=200)
        status_info_frame.pack(side=LEFT, fill=Y, padx=(10, 0))


        Label(status_info_frame, text="Status da Produção", bg="#121212", fg="#e6edf3",
            font=("Segoe UI", 14, "bold")).pack(anchor="w")

        self.stats_label = Label(status_info_frame, bg="#121212", fg="#cbd5e1",
                                justify=LEFT, font=("Consolas", 11))
        self.stats_label.pack(anchor="w", pady=(5, 0))

        # Posições das máquinas
        self.x_feeder, self.x_filler, self.x_packer = 200, 500, 800
        self.y_base, self.y_mixer = 300, 100

        for name, x, y in [
            ("feeder", self.x_feeder, self.y_base),
            ("filler", self.x_filler, self.y_base),
            ("packer", self.x_packer, self.y_base),
            ("mixer", self.x_filler, self.y_mixer)
        ]:
            self.desenhar_maquina(name, x, y)

        self.atualizar_status_prod()

    def carregar_imagem_redimensionada(self, path, width=200, height=160):
        img = Image.open(path)
        img = img.resize((width, height), Image.LANCZOS)
        return ImageTk.PhotoImage(img)


    def desenhar_maquina(self, name, x, y):
        img_maq = self.canvas.create_image(x,y,image=self.maquinas_imagens[name])
        text = self.canvas.create_text(x, y+80, text=name.upper(),
                                       fill="#e6edf3", font=("Segoe UI", 11, "bold"))
        light = self.canvas.create_oval(x+40, y-60, x+60, y-40, fill="#27272a", outline="")
        setattr(self, f"{name}_light", light)
        setattr(self,f"{name}",img_maq)
        setattr(self, f"{name}_text", text)

    def ouvir_Mensagens_servidor(self, msg):
        if "payload" not in msg:
            return
        payload = msg["payload"]
        self.queue_event.put(("msg", payload))

    def eventos_fila(self):
        try:
            while True:
                kind, payload = self.queue_event.get_nowait()
                if kind == "msg":
                    self.resposta_Mensagens(payload)
                elif kind == "visual":
                    typ, val = payload
                    if typ == "package_packed":
                        self.para_Empacotar = [1]
        except Empty:
            pass

    def resposta_Mensagens(self, text):
        t_lower = text.lower()
        self._log(text)

        if "feeder" in t_lower and "desligando" in t_lower and "estoque" in t_lower:
            self.canvas.itemconfig(self.feeder_light, fill="#b91c1c")
            return  
        
        elif "garrafa" in t_lower and "pronta" in t_lower:
            self.desenhar_garrafa("feeder")
            self.queue_event.put(("visual", ("move_to_filler", None)))

        elif "garrafa" in t_lower and "cheia" in t_lower:
            self.Contador["garrafas_totais"] += 1
            self.atualizar_status_prod()
            self.desenhar_garrafa("filler")
            self.queue_event.put(("visual", ("move_to_packer", None)))


        elif "caixa" in t_lower and "empacot" in t_lower:
            self.Contador["pacotes_totais"] += 1
            self.atualizar_status_prod()
            self.queue_event.put(("visual", ("package_packed", None)))

        elif "enviou" in t_lower and "mixer" in t_lower:
            self._log("Mixer transferiu líquido ao Filler 💧")
            self.Contador["Mixer_enviou"] += 1
            self.atualizar_status_prod()
            x = self.x_filler
            y = self.y_mixer + 40
            drop = self.canvas.create_oval(x - 10, y - 10, x + 10, y + 10,
                                        fill="#c27e26", outline="")
            self.gotas.append({"id": drop, "x": x, "y": y})

    def atualizar_status_prod(self):
        t = f"""
 🍾Garrafas cheias:  {self.Contador['garrafas_totais']}
 📦Caixas embaladas: {self.Contador['pacotes_totais']}
 🚨Emergencias: {self.Contador['emergencias_totais']}
 💧Mixer enviou liquido: {self.Contador['Mixer_enviou']}
        """
        self.stats_label.config(text=t)

    def desenhar_garrafa(self, origem_maquina):
        coords = {
            "feeder": (self.x_feeder + 60, self.y_base),
            "filler": (self.x_filler + 60, self.y_base),
            "packer": (self.x_packer + 60, self.y_base)
        }
        x, y = coords.get(origem_maquina, (self.x_feeder, self.y_base))

        def criar_Garrafa():
            try:
                if origem_maquina == "feeder":
                    img = self.garrafa_imagens["empty"]
                else:
                    img = self.garrafa_imagens["full"]

                bottle_id = self.canvas.create_image(x, y, image=img, anchor="s")
                sprite = {"id": bottle_id, "x": x, "y": y, "origem": origem_maquina}
                self.garrafas.append(sprite)
            except Exception as e:
                print("Erro ao criar imagem, usando oval:", e)
                bottle = self.canvas.create_oval(x - 6, y - 12, x + 6, y, fill="#38bdf8", outline="")
                sprite = {"id": bottle, "x": x, "y": y, "origem": origem_maquina}
                self.garrafas.append(sprite)

        self.root.after(0, criar_Garrafa)

    def _animacao_emergencia(self):
        if not self.ta_emergencia:
            if self.alarme_widget is not None:
                self.canvas.delete(self.alarme_widget)
                self.alarme_widget = None
            return
        
        if self.alarme_widget is None:
            self.alarme_imagem = PhotoImage(file="assets/alarm.png").zoom(3, 3)
            self.alarme_widget = self.canvas.create_image(
                self.x_packer + 250,
                self.y_base - 250,
                image=self.alarme_imagem
            )
            self.estado_alarme_piscando = True

        #(piscar)
        self.estado_alarme_piscando = not self.estado_alarme_piscando
        self.canvas.itemconfig(
            self.alarme_widget,
            state="normal" if self.estado_alarme_piscando else "hidden"
        )

        # repete o piscar
        self.root.after(500, self._animacao_emergencia)




    def animacoes(self):
        para_remover = []
        for b in self.garrafas:
            b["x"] += 12  
            self.canvas.move(b["id"], 12, 0)

            # garrafa do feeder some um pouco depois do filler
            if b.get("origem") == "feeder" and b["x"] > self.x_filler:
                para_remover.append(b)

            # garrafa do filler some um pouco depois do packer
            elif b.get("origem") == "filler" and b["x"] > self.x_packer :
                para_remover.append(b)

        for b in para_remover:
            self.canvas.delete(b["id"])
            self.garrafas.remove(b)

        # animação das gotas (mixer → filler)
        para_remover_gotas = []
        for d in self.gotas:
            # velocidade vertical controlada
            d["y"] += 8
            self.canvas.move(d["id"], 0, 8)

            # quando chega na altura do filler, apaga e mostra splash
            if d["y"] >= self.y_base - 20:
                para_remover_gotas.append(d)

        for d in para_remover_gotas:
            x, y = d["x"], d["y"]
            self.canvas.delete(d["id"])
            self.gotas.remove(d)
            splash = self.canvas.create_oval(x - 20, y - 10, x + 20, y + 10,
                                            fill="#c27e26", outline="")
            self.root.after(200, lambda s=splash: self.canvas.delete(s))


            # pequena animação de fade
            def fade_out(s=splash, alpha=1.0):
                if alpha > 0:
                    color = f"#{int(14*alpha):02x}{int(165*alpha):02x}{int(233*alpha):02x}"
                    self.canvas.itemconfig(s, fill=color)
                    self.root.after(80, lambda: fade_out(s, alpha - 0.1))
                else:
                    self.canvas.delete(s)
            fade_out()

        if self.para_Empacotar:
            self.para_Empacotar.pop()
            base_x = self.x_packer + 120  
            base_y = self.y_base - 40

            CAIXAS_POR_LINHA = 5

            indice = len(self.caixas)
            linha = indice // CAIXAS_POR_LINHA
            coluna = indice % CAIXAS_POR_LINHA

            x = base_x + (coluna * 35)
            y = base_y + (linha * 40)

            caixa_id = self.canvas.create_image(x, y, image=self.caixa_img, anchor="s")

            self.caixas.append({"id": caixa_id, "x": x, "y": y})



    def _loop_atualizar(self):
        self.eventos_fila()
        self.animacoes()
        self.root.after(80, self._loop_atualizar)

    def _cmd(self, maquina, comando):
        self.controlador.enviar_comando(maquina, comando)
        self._log(f"Enviado comando: {maquina.upper()} → {comando}")

        if maquina=="feeder" and comando == "OPERAR":
            self.canvas.itemconfig(getattr(self, f"{"feeder"}_light"), fill="#22c55e")

    def _repor_feeder(self):
        quantidade = 10 
        self.controlador.enviar_comando("feeder", "REPOR", quantidade=quantidade)
        self._log(f"Enviado comando: FEEDER → REPOR ({quantidade} garrafas)")


    def _ligar_tudo(self):
        self.ta_emergencia = False
        self._animacao_emergencia()
        for m in ["feeder", "mixer", "filler", "packer"]:
            self._cmd(m, "OPERAR")
            for name in ["feeder", "mixer", "filler", "packer"]:
                self.canvas.itemconfig(getattr(self, f"{name}_light"), fill="#22c55e")

    def _emergencia(self):
        self.ta_emergencia = True
        self._animacao_emergencia()
        self.Contador["emergencias_totais"] += 1
        self.atualizar_status_prod()
        for m in ["feeder", "mixer", "filler", "packer"]:
            self._cmd(m, "PARAR")
        for name in ["feeder", "mixer", "filler", "packer"]:
            self.canvas.itemconfig(getattr(self, f"{name}_light"), fill="#b91c1c")
        self._log("🚨 Emergência acionada! Todas as máquinas paradas.")

    def _log(self, text):
        self.log_text.insert(END, text + "\n")
        self.log_text.see(END)


if __name__ == "__main__":
    root = Tk()
    app = InterfaceControlador(root)
    root.mainloop()
