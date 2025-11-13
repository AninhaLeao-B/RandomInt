from flask import Flask, jsonify, render_template_string, request
import requests, random, time, threading
from concurrent.futures import ThreadPoolExecutor
import subprocess
import os
import signal

app = Flask(__name__)

SERVERS = [
    {'id': 'Server1', 'url': 'http://127.0.0.1:5001', 'weight': 60, 'healthy': True},
    {'id': 'Server2', 'url': 'http://127.0.0.1:5002', 'weight': 30, 'healthy': True},
    {'id': 'Server3', 'url': 'http://127.0.0.1:5003', 'weight': 10, 'healthy': True}
]

# --- Controle de processos dos servidores --- #
processes = {}  # guarda os processos ativos

def start_server(server_id):
    if server_id in processes:
        return False, "Servidor já está rodando."

    server = next((s for s in SERVERS if s['id'] == server_id), None)
    if not server:
        return False, "Servidor não encontrado."

    port = int(server['url'].split(":")[-1])
    env = os.environ.copy()
    env["SERVER_ID"] = server_id
    env["SERVER_PORT"] = str(port)

    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.py")
    proc = subprocess.Popen(["python", script_path], env=env)
    processes[server_id] = proc
    server['healthy'] = True
    return True, f"{server_id} iniciado na porta {port}."

def stop_server(server_id):
    if server_id not in processes:
        return False, "Servidor não está rodando."

    proc = processes[server_id]
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()

    del processes[server_id]

    server = next((s for s in SERVERS if s['id'] == server_id), None)
    if server:
        server['healthy'] = False

    return True, f"{server_id} foi encerrado."

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

@app.route('/set_weight')
def set_weight():
    server_id = request.args.get('server')
    new_weight = request.args.get('weight', type=int)

    if not server_id or new_weight is None:
        return jsonify({
            'error': 'Parâmetros inválidos. Use /set_weight?server=Server1&weight=80'
        }), 400

    for s in SERVERS:
        if s['id'].lower() == server_id.lower():
            old_weight = s['weight']
            s['weight'] = new_weight
            print(f"[UPDATE] Peso de {server_id} alterado: {old_weight} → {new_weight}")
            return jsonify({
                'message': f"Peso de {server_id} atualizado com sucesso.",
                'old_weight': old_weight,
                'new_weight': new_weight
            }), 200

    return jsonify({'error': 'Servidor não encontrado.'}), 404

@app.route('/start_server')
def start_server_route():
    server_id = request.args.get('server')
    ok, msg = start_server(server_id)
    code = 200 if ok else 400
    print(f"[SERVER] {msg}")
    return jsonify({'message': msg}), code

@app.route('/stop_server')
def stop_server_route():
    server_id = request.args.get('server')
    ok, msg = stop_server(server_id)
    code = 200 if ok else 400
    print(f"[SERVER] {msg}")
    return jsonify({'message': msg}), code

@app.route('/toggle_server')
def toggle_server():
    server_id = request.args.get('server')
    for s in SERVERS:
        if s['id'].lower() == server_id.lower():
            s['healthy'] = not s['healthy']
            new_status = "ON" if s['healthy'] else "OFF"
            print(f"[TOGGLE] {s['id']} agora está {new_status}")
            return jsonify({'message': f"{s['id']} atualizado.", 'new_status': new_status})
    return jsonify({'error': 'Servidor não encontrado'}), 404

@app.route('/')
def dashboard():
    with stats_lock:
        healthy = {s['id']: 'ON' if s['healthy'] else 'OFF' for s in SERVERS}
        weights = {s['id']: s['weight'] for s in SERVERS}
        return render_template_string('''
        <meta http-equiv="refresh" content="3">
        <h1>RandDistri - Dashboard</h1>
        <h3>Servidores:</h3>
        <pre>
Server1: {{ healthy.Server1 }} ({{ stats.Server1 }} reqs) | Peso: {{ weights.Server1 }}
Server2: {{ healthy.Server2 }} ({{ stats.Server2 }} reqs) | Peso: {{ weights.Server2 }}
Server3: {{ healthy.Server3 }} ({{ stats.Server3 }} reqs) | Peso: {{ weights.Server3 }}
        </pre>
        <hr>
        <h4>Alterar peso manualmente:</h4>
        <form method="get" action="/set_weight">
          Servidor:
          <select name="server">
            <option>Server1</option>
            <option>Server2</option>
            <option>Server3</option>
          </select>
          Novo peso: <input type="number" name="weight" min="1" required>
          <button type="submit">Atualizar</button>
        </form>
        ''', stats=stats, healthy=healthy, weights=weights)

if __name__ == '__main__':
    print("Load Balancer → http://localhost:8080")
    app.run(host='0.0.0.0', port=8080)
