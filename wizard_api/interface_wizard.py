import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA E MEMÓRIA ---
st.set_page_config(page_title="A Visão do Mago", layout="wide", page_icon="🧙‍♂️")

# Memória anti-amnésia
if 'dados_processados' not in st.session_state:
    st.session_state.dados_processados = None
if 'meta_dados' not in st.session_state:
    st.session_state.meta_dados = None

# Customização de CSS
st.markdown("""
    <style>
    .stApp { background-color: #1a1c29; color: #e6e6e6; }
    div[data-testid="metric-container"] {
        background-color: #2e3046; border-radius: 12px; padding: 20px;
        border: 1px solid #3b3b54; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    div[data-testid="stTabs"] { background-color: #2e3046; border-radius: 8px; padding: 5px; }
    button[data-testid="stTabsTabActive"] { color: #ff1744 !important; border-bottom: 3px solid #ff1744 !important; }
    .stButton > button { background-color: #2979ff; color: white; font-weight: bold; border-radius: 8px; }
    .stButton > button:hover { background-color: #004ecb; }
    </style>
""", unsafe_allow_html=True)

st.title("A Visão do Mago🧙‍♂️")
st.markdown("Plataforma de inteligência para gestão proativa de estoque e automação de suprimentos.")
st.markdown("---")

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Configuração de Runa")
api_key = st.sidebar.text_input("Runa de Segurança", type="password", value="1234")
st.sidebar.markdown("---")
if st.sidebar.button("Reescrever Grimório"):
    st.session_state.dados_processados = None
    st.session_state.meta_dados = None
    st.rerun()

# --- ÁREA PRINCIPAL: UPLOAD ---
st.subheader("1. Ingestão de Dados (CSV)")
uploaded_file = st.file_uploader("Arraste o relatório de movimentação aqui", type=["csv"])

if uploaded_file is not None:
    if st.button("🚀 Iniciar Processamento e Análise", use_container_width=True, type="primary"):
        with st.spinner('Sintonizando com o SQL Server...'):
            files = {"file": uploaded_file.getvalue()}
            headers = {"x-api-key": api_key}
            try:
                response = requests.post("http://127.0.0.1:8000/v1/analyze", files=files, headers=headers)
                if response.status_code == 200:
                    result = response.json()
                    st.session_state.dados_processados = result.get('data', [])
                    st.session_state.meta_dados = result.get('metadata', {})
                else:
                    try: erro = response.json().get('detail', 'Erro interno.')
                    except: erro = response.text
                    st.error(f"🚨 Erro no Motor: {erro}")
            except Exception as e:
                st.error(f"🚨 Falha de Comunicação: {e}")

