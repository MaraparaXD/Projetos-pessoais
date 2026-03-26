# ==============================================================================
# SISTEMA DE MONITORAMENTO UNIFICADO - DISTRIBUIDORA DURÃES (MWV)
# Arquivo: recebe_logs.py | Versão: 31.0 (COMPLETA - SEM RESUMOS)
# ==============================================================================

import socket
import os
import re
import json
import requests
import subprocess
import platform
import time
import threading
import hashlib
import random
import concurrent.futures
from datetime import datetime

# --------------------------------------------------------------------------
# CONFIGURAÇÕES DE CAMINHO (À PROVA DE FALHAS)
# --------------------------------------------------------------------------
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))

# Se o script estiver dentro da pasta 'scripts', volta um nível para achar 'dados'
if os.path.basename(DIRETORIO_ATUAL) == "scripts":
    DIRETORIO_RAIZ = os.path.dirname(DIRETORIO_ATUAL)
else:
    DIRETORIO_RAIZ = DIRETORIO_ATUAL

MAP_FILE = os.path.join(DIRETORIO_RAIZ, "dados", "dispositivos.json")
ESTADO_FILE = os.path.join(DIRETORIO_RAIZ, "dados", "estado_atual.json")

# --------------------------------------------------------------------------
# CONFIGURAÇÕES DE REDE (CORRIGIDAS PARA A DURÃES)
# --------------------------------------------------------------------------
URL_LOGISTICA = "http://192.168.1.244:8080"  # IP do Roteador Intelbras
USUARIO_ROTEADOR = "admin"
SENHA_ROTEADOR = "260832leo"

REDE_TI_PREFIXO = "192.168.1."
IP_ESCUTA_SYSLOG = "0.0.0.0"
PORTA_SYSLOG = 514

# --------------------------------------------------------------------------
# ESTADO GLOBAL E MEMÓRIA
# --------------------------------------------------------------------------
lock_dados = threading.Lock()
dispositivos_ativos = {}      # Quem está online no momento
dispositivos_conhecidos = set() # Memória para evitar flag vermelha em conhecidos

# Garante que a pasta de dados existe
os.makedirs(os.path.dirname(ESTADO_FILE), exist_ok=True)

# --------------------------------------------------------------------------
# FUNÇÕES DE APOIO
# --------------------------------------------------------------------------

def carregar_mapeamento_nomes():
    """Busca o 'RG' dos aparelhos no dispositivos.json"""
    if os.path.exists(MAP_FILE):
        try:
            with open(MAP_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def salvar_estado_no_json():
    """Exporta os dados para o dashboard ler"""
    with lock_dados:
        try:
            with open(ESTADO_FILE, "w", encoding="utf-8") as f:
                json.dump(dispositivos_ativos, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"❌ Erro ao salvar estado: {e}")

def registrar_dispositivo(id_unico, ip, nome_padrao, setor):
    """id_unico: IP na logística ou MAC no T.I."""
    agora_ts = time.time()
    nomes_map = carregar_mapeamento_nomes()
    
    nome_final = nomes_map.get(id_unico, nome_padrao)
    chave_dashboard = f"{setor[:3].upper()}-{id_unico}"

    with lock_dados:
        # Lógica da Flag Vermelha (Piscante no Dashboard)
        eh_novo = id_unico not in dispositivos_conhecidos
        
        if eh_novo:
            dispositivos_conhecidos.add(id_unico)
            print(f"🚩 [Cyberitu] NOVO EM {setor.upper()}: {nome_final} ({ip})")

        dispositivos_ativos[chave_dashboard] = {
            "ip": ip,
            "nome": nome_final,
            "setor": setor,
            "ultimo_sinal": agora_ts,
            "eh_novo": eh_novo,
            "id_real": id_unico
        }

# --------------------------------------------------------------------------
# MOTOR LOGÍSTICA (BYPASS INTELBRAS)
# --------------------------------------------------------------------------

def realizar_login_logistica():
    sessao = requests.Session()
    hash_senha = hashlib.md5(SENHA_ROTEADOR.encode('utf-8')).hexdigest()
    
    payload = {"username": USUARIO_ROTEADOR, "password": hash_senha}
    headers = {
        "Referer": f"{URL_LOGISTICA}/login.html",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 Cyberitu/1.0"
    }
    try:
        res = sessao.post(f"{URL_LOGISTICA}/login/Auth", data=payload, headers=headers, timeout=5)
        if res.status_code == 200:
            return sessao
    except:
        return None

def tarefa_logistica():
    print("📦 [Motor] Logística conectado em 192.168.1.244")
    sessao = realizar_login_logistica()
    
    while True:
        if not sessao:
            sessao = realizar_login_logistica()
            time.sleep(10)
            continue
        
        try:
            url_list = f"{URL_LOGISTICA}/goform/getOnlineList?{random.random()}"
            res = sessao.get(url_list, headers={"X-Requested-With": "XMLHttpRequest"}, timeout=10)
            
            if res.status_code == 200:
                texto = res.text
                if "<!DOCTYPE html>" in texto: # Sessão expirou
                    sessao = None
                    continue
                
                # Procura IPs da rede interna 10.0.0.X da logística
                ips_encontrados = re.findall(r'10\.0\.0\.\d+', texto)
                for ip in set(ips_encontrados):
                    if ip == "10.0.0.1": continue
                    registrar_dispositivo(ip, ip, f"Logística {ip}", "Logística")
            else:
                sessao = None
        except:
            sessao = None
        
        salvar_estado_no_json()
        time.sleep(25)

# --------------------------------------------------------------------------
# MOTOR T.I. (SCANNER TURBO + SYSLOG)
# --------------------------------------------------------------------------

def checar_presenca(ip):
    sistema = platform.system().lower()
    cmd = ["ping", "-n" if sistema == "windows" else "-c", "1", "-w", "200", ip]
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

def escanear_ip_ti(ip):
    if checar_presenca(ip):
        registrar_dispositivo(ip, ip, f"Host {ip}", "T.I.")

def tarefa_scanner_ti():
    print("⚡ [Motor] Scanner T.I. Turbo Ativo")
    while True:
        ips = [f"{REDE_TI_PREFIXO}{i}" for i in range(2, 255) if i != 244]
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            executor.map(escanear_ip_ti, ips)
        
        salvar_estado_no_json()
        time.sleep(20)

def tarefa_syslog_dhcp():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        servidor.bind((IP_ESCUTA_SYSLOG, PORTA_SYSLOG))
        print("🚀 [Motor] Receptor Syslog (UDP 514) Ativo")
    except:
        print("⚠️ Erro: Porta 514 ocupada. Syslog desativado.")
        return

    while True:
        try:
            dados, _ = servidor.recvfrom(4096)
            msg = dados.decode(errors='ignore')
            if "DHCP" in msg and "ACK" in msg:
                mac = re.search(r'([0-9A-F]{2}[:-]){5}([0-9A-F]{2})', msg, re.I)
                ip = re.search(r'192\.168\.1\.\d+', msg)
                if mac and ip:
                    registrar_dispositivo(mac.group(0).upper(), ip.group(0), "Novo via DHCP", "T.I.")
                    salvar_estado_no_json()
        except:
            continue

# --------------------------------------------------------------------------
# FAXINA E RELATÓRIO
# --------------------------------------------------------------------------

def tarefa_faxina():
    """Remove dispositivos que sumiram há 5 minutos"""
    while True:
        time.sleep(30)
        agora = time.time()
        with lock_dados:
            for k in list(dispositivos_ativos.keys()):
                if agora - dispositivos_ativos[k]["ultimo_sinal"] > 300:
                    del dispositivos_ativos[k]
        salvar_estado_no_json()

def tarefa_relatorio_voz():
    while True:
        time.sleep(60)
        with lock_dados:
            qtd_log = sum(1 for d in dispositivos_ativos.values() if d['setor'] == 'Logística')
            qtd_ti = sum(1 for d in dispositivos_ativos.values() if d['setor'] == 'T.I.')
            print(f"\n📊 [Cyberitu] STATUS ATUAL | Logística: {qtd_log} | T.I.: {qtd_ti}")

# --------------------------------------------------------------------------
# EXECUÇÃO PRINCIPAL
# --------------------------------------------------------------------------

if __name__ == "__main__":
    banner = """
    =======================================================
       ___  _   _  ____    _    _____ ____  
      |  _ \| | | |  _ \  / \  | ____/ ___| 
      | | | | | | | |_) |/ _ \ |  _| \___ \ 
      | |_| | |_| |  _ < / ___ \| |___ ___) |
      |____/ \___/|_| \_/_/   \_\_____|____/ 
                                             
             🤖 SISTEMA CYBERITU ONLINE - MWV
    =======================================================
    """
    print("\033[94m" + banner + "\033[0m")
    
    # Pré-carrega quem já conhecemos no dispositivos.json
    map_inicial = carregar_mapeamento_nomes()
    for chave in map_inicial.keys():
        dispositivos_conhecidos.add(chave)

    # Dispara as Threads de Monitoramento
    threading.Thread(target=tarefa_logistica, daemon=True).start()
    threading.Thread(target=tarefa_scanner_ti, daemon=True).start()
    threading.Thread(target=tarefa_syslog_dhcp, daemon=True).start()
    threading.Thread(target=tarefa_faxina, daemon=True).start()
    threading.Thread(target=tarefa_relatorio_voz, daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Encerrando Cyberitu... Até logor!")