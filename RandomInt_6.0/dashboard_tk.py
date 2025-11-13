import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
import time

LB_URL = "http://127.0.0.1:8080"

servers = ["Server1", "Server2", "Server3"]

status_data = {s: "??" for s in servers}
weight_data = {s: 0 for s in servers}
stats_data = {s: 0 for s in servers}

# --- Atualização de dados --- #
def atualizar_dados():
    while True:
        try:
            resp = requests.get(f"{LB_URL}/").text
            for s in servers:
                if f"{s}:" in resp:
                    part = resp.split(f"{s}:")[1].split("\n")[0]
                    status = "ON" if "ON" in part else "OFF"
                    weight = int(part.split("Peso:")[-1].strip()) if "Peso:" in part else 0
                    reqs = int(part.split("(")[1].split("reqs")[0].strip()) if "(" in part else 0
                    status_data[s] = status
                    weight_data[s] = weight
                    stats_data[s] = reqs
            atualizar_interface()
        except Exception:
            for s in servers:
                status_data[s] = "??"
            atualizar_interface()
        time.sleep(3)

# --- Atualização visual --- #
def atualizar_interface():
    for s in servers:
        labels_status[s].config(
            text=f"{s}: {status_data[s]}",
            fg=("lime" if status_data[s] == "ON" else "red")
        )
        labels_weight[s].config(text=f"Peso atual: {weight_data[s]}")
        labels_reqs[s].config(text=f"Requisições: {stats_data[s]}")

# --- Alterar pesos de todos os servidores --- #
def aplicar_todos():
    try:
        for s in servers:
            valor = entries[s].get().strip()
            if not valor:
                continue
            valor = int(valor)
            if valor < 0 or valor > 100:
                messagebox.showwarning("Valor inválido", f"O peso de {s} deve estar entre 0 e 100.")
                return
            resp = requests.get(f"{LB_URL}/set_weight?server={s}&weight={valor}")
            if resp.status_code == 200:
                print(f"[UPDATE] Peso de {s} alterado para {valor}")
        messagebox.showinfo("Sucesso", "Pesos atualizados com sucesso!")
    except ValueError:
        messagebox.showwarning("Valor inválido", "Digite apenas números inteiros.")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao se comunicar com o Load Balancer.\n{e}")

# --- Ligar/Desligar servidor (simulação de falha) --- #
def ligar_server(server):
    try:
        resp = requests.get(f"{LB_URL}/start_server?server={server}")
        messagebox.showinfo("Servidor", resp.json().get("message", ""))
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível ligar {server}.\n{e}")

def desligar_server(server):
    try:
        resp = requests.get(f"{LB_URL}/stop_server?server={server}")
        messagebox.showinfo("Servidor", resp.json().get("message", ""))
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível desligar {server}.\n{e}")

