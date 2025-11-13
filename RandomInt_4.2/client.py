import requests
import time
from colorama import init, Fore, Style

# Inicializa cores no terminal (funciona no Windows e Linux)
init(autoreset=True)

LB = 'http://127.0.0.1:8080/generate'

print(Fore.CYAN + Style.BRIGHT + "\nIniciando geração de 10 números aleatórios...\n" + Style.RESET_ALL)
time.sleep(1)

for i in range(10):
    try:
        resp = requests.get(LB, timeout=5)
        data = resp.json()

        print(Fore.LIGHTBLACK_EX + f"[{i+1:02}] ", end="")

        if 'error' in data:
            print(Fore.RED + f"Erro: {data['error']}" + Style.RESET_ALL)
        else:
            # Cores diferentes por servidor
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

print(Fore.GREEN + Style.BRIGHT + "\nConcluído! Todos os números foram gerados.\n" + Style.RESET_ALL)
