# 🌐 RandomInt — Sistema Distribuído de Geração de Números Aleatórios

### 🔢 Load Balancer + Multi-Servidores + Dashboard Web + Painel CLI  

> **RandomInt** é um sistema distribuído completo para geração de números aleatórios, composto por múltiplos servidores com balanceamento de carga, tolerância a falhas e um painel de controle interativo totalmente funcional.

----------

## 📡 Visão Geral da Arquitetura

O sistema é composto por:

### 🖥️ **Servidores Independentes (3 unidades)**

Cada servidor Flask:

-   Gera números aleatórios
    
-   Possui seu próprio intervalo configurável
    
-   Tem rota de health check
    
-   Responde ao Load Balancer
    

Portas padrão: **5001, 5002, 5003**

----------

### ⚖️ **Load Balancer Inteligente**

O balanceador:

-   Distribui requisições baseado em **peso (weighted round-robin)**
    
-   Realiza **health check automático**
    
-   Remove servidores instáveis do pool
    
-   Pode **iniciar/parar servidores** via painel
    
-   Mantém métricas e estatísticas
    

----------

### 📊 **Dashboard Web (HTML + CSS + JS)**

#### A interface web permite:
| Função | Descrição |
|--|--|
| 🟢 Iniciar / 🔴 Parar servidores | Controle individual de cada servidor |
|🔁 Reiniciar todos |Sincronização total|
|🧪 Simular falhas |Derruba servidores por alguns segundos|
|⚖️ Ajustar pesos |Balanceamento em tempo real-|
|🔢 Gerar números |Definir quantidade, min e max-|
|📜 Log colorido |Visualização das últimas requisições-|

----------

### 🖥️ **Painel Interativo via Terminal (CLI Menu)**

Além do dashboard web, há um **menu completo no terminal**, permitindo:

-   Iniciar/parar todos os servidores
    
-   Ajustar pesos
    
-   Gerar números
    
-   Simular falhas
    
-   Ver status do sistema
    
-   Visualizar contadores
    
-   Reiniciar tudo
    

Ideal para apresentação e testes rápidos.

----------

## ⚙️ Tecnologias Utilizadas

### Backend

-   Python 3.12
    
-   Flask
    
-   Requests
    
-   ThreadPoolExecutor
    
-   Subprocess
    
-   Random
    

### Frontend (Dashboard Web)

-   HTML5
    
-   CSS3
    
-   JavaScript ES6
    

### Outros

-   Arquitetura distribuída
    
-   Balanceamento ponderado
    
-   Health checks automáticos
    
-   Polling a cada 2s
    
-   Tolerância a falhas
    

----------

## 🧱 Estrutura do Projeto

`/Projeto/
│
├── server.py # Servidores independentes ├── dashboard_web.py # Load Balancer + API + Dashboard HTML ├── static/
│   ├── style.css # Estilos do Dashboard │   └── script.js # Lógica do Dashboard ├── templates/
│   └── dashboard.html # Página principal ├── start_all.py # Painel CLI (terminal) └── README.md # Documentação` 

----------

## 🚀 Como Rodar o Projeto

### 1️⃣ Iniciar os servidores manualmente

`set SERVER_ID=Server1 && set SERVER_PORT=5001 && python server.py  set SERVER_ID=Server2 && set SERVER_PORT=5002 && python server.py set SERVER_ID=Server3 && set SERVER_PORT=5003 && python server.py` 

### 2️⃣ Iniciar tudo pelo menu interativo (recomendado)

`python start_all.py` 

O menu permite:

-   iniciar/parar servidores
    
-   simular falhas
    
-   alterar pesos
    
-   visualizar status
    
-   gerar números
    

----------

### 3️⃣ Abrir o Dashboard Web

`python dashboard_web.py` 

Acesse no navegador:

`http://localhost:8080` 

----------

## 🌈 Funcionalidades do Dashboard

### 🟢 Status dos Servidores

-   ON/OFF
    
-   Requisições atendidas
    
-   Peso atual
    
-   Falhas temporárias
    

### ⚖️ Ajuste de Pesos

-   Configuração instantânea
    
-   Pausa automática do refresh enquanto edita
    

### 🔢 Geração de Números

-   quantidade
    
-   mínimo
    
-   máximo
    

### 📜 Log colorido

-   Server1 → amarelo
    
-   Server2 → azul
    
-   Server3 → roxo
    
-   Erros → vermelho
    

----------

## 🛡️ Tolerância a Falhas

O sistema detecta automaticamente quando um servidor:

-   cai
    
-   trava
    
-   fica indisponível
    

E remove ele do pool até voltar.

Também é possível **simular falhas** manualmente.

----------

## 🎯 Objetivos Didáticos

Este projeto demonstra:

-   Balanceamento de carga
    
-   Tolerância a falhas
    
-   Health checks
    
-   Concorrência
    
-   Arquitetura distribuída
    
-   Comunicação entre processos
    
-   Monitoramento e controle
    
-   Frontend + Backend em tempo real
    

----------

## 📌 Sugestões de Evolução

-   Configurar intervalos de geração por servidor
    
-   Salvar logs em arquivo
    
-   Adicionar autenticação no painel
    
-   WebSockets para atualização em tempo real
    
-   Versão com Docker Compose
    
-   Exportar relatório das execuções
    

----------

## 🧑‍💻 Objetivo

Projeto desenvolvido como atividade prática da disciplina de **Sistemas Distribuídos**.