# --- RENDERIZAÇÃO DO DASHBOARD (Lê da Memória) ---
if st.session_state.dados_processados is not None:
    df = pd.DataFrame(st.session_state.dados_processados)
    meta = st.session_state.meta_dados
    
    # Cálculos Financeiros
    df['deficit_unidades'] = df.apply(lambda x: x['quantidade'] - x['estoque_atual'] if x['quantidade'] > x['estoque_atual'] else 0, axis=1)
    df['custo_reposicao_item'] = df['deficit_unidades'] * df['preco']
    custo_total_reposicao = df['custo_reposicao_item'].sum()

    st.markdown("---")
    st.subheader("📊 Indicadores de Performance")
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("📦 Volume Processado", f"{meta.get('total_itens', 0)} Itens")
    col2.metric("⚠️ Alertas de Ruptura", meta.get('alertas_gerados', 0), delta="Requer Atenção", delta_color="inverse")
    col3.metric("💰 Custo de Reposição Total", f"R$ {custo_total_reposicao:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), delta="Orçamento", delta_color="off")
    col4.metric("⏱️ Tempo do Motor", meta.get('tempo', "0s"))

    st.markdown("---")

    # --- ABAS ---
    tab1, tab2, tab3 = st.tabs(["📋 Tabela e Filtros", "📈 Painel de Gráficos", "📥 Exportação"])

    # ABA 1: TABELA E FILTROS AVANÇADOS (Estão de volta!)
    with tab1:
        st.markdown("### 🔍 Central de Pesquisa")
        f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
        
        with f_col1:
            busca_livre = st.text_input("🔍 Pesquisar Produto ou Código", placeholder="Ex: V100, 1042...")
        with f_col2:
            lista_vendedores = df['vendedor'].unique().tolist()
            filtro_vendedor = st.multiselect("👤 Vendedor", lista_vendedores, placeholder="Todos")
        with f_col3:
            opcoes_status = ["Mostrar Tudo", "✅ LIBERADOS", "🚨 ESTOQUE INSUFICIENTE"]
            filtro_status = st.selectbox("📦 Status Logístico", opcoes_status)

        st.markdown("---")
        df_exibicao = df.copy()
        
        if busca_livre:
            busca = busca_livre.lower().strip()
            df_exibicao = df_exibicao[df_exibicao['produto'].str.lower().str.contains(busca) | df_exibicao['id'].astype(str).str.contains(busca)]
        if filtro_vendedor:
            df_exibicao = df_exibicao[df_exibicao['vendedor'].isin(filtro_vendedor)]
        if filtro_status == "✅ LIBERADOS":
            df_exibicao = df_exibicao[df_exibicao['status_logistico'] == 'LIBERADO']
        elif filtro_status == "🚨 ESTOQUE INSUFICIENTE":
            df_exibicao = df_exibicao[df_exibicao['status_logistico'] == 'ESTOQUE_INSUFICIENTE']
        
        def color_status(val):
            color = '#ff1744' if val == 'ESTOQUE_INSUFICIENTE' else '#28a745'
            return f'background-color: {color}; color: white; font-weight: bold; text-align: center'

        st.dataframe(df_exibicao.drop(columns=['deficit_unidades', 'custo_reposicao_item']).style.map(color_status, subset=['status_logistico']), use_container_width=True, height=350)
        
        if df_exibicao.empty:
            st.warning("Nenhum item encontrado com esses filtros.")

    # ABA 2: NOVO PAINEL DE GRÁFICOS MULTIPLOS
    with tab2:
        st.markdown("### 📊 Análise de Operação e Anomalias")
        
        # Coloca dois gráficos lado a lado
        col_graf1, col_graf2 = st.columns(2)
        
        # Gráfico 1: O Rombo de Estoque
        with col_graf1:
            st.markdown("#### 🚨 Itens com Maior Déficit")
            df_rombo = df[df['deficit_unidades'] > 0]
            if not df_rombo.empty:
                df_rombo = df_rombo.sort_values(by='deficit_unidades', ascending=True).tail(5)
                df_rombo['Impacto R$'] = df_rombo['custo_reposicao_item'].apply(lambda x: f"R$ {x:,.2f}")
                fig_rombo = px.bar(df_rombo, x='deficit_unidades', y='produto', orientation='h', text='deficit_unidades', hover_data=['Impacto R$'], color_discrete_sequence=['#ff1744'])
                fig_rombo.update_traces(textposition='outside', marker_line_width=0)
                fig_rombo.update_layout(plot_bgcolor='#2e3046', paper_bgcolor='#2e3046', font_color='#e6e6e6', xaxis=dict(showgrid=True, gridcolor='#3b3b54'), yaxis_title="", bargap=0.3, margin=dict(l=10, r=40, t=10, b=10))
                st.plotly_chart(fig_rombo, use_container_width=True)
            else:
                st.success("Estoque Equilibrado!")

        # Gráfico 2: Top Vendedores
        with col_graf2:
            st.markdown("#### 🏆 Top Vendedores")
            # Soma a quantidade pedida por cada vendedor
            df_vend = df.groupby('vendedor')['quantidade'].sum().reset_index().sort_values(by='quantidade', ascending=True)
            fig_vend = px.bar(df_vend, x='quantidade', y='vendedor', orientation='h', text='quantidade', color_discrete_sequence=['#2979ff'])
            fig_vend.update_traces(textposition='outside', marker_line_width=0)
            fig_vend.update_layout(plot_bgcolor='#2e3046', paper_bgcolor='#2e3046', font_color='#e6e6e6', xaxis=dict(showgrid=True, gridcolor='#3b3b54'), yaxis_title="", bargap=0.3, margin=dict(l=10, r=40, t=10, b=10))
            st.plotly_chart(fig_vend, use_container_width=True)

        st.markdown("---")
        
        # Gráfico 3: Análise de Z-Score (Anomalias de Preço)
        st.markdown("#### 📉 Auditoria de Preços ")
        st.info("💡 **Como ler isso:** Bolinhas muito à direita (vermelhas) indicam itens muito mais caros que a média. Bolinhas muito à esquerda (azuis) indicam itens baratos demais. Ótimo para achar erros de digitação no sistema!")
        
        # Gráfico de Dispersão (Scatter Plot) para o Z-Score
        fig_z = px.scatter(
            df, x='z_score', y='produto', color='z_score', size='preco',
            hover_data=['preco', 'vendedor'],
            color_continuous_scale='RdBu_r', # Escala Azul (barato) para Vermelho (caro)
            labels={'z_score': 'Desvio Padrão', 'produto': ''}
        )
        fig_z.update_layout(plot_bgcolor='#2e3046', paper_bgcolor='#2e3046', font_color='#e6e6e6', xaxis=dict(showgrid=True, gridcolor='#3b3b54', zeroline=True, zerolinecolor='#e6e6e6'), yaxis=dict(showgrid=True, gridcolor='#3b3b54'), margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_z, use_container_width=True)

    # ABA 3: EXPORTAÇÃO
    with tab3:
        st.markdown("### Download de Relatórios Formatados")
        col_down1, col_down2 = st.columns(2)
        df_export = df.drop(columns=['deficit_unidades', 'custo_reposicao_item'])
        
        csv_data = df_export.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
        with col_down1:
            st.download_button("📥 Baixar CSV", data=csv_data, file_name="auditoria_wizard.csv", mime="text/csv", use_container_width=True)

        buffer_excel = io.BytesIO()
        with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Auditoria_Estoque')
        with col_down2:
            st.download_button("📊 Baixar Excel", data=buffer_excel.getvalue(), file_name="auditoria_wizard.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary", use_container_width=True)