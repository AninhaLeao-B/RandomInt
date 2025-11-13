import requests
import time
from colorama import init, Fore, Style

# Inicializa cores no terminal
init(autoreset=True)

LB = 'http://127.0.0.1:8080/generate'

print(Fore.CYAN + Style.BRIGHT + "\n=== Gerador de Números Aleatórios ===\n" + Style.RESET_ALL)

# Quantos números gerar
while True:
    try:
        total = int(input(Fore.WHITE + "Quantos números você deseja gerar? " + Style.RESET_ALL))
        if total <= 0:
            print(Fore.RED + "Por favor, digite um número positivo.\n")
            continue
        break
    except ValueError:
        print(Fore.RED + "Entrada inválida! Digite um número inteiro.\n")

# Intervalo de geração
while True:
    try:
        min_val = int(input(Fore.WHITE + "Número mínimo: " + Style.RESET_ALL))
        max_val = int(input(Fore.WHITE + "Número máximo: " + Style.RESET_ALL))
        if min_val >= max_val:
            print(Fore.RED + "O mínimo deve ser menor que o máximo!\n")
            continue
        break
    except ValueError:
        print(Fore.RED + "Entrada inválida! Digite números inteiros.\n")

print(Fore.CYAN + f"\nGerando {total} números entre {min_val} e {max_val}...\n" + Style.RESET_ALL)
time.sleep(1)

# Contadores de servidores
counts = {"Server1": 0, "Server2": 0, "Server3": 0}

# Loop principal
for i in range(total):
    try:
        # Envia parâmetros de intervalo via query string
        resp = requests.get(LB, params={"min": min_val, "max": max_val}, timeout=5)
        data = resp.json()

        print(Fore.LIGHTBLACK_EX + f"[{i+1:02}] ", end="")

        if 'error' in data:
            print(Fore.RED + f"Erro: {data['error']}" + Style.RESET_ALL)
        else:
            color = {
                "Server1": Fore.GREEN,
                "Server2": Fore.CYAN,
                "Server3": Fore.MAGENTA
            }.get(data["from_server"], Fore.WHITE)

            if data["from_server"] in counts:
                counts[data["from_server"]] += 1

            print(
                f"Número: {Fore.YELLOW}{data['number']:3}{Style.RESET_ALL}  "
                f"| Servidor: {color}{data['from_server']:<8}{Style.RESET_ALL}  "
                f"| Rota: {Fore.LIGHTBLACK_EX}{data['request_to']}{Style.RESET_ALL}"
            )

    except Exception as e:
        print(Fore.RED + f"Erro ao conectar: {e}" + Style.RESET_ALL)

    time.sleep(0.8)

# Resumo final
print(Fore.GREEN + Style.BRIGHT + f"\nConcluído! {total} números foram gerados.\n" + Style.RESET_ALL)
print(Fore.CYAN + "Resumo de uso dos servidores:" + Style.RESET_ALL)
print(Fore.LIGHTBLACK_EX + "───────────────────────────────" + Style.RESET_ALL)
for s, c in counts.items():
    color = {"Server1": Fore.GREEN, "Server2": Fore.CYAN, "Server3": Fore.MAGENTA}[s]
    print(f"{color}{s}:{Style.RESET_ALL} {c} requisições")
print(Fore.LIGHTBLACK_EX + "───────────────────────────────\n" + Style.RESET_ALL)
