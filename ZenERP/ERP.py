import streamlit as st
import pandas as pd
import pyodbc
import requests
import time

# ==============================================================================
# 1. CONFIGURAÇÕES E CONEXÃO BLINDADA
# ==============================================================================
st.set_page_config(page_title="ZenERP", layout="wide", page_icon="🚛")

# Estilos CSS (Dark Mode Clean)
st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #262730;
        border: 1px solid #464b5f;
        padding: 15px;
        border-radius: 8px;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# ⚠️ SUA SENHA AQUI
SENHA_AZURE = "Tiago23072004!"

def get_connection():
    server = 'zendarerp.database.windows.net'
    database = 'zendatabase'
    username = 'zendar'
    driver = '{ODBC Driver 18 for SQL Server}'
    
    conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={SENHA_AZURE};Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=30;'
    
    try:
        return pyodbc.connect(conn_str)
    except Exception as e:
        st.error("❌ Erro de Conexão")
        return None

# Dicionário de Estados
ESTADOS_BRASIL = {
    'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas', 'BA': 'Bahia',
    'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo', 'GO': 'Goiás',
    'MA': 'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul', 'MG': 'Minas Gerais',
    'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná', 'PE': 'Pernambuco', 'PI': 'Piauí',
    'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte', 'RS': 'Rio Grande do Sul',
    'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina', 'SP': 'São Paulo',
    'SE': 'Sergipe', 'TO': 'Tocantins'
}

# Função de Navegação (Essencial para os botões funcionarem)
def navegar_para(pagina):
    st.session_state['pagina_atual'] = pagina

# ==============================================================================
# 2. ROTINAS DO SISTEMA
# ==============================================================================

def dashboard_home():
    st.title("📊 Visão Geral")
    conn = get_connection()
    if conn:
        try:
            # Consultas SQL
            df_metas = pd.read_sql("""
                SELECT c.nome as Vendedor, SUM(m.valor) as Meta 
                FROM metas m JOIN colaboradores c ON m.id_colaborador = c.id 
                GROUP BY c.nome ORDER BY Meta DESC
            """, conn)
            
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM produtos")
            total_skus = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM clientes")
            total_clientes = cursor.fetchone()[0]
            
            # KPIs
            with st.container():
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("💰 Faturamento", "R$ 0,00", "0%")
                c2.metric("👥 Clientes", f"{total_clientes}", "Base")
                c3.metric("📦 Mix Produtos", f"{total_skus}", "Ativos")
                c4.metric("👔 Equipe", f"{len(df_metas)}", "RCAs")
            
            st.divider()
            
            col_graf, col_info = st.columns([2, 1])
            with col_graf:
                st.subheader("Ranking de Metas")
                st.bar_chart(df_metas.set_index("Vendedor"), color="#4caf50", horizontal=True)
            
            with col_info:
                st.info(f"💡 Base de dados operando com **{total_clientes} clientes** cadastrados.")

        except Exception as e:
            st.error(f"Erro no Dashboard: {e}")
        finally:
            conn.close()

def rotina_302_cadastrar_cliente():
    st.header("👥 Rotina 302 - Cadastrar Cliente")
    
    if 'end_rua' not in st.session_state: st.session_state['end_rua'] = ''
    if 'end_bairro' not in st.session_state: st.session_state['end_bairro'] = ''
    if 'end_cidade' not in st.session_state: st.session_state['end_cidade'] = ''
    if 'end_uf' not in st.session_state: st.session_state['end_uf'] = 'PA'

    with st.expander("🔍 Buscar Endereço (BrasilAPI)", expanded=True):
        col_cep, col_btn = st.columns([3, 1])
        cep_input = col_cep.text_input("CEP", max_chars=8)
        if col_btn.button("Buscar"):
            if len(cep_input) == 8:
                try:
                    url = f"https://brasilapi.com.br/api/cep/v1/{cep_input}"
                    response = requests.get(url)
                    if response.status_code == 200:
                        dados = response.json()
                        st.session_state['end_rua'] = dados.get('street', '')
                        st.session_state['end_bairro'] = dados.get('neighborhood', '')
                        st.session_state['end_cidade'] = dados.get('city', '')
                        st.session_state['end_uf'] = dados.get('state', 'PA')
                        st.success("Achamos!")
                    else:
                        st.warning("CEP desconhecido.")
                except:
                    st.error("Erro API.")

    with st.form("form_302"):
        c1, c2 = st.columns([1, 2])
        cpf = c1.text_input("CPF/CNPJ")
        nome = c2.text_input("Nome / Razão Social")
        
        r1, r2 = st.columns([3, 1])
        rua = r1.text_input("Logradouro", value=st.session_state['end_rua'])
        num = r2.text_input("Número")
        
        r3, r4, r5 = st.columns([2, 2, 1])
        bairro = r3.text_input("Bairro", value=st.session_state['end_bairro'])
        cidade = r4.text_input("Cidade", value=st.session_state['end_cidade'])
        
        uf_idx = list(ESTADOS_BRASIL.keys()).index(st.session_state['end_uf']) if st.session_state['end_uf'] in ESTADOS_BRASIL else 13
        uf = r5.selectbox("UF", list(ESTADOS_BRASIL.keys()), index=uf_idx)

        if st.form_submit_button("💾 Salvar Cliente"):
            conn = get_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO clientes (cpf_cnpj, nome, cep, logradouro, numero, bairro, cidade, uf)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (cpf, nome, cep_input, rua, num, bairro, cidade, uf))
                    conn.commit()
                    st.toast(f"Cliente {nome} cadastrado!", icon="✅")
                    time.sleep(1)
                except Exception as e:
                    st.error(f"Erro: {e}")
                finally:
                    conn.close()

def rotina_332_cadastro_produto():
    st.header("📦 Rotina 332 - Cadastrar Produto")
    conn = get_connection()
    if conn:
        with st.form("form_332"):
            df_forn = pd.read_sql("SELECT id, nome_fantasia FROM fornecedores", conn)
            lista_forn = dict(zip(df_forn['nome_fantasia'], df_forn['id']))
            
            nome = st.text_input("Descrição")
            c1, c2, c3 = st.columns(3)
            cod_erp = c1.number_input("Cód. ERP", step=1)
            sku = c2.text_input("EAN")
            preco = c3.number_input("Preço", format="%.2f")
            forn_key = st.selectbox("Fornecedor", list(lista_forn.keys()))
            
            if st.form_submit_button("💾 Salvar Produto"):
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO produtos (id_fornecedor, codigo_erp, nome, sku, codigo_barras, preco)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (lista_forn[forn_key], cod_erp, nome, sku, sku, preco))
                    conn.commit()
                    st.success("Produto salvo!")
                except Exception as e:
                    st.error(f"Erro: {e}")
        conn.close()

def rotina_336_pedido_venda():
    st.header("🛒 Rotina 336 - Pedido de Venda")
    conn = get_connection()
    if conn:
        # Carrega Vendedores
        df_vend = pd.read_sql("SELECT c.id, c.nome FROM colaboradores c JOIN rcas r ON c.id_rca = r.id WHERE c.id_cargo = (SELECT id FROM cargos WHERE descricao='Vendedor')", conn)
        lista_vend = dict(zip(df_vend['nome'], df_vend['id']))
        
        # Carrega Produtos
        df_prod = pd.read_sql("SELECT id, nome, preco, codigo_erp FROM produtos", conn)
        lista_prod = {f"{row['codigo_erp']} - {row['nome']} (R$ {row['preco']:.2f})": row['id'] for i, row in df_prod.iterrows()}
        
        # Carrega Clientes (NOVIDADE!)
        df_cli = pd.read_sql("SELECT id, nome FROM clientes", conn)
        lista_cli = dict(zip(df_cli['nome'], df_cli['id'])) if not df_cli.empty else {"Sem clientes cadastrados": 0}

        with st.form("form_336"):
            c1, c2 = st.columns(2)
            vendedor_key = c1.selectbox("Vendedor (RCA)", list(lista_vend.keys()))
            cliente_key = c2.selectbox("Selecione o Cliente", list(lista_cli.keys()))
            
            st.divider()
            c3, c4 = st.columns([3, 1])
            prod_key = c3.selectbox("Produto", list(lista_prod.keys()))
            qtd = c4.number_input("Qtd", min_value=1, value=1)
            
            if st.form_submit_button("✅ Fechar Pedido"):
                if lista_cli.get(cliente_key) == 0:
                    st.error("Cadastre um cliente primeiro!")
                else:
                    try:
                        cursor = conn.cursor()
                        id_vend = lista_vend[vendedor_key]
                        id_prod = lista_prod[prod_key]
                        
                        # Preço e Total
                        preco = df_prod[df_prod['id'] == id_prod]['preco'].values[0]
                        total = float(preco) * qtd
                        
                        # 1. Cria Pedido
                        cursor.execute("INSERT INTO pedidos (id_vendedor, valor_total) VALUES (?, ?)", (id_vend, total))
                        cursor.execute("SELECT @@IDENTITY")
                        id_pedido = cursor.fetchone()[0]
                        
                        # 2. Cria Item
                        cursor.execute("INSERT INTO pedidos_itens (id_pedido, id_produto, qtd, total_item) VALUES (?, ?, ?, ?)", 
                                       (id_pedido, id_prod, qtd, total))
                        conn.commit()
                        st.balloons()
                        st.success(f"Pedido Nº {id_pedido} gerado! Total: R$ {total:.2f}")
                    except Exception as e:
                        st.error(f"Erro: {e}")
        conn.close()

def rotina_1452_faturamento():
    st.header("📄 Rotina 1452 - Emissão NFe")
    conn = get_connection()
    if conn:
        # Mostra os últimos 10 pedidos
        query = """
        SELECT TOP 10 
            p.id as [Nº Pedido], 
            p.data_emissao as [Data], 
            c.nome as [Vendedor], 
            p.valor_total as [Total R$]
        FROM pedidos p 
        JOIN colaboradores c ON p.id_vendedor = c.id 
        ORDER BY p.id DESC
        """
        try:
            df = pd.read_sql(query, conn)
            st.dataframe(df, use_container_width=True)
            
            if not df.empty:
                col1, col2 = st.columns([3,1])
                n_ped = col1.number_input("Nº Pedido para Faturar", min_value=1)
                if col2.button("🖨️ Emitir Nota"):
                    if n_ped in df['Nº Pedido'].values:
                        with st.spinner('Transmitindo para SEFAZ...'):
                            time.sleep(2)
                        st.success(f"Nota Fiscal do pedido {n_ped} autorizada!")
                    else:
                        st.warning("Pedido não encontrado na lista.")
            else:
                st.info("Nenhum pedido para faturar.")
        except Exception as e:
            st.error(f"Erro ao buscar pedidos: {e}")
        conn.close()

# ==============================================================================
# 3. NAVEGAÇÃO
# ==============================================================================
def main():
    if 'logado' not in st.session_state: st.session_state['logado'] = False
    if 'pagina_atual' not in st.session_state: st.session_state['pagina_atual'] = "Dashboard"

    # LOGIN
    if not st.session_state['logado']:
        c1, c2, c3 = st.columns([1,1,1])
        with c2:
            st.title("🔐 ZenERP")
            u = st.text_input("Usuário")
            p = st.text_input("Senha", type="password")
            if st.button("Entrar"):
                if u == "admin" and p == "123":
                    st.session_state['logado'] = True
                    st.rerun()
                else:
                    st.error("Login inválido")
        return

    # SIDEBAR COMPLETA
    with st.sidebar:
        st.title("🚚 ZenERP")
        st.write("Logado: **Tiago Leão**")
        
        busca = st.text_input("🔍 Ir para...", placeholder="Ex: 336")
        if busca:
            if "302" in busca: st.session_state['pagina_atual'] = "302"
            elif "336" in busca: st.session_state['pagina_atual'] = "336"
            elif "332" in busca: st.session_state['pagina_atual'] = "332"
            elif "1452" in busca: st.session_state['pagina_atual'] = "1452"
        
        st.divider()
        st.button("📊 Dashboard", on_click=navegar_para, args=("Dashboard",), use_container_width=True)
        
        with st.expander("📂 Vendas / Clientes", expanded=True):
            st.button("336 - Pedido de Venda", on_click=navegar_para, args=("336",), use_container_width=True)
            st.button("302 - Cadastrar Cliente", on_click=navegar_para, args=("302",), use_container_width=True)
        
        with st.expander("📦 Produtos"):
            st.button("332 - Cadastrar Produto", on_click=navegar_para, args=("332",), use_container_width=True)
            
        with st.expander("💰 Financeiro"):
            st.button("1452 - Faturamento", on_click=navegar_para, args=("1452",), use_container_width=True)
        
        if st.button("Sair"):
            st.session_state['logado'] = False
            st.rerun()

    # ROTEAMENTO
    pagina = st.session_state['pagina_atual']
    if pagina == "Dashboard": dashboard_home()
    elif pagina == "302": rotina_302_cadastrar_cliente()
    elif pagina == "332": rotina_332_cadastro_produto()
    elif pagina == "336": rotina_336_pedido_venda()
    elif pagina == "1452": rotina_1452_faturamento()

if __name__ == "__main__":
    main()