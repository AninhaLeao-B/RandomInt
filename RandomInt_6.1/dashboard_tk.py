# dashboard_web.py
from flask import Flask, render_template_string, jsonify, request
import requests
import subprocess
import os
import time
import threading
import random  # <--- IMPORT OBRIGATÓRIO!
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
            # Adiciona ao log
            global generation_log
            log_entry = f"{len(generation_log) + 1}. {data['number']} ← {data['from_server']} (via {chosen['url'].split(':')[-1]})"
            generation_log.append(log_entry)
            if len(generation_log) > 50:
                generation_log.pop(0)
        return jsonify(data)
    except Exception as e:
        print(f"[ERRO] Falha em {chosen['id']}: {e}")
        chosen['healthy'] = False
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
            'generation_log': generation_log[-20:]  # últimos 20
        })

@ app.route('/')
def dashboard():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>RandDistri - Painel</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #1a1a1a; color: #eee; margin: 0; padding: 20px; }
            .container { max-width: 1000px; margin: auto; }
            h1 { color: #00ffff; text-align: center; }
            .card { background: #2d2d2d; padding: 15px; margin: 10px 0; border-radius: 10px; }
            .server { display: flex; justify-content: space-between; align-items: center; padding: 10px; background: #3d3d3d; margin: 5px 0; border-radius: 8px; }
            .status-on { color: lime; font-weight: bold; }
            .status-off { color: red; font-weight: bold; }
            button { padding: 8px 12px; margin: 0 5px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
            .btn-start { background: #008000; color: white; }
            .btn-stop { background: #800000; color: white; }
            .btn-restart { background: #ff9800; color: white; }
            .btn-fail { background: #ff5722; color: white; }
            .btn-gen { background: #0077cc; color: white; }
            input, select { padding: 8px; margin: 0 5px; border-radius: 5px; border: none; }
            .log { background: #000; color: #0f0; padding: 10px; height: 250px; overflow-y: auto; font-family: Consolas; border-radius: 8px; white-space: pre-line; }
            .controls { display: flex; gap: 10px; margin: 10px 0; flex-wrap: wrap; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>RandDistri - Painel de Controle</h1>

            <div class="card">
                <h3>Servidores</h3>
                <div id="servers"></div>
            </div>

            <div class="card">
                <h3>Ações</h3>
                <div class="controls">
                    <button class="btn-restart" onclick="restartAll()">Reiniciar Tudo</button>
                    <button class="btn-gen" onclick="openGenerator()">Gerar Números</button>
                </div>
            </div>

            <div class="card">
                <h3>Log de Geração</h3>
                <div id="log" class="log">Aguardando...</div>
            </div>
        </div>

        <script>
            function update() {
                fetch('/api/status').then(r => r.json()).then(data => {
                    // Servidores
                    const container = document.getElementById('servers');
                    container.innerHTML = '';
                    data.servers.forEach(s => {
                        const div = document.createElement('div');
                        div.className = 'server';
                        div.innerHTML = `
                            <span><b>${s.id}</b>: 
                                <span class="${s.status === 'ON' ? 'status-on' : 'status-off'}">
                                    ${s.status} ${s.failure_in > 0 ? '(Falha em ' + s.failure_in + 's)' : ''}
                                </span>
                            </span>
                            <span>Peso: <input type="number" value="${s.weight}" size="3" 
                                onchange="setWeight('${s.id}', this.value)"> 
                                <button class="btn-gen" onclick="setWeight('${s.id}', this.previousElementSibling.value)">OK</</button>
                            </span>
                            <span>Reqs: <b>${s.requests}</b></span>
                            <div>
                                ${s.running 
                                    ? `<button class="btn-stop" onclick="stopServer('${s.id}')">Parar</button>`
                                    : `<button class="btn-start" onclick="startServer('${s.id}')">Iniciar</button>`
                                }
                                <button class="btn-fail" onclick="simulateFail('${s.id}')">Falha 10s</button>
                            </div>
                        `;
                        container.appendChild(div);
                    });

                    // Log
                    const log = document.getElementById('log');
                    log.innerHTML = data.generation_log.join('\\n') || 'Nenhum número gerado ainda.';
                    log.scrollTop = log.scrollHeight;
                }).catch(() => {
                    document.getElementById('log').innerText = 'Erro ao conectar ao LB.';
                });
            }

            // Atualiza a cada 2s SEM recarregar a página!
            setInterval(update, 2000);
            update();

            // Funções de ação
            function startServer(id) { fetch(`/start?server=${id}`).then(update); }
            function stopServer(id) { fetch(`/stop?server=${id}`).then(update); }
            function restartAll() { fetch('/restart_all').then(update); }
            function setWeight(id, w) { fetch(`/set_weight?server=${id}&weight=${w}`).then(update); }
            function simulateFail(id) { fetch(`/simulate_failure?server=${id}&seconds=10`).then(update); }

            function openGenerator() {
                const qtd = prompt("Quantos números?", "10");
                const min = prompt("Mínimo?", "1");
                const max = prompt("Máximo?", "100");
                if (!qtd || !min || !max) return;
                let count = 0;
                const interval = setInterval(() => {
                    if (count >= qtd) { clearInterval(interval); update(); return; }
                    fetch(`/generate?min=${min}&max=${max}`)
                        .then(r => r.json())
                        .then(d => {
                            const log = document.getElementById('log');
                            log.innerHTML += `${++count}. ${d.number} ← ${d.from_server}\\n`;
                            log.scrollTop = log.scrollHeight;
                        });
                }, 600);
            }
        </script>
    </body>
    </html>
    ''')


if __name__ == '__main__':
    print("Dashboard → http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=False)