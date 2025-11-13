
let generationInterval = null;
let generatedCount = 0;
let targetCount = 0;

function updateDashboard() {
    fetch('/api/status')
        .then(r => r.json())
        .then(data => {
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
                    <span>
                        Peso: <input type="number" value="${s.weight}" min="1" max="100" class="weight-input">
                        <button class="btn-gen" onclick="setWeight('${s.id}', this.previousElementSibling.value)">OK</button>
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

            const log = document.getElementById('log');
            log.innerHTML = ''; // Limpa

            if (data.generation_log.length === 0) {
                log.innerHTML = 'Nenhum número gerado ainda.';
            } else {
                data.generation_log.forEach(entry => {
                    const span = document.createElement('span');

                    if (entry.includes('Server1')) span.className = 'server1';
                    else if (entry.includes('Server2')) span.className = 'server2';
                    else if (entry.includes('Server3')) span.className = 'server3';
                    else if (entry.includes('[ERRO]')) span.className = 'error';

                    span.textContent = entry + '\n';
                    log.appendChild(span);
                });
            }
            log.scrollTop = log.scrollHeight;
        })
        .catch(() => {
            document.getElementById('log').innerText = 'Erro ao conectar ao servidor.';
        });
}

function startServer(id) { fetch(`/start?server=${id}`).then(updateDashboard); }
function stopServer(id) { fetch(`/stop?server=${id}`).then(updateDashboard); }
function restartAll() { fetch('/restart_all').then(updateDashboard); }

function setWeight(id, input) {
    const weight = parseInt(input);
    if (weight >= 1 && weight <= 100) {
        fetch(`/set_weight?server=${id}&weight=${weight}`).then(updateDashboard);
    }
}

function simulateFail(id) { fetch(`/simulate_failure?server=${id}&seconds=10`).then(updateDashboard); }

function startGeneration() {
    const qtd = parseInt(document.getElementById('qtd').value);
    const min = parseInt(document.getElementById('min').value);
    const max = parseInt(document.getElementById('max').value);

    if (isNaN(qtd) || qtd < 1 || isNaN(min) || isNaN(max) || min >= max) {
        alert('Verifique: quantidade > 0, mínimo < máximo');
        return;
    }

    targetCount = qtd;
    generatedCount = 0;
    document.getElementById('stopBtn').style.display = 'inline-block';
    document.getElementById('progress').innerText = `Gerando 0 de ${qtd}...`;

    generationInterval = setInterval(() => {
        if (generatedCount >= targetCount) {
            stopGeneration();
            return;
        }

        fetch(`/generate?min=${min}&max=${max}`)
            .then(r => r.json())
            .then(d => {
                generatedCount++;
                const log = document.getElementById('log');

                const span = document.createElement('span');
                span.className = `server${d.from_server.slice(-1)}`; // Server1 → server1
                span.textContent = `${generatedCount}. ${d.number} ← ${d.from_server}\n`;

                log.appendChild(span);
                log.scrollTop = log.scrollHeight;

                document.getElementById('progress').innerText = `Gerando ${generatedCount} de ${targetCount}...`;
            })
            .catch(() => {
                generatedCount++;
                const log = document.getElementById('log');
                const span = document.createElement('span');
                span.className = 'error';
                span.textContent = `${generatedCount}. [ERRO] Servidor offline\n`;
                log.appendChild(span);
                log.scrollTop = log.scrollHeight;
            });
    }, 600);
}

function stopGeneration() {
    if (generationInterval) clearInterval(generationInterval);
    generationInterval = null;
    document.getElementById('stopBtn').style.display = 'none';
    const msg = generatedCount >= targetCount
        ? `Concluído: ${generatedCount} números gerados!`
        : `Parado: ${generatedCount} de ${targetCount} gerados.`;
    document.getElementById('progress').innerText = msg;
}

function clearLog() {
    // Limpa no frontend
    document.getElementById('log').innerHTML = 'Log limpo.\n';

    // Limpa no backend (opcional, mas recomendado)
    fetch('/api/clear_log', { method: 'POST' })
        .then(() => updateDashboard())
        .catch(() => {
            document.getElementById('log').innerHTML = 'Erro ao limpar log no servidor.\n';
        });
}

function startAllServers() {
    const btn = document.getElementById('startAllBtn');
    const progress = document.getElementById('startAllProgress');

    // Desabilita botão
    btn.disabled = true;
    btn.innerText = 'Iniciando...';
    progress.innerText = 'Verificando servidores...';

    const servers = ['Server1', 'Server2', 'Server3'];
    let started = 0;
    let alreadyRunning = 0;

    servers.forEach(id => {
        fetch(`/start?server=${id}`)
            .then(r => r.json())
            .then(data => {
                if (data.message.includes('Já rodando') || data.message.includes('iniciado')) {
                    started++;
                    if (data.message.includes('Já rodando')) alreadyRunning++;
                }
                checkAllDone();
            })
            .catch(() => {
                started++;
                checkAllDone();
            });
    });

    function checkAllDone() {
        if (started === 3) {
            const success = 3 - alreadyRunning;
            progress.innerText = alreadyRunning === 3
                ? 'Todos já estavam rodando!'
                : `${success} iniciado(s), ${alreadyRunning} já rodando.`;

            setTimeout(() => {
                btn.disabled = false;
                btn.innerText = 'Iniciar Todos';
                progress.innerText = '';
                updateDashboard();
            }, 1500);
        }
    }
}

// Atualiza a cada 2 segundos
setInterval(updateDashboard, 2000);
updateDashboard();