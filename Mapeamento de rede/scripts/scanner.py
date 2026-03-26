import nmap
import pandas as pd
import os

# --- NAVEGAÇÃO INTELIGENTE DE PASTAS ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) # Pasta 'scripts'
BASE_DIR = os.path.dirname(SCRIPT_DIR)                  # Pasta raiz 'Mini-SIEM Duraes'
DADOS_DIR = os.path.join(BASE_DIR, "dados")             # Pasta 'dados'

# Cria a pasta 'dados' se ela ainda não existir
os.makedirs(DADOS_DIR, exist_ok=True)

# Caminho do Nmap no sistema
NMAP_PATH = [r"C:\Program Files (x86)\Nmap\nmap.exe"]

# Lista Mestre de Servidores
SERVIDORES_DURAES = {
    '192.168.1.2': 'TS Antigo (VM)',
    '192.168.1.3': 'TS Novo (Dell Led Azul)',
    '192.168.1.88': 'VM Sellers (no .101)',
    '192.168.1.98': 'BI Tarkuss',
    '192.168.1.99': 'Maxima Tech (Físico - Host Bsoft)',
    '192.168.1.101': 'VM HOST (Físico)',
    '192.168.1.108': 'BSOFT Office (VM)',
    '192.168.1.109': 'BSOFT Tapajos (VM)',
    '192.168.1.130': 'VMSERVER (API REPPOS)',
    '192.168.1.180': 'Winthor Remoto (VPN)',
    '192.168.1.202': 'WTA',
    '192.168.1.204': 'VM Ware (Host TS Antigo/Winthor)',
    '192.168.1.206': 'NFE Docfiscal'
}

def scan_duraes():
    try:
        nm = nmap.PortScanner(nmap_search_path=NMAP_PATH)
        print("--- Iniciando Mapeamento Durães (Rede 192.168.1.0/24) ---")
        
        nm.scan(hosts='192.168.1.0/24', arguments='-sn')
        
        resultados = []
        for host in nm.all_hosts():
            ip = host
            mac = nm[host]['addresses'].get('mac', 'Não detectado')
            vendor = nm[host]['vendor'].get(mac, 'Desconhecido')
            hostname = nm[host].hostname() if nm[host].hostname() else "Sem Nome"
            
            descricao = SERVIDORES_DURAES.get(ip, "PC Usuário / Possível Intruso")
            
            resultados.append({
                'IP': ip,
                'Hostname': hostname,
                'MAC Address': mac,
                'Fabricante': vendor,
                'Descrição': descricao
            })

        df = pd.DataFrame(resultados)
        
        # Salva o arquivo dinamicamente na pasta DADOS
        caminho_saida = os.path.join(DADOS_DIR, "inventario_rede_duraes.xlsx")
        df.to_excel(caminho_saida, index=False)
        
        print(f"\nSucesso! {len(resultados)} dispositivos encontrados.")
        print(f"Arquivo salvo em: {caminho_saida}")

    except Exception as e:
        print(f"Erro ao rodar o scanner: {e}")

if __name__ == "__main__":
    scan_duraes()