from flask import Flask, jsonify
import random, time, os

app = Flask(__name__)
SERVER_ID = os.getenv('SERVER_ID', 'Server1')
PORT = int(os.getenv('SERVER_PORT', 5001))

RANGES = {'Server1': (1, 50), 'Server2': (40, 80), 'Server3': (70, 100)}

@app.route('/generate')
def generate():
    time.sleep(0.05)
    num = random.randint(*RANGES[SERVER_ID])
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
    