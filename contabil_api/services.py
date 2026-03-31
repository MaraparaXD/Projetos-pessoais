import os
import requests
import oracledb
from dotenv import load_dotenv
from pathlib import Path

# Carrega as credenciais de banco e token do .env
base_path = Path(__file__).parent
load_dotenv(base_path / "dados.env")

class LedgerService:
    
    @staticmethod
    def get_winthor_data(cnpj_pesquisado: str, data_inicio: str, data_fim: str):
        user = os.getenv("ORACLE_USER")
        password = os.getenv("ORACLE_PASSWORD")
        dsn = os.getenv("ORACLE_CONNECT_STRING")
        try:
            conn = oracledb.connect(user=user, password=password, dsn=dsn)
            cursor = conn.cursor()
            
            ### Nota: Mude a query para uma que faça sentindo no seu banco de dados
            query = """
                SELECT c.CLIENTE, c.LIMCRED,
                    (SELECT SUM(f.VLTOTAL) FROM DURAES.PCNFSAID f WHERE f.CODCLI = c.CODCLI AND f.DTFAT BETWEEN TO_DATE(:inicio, 'YYYY-MM-DD') AND TO_DATE(:fim, 'YYYY-MM-DD')) as VENDAS,
                    (SELECT COUNT(*) FROM DURAES.PCPREST p WHERE p.CODCLI = c.CODCLI AND p.DTVENC < TRUNC(SYSDATE) AND p.DTPAG IS NULL) as QTD_ATRASO,
                    (SELECT SUM(p.VALOR) FROM DURAES.PCPREST p WHERE p.CODCLI = c.CODCLI AND p.DTVENC < TRUNC(SYSDATE) AND p.DTPAG IS NULL) as VALOR_ATRASO
                FROM DURAES.PCCLIENT c
                WHERE REGEXP_REPLACE(c.CGCENT, '[^0-9]', '') = :cnpj AND ROWNUM = 1
            """
            cursor.execute(query, cnpj=cnpj_pesquisado, inicio=data_inicio, fim=data_fim)
            res = cursor.fetchone()
            cursor.close()
            conn.close()
            if res:
                return {"nome_winthor": str(res[0] or "Não Identificado"), "limite": float(res[1] or 0), "vendas_periodo": float(res[2] or 0), "titulos_vencidos": int(res[3] or 0), "valor_em_atraso": float(res[4] or 0)}
            return None
        except Exception as e: 
            print(f"❌ ERRO ORACLE (Resumo): {e}")
            return None

    @staticmethod
    def get_monthly_sales(cnpj_limpo: str, data_inicio: str, data_fim: str):
        user = os.getenv("ORACLE_USER")
        password = os.getenv("ORACLE_PASSWORD")
        dsn = os.getenv("ORACLE_CONNECT_STRING")
        try:
            conn = oracledb.connect(user=user, password=password, dsn=dsn)
            cursor = conn.cursor()
            ### Nota: Mude a query para uma que faça sentindo no seu banco de dados
            query = """
                SELECT TO_CHAR(f.DTFAT, 'MM/YYYY') as MES, SUM(f.VLTOTAL) as TOTAL
                FROM DURAES.PCNFSAID f JOIN DURAES.PCCLIENT c ON f.CODCLI = c.CODCLI
                WHERE REGEXP_REPLACE(c.CGCENT, '[^0-9]', '') = :cnpj AND f.DTFAT BETWEEN TO_DATE(:inicio, 'YYYY-MM-DD') AND TO_DATE(:fim, 'YYYY-MM-DD')
                GROUP BY TO_CHAR(f.DTFAT, 'MM/YYYY'), TO_CHAR(f.DTFAT, 'YYYYMM') ORDER BY TO_CHAR(f.DTFAT, 'YYYYMM')
            """
            cursor.execute(query, cnpj=cnpj_limpo, inicio=data_inicio, fim=data_fim)
            res = cursor.fetchall()
            cursor.close()
            conn.close()
            return {"labels": [row[0] for row in res], "valores": [float(row[1] or 0) for row in res]}
        except Exception as e: 
            print(f"❌ ERRO ORACLE (Gráfico): {e}")
            return {"labels": [], "valores": []}

    @staticmethod
    async def buscar_dados_unificados(cnpj: str, data_inicio: str, data_fim: str):
        cnpj_limpo = "".join(filter(str.isdigit, cnpj))
        empresa_gov, situacao = None, "OFFLINE"
        dados_logistica = {"cidade": "Desconhecida", "uf": "-", "bairro": "Não Mapeado"}
        
        #  Integração Governo & ViaCEP
        try:
            resp = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}", timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                empresa_gov = data.get("razao_social")
                situacao = data.get("descricao_situacao_cadastral", "ATIVA")
                cep_cliente = data.get("cep")
                if cep_cliente:
                    cep_limpo = "".join(filter(str.isdigit, str(cep_cliente)))
                    resp_cep = requests.get(f"https://viacep.com.br/ws/{cep_limpo}/json/", timeout=3)
                    if resp_cep.status_code == 200:
                        data_cep = resp_cep.json()
                        if not data_cep.get("erro"):
                            dados_logistica = {"cidade": data_cep.get("localidade", "Desconhecida"), "uf": data_cep.get("uf", "-"), "bairro": data_cep.get("bairro", "Centro")}
        except Exception: 
            pass

        #  Integração ERP Winthor
        resumo = LedgerService.get_winthor_data(cnpj_limpo, data_inicio, data_fim)
        grafico = LedgerService.get_monthly_sales(cnpj_limpo, data_inicio, data_fim)

        if not resumo: return {"erro": "Cliente não localizado no banco de dados."}

        # Motor Neural de Crédito (CNPJ Analytics)
        limite = resumo["limite"]
        vendas = resumo["vendas_periodo"]
        atraso = resumo["valor_em_atraso"]
        status_gov = situacao.upper()

        sugestao = "MANTER CRÉDITO"
        motivo = "Movimentação financeira e risco dentro da normalidade."

        if status_gov in ["BAIXADA", "INAPTA", "SUSPENSA", "NULA"]:
            sugestao = "BLOQUEIO IMEDIATO"
            motivo = "CNPJ irregular na base da Receita Federal."
        elif atraso > (limite * 0.1) and limite > 0:
            sugestao = "REDUZIR OU BLOQUEAR"
            motivo = "Risco elevado. Atraso superior a 10% do limite aprovado."
        elif vendas > (limite * 1.5) and atraso == 0 and limite > 0:
            sugestao = "AUMENTAR LIMITE (+20%)"
            motivo = "Ótimo pagador. Volume de compras muito superior ao limite atual."
        elif vendas < (limite * 0.1) and limite > 0:
            sugestao = "REVISAR LIMITE (OCIOSO)"
            motivo = "Cliente comprando muito abaixo do limite aprovado."
        elif limite == 0 and vendas > 0 and atraso == 0:
            sugestao = "LIBERAR CRÉDITO"
            motivo = "Cliente sem limite cadastrado, mas com bom histórico de compras à vista."

        return {
            "empresa_real": empresa_gov if empresa_gov else resumo["nome_winthor"],
            "governo": {"situacao_cadastral": situacao},
            "logistica": dados_logistica,
            "winthor": {"limite": limite, "vendas_ano": vendas},
            "atrasos": {"quantidade": resumo["titulos_vencidos"], "valor_total": atraso},
            "evolucao_grafico": grafico,
            "inteligencia": {"sugestao": sugestao, "motivo": motivo}
        }
