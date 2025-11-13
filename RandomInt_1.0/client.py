import requests, time

LB = 'http://127.0.0.1:8080/generate'

print("Gerando 10 números aleatórios...\n")
for i in range(10):
    try:
        resp = requests.get(LB, timeout=5)
        data = resp.json()
        print(f"{i+1:2}. Número: {data['number']:3} | De: {data['from_server']} | Via: {data['request_to']}")
    except Exception as e:
        print(f"{i+1:2}. ERRO: {e}")
    time.sleep(1)
    