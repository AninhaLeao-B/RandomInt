from flask import Flask, jsonify, render_template_string, request
import requests, random, time, threading
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

SERVERS = [
    {'id': 'Server1', 'url': 'http://127.0.0.1:5001', 'weight': 60, 'healthy': True},
    {'id': 'Server2', 'url': 'http://127.0.0.1:5002', 'weight': 30, 'healthy': True},
    {'id': 'Server3', 'url': 'http://127.0.0.1:5003', 'weight': 10, 'healthy': True}
]

executor = ThreadPoolExecutor()
stats = {'Server1': 0, 'Server2': 0, 'Server3': 0}
stats_lock = threading.Lock()

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

    # Pega parâmetros da requisição (ex.: ?min=20&max=50)
    params = request.args.to_dict()

    try:
        # Repassa os mesmos parâmetros pro servidor escolhido
        resp = requests.get(f"{chosen['url']}/generate", params=params, timeout=3)
        data = resp.json()
        data['request_to'] = chosen['url']

        with stats_lock:
            stats[chosen['id']] += 1

        print(f"LB → {chosen['id']} → {data['number']}")
        return jsonify(data)
    except:
        chosen['healthy'] = False
        return jsonify({'error': f"{chosen['id']} está offline"}), 500

@app.route('/')
def dashboard():
    with stats_lock:
        healthy = {s['id']: 'ON' if s['healthy'] else 'OFF' for s in SERVERS}
        return render_template_string('''
        <meta http-equiv="refresh" content="2">
        <h1>RandDistri - Dashboard</h1>
        <h3>Servidores:</h3>
        <pre>
Server1: {{ healthy.Server1 }} ({{ stats.Server1 }} reqs)
Server2: {{ healthy.Server2 }} ({{ stats.Server2 }} reqs)
Server3: {{ healthy.Server3 }} ({{ stats.Server3 }} reqs)
        </pre>
        <button onclick="fetch('/generate').then(r=>r.json()).then(d=>alert('Número: '+d.number+' de '+d.from_server))">
          Gerar com JS
        </button>
        <hr>
        <h3>Teste com curl:</h3>
        <code>curl http://localhost:8080/generate</code>
        ''', stats=stats, healthy=healthy)

if __name__ == '__main__':
    print("Load Balancer → http://localhost:8080")
    app.run(host='0.0.0.0', port=8080)
