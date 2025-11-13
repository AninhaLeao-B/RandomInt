let pauseUpdate = false;
let generationInterval = null;
let generatedCount = 0;
let targetCount = 0;

function updateDashboard() {
    if (pauseUpdate) return; // não atualiza se o usuário estiver editando

    fetch('/api/status')
        .then(r => r.json())
        .then(data => {
            const container = document.getElementById('servers');
            container.innerHTML = '';

            data.servers.forEach(s => {
                // Cria o bloco de servidor
                const serverDiv = document.createElement('div');
                serverDiv.className = 'server';
                serverDiv.dataset.serverId = s.id;

                // Cria input de peso
                const weightInput = document.createElement('input');
                weightInput.type = 'number';
                weightInput.min = 1;
                weightInput.max = 100;
                weightInput.value = s.weight;
                weightInput.className = 'weight-input';

                // Quando o usuário foca → pausa as atualizações
                weightInput.addEventListener('focus', () => pauseUpdate = true);

                // Quando sai do input → retoma atualização após 0.3s
                weightInput.addEventListener('blur', () => {
                    pauseUpdate = false;
                    setTimeout(updateDashboard, 300);
                });

                // Pressionar Enter também aplica o peso
                weightInput.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter') {
                        setWeight(s.id, weightInput);
                        weightInput.blur();
                    }
                });

                // Cria o conteúdo do servidor
                serverDiv.innerHTML = `
                    <div>
                        <b>${s.id}</b>:
                        <span class="${s.status === 'ON' ? 'status-on' : 'status-off'}">
                            ${s.status} ${s.failure_in > 0 ? '(Falha em ' + s.failure_in + 's)' : ''}
                        </span>
                    </div>
                    <div>
                        Peso:
                        <button class="btn-ok" onclick="setWeight('${s.id}', this.previousElementSibling)">OK</button>
                    </div>
                    <div class="reqs">Reqs: ${s.requests}</div>
                    <div class="actions">
                        ${s.running
                            ? `<button class="btn-stop" onclick="stopServer('${s.id}')">Parar</button>`
                            : `<button class="btn-start" onclick="startServer('${s.id}')">Iniciar</button>`
                        }
                        <button class="btn-fail" onclick="simulateFail('${s.id}')">Falha 10s</button>
                    </div>
                `;

                // Coloca o input de peso no lugar certo
                const pesoDiv = serverDiv.querySelector('div:nth-child(2)');
                pesoDiv.insertBefore(weightInput, pesoDiv.querySelector('button'));

                container.appendChild(serverDiv);
            });

            // Atualiza o log de geração
            const log = document.getElementById('log');
            log.innerHTML = '';
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
    const weight = parseInt(input.value);
    if (isNaN(weight) || weight < 1 || weight > 100) {
        alert('Peso deve ser entre 1 e 100');
        return;
    }

    // pausa atualizações durante envio
    pauseUpdate = true;

    fetch(`/set_weight?server=${id}&weight=${weight}`)
        .then(r => r.json())
        .then(data => {
            console.log(`[OK] ${id}: ${data.message}`);
            // exibe um mini feedback no botão
            input.nextElementSibling.textContent = '✔';
            setTimeout(() => {
                input.nextElementSibling.textContent = 'OK';
            }, 800);
        })
        .catch(err => {
            console.error(`[ERRO] Falha ao alterar peso de ${id}`, err);
            alert('Falha ao alterar peso.');
        })
        .finally(() => {
            // retoma atualizações com leve atraso pra evitar sobrescrever
            setTimeout(() => {
                pauseUpdate = false;
                updateDashboard();
            }, 500);
        });
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

    document.getElementById('stopBtn').style.display = 'inline-block';
    document.getElementById('progress').innerText = 'Iniciando geração...';

    let count = 0;
    const interval = setInterval(() => {
        if (count >= qtd) {
            clearInterval(interval);
            stopGeneration();
            return;
        }

        fetch(`/generate?min=${min}&max=${max}`)
            .then(() => {
                count++;
                document.getElementById('progress').innerText = `Gerando ${count} de ${qtd}...`;
            })
            .catch(() => {
                count++;
            });
    }, 600);

    // Salva para parar
    window.generationInterval = interval;
}

function stopGeneration() {
    if (window.generationInterval) {
        clearInterval(window.generationInterval);
        window.generationInterval = null;
    }
    document.getElementById('stopBtn').style.display = 'none';
    updateDashboard(); // Atualiza com log completo
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