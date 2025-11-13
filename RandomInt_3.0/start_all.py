import subprocess
import time
import os
import platform

IS_WINDOWS = platform.system() == "Windows"

def run_server(server_id, port):
    env = os.environ.copy()
    env["SERVER_ID"] = server_id
    env["SERVER_PORT"] = str(port)
    print(f"[START] {server_id} na porta {port}")
    return subprocess.Popen(
        ["python", "server.py"], 
        env=env,
        cwd=os.getcwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

def run_lb():
    print("[START] Load Balancer na porta 8080")
    return subprocess.Popen(
        ["python", "load_balancer.py"],
        cwd=os.getcwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

# Inicia os servidores
servers = [
    run_server("Server1", 5001),
    run_server("Server2", 5002),
    run_server("Server3", 5003)
]

# Aguarda um pouquinho
time.sleep(2)

# Inicia o balanceador
lb = run_lb()

# Aguarda o balanceador ficar pronto
print("\n[INFO] Aguardando Load Balancer subir (5s)...")
time.sleep(5)

# Testa as requisições
print("\n[TESTE] Enviando 10 requisições...\n")
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

print("\n[SUCESSO] Sistema rodando!")
print("Dashboard: http://localhost:8080")
print("Para parar: Ctrl+C neste terminal ou feche os processos.")
