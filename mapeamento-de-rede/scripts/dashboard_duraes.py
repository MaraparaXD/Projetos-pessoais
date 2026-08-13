# ==============================================================================
# SISTEMA DE MONITORAMENTO UNIFICADO - DISTRIBUIDORA DURÃES (MWV)
# ==============================================================================

from flask import Flask, jsonify, send_from_directory
import json, os

# --------------------------------------------------------------------------
# CONFIGURAÇÕES DE CAMINHO (À PROVA DE FALHAS)
# --------------------------------------------------------------------------
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))

# Se o script estiver dentro da pasta 'scripts', volta um nível para achar 'dados' e a LOGO
if os.path.basename(DIRETORIO_ATUAL) == "scripts":
    DIRETORIO_RAIZ = os.path.dirname(DIRETORIO_ATUAL)
else:
    DIRETORIO_RAIZ = DIRETORIO_ATUAL

ESTADO_FILE = os.path.join(DIRETORIO_RAIZ, "dados", "estado_atual.json")

app = Flask(__name__)

# --------------------------------------------------------------------------
# TEMPLATE HTML (O CORAÇÃO DO DASHBOARD)
# --------------------------------------------------------------------------
TEMPLATE_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cyberitu Dashboard | Durães MWV</title>
    <style>
        :root {
            --bg: #0f172a; --card-bg: #1e293b; --text-main: #f8fafc;
            --text-muted: #94a3b8; --ti-accent: #3b82f6; --log-accent: #f59e0b;
            --success: #10b981; --border: #334155; --danger: #ef4444;
        }

        body { font-family: 'Segoe UI', Roboto, Helvetica, sans-serif; background: var(--bg); color: var(--text-main); margin: 0; padding: 30px; }
        
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid var(--border); }
        .header-title { display: flex; align-items: center; gap: 20px; }
        .header-title h1 { margin: 0; font-size: 2.2rem; }

        .counters { display: flex; gap: 20px; }
        .counter-box { background-color: var(--card-bg); padding: 15px 25px; border-radius: 8px; text-align: center; border-left: 4px solid var(--text-muted); min-width: 120px; }
        .counter-box.ti { border-color: var(--ti-accent); }
        .counter-box.log { border-color: var(--log-accent); }
        .counter-number { font-size: 28px; font-weight: bold; margin-top: 5px; }

        /* Controles de Pesquisa e Filtro */
        .controls-row { display: flex; gap: 15px; margin-bottom: 20px; align-items: stretch; }
        .search-bar { flex-grow: 1; padding: 15px; border-radius: 8px; border: 1px solid var(--border); background-color: var(--card-bg); color: white; font-size: 16px; }

        .filter-group { display: flex; gap: 10px; }
        .btn-filter { padding: 0 20px; border-radius: 8px; border: 1px solid var(--border); background: var(--card-bg); color: var(--text-muted); cursor: pointer; font-weight: bold; transition: all 0.2s; }
        .btn-filter:hover { background: #2d3e5a; color: white; }
        
        .btn-filter.active[data-filter="todos"] { border-color: var(--text-main); color: white; background: #334155; }
        .btn-filter.active[data-filter="ti"] { border-color: var(--ti-accent); color: var(--ti-accent); background: rgba(59, 130, 246, 0.1); }
        .btn-filter.active[data-filter="log"] { border-color: var(--log-accent); color: var(--log-accent); background: rgba(245, 158, 11, 0.1); }

        table { width: 100%; border-collapse: separate; border-spacing: 0 8px; }
        th { text-align: left; padding: 15px; color: var(--text-muted); text-transform: uppercase; font-size: 0.8rem; }
        
        tr.dispositivo { background: var(--card-bg); transition: transform 0.1s; }
        tr.dispositivo:hover { transform: scale(1.005); }
        
        td { padding: 18px 15px; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }
        td:first-child { border-left: 5px solid var(--border); border-radius: 8px 0 0 8px; }
        td:last-child { border-radius: 0 8px 8px 0; border-right: 1px solid var(--border); }

        .border-ti { border-left-color: var(--ti-accent) !important; }
        .border-log { border-left-color: var(--log-accent) !important; }
        
        code { background: rgba(255,255,255,0.1); padding: 4px 8px; border-radius: 4px; font-family: monospace; font-size: 1.1rem; }
        .status-pill { padding: 6px 15px; border-radius: 20px; font-size: 0.85rem; font-weight: bold; background: var(--success); color: #000; }
        
        /* Flag Vermelha de Novo Dispositivo */
        .novo-flag { height: 12px; width: 12px; background-color: var(--danger); border-radius: 50%; display: inline-block; margin-right: 10px; box-shadow: 0 0 10px var(--danger); animation: pulse-danger 1.5s infinite; }
        @keyframes pulse-danger { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }
        
        .no-devices { text-align: center; padding: 80px; color: var(--text-muted); background: var(--card-bg); border-radius: 8px; }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-title">
            <img src="/LOGO_DURAES_VETORIZADA.png" alt="Logo Durães" style="height: 75px; border-radius: 5px;">
            <div>
                <h1 style="margin: 0; padding-bottom: 5px;"> Cyberitu Monitor</h1>
                <p style="color: var(--text-muted); margin: 0;">Distribuidora Durães (Santarém/PA)</p>
            </div>
        </div>
        <div class="counters">
            <div class="counter-box ti"><div style="font-size: 11px; color: var(--text-muted);">T.I. / TECNOLOGIA</div><div class="counter-number" id="count-ti">0</div></div>
            <div class="counter-box log"><div style="font-size: 11px; color: var(--text-muted);">LOGÍSTICA</div><div class="counter-number" id="count-log">0</div></div>
        </div>
    </div>

    <div class="controls-row">
        <input type="text" id="searchInput" class="search-bar" placeholder="🔍 Pesquisar por Nome, IP ou Identificador...">
        <div class="filter-group">
            <button class="btn-filter active" data-filter="todos">🌐 Todos</button>
            <button class="btn-filter" data-filter="ti">💻 T.I.</button>
            <button class="btn-filter" data-filter="log">📦 Logística</button>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th width="15%">Setor</th>
                <th width="35%">Dispositivo</th>
                <th width="25%">Endereço IP</th>
                <th width="25%">Status na Rede</th>
            </tr>
        </thead>
        <tbody id="dispositivos-tbody"></tbody>
    </table>

    <script>
        let filtroSetor = 'todos';

        async function atualizarDashboard() {
            try {
                const response = await fetch(`/api/dados?t=${new Date().getTime()}`);
                const data = await response.json();
                const tbody = document.getElementById('dispositivos-tbody');
                const searchVal = document.getElementById('searchInput').value.toLowerCase();
                
                let html = '';
                let countTI = 0; let countLog = 0;

                const lista = Object.values(data).sort((a, b) => a.nome.localeCompare(b.nome));

                lista.forEach(dev => {
                    const ehTI = dev.setor.includes('T.I.');
                    if (ehTI) countTI++; else countLog++;

                    const bateFiltro = (filtroSetor === 'todos') || (filtroSetor === 'ti' && ehTI) || (filtroSetor === 'log' && !ehTI);
                    const bateBusca = dev.nome.toLowerCase().includes(searchVal) || dev.ip.includes(searchVal);

                    if (bateFiltro && bateBusca) {
                        const flag = dev.eh_novo ? '<span class="novo-flag" title="Recém conectado!"></span>' : '';
                        html += `
                            <tr class="dispositivo">
                                <td class="${ehTI ? 'border-ti' : 'border-log'}">${ehTI ? '💻 T.I.' : '📦 LOGÍSTICA'}</td>
                                <td>${flag}<strong>${dev.nome}</strong></td>
                                <td><code>${dev.ip}</code></td>
                                <td><span class="status-pill">ONLINE 🟢</span></td>
                            </tr>
                        `;
                    }
                });

                tbody.innerHTML = html || '<tr><td colspan="4" class="no-devices">Nenhum host encontrado.</td></tr>';
                document.getElementById('count-ti').innerText = countTI;
                document.getElementById('count-log').innerText = countLog;
            } catch (e) { console.error("Erro na atualização assíncrona:", e); }
        }

        // Lógica dos Botões de Filtro
        document.querySelectorAll('.btn-filter').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.btn-filter').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                filtroSetor = btn.getAttribute('data-filter');
                atualizarDashboard();
            });
        });

        document.getElementById('searchInput').addEventListener('input', atualizarDashboard);
        setInterval(atualizarDashboard, 3000); // Atualiza sem piscar a cada 3s
        atualizarDashboard();
    </script>
</body>
</html>
"""

# --------------------------------------------------------------------------
# ROTAS FLASK
# --------------------------------------------------------------------------
@app.route('/')
def index():
    return TEMPLATE_HTML

@app.route('/api/dados')
def api_dados():
    try:
        if os.path.exists(ESTADO_FILE):
            with open(ESTADO_FILE, "r", encoding="utf-8") as f:
                return jsonify(json.load(f))
    except: pass
    return jsonify({})

@app.route('/LOGO_DURAES_VETORIZADA.png')
def servir_logo():
    # Puxa o arquivo renomeado da raiz
    return send_from_directory(DIRETORIO_RAIZ, 'LOGO_DURAES_VETORIZADA.png')

# --------------------------------------------------------------------------
# INICIALIZAÇÃO
# --------------------------------------------------------------------------
if __name__ == "__main__":
    banner = """
  ____  _     _        _ _           _     _                 ____                    
 |  _ \(_)___| |_ _ __(_) |__  _   _(_) __| | ___  _ __ __ _|  _ \ _   _ _ __ __ _ ___ 
 | | | | / __| __| '__| | '_ \| | | | |/ _` |/ _ \| '__/ _` | | | | | | | '__/ _` / __|
 | |_| | \__ \ |_| |  | | |_) | |_| | | (_| | (_) | | | (_| | |_| | |_| | | | (_| \__ \\
 |____/|_|___/\__|_|  |_|_.__/ \__,_|_|\__,_|\___/|_|  \__,_|____/ \__,_|_|  \__,_|___/
                                                                                       
                       🤖 PAINEL DURÃES ONLINE - PORTA 5000
    """
    print("\033[96m" + banner + "\033[0m")
    app.run(host="0.0.0.0", port=5000, debug=False)