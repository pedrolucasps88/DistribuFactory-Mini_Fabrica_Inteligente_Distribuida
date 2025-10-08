# 🏭 DistribuFactory — Fábrica Distribuída de Engarrafamento

Simulação de uma **mini fábrica de engarrafamento inteligente**, conectada por **MQTT** e controlada remotamente via **TCP/GUI**.  
O projeto demonstra, de forma prática, os **conceitos de sistemas distribuídos**, aplicados em um ambiente industrial simulado.

---

## 🚀 Visão Geral

**DistribuFactory** representa uma pequena **linha de produção automatizada**, composta por máquinas IoT simuladas que se comunicam com um **servidor central**.  
O servidor monitora os processos, detecta falhas e permite que um **operador humano**, através de uma interface de controle, **tome decisões** sobre o andamento da produção.

🧠 O objetivo é mostrar na prática como sistemas distribuídos podem coordenar processos industriais — integrando **comunicação assíncrona (MQTT)** e **controle síncrono (TCP)**.

---

## ⚙️ Arquitetura do Sistema

```text
+------------------+        +---------------------+        +---------------------+
|   Máquinas MQTT  | <----> |  Servidor Central   | <----> | Controlador (GUI/TCP)|
| (Feeder, Mixer,  |        |  + Broker MQTT      |        |  + Interface Usuário |
|  Filler, etc.)   |        |  + Lógica de Falhas |        |  + Tomada de decisão |
+------------------+        +---------------------+        +---------------------+

````


### 🔸 Componentes principais

| Componente | Função |
|-------------|--------|
| **Máquinas simuladas (MQTT)** | Enviam leituras de sensores e status de operação. Geram eventos aleatórios de falha. |
| **Servidor central** | Atua como middleware: recebe mensagens MQTT, processa alertas e repassa decisões via TCP. |
| **Controlador (GUI)** | Interface do operador humano. Exibe status da fábrica e permite enviar ações corretivas. |

---

## 💬 Fluxo Simplificado

1. Máquinas publicam dados periódicos (temperatura, nível, status) via **MQTT**.  
2. O **servidor central** identifica falhas ou anomalias e notifica o **controlador humano**.  
3. O **operador** analisa o problema pela GUI e envia comandos (reiniciar, pausar, continuar).  
4. O servidor aplica a decisão e o processo segue normalmente.  

---

## ⚡ Tecnologias Utilizadas

| Categoria | Tecnologias |
|------------|-------------|
| **Linguagem principal** | Python |
| **Comunicação assíncrona** | MQTT (via `paho-mqtt`) |
| **Comunicação síncrona** | TCP (via `socket`) |
| **Interface gráfica** | Tkinter |
| **Broker MQTT** | Eclipse Mosquitto |
| **Extras** | threading, JSON, logging |

---

## 🧩 Estrutura do Projeto
```text
DistribuFactory/
├── maquinas/ # Simulação das máquinas MQTT
│ ├── maquina_base.py
│ ├── feeder.py
│ ├── mixer.py
│ └── filler.py
├── servidor/ # Lógica central e comunicação
│ ├── gerenciador_central.py
│ └── servidor_tcp.py
├── controlador/ # Interface do operador
│ ├── cliente_tcp_console.py
│ └── gui_tkinter.py
├── docs/ # Diagramas, relatórios e documentação
│ └── arquitetura.md
├── requirements.txt
└── README.md
```

---

## ⚠️ Tipos de Falhas Simuladas

| Evento | Causa simulada | Decisão esperada |
|---------|----------------|------------------|
| ⚠️ Temperatura alta | Sobrecarga do motor | Reduzir velocidade ou pausar linha |
| ❌ Falha no enchimento | Erro de sensor | Reiniciar máquina |
| 🧴 Reservatório vazio | Falta de insumo | Repor e reiniciar processo |
| 🔁 Máquina travada | Timeout de operação | Reset remoto |
| ✅ Normal | Operação padrão | Continuar produção |

---

## 🧠 Conceitos de Sistemas Distribuídos Aplicados

- **Concorrência e comunicação entre processos** (máquinas independentes e servidor).  
- **Mensageria e comunicação assíncrona** via MQTT.  
- **Coordenação centralizada e decisão distribuída** (operador humano).  
- **Tolerância a falhas** e simulação de recuperação.  
- **Escalabilidade** — novas máquinas podem ser adicionadas facilmente.  

---

## 🎮 Interface do Operador (GUI)

A interface gráfica exibirá:

- Estado atual das máquinas  
- Logs de eventos e falhas  
- Botões de ação: **Reiniciar**, **Pausar**, **Continuar**, **Manutenção**

---

## 🧠 Próximos Passos

- [ ] Implementar as máquinas MQTT básicas.  
- [ ] Criar servidor central com integração MQTT + TCP.  
- [ ] Desenvolver GUI simples para controle.  
- [ ] Simular falhas e decisões manuais.  

---

## 🧑‍💻 Autor

**Pedro Lucas Prado e Silva - Engenharia de Computação**  
Desenvolvido como projeto prático da disciplina de **Sistemas Distribuídos** — 2025  

> “Uma mini fábrica inteligente, totalmente conectada e controlada por decisões humanas distribuídas.”

---

⭐ **Curtiu o projeto?**  
Deixe uma estrela no repositório e acompanhe o desenvolvimento das próximas versões!  
