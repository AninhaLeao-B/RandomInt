import subprocess
import time
import os
import platform
import sys
import threading

# Força UTF-8 para evitar erros de codificação no Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass

IS_WINDOWS = platform.system() == "Windows"

processes = {
    "Server1": None,
    "Server2": None,
    "Server3": None,
    "LoadBalancer": None
}

# =========================
# Funções de inicialização
# =========================

def run_server(server_id, port):
    env = os.environ.copy()
    env["SERVER_ID"] = server_id
    env["SERVER_PORT"] = str(port)
    print(f"[START] {server_id} na porta {port}")
    return subprocess.Popen(
        ["python", "server.py"],
        env=env,
        cwd=os.getcwd(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT
    )

def run_lb():
    print("[START] Load Balancer na porta 8080")
    return subprocess.Popen(
        ["python", "load_balancer.py"],
        cwd=os.getcwd(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT
    )

# =========================
# Controle de processos
# =========================

def stop_process(name):
    proc = processes.get(name)
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        processes[name] = None
        print(f"[STOP] {name} encerrado.")
    else:
        print(f"[INFO] {name} não está em execução.")

def start_server(name):
    """Inicia um servidor individualmente"""
    if name == "LoadBalancer":
        if processes[name] and processes[name].poll() is None:
            print("[INFO] Load Balancer já está rodando.")
            return
        processes[name] = run_lb()
    else:
        ports = {"Server1": 5001, "Server2": 5002, "Server3": 5003}
        if processes[name] and processes[name].poll() is None:
            print(f"[INFO] {name} já está rodando.")
            return
        processes[name] = run_server(name, ports[name])

def stop_server(name):
    """Para um servidor individualmente"""
    stop_process(name)

def start_all():
    for s in ["Server1", "Server2", "Server3"]:
        start_server(s)
    time.sleep(2)
    start_server("LoadBalancer")
    time.sleep(2)
    print("\n✅ Todos os serviços foram iniciados!\n")

def stop_all():
    for name in list(processes.keys()):
        stop_process(name)
    print("\n🛑 Todos os serviços foram encerrados.")

def restart_all():
    print("\n🔄 Reiniciando todos os serviços...")
    stop_all()
    time.sleep(2)
    start_all()

# =========================
# Testes e Status
# =========================

def test_requests():
    print("\n[TESTE] Enviando 10 requisições pro Load Balancer...\n")
    subprocess.run(["python", "client.py"])

def status():
    print("\n📊 Status atual dos serviços:\n")
    for name, proc in processes.items():
        estado = "🟢 Rodando" if proc and proc.poll() is None else "🔴 Parado"
        print(f" - {name:<13} {estado}")
    print("")

# =========================
# Simulação de Falha
# =========================

def simulate_failure(server_name="Server2", downtime=10):
    """Simula uma falha temporária em um servidor"""
    if server_name not in processes or server_name == "LoadBalancer":
        print("❌ Escolha um servidor válido (Server1, Server2 ou Server3).")
        return

    def _simulate():
        print(f"\n⚠️  Simulando falha em {server_name} por {downtime} segundos...")
        stop_server(server_name)
        for i in range(downtime):
            time.sleep(1)
            print(f"   {downtime - i:2}s restantes...", end="\r")
        print(f"\n♻️  Restaurando {server_name}...")
        start_server(server_name)
        print(f"✅ {server_name} voltou a operar normalmente!\n")

    # Roda em thread separada pra não travar o menu
    threading.Thread(target=_simulate, daemon=True).start()

# =========================
# Menus interativos
# =========================

def show_main_menu():
    print("""
=============================
⚙️  RandDistri - Gerenciador
=============================
1️⃣  Iniciar todos os serviços
2️⃣  Parar todos os serviços
3️⃣  Reiniciar todos os serviços
4️⃣  Gerar números aletórios
5️⃣  Ver status dos serviços
6️⃣  Gerenciar servidores individualmente
7️⃣  Simular falha temporária
0️⃣  Sair
""")

def show_server_menu():
    print("""
=============================
🔧  Gerenciar Servidores
=============================
1️⃣  Iniciar um servidor específico
2️⃣  Parar um servidor específico
3️⃣  Voltar ao menu principal
""")

def choose_server():
    print("""
Escolha o servidor:
1️⃣  Server1
2️⃣  Server2
3️⃣  Server3
4️⃣  LoadBalancer
0️⃣  Cancelar
""")
    opt = input("→ ").strip()
    mapping = {"1": "Server1", "2": "Server2", "3": "Server3", "4": "LoadBalancer"}
    return mapping.get(opt)

# =========================
# Loop principal
# =========================

if __name__ == "__main__":
    while True:
        show_main_menu()
        choice = input("Escolha uma opção: ").strip()

        if choice == "1":
            start_all()
        elif choice == "2":
            stop_all()
        elif choice == "3":
            restart_all()
        elif choice == "4":
            test_requests()
        elif choice == "5":
            status()
        elif choice == "6":
            while True:
                show_server_menu()
                sub_choice = input("Escolha uma opção: ").strip()
                if sub_choice == "1":
                    s = choose_server()
                    if s: start_server(s)
                elif sub_choice == "2":
                    s = choose_server()
                    if s: stop_server(s)
                elif sub_choice in ["3", "0"]:
                    break
                else:
                    print("❌ Opção inválida.")
        elif choice == "7":
            print("\n💥 Simulação de falha:")
            s = choose_server()
            if s and s != "LoadBalancer":
                t = input("Tempo da falha em segundos (padrão 10): ").strip()
                downtime = int(t) if t.isdigit() else 10
                simulate_failure(s, downtime)
            else:
                print("❌ Não é possível simular falha no Load Balancer.")
        elif choice == "0":
            print("\nEncerrando o gerenciador...")
            stop_all()
            sys.exit(0)
        else:
            print("❌ Opção inválida, tente novamente.\n")
