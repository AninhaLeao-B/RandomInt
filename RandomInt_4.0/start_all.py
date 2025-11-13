# start_all.py (UTF-8 friendly)
import subprocess
import time
import os
import platform
import sys

# Reconfigura stdout/stderr para UTF-8 (evita UnicodeEncodeError no Windows)
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

def run_server(server_id, port):
    env = os.environ.copy()
    env["SERVER_ID"] = server_id
    env["SERVER_PORT"] = str(port)
    print(f"[START] {server_id} na porta {port}")
    return subprocess.Popen(
        ["python", "server.py"],
        env=env,
        cwd=os.getcwd(),
        stdout=subprocess.DEVNULL,  # evita encher buffer do processo no terminal
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

def start_all():
    if any(p and p.poll() is None for p in processes.values()):
        print("[WARN] Alguns serviços já estão rodando. Pare antes de iniciar novamente.")
        return

    processes["Server1"] = run_server("Server1", 5001)
    processes["Server2"] = run_server("Server2", 5002)
    processes["Server3"] = run_server("Server3", 5003)

    time.sleep(2)
    processes["LoadBalancer"] = run_lb()

    time.sleep(4)
    print("\n✅ Todos os serviços foram iniciados!")
    print("Dashboard: http://localhost:8080\n")

def stop_all():
    for name in list(processes.keys()):
        stop_process(name)
    print("\n🛑 Todos os serviços foram encerrados.")

def restart_all():
    print("\n🔄 Reiniciando todos os serviços...")
    stop_all()
    time.sleep(2)
    start_all()

def test_requests():
    print("\n[TESTE] Enviando 10 requisições pro Load Balancer...\n")
    for i in range(10):
        try:
            result = subprocess.run(
                ["curl", "http://localhost:8080/generate"],
                capture_output=True, text=True, timeout=5
            )
            print(f"{i+1:2}. {result.stdout.strip()}")
        except Exception as e:
            print(f"{i+1:2}. ERRO: {e}")
        time.sleep(1)
    print("\n✅ Teste concluído!\n")

def show_menu():
    print("""
=============================
 RandDistri - Gerenciador
=============================
1  Iniciar todos os serviços
2  Parar todos os serviços
3  Reiniciar todos os serviços
4  Testar 10 requisições
5  Ver status dos serviços
0  Sair
""")

def status():
    print("\nStatus atual dos serviços:\n")
    for name, proc in processes.items():
        estado = "Rodando" if proc and proc.poll() is None else "Parado"
        print(f" - {name:<13} {estado}")
    print("")

if __name__ == "__main__":
    while True:
        show_menu()
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
        elif choice == "0":
            print("\nEncerrando o gerenciador...")
            stop_all()
            sys.exit(0)
        else:
            print("Opção inválida, tente novamente.\n")
