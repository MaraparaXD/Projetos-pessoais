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
    '': 'TS Antigo (VM)',
    '': 'TS Novo (Dell Led Azul)',
    '': 'VM Sellers (no .101)',
    '': 'BI Tarkuss',
    '': 'Maxima Tech (Físico - Host Bsoft)',
    '': 'VM HOST (Físico)',
    '': 'BSOFT Office (VM)',
    '': 'BSOFT Tapajos (VM)',
    '': 'VMSERVER (API REPPOS)',
    '': 'Winthor Remoto (VPN)',
    '': 'WTA',
    '': 'VM Ware (Host TS Antigo/Winthor)',
    '': 'NFE Docfiscal'
}

def scan_duraes():
    try:
        nm = nmap.PortScanner(nmap_search_path=NMAP_PATH)
        print("--- Iniciando Mapeamento Durães (Rede #######/24) ---")
        
        nm.scan(hosts='#######/24', arguments='-sn')
        
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
