from flask import Flask, jsonify
import requests, random, time, threading
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

SERVERS = [
    {'id': 'Server1', 'url': 'http://127.0.0.1:5001', 'weight': 60, 'healthy': True},
    {'id': 'Server2', 'url': 'http://127.0.0.1:5002', 'weight': 30, 'healthy': True},
    {'id': 'Server3', 'url': 'http://127.0.0.1:5003', 'weight': 10, 'healthy': True}
]

executor = ThreadPoolExecutor()

def health_check(server):
    try:
        resp = requests.get(f"{server['url']}/health", timeout=1)
        server['healthy'] = resp.status_code == 200
    except:
        server['healthy'] = False

def periodic_health():
    while True:
        time.sleep(5)
        for s in SERVERS:
            executor.submit(health_check, s)

threading.Thread(target=periodic_health, daemon=True).start()

@app.route('/generate')
def generate():
    healthy = [s for s in SERVERS if s['healthy']]
    if not healthy:
        return jsonify({'error': 'No servers'}), 503

    weights = [s['weight'] for s in healthy]
    chosen = random.choices(healthy, weights=weights)[0]
    
    try:
        resp = requests.get(f"{chosen['url']}/generate", timeout=3)
        data = resp.json()
        data['request_to'] = chosen['url']
        print(f"LB → {chosen['id']} → {data['number']}")
        return jsonify(data)
    except:
        chosen['healthy'] = False
        return jsonify({'error': 'Server down'}), 500

if __name__ == '__main__':
    print("Load Balancer rodando na porta 8080")
    app.run(host='0.0.0.0', port=8080)
    