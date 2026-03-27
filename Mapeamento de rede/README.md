🛰️ A Sentinela de Cyberitu — Vigilância das Terras de Durães
"Nas fronteiras entre a Tecnologia e a Logística, nenhum pacote viaja sem ser notado. O Olho de Cyberitu tudo vê."

Bem-vindo ao Posto Avançado de Monitoramento. Este artefato foi forjado para resolver um desafio real nas terras de Santarém/PA: unificar a visão de dispositivos em redes distintas e garantir a segurança proativa da Distribuidora Durães.

📜 A Natureza do Artefato (Como Funciona)
O Cyberitu não é apenas um código; é um ecossistema de vigilância dividido em duas frentes mágicas que trabalham em harmonia:

🐍 O Batedor (recebe_logs.py)
É o motor de busca assíncrono que patrulha as redes.

Invasão Silenciosa (Bypass Intelbras): Realiza um "login ninja" via requisições HTTP para extrair a lista de dispositivos conectados diretamente do roteador da Logística (192.168.1.244), superando as barreiras do firmware original.

Velocidade Arcana (Multithreading): Utiliza o poder do processamento paralelo para disparar centenas de pings simultâneos, mapeando o setor de Tecnologia em segundos sem travar o sistema.

Ouvido Atento (Receptor Syslog): Escuta na porta UDP 514 por mensagens de DHCP, identificando instantaneamente quando um novo viajante (dispositivo) solicita entrada na rede.

🏰 A Torre de Vigia (dashboard_duraes.py)
É a interface mística que apresenta a verdade aos líderes da guilda.

Visão em Tempo Real: Através de feitiços de AJAX/JavaScript, o painel se atualiza a cada 3 segundos sem que a página precise ser recarregada.

O Sinal de Alerta (Flag Red): Uma luz vermelha pulsante surge ao lado de qualquer dispositivo cujo ID não conste no Grande Códice de Nomes, alertando sobre possíveis intrusos.

📦 Inventário Necessário (Pré-requisitos)
Para conjurar este sistema, você deve ter em seu inventário:

Linguagem: Python 3.10 ou superior.

Bibliotecas de Apoio: * Flask (Para erguer a Torre Web).

Requests (Para as missões de invasão ao roteador).

Hardware: Estar conectado fisicamente (ou via túnel VPN) às redes da Distribuidora.

⚡ O Ritual de Conjuração (Como fazer funcionar)
Siga estes passos para ativar a sentinela em seu próprio território:

1. Preparando o Terreno
Certifique-se de que a estrutura de pastas está organizada:

Plaintext
Caminho/
├── dashboard_duraes.py
├── recebe_logs.py
├── LOGO_DURAES_VETORIZADA.png
└── dados/
    └── dispositivos.json
2. O Grande Códice (dispositivos.json)
Edite este pergaminho para dar nome aos IPs conhecidos. Sem isso, todos aparecerão com a flag de "Novo".

JSON
{
    "192.168.1.50": "PC T.I. - Zendar",
    "10.0.0.182": "Coletor Logística 01"
}
3. Ajustando as Coordenadas
Abra o recebe_logs.py e certifique-se de que as coordenadas (IPs e Senhas) estão corretas para a rede local:

Python
URL_LOGISTICA = "http://192.168.1.244:8080"
USUARIO_ROTEADOR = "admin"
SENHA_ROTEADOR = "SUA_SENHA_AQUI"
4. Iniciando a Vigília
Abra dois terminais (pergaminhos de comando) e execute:

Terminal 1: python recebe_logs.py (Inicia o escaneamento).

Terminal 2: python dashboard_duraes.py (Ergue o painel web).

Acesse http://localhost:5000 em seu navegador e contemple a rede protegida!

🛡️ Leis de Segurança do Aventureiro
Nunca compartilhe o código com as senhas reais do roteador expostas.

Use arquivos .env ou variáveis de ambiente para esconder as chaves de acesso antes de subir para o GitHub público.

🎯 Missão Concluída
Este projeto demonstra domínio em Sistemas Distribuídos, Automação de Infraestrutura e Desenvolvimento Web Fullstack. Criado por um aventureiro de Sistemas de Informação da UFOPA para o mundo real.
