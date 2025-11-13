from flask import Flask, jsonify, request
import random, time, os

app = Flask(__name__)
SERVER_ID = os.getenv('SERVER_ID', 'Server1')
PORT = int(os.getenv('SERVER_PORT', 5001))

# Intervalos padrão de cada servidor (caso o cliente não envie)
RANGES = {'Server1': (1, 50), 'Server2': (40, 80), 'Server3': (70, 100)}

@app.route('/generate')
def generate():
    time.sleep(0.05)

    # Lê parâmetros enviados pelo cliente (ou usa padrão)
    try:
        min_val = int(request.args.get('min', RANGES[SERVER_ID][0]))
        max_val = int(request.args.get('max', RANGES[SERVER_ID][1]))
    except ValueError:
        min_val, max_val = RANGES[SERVER_ID]

    if min_val >= max_val:
        return jsonify({'error': 'Intervalo inválido!'}), 400

    num = random.randint(min_val, max_val)
    return jsonify({
        'number': num,
        'from_server': SERVER_ID,
        'timestamp': time.time(),
        'latency_ms': 50
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print(f"Servidor {SERVER_ID} rodando na porta {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
