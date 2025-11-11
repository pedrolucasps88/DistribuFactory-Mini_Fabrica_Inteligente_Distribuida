import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import random
import time
import threading

class PainelControladorSimulado:
    def __init__(self, root):
        self.root = root
        self.root.title("Painel do Controlador - Simulação Visual")
        self.root.geometry("1200x700")
        self.root.configure(bg="#121212")

        self._montar_interface()
        self._iniciar_simulacao()

    def _montar_interface(self):
        # ======= Estilo geral =======
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton",
                        font=("Segoe UI", 11, "bold"),
                        foreground="white",
                        background="#1e1e1e",
                        padding=10)
        style.map("TButton", background=[("active", "#333333")])

        # ======= Título =======
        titulo = tk.Label(self.root,
                          text="⚙️ Painel de Controle - DistribuFactory",
                          font=("Segoe UI", 20, "bold"),
                          bg="#121212",
                          fg="#00bcd4")
        titulo.pack(pady=20)

        # ======= Frame principal =======
        frame_principal = tk.Frame(self.root, bg="#121212")
        frame_principal.pack(pady=10)

        # ======= Área das máquinas =======
        self.canvas = tk.Canvas(frame_principal,
                                width=1100,
                                height=450,
                                bg="#1a1a1a",
                                highlightthickness=0)
        self.canvas.pack()

        # ======= Coordenadas =======
        self.x_feeder = 150
        self.x_filler = 500
        self.x_packer = 850
        self.y_base = 300
        self.y_mixer = 150  # mixer acima do filler

        # ======= Imagens simuladas =======
        self.imagens = {}
        cores = {"feeder": (40, 60, 150), "filler": (70, 150, 70),
                 "mixer": (150, 100, 30), "packer": (120, 40, 120)}
        for nome, cor in cores.items():
            img = Image.new("RGB", (100, 100), cor)
            self.imagens[nome] = ImageTk.PhotoImage(img)

        # ======= Desenhar máquinas =======
        self._criar_maquina("feeder", self.x_feeder, self.y_base)
        self._criar_maquina("filler", self.x_filler, self.y_base)
        self._criar_maquina("packer", self.x_packer, self.y_base)
        self._criar_maquina("mixer", self.x_filler, self.y_mixer)

        # ======= Conexões visuais =======
        self._desenhar_conexoes()

        # ======= Indicadores =======
        self.label_pacotes = tk.Label(self.root,
                                      text="Pacotes produzidos: 0",
                                      bg="#121212",
                                      fg="white",
                                      font=("Segoe UI", 13))
        self.label_pacotes.pack(pady=10)
        self.pacotes = 0

        # ======= Frame de botões =======
        frame_botoes = tk.Frame(self.root, bg="#121212")
        frame_botoes.pack(pady=20)

        botoes = [
            ("Ligar Feeder", lambda: self._simular_ligar("feeder")),
            ("Ligar Mixer", lambda: self._simular_ligar("mixer")),
            ("Ligar Filler", lambda: self._simular_ligar("filler")),
            ("Ligar Packer", lambda: self._simular_ligar("packer")),
            ("Ligar Todas", self._ligar_todas),
            ("🚨 Emergência", self._emergencia)
        ]

        for texto, cmd in botoes:
            ttk.Button(frame_botoes, text=texto, command=cmd).pack(side="left", padx=10)

    def _criar_maquina(self, nome, x, y):
        """Cria imagem + nome + indicador"""
        self.canvas.create_image(x, y, image=self.imagens[nome])
        self.canvas.create_text(x, y + 70,
                                text=nome.upper(),
                                fill="white",
                                font=("Segoe UI", 11, "bold"))
        self.indicadores = getattr(self, "indicadores", {})
        self.indicadores[nome] = self.canvas.create_oval(
            x - 10, y - 60, x + 10, y - 40,
            fill="gray", outline="black"
        )

    def _desenhar_conexoes(self):
        """Desenha linhas conectando máquinas"""
        # Linha feeder → filler → packer
        self.canvas.create_line(self.x_feeder + 60, self.y_base,
                                self.x_filler - 60, self.y_base,
                                fill="#00bcd4", width=3, arrow=tk.LAST)
        self.canvas.create_line(self.x_filler + 60, self.y_base,
                                self.x_packer - 60, self.y_base,
                                fill="#00bcd4", width=3, arrow=tk.LAST)
        # Mixer → Filler (vertical)
        self.canvas.create_line(self.x_filler, self.y_mixer + 60,
                                self.x_filler, self.y_base - 60,
                                fill="#00bcd4", width=3, arrow=tk.LAST)

    def _simular_ligar(self, maquina):
        self.canvas.itemconfig(self.indicadores[maquina], fill="lime")
        print(f"[Simulação] {maquina.upper()} ligado!")
        if maquina == "packer":
            self.pacotes += random.randint(1, 3)
            self.label_pacotes.config(text=f"Pacotes produzidos: {self.pacotes}")

    def _ligar_todas(self):
        for nome in self.indicadores:
            self._simular_ligar(nome)

    def _emergencia(self):
        for nome in self.indicadores:
            self.canvas.itemconfig(self.indicadores[nome], fill="red")
        print("[Simulação] 🚨 Emergência ativada! Todas as máquinas paradas.")

    def _iniciar_simulacao(self):
        """Simula garrafas passando de uma máquina para outra"""
        def loop():
            while True:
                self._animar_fluxo()
                time.sleep(2)
        threading.Thread(target=loop, daemon=True).start()

    def _animar_fluxo(self):
        """Mostra uma 'garrafa' passando entre as máquinas"""
        y = self.y_base
        x_positions = [self.x_feeder, self.x_filler, self.x_packer]
        bola = self.canvas.create_oval(0, y - 5, 10, y + 5, fill="#00bcd4", outline="")
        for x in x_positions:
            self._mover_bola(bola, x)
        self.canvas.delete(bola)

        # Simula líquido do mixer → filler
        self._animar_fluxo_mixer()

    def _animar_fluxo_mixer(self):
        """Mostra líquido descendo do mixer até o filler"""
        x = self.x_filler
        y_top, y_bottom = self.y_mixer + 60, self.y_base - 60
        gota = self.canvas.create_oval(x - 5, y_top, x + 5, y_top + 10,
                                       fill="#009688", outline="")
        for y in range(y_top, y_bottom, 5):
            self.canvas.coords(gota, x - 5, y, x + 5, y + 10)
            self.root.update()
            time.sleep(0.02)
        self.canvas.delete(gota)

    def _mover_bola(self, bola, destino_x):
        """Move a bolinha de forma suave"""
        while True:
            x1, _, x2, _ = self.canvas.coords(bola)
            centro = (x1 + x2) / 2
            if centro >= destino_x:
                break
            self.canvas.move(bola, 5, 0)
            self.root.update()
            time.sleep(0.02)

# Executa o modo simulado
if __name__ == "__main__":
    root = tk.Tk()
    app = PainelControladorSimulado(root)
    root.mainloop()
