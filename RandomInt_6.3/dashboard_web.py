from flask import Flask, jsonify, request, render_template
import requests
import subprocess
import os
import time
import threading
import random
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# --- CONFIG SERVIDORES ---
SERVERS = [
    {'id': 'Server1', 'url': 'http://127.0.0.1:5001', 'weight': 60, 'healthy': True, 'port': 5001},
    {'id': 'Server2', 'url': 'http://127.0.0.1:5002', 'weight': 30, 'healthy': True, 'port': 5002},
    {'id': 'Server3', 'url': 'http://127.0.0.1:5003', 'weight': 10, 'healthy': True, 'port': 5003}
]

processes = {}
executor = ThreadPoolExecutor()
stats = {'Server1': 0, 'Server2': 0, 'Server3': 0}
stats_lock = threading.Lock()
failure_simulations = {}
generation_log = []  # Log de números gerados


# --- CONTROLE DE PROCESSOS ---
def start_server(server_id):
    if server_id in processes and processes[server_id].poll() is None:
        return False, "Já rodando"
    server = next((s for s in SERVERS if s['id'] == server_id), None)
    if not server: return False, "Não encontrado"
    env = os.environ.copy()
    env["SERVER_ID"] = server_id
    env["SERVER_PORT"] = str(server['port'])
    proc = subprocess.Popen(["python", "server.py"], env=env, cwd=os.getcwd())
    processes[server_id] = proc
    server['healthy'] = True
    return True, f"{server_id} iniciado"


def stop_server(server_id):
    if server_id not in processes or processes[server_id].poll() is not None:
        return False, "Não rodando"
    proc = processes[server_id]
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except:
        proc.kill()
    del processes[server_id]
    server = next(s for s in SERVERS if s['id'] == server_id)
    server['healthy'] = False
    return True, f"{server_id} parado"


# --- HEALTH CHECK ---
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


# --- SIMULAÇÃO DE FALHA ---
def simulate_failure(server_id, seconds=10):
    if server_id not in processes:
        return False, "Servidor não rodando"
    stop_server(server_id)

    def recover():
        time.sleep(seconds)
        start_server(server_id)
        if server_id in failure_simulations:
            del failure_simulations[server_id]

    threading.Thread(target=recover, daemon=True).start()
    failure_simulations[server_id] = seconds
    return True, f"Falha simulada por {seconds}s"


# --- ROTAS ---
@app.route('/generate')
def generate():
    healthy = [s for s in SERVERS if s['healthy']]
    if not healthy:
        return jsonify({'error': 'Nenhum servidor ativo'}), 503

    weights = [s['weight'] for s in healthy]
    chosen = random.choices(healthy, weights=weights)[0]
    params = request.args.to_dict()

    try:
        resp = requests.get(f"{chosen['url']}/generate", params=params, timeout=3)
        if resp.status_code != 200:
            raise Exception("Erro no servidor")
        data = resp.json()
        data['request_to'] = chosen['url']

        with stats_lock:
            stats[chosen['id']] += 1
            entry = f"{len(generation_log) + 1}. {data['number']} ← {data['from_server']}"
            generation_log.append(entry)
            if len(generation_log) > 1000:  # Limite opcional
                generation_log.pop(0)

        return jsonify(data)
    except Exception as e:
        print(f"[ERRO] Falha em {chosen['id']}: {e}")
        chosen['healthy'] = False
        entry = f"{len(generation_log) + 1}. [ERRO] {chosen['id']} offline"
        generation_log.append(entry)
        return jsonify({'error': f"{chosen['id']} offline"}), 500


@app.route('/set_weight')
def set_weight():
    server_id = request.args.get('server')
    weight = request.args.get('weight', type=int)
    if not server_id or weight is None or weight < 0:
        return jsonify({'error': 'Parâmetros inválidos'}), 400
    for s in SERVERS:
        if s['id'] == server_id:
            old = s['weight']
            s['weight'] = max(1, weight)
            return jsonify({'message': f'Peso: {old} → {s["weight"]}'})
    return jsonify({'error': 'Servidor não encontrado'}), 404


@app.route('/start')
def start_server_route():
    server_id = request.args.get('server')
    ok, msg = start_server(server_id)
    return jsonify({'message': msg}), 200 if ok else 400


@app.route('/stop')
def stop_server_route():
    server_id = request.args.get('server')
    ok, msg = stop_server(server_id)
    return jsonify({'message': msg}), 200 if ok else 400


@app.route('/restart_all')
def restart_all():
    for s in SERVERS:
        stop_server(s['id'])
        time.sleep(0.3)
        start_server(s['id'])
    return jsonify({'message': 'Reiniciando todos...'})


@app.route('/simulate_failure')
def sim_failure():
    server_id = request.args.get('server')
    seconds = request.args.get('seconds', 10, type=int)
    ok, msg = simulate_failure(server_id, seconds)
    return jsonify({'message': msg}), 200 if ok else 400


@app.route('/api/status')
def api_status():
    with stats_lock:
        return jsonify({
            'servers': [
                {
                    'id': s['id'],
                    'status': 'ON' if s['healthy'] else 'OFF',
                    'weight': s['weight'],
                    'requests': stats[s['id']],
                    'running': s['id'] in processes and processes[s['id']].poll() is None,
                    'failure_in': failure_simulations.get(s['id'], 0)
                } for s in SERVERS
            ],
            'total_requests': sum(stats.values()),
            'generation_log': generation_log[-200:]  # últimos 20
        })

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/clear_log', methods=['POST'])
def clear_log():
    global generation_log
    generation_log = []
    return jsonify({'message': 'Log limpo'}), 200

if __name__ == '__main__':
    print("Dashboard → http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
