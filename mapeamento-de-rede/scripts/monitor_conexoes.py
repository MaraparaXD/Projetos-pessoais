import subprocess
from datetime import datetime
import time

# --- CONFIGURAÇÃO ---
# Coloque aqui a porta do serviço que quer vigiar no servidor
# Ex: 8082 (BI Tarkuss), 1521 (Oracle WinThor), 3389 (TS/Acesso Remoto)
PORTA_ALVO = "8082" 

def monitorar_servidor():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando vigilância na porta {PORTA_ALVO}...\n")
    
    # Executa o comando netstat nativo do Windows silenciosamente
    comando = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
    
    ips_conectados = []
    
    # Vasculha o resultado do netstat
    for linha in comando.stdout.splitlines():
        # Queremos apenas conexões estabelecidas (ativas) na porta alvo
        if f":{PORTA_ALVO}" in linha and "ESTABLISHED" in linha:
            partes = linha.split()
            if len(partes) >= 3:
                # No Windows, a 3ª coluna é o Endereço Externo (IP do usuário)
                ip_remoto_completo = partes[2] 
                # Separa o IP da porta do usuário
                ip_remoto = ip_remoto_completo.split(':')[0]
                
                # Ignora a própria máquina
                if ip_remoto not in ['127.0.0.1', '0.0.0.0', '::1']:
                    ips_conectados.append(ip_remoto)

    # Remove IPs duplicados da lista
    ips_unicos = list(set(ips_conectados))
    
    if not ips_unicos:
        print("-> Nenhuma conexão externa ativa neste momento.")
    else:
        print("ALERTA: Seguintes IPs estão conectados agora:")
        for ip in ips_unicos:
            print(f" -> {ip}")

        # Salva em um log de auditoria para você investigar depois
        with open("auditoria_conexoes.txt", "a") as log:
            for ip in ips_unicos:
                registro = f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | Porta: {PORTA_ALVO} | IP Suspeito/Ativo: {ip}\n"
                log.write(registro)
        print("\nLog salvo no arquivo 'auditoria_conexoes.txt'.")

if __name__ == "__main__":
    # Roda a função
    monitorar_servidor()