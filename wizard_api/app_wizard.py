import streamlit as st
import pandas as pd
import requests
import io

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Wizard Tech - Dashboard Duraes",
    page_icon="🧙‍♂️",
    layout="wide"
)

# 2. CONFIGURAÇÕES DE INTEGRAÇÃO (Ajuste se necessário)
API_URL_ANALYZE = "http://localhost:8000/v1/analyze"
API_URL_EXCEL = "http://localhost:8000/v1/export/excel"
DEFAULT_KEY = "SUA_CHAVE_SECRETA"

# 3. INTERFACE LATERAL (Sidebar)
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1548/1548784.png", width=100)
    st.title("Configurações")
    api_key = st.text_input("Chave de Segurança (API Key)", type="password", value=DEFAULT_KEY)
    st.divider()
    st.info("Este portal se conecta à Engine v4.2.1 para saneamento automático de dados via SQL Server.")

# 4. CORPO PRINCIPAL
st.title("🧙‍♂️ Wizard Tech Engine - Dashboard")
st.markdown("### Processamento Universal de Dados - Distribuidora Duraes")

uploaded_file = st.file_uploader("Arraste o arquivo CSV da distribuidora aqui", type="csv")

if uploaded_file is not None:
    # Preparando a requisição para a API
    headers = {"x-api-key": api_key}
    files = {"file": ("arquivo.csv", uploaded_file.getvalue(), "text/csv")}
    
    with st.spinner("Conjurando dados da ENGINE no SQL Server..."):
        try:
            # Chamada para a rota de análise
            response = requests.post(API_URL_ANALYZE, headers=headers, files=files)
            
            if response.status_code == 200:
                res = response.json()
                
                # --- AQUI O 'df' É CRIADO COM SEGURANÇA ---
                df = pd.DataFrame(res['dados'])
                
                # --- MÉTRICAS DE TOPO ---
                st.divider()
                m1, m2, m3 = st.columns(3)
                m1.metric("Itens Processados", res['metadata']['total_itens'])
                m2.metric("Alertas de Estoque", res['metadata']['alertas_estoque'], delta="- Crítico", delta_color="inverse")
                m3.metric("Tempo de Resposta", res['metadata']['tempo_processamento'])

                # --- VISUALIZAÇÃO GRÁFICA ---
                st.write("### 📊 Visão Geral da Operação")
                col_chart, col_stats = st.columns([2, 1])

                with col_chart:
                    # Gráfico de barras do Status Logístico
                    status_counts = df['status_logistico'].value_counts()
                    st.bar_chart(status_counts, color="#1F4E78")

                with col_stats:
                    # Tabela de preços (Top 5 mais caros)
                    st.write("**Top 5 Itens (Maior Valor)**")
                    top5 = df.nlargest(5, 'preco')[['produto', 'preco']]
                    st.table(top5)

                # --- TABELA DE DADOS COMPLETA ---
                st.write("### 📋 Tabela de Dados Enriquecidos (SQL Server)")
                st.dataframe(df, use_container_width=True, hide_index=True)

                # --- CENTRAL DE EXPORTAÇÃO (Agora dentro do IF) ---
                st.divider()
                st.subheader("📥 Central de Exportação")
                st.write("Escolha o formato desejado para o relatório final:")
                
                exp_col1, exp_col2 = st.columns(2)

                with exp_col1:
                    # Exportação CSV otimizada para Excel Brasileiro (ponto e vírgula)
                    csv_data = df.to_csv(index=False, sep=';').encode('utf-8-sig')
                    st.download_button(
                        label="📄 Baixar CSV (Padrão Excel BR)",
                        data=csv_data,
                        file_name="wizard_relatorio_br.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

                with exp_col2:
                    # Chamada para a rota de EXCEL ESTILIZADO (XLSX)
                    if st.button("🎨 Gerar Excel Profissional (Colorido)", use_container_width=True):
                        with st.spinner("Estilizando colunas e aplicando cores..."):
                            # Re-envia o arquivo para a rota de exportação específica
                            excel_resp = requests.post(API_URL_EXCEL, headers=headers, files=files)
                            
                            if excel_resp.status_code == 200:
                                st.download_button(
                                    label="💾 Clique para Salvar o .xlsx",
                                    data=excel_resp.content,
                                    file_name="Relatorio_Duraes_Final.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    use_container_width=True
                                )
                            else:
                                st.error("Erro ao gerar Excel. Verifique se a rota /v1/export/excel existe no main.py.")

            elif response.status_code == 401:
                st.error("ERRO DE SEGURANÇA: A chave de API fornecida é inválida.")
            else:
                st.error(f"ERRO INTERNO: A API retornou status {response.status_code}. Detalhe: {response.text}")

        except Exception as e:
            st.error(f"FALHA DE CONEXÃO: Verifique se o comando 'python main.py' está rodando no terminal. Erro: {e}")

else:
    # Tela inicial amigável
    st.info("Aguardando upload do arquivo para iniciar o saneamento...")
    st.image("https://i.imgur.com/39p6V6L.png", caption="Fluxo de Dados: CSV -> Python -> SQL Server -> Dashboard")