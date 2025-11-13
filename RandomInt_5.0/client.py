import requests
import time
from colorama import init, Fore, Style

# Inicializa as cores no terminal
init(autoreset=True)

LB = 'http://127.0.0.1:8080/generate'

# Pede ao usuário a quantidade de números
print(Fore.CYAN + Style.BRIGHT + "\n=== Gerador de Números Aleatórios ===\n" + Style.RESET_ALL)
while True:
    try:
        total = int(input(Fore.WHITE + "Quantos números você deseja gerar? " + Style.RESET_ALL))
        if total <= 0:
            print(Fore.RED + "Por favor, digite um número positivo.\n")
            continue
        break
    except ValueError:
        print(Fore.RED + "Entrada inválida! Digite um número inteiro.\n")

print(Fore.CYAN + f"\nGerando {total} números aleatórios...\n" + Style.RESET_ALL)
time.sleep(1)

# Loop de geração
for i in range(total):
    try:
        resp = requests.get(LB, timeout=5)
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

            print(
                f"Número: {Fore.YELLOW}{data['number']:3}{Style.RESET_ALL}  "
                f"| Servidor: {color}{data['from_server']:<8}{Style.RESET_ALL}  "
                f"| Rota: {Fore.LIGHTBLACK_EX}{data['request_to']}{Style.RESET_ALL}"
            )

    except Exception as e:
        print(Fore.RED + f"Erro ao conectar: {e}" + Style.RESET_ALL)

    time.sleep(0.8)

print(Fore.GREEN + Style.BRIGHT + f"\nConcluído! {total} números foram gerados.\n" + Style.RESET_ALL)