def gerar_numeros():
    try:
        qtd = int(entry_qtd.get())
        if qtd <= 0:
            messagebox.showwarning("Valor inválido", "Digite uma quantidade positiva.")
            return

        output_box.configure(state="normal")
        output_box.delete("1.0", "end")
        output_box.insert("end", f"🔹 Gerando {qtd} números aleatórios...\n\n")

        contagem = {s: 0 for s in servers}

        for i in range(qtd):
            try:
                resp = requests.get(f"{LB_URL}/generate", timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    numero = data.get("number", "??")
                    origem = data.get("from_server", "??")
                    via = data.get("request_to", "??")
                    contagem[origem] += 1
                    output_box.insert("end", f"{i+1:2}. Número: {numero:3} | Servidor: {origem} | Via: {via}\n")
                else:
                    output_box.insert("end", f"{i+1:2}. Erro na requisição ({resp.status_code})\n")
            except Exception as e:
                output_box.insert("end", f"{i+1:2}. Falha: {e}\n")

            output_box.see("end")
            time.sleep(0.5)

        output_box.insert("end", "\nResumo de uso dos servidores:\n")
        for s, c in contagem.items():
            output_box.insert("end", f" - {s}: {c} requisições\n")

        output_box.insert("end", "\n✅ Concluído!\n")
        output_box.configure(state="disabled")

    except ValueError:
        messagebox.showwarning("Valor inválido", "Digite um número inteiro.")

# --- Interface Tkinter --- #
root = tk.Tk()
root.title("RandomInt - Painel de Controle")
root.geometry("640x420")
root.resizable(False, False)
root.configure(bg="#1e1e1e")

title = tk.Label(root, text="Painel de Controle RandomInt", font=("Segoe UI", 14, "bold"), bg="#1e1e1e", fg="white")
title.pack(pady=10)

frame = tk.Frame(root, bg="#1e1e1e")
frame.pack(pady=10)

labels_status, labels_weight, labels_reqs, entries = {}, {}, {}, {}

for i, s in enumerate(servers):
    tk.Label(frame, text=s, font=("Segoe UI", 12, "bold"), bg="#1e1e1e", fg="#00ffff").grid(row=i, column=0, padx=10, pady=5, sticky="w")

    labels_status[s] = tk.Label(frame, text="Status: --", bg="#1e1e1e", fg="gray")
    labels_status[s].grid(row=i, column=1, padx=10)

    labels_weight[s] = tk.Label(frame, text="Peso atual: --", bg="#1e1e1e", fg="white")
    labels_weight[s].grid(row=i, column=2, padx=10)

    labels_reqs[s] = tk.Label(frame, text="Requisições: 0", bg="#1e1e1e", fg="white")
    labels_reqs[s].grid(row=i, column=3, padx=10)

    tk.Label(frame, text="Novo Peso:", bg="#1e1e1e", fg="white").grid(row=i, column=4)
    entries[s] = tk.Entry(frame, width=6, justify="center")
    entries[s].grid(row=i, column=5, padx=5)

    btn_on = tk.Button(frame, text="Ligar", command=lambda srv=s: ligar_server(srv),
                       bg="#008000", fg="white", relief="raised", width=8)
    btn_on.grid(row=i, column=6, padx=3)

    btn_off = tk.Button(frame, text="Desligar", command=lambda srv=s: desligar_server(srv),
                        bg="#800000", fg="white", relief="raised", width=8)
    btn_off.grid(row=i, column=7, padx=3)

btn_aplicar_todos = tk.Button(root, text="Aplicar todos os pesos", command=aplicar_todos,
                              bg="#00aa00", fg="white", font=("Segoe UI", 11, "bold"), width=25)
btn_aplicar_todos.pack(pady=15)

# --- Seção de geração de números --- #
separator = tk.Label(root, text="─" * 60, bg="#1e1e1e", fg="gray")
separator.pack(pady=5)

section_title = tk.Label(root, text="Gerar números aleatórios", bg="#1e1e1e", fg="#00ffff", font=("Segoe UI", 12, "bold"))
section_title.pack(pady=5)

frame_gen = tk.Frame(root, bg="#1e1e1e")
frame_gen.pack()

tk.Label(frame_gen, text="Quantidade:", bg="#1e1e1e", fg="white").grid(row=0, column=0, padx=5)
entry_qtd = tk.Entry(frame_gen, width=5, justify="center")
entry_qtd.insert(0, "10")
entry_qtd.grid(row=0, column=1, padx=5)

tk.Button(frame_gen, text="Gerar", bg="#0077cc", fg="white", relief="raised",
          command=lambda: threading.Thread(target=gerar_numeros, daemon=True).start()
).grid(row=0, column=2, padx=10)

output_box = tk.Text(root, height=20, width=65, bg="#101010", fg="#00ff99", font=("Consolas", 10))
output_box.pack(pady=10)
output_box.insert("end", "Resultados aparecerão aqui...\n")
output_box.configure(state="disabled")


footer = tk.Label(root, text="Atualizando a cada 3s", bg="#1e1e1e", fg="gray", font=("Segoe UI", 9))
footer.pack(pady=5)

threading.Thread(target=atualizar_dados, daemon=True).start()
root.mainloop()
