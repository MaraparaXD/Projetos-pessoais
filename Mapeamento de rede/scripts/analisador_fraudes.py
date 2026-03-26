import pandas as pd
import os

def gerar_relatorio_discrepancias():
    arquivo_inventario = "inventario_rede_duraes.xlsx"
    arquivo_log = "auditoria_conexoes.txt"

    # Verifica se os arquivos base existem
    if not os.path.exists(arquivo_inventario) or not os.path.exists(arquivo_log):
        print("Erro: Certifique-se de que os arquivos do Passo 1 (Excel) e Passo 2 (TXT) estão nesta pasta.")
        return

    print("--- Iniciando Cruzamento de Dados de Auditoria da Durães ---\n")

    # 1. Carrega o inventário da rede gerado pelo Nmap
    df_inventario = pd.read_excel(arquivo_inventario)
    
    # Cria um dicionário para busca rápida: {IP: (Hostname, MAC, Descricao)}
    mapa_rede = {}
    for index, row in df_inventario.iterrows():
        mapa_rede[row['IP']] = {
            'Hostname': row['Hostname'],
            'MAC': row['MAC Address'],
            'Descricao': row['Descrição']
        }

    # 2. Lê os acessos capturados no servidor
    alertas = []
    # Adicionado encoding para evitar problemas com o Bloco de Notas
    with open(arquivo_log, "r", encoding="utf-8") as log:
        linhas = log.readlines()
        
        # --- DEBUG: Mostra o que o Python está enxergando no arquivo ---
        print(f"[DEBUG] O script encontrou {len(linhas)} linhas no arquivo TXT.")
        
        for linha in linhas:
            print(f"[DEBUG] Lendo a linha: '{linha.strip()}'") 
            # --------------------------------------------------------------

            if "IP Suspeito/Ativo:" in linha:
                # Extrai o IP da linha de log
                ip_conectado = linha.split("IP Suspeito/Ativo:")[1].strip()
                data_hora = linha.split("|")[0].strip()
                porta = linha.split("|")[1].strip()

                print(f"[DEBUG] -> IP Extraído para verificação: '{ip_conectado}'")

                # 3. O Cruzamento (Procurando a Discrepância)
                if ip_conectado in mapa_rede:
                    dados_maquina = mapa_rede[ip_conectado]
                    
                    # Se a máquina não é um servidor conhecido, é um alerta!
                    if "Possível Intruso" in dados_maquina['Descricao'] or "Desconhecido" in dados_maquina['Descricao']:
                        alertas.append({
                            'Data/Hora': data_hora,
                            'Porta Alvo': porta,
                            'IP Ofensor': ip_conectado,
                            'Hostname': dados_maquina['Hostname'],
                            'MAC Address': dados_maquina['MAC'],
                            'Status': 'CRÍTICO - Dispositivo Desconhecido na Rede'
                        })
                else:
                    # O IP acessou o servidor, mas nem sequer apareceu no scan do Nmap
                    alertas.append({
                        'Data/Hora': data_hora,
                        'Porta Alvo': porta,
                        'IP Ofensor': ip_conectado,
                        'Hostname': 'NÃO ENCONTRADO',
                        'MAC Address': 'NÃO ENCONTRADO',
                        'Status': 'FANTASMA - IP não mapeado no inventário'
                    })

    # 4. Exibe e salva o relatório de discrepâncias
    print("\n--- Resultados da Análise ---")
    if alertas:
        df_alertas = pd.DataFrame(alertas)
        print("!!! DISCREPÂNCIAS ENCONTRADAS !!!\n")
        print(df_alertas[['Data/Hora', 'IP Ofensor', 'Hostname', 'Status']].to_string(index=False))
        
        # Salva o relatório de fraude para a gerência
        df_alertas.to_excel("relatorio_fraudes_duraes.xlsx", index=False)
        print("\n=> Relatório completo salvo como 'relatorio_fraudes_duraes.xlsx'.")
    else:
        print("Auditoria limpa. Nenhum dispositivo desconhecido acessou os servidores monitorados neste log.")

if __name__ == "__main__":
    gerar_relatorio_discrepancias()