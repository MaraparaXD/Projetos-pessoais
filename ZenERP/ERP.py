import streamlit as st
import pandas as pd
import pyodbc
import requests
import time
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ==============================================================================
# 1. CONFIGURAÇÕES E CONEXÃO
# ==============================================================================
st.set_page_config(page_title="ZenERP", layout="wide", page_icon="🗂️", initial_sidebar_state="expanded")

# Mapa de rotinas: código -> (título, ícone) — usado no cabeçalho e na busca rápida
ROTINAS = {
    "Dashboard": {"codigo": "000", "titulo": "Visão Geral"},
    "301":       {"codigo": "301", "titulo": "Cadastrar Funcionário"},
    "302":       {"codigo": "302", "titulo": "Cadastrar Cliente"},
    "303":       {"codigo": "303", "titulo": "Consulta de Clientes"},
    "310":       {"codigo": "310", "titulo": "Cadastrar Fornecedor"},
    "332":       {"codigo": "332", "titulo": "Cadastrar Produto"},
    "333":       {"codigo": "333", "titulo": "Consulta de Produtos"},
    "336":       {"codigo": "336", "titulo": "Pedido de Venda"},
    "338":       {"codigo": "338", "titulo": "Consulta de Vendas"},
    "1450":      {"codigo": "1450", "titulo": "Relatório de Faturamento"},
    "1452":      {"codigo": "1452", "titulo": "Emissão NFe"},
}

# ------------------------------------------------------------------------------
# Tema visual — paleta corporativa (azul-marinho / cinza claro), grid denso,
# barra de rotina no topo e barra de atalhos no rodapé, no estilo de ERPs
# corporativos tradicionais (WinThor e semelhantes).
# ------------------------------------------------------------------------------
st.markdown("""
    <style>
    :root{
        --zen-navy: #0C2D57;
        --zen-navy-dark: #081F3D;
        --zen-blue: #1565C0;
        --zen-bg: #EEF1F5;
        --zen-panel: #FFFFFF;
        --zen-border: #C7D0DC;
        --zen-stripe: #F4F6F9;
        --zen-text: #1C2733;
        --zen-muted: #5B6B7C;
    }

    .stApp { background-color: var(--zen-bg); }

    /* ---- barra de rotina (topo) ---- */
    .zen-topbar{
        background: linear-gradient(180deg, var(--zen-navy) 0%, var(--zen-navy-dark) 100%);
        color: #fff; padding: 10px 22px; margin: -1rem -1rem 1.2rem -1rem;
        display:flex; align-items:center; justify-content:space-between;
        border-bottom: 3px solid var(--zen-blue);
        font-family: 'Consolas', 'Courier New', monospace;
    }
    .zen-topbar .zen-brand{ font-weight:700; font-size:16px; letter-spacing:.03em; }
    .zen-topbar .zen-routine{ font-size:14px; opacity:.92; }
    .zen-topbar .zen-routine b{ background:var(--zen-blue); padding:2px 8px; border-radius:3px; margin-right:6px; }
    .zen-topbar .zen-clock{ font-size:12.5px; opacity:.85; text-align:right; }

    /* ---- painéis / cards ---- */
    div[data-testid="stMetric"] {
        background-color: var(--zen-panel);
        border: 1px solid var(--zen-border);
        border-left: 4px solid var(--zen-blue);
        padding: 14px 16px; border-radius: 4px; color: var(--zen-text);
    }
    div[data-testid="stMetric"] label { color: var(--zen-muted) !important; }

    /* ---- inputs e formulários: bordas quadradas, estilo "sistema" ---- */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {
        border-radius: 3px !important; border: 1px solid var(--zen-border) !important;
    }

    /* ---- botões ---- */
    .stButton > button, .stFormSubmitButton > button {
        background-color: var(--zen-blue); color: #fff; border: none;
        border-radius: 3px; font-weight: 600;
    }
    .stButton > button:hover, .stFormSubmitButton > button:hover { background-color: var(--zen-navy); color:#fff; }

    /* ---- tabelas: cabeçalho escuro, listras, estilo grid corporativo ---- */
    div[data-testid="stDataFrame"] { border: 1px solid var(--zen-border); border-radius: 3px; }
    div[data-testid="stDataFrame"] [role="columnheader"]{
        background-color: var(--zen-navy) !important; color: #fff !important; font-weight:600 !important;
    }

    /* ---- sidebar ---- */
    section[data-testid="stSidebar"]{
        background-color: var(--zen-panel); border-right: 1px solid var(--zen-border);
    }

    /* ---- barra de atalhos (rodapé) ---- */
    .zen-statusbar{
        position: fixed; left:0; right:0; bottom:0; z-index: 999;
        background: var(--zen-navy-dark); color:#B9C6D6;
        font-family:'Consolas','Courier New',monospace; font-size:11.5px;
        padding:6px 18px; display:flex; gap:22px; border-top:1px solid var(--zen-blue);
    }
    .zen-statusbar b{ color:#fff; }
    </style>
    """, unsafe_allow_html=True)


def get_connection():
    """Conecta ao Azure SQL usando credenciais de variáveis de ambiente (nunca hardcoded)."""
    server = os.getenv("ZENERP_DB_SERVER", "")
    database = os.getenv("ZENERP_DB_NAME", "")
    username = os.getenv("ZENERP_DB_USER", "")
    senha = os.getenv("ZENERP_DB_PASSWORD", "")
    driver = "{ODBC Driver 18 for SQL Server}"

    conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={senha};Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=30;"

    try:
        return pyodbc.connect(conn_str)
    except Exception as e:
        st.error("❌ Erro de Conexão com o banco de dados. Verifique as variáveis de ambiente (ver .env.example).")
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


def navegar_para(pagina):
    st.session_state['pagina_atual'] = pagina


def render_topbar():
    """Barra superior estilo ERP: marca, rotina atual (código + nome) e relógio."""
    pagina = st.session_state.get('pagina_atual', 'Dashboard')
    info = ROTINAS.get(pagina, {"codigo": "???", "titulo": pagina})
    agora = datetime.now().strftime("%d/%m/%Y  %H:%M")
    st.markdown(f"""
        <div class="zen-topbar">
            <div class="zen-brand">🗂️ ZenERP <span style="opacity:.6;font-weight:400;">· Distribuidora</span></div>
            <div class="zen-routine"><b>{info['codigo']}</b>{info['titulo']}</div>
            <div class="zen-clock">{st.session_state.get('usuario_logado', 'admin')} &nbsp;|&nbsp; Filial 01 &nbsp;|&nbsp; {agora}</div>
        </div>
    """, unsafe_allow_html=True)


def render_statusbar():
    """Barra de atalhos no rodapé, no estilo clássico de ERP (F5/F8/ESC)."""
    st.markdown("""
        <div class="zen-statusbar">
            <span><b>F5</b> Atualizar</span>
            <span><b>F8</b> Salvar</span>
            <span><b>F2</b> Pesquisar</span>
            <span><b>ESC</b> Cancelar</span>
            <span style="margin-left:auto;">ZenERP v2.4 &nbsp;·&nbsp; Conectado ao Azure SQL</span>
        </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# 2. ROTINAS DO SISTEMA
# ==============================================================================

def dashboard_home():
    st.title("Visão Geral")
    conn = get_connection()
    if conn:
        try:
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

            with st.container():
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Faturamento", "R$ 0,00", "0%")
                c2.metric("Clientes", f"{total_clientes}", "Base")
                c3.metric("Mix Produtos", f"{total_skus}", "Ativos")
                c4.metric("Equipe", f"{len(df_metas)}", "RCAs")

            st.divider()

            col_graf, col_info = st.columns([2, 1])
            with col_graf:
                st.subheader("Ranking de Metas")
                st.bar_chart(df_metas.set_index("Vendedor"), color="#1565C0", horizontal=True)

            with col_info:
                st.info(f"Base de dados operando com **{total_clientes} clientes** cadastrados.")

        except Exception as e:
            st.error(f"Erro no Dashboard: {e}")
        finally:
            conn.close()


def rotina_302_cadastrar_cliente():
    st.header("Rotina 302 · Cadastrar Cliente")

    if 'end_rua' not in st.session_state: st.session_state['end_rua'] = ''
    if 'end_bairro' not in st.session_state: st.session_state['end_bairro'] = ''
    if 'end_cidade' not in st.session_state: st.session_state['end_cidade'] = ''
    if 'end_uf' not in st.session_state: st.session_state['end_uf'] = 'PA'

    with st.expander("Buscar Endereço (BrasilAPI)", expanded=True):
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
                        st.success("Endereço localizado.")
                    else:
                        st.warning("CEP desconhecido.")
                except Exception:
                    st.error("Erro ao consultar API.")

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

        if st.form_submit_button("Salvar Cliente (F8)"):
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


def rotina_303_consulta_clientes():
    st.header("Rotina 303 · Consulta de Clientes")
    conn = get_connection()
    if conn:
        try:
            termo = st.text_input("Buscar por nome ou CPF/CNPJ", placeholder="Digite parte do nome ou documento...")

            query = "SELECT id as [Cód.], nome as [Nome], cpf_cnpj as [CPF/CNPJ], cidade as [Cidade], uf as [UF] FROM clientes"
            params = None
            if termo:
                query += " WHERE nome LIKE ? OR cpf_cnpj LIKE ?"
                params = (f"%{termo}%", f"%{termo}%")
            query += " ORDER BY nome"

            df = pd.read_sql(query, conn, params=params)
            st.caption(f"{len(df)} cliente(s) encontrado(s)")
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao consultar clientes: {e}")
        finally:
            conn.close()


def rotina_310_cadastrar_fornecedor():
    st.header("Rotina 310 · Cadastrar Fornecedor")
    conn = get_connection()
    if conn:
        with st.form("form_310"):
            c1, c2 = st.columns([2, 1])
            nome_fantasia = c1.text_input("Nome Fantasia")
            cnpj = c2.text_input("CNPJ")

            c3, c4 = st.columns(2)
            telefone = c3.text_input("Telefone")
            email = c4.text_input("E-mail")

            if st.form_submit_button("Salvar Fornecedor (F8)"):
                if not nome_fantasia.strip():
                    st.error("Informe o nome fantasia do fornecedor.")
                else:
                    try:
                        cursor = conn.cursor()
                        # Observação: a tabela 'fornecedores' precisa ter as colunas
                        # cnpj/telefone/email para este INSERT completo funcionar.
                        # Se ainda não existirem, rode um ALTER TABLE antes de usar
                        # esta rotina, ou remova os campos extras do INSERT abaixo.
                        cursor.execute("""
                            INSERT INTO fornecedores (nome_fantasia, cnpj, telefone, email)
                            VALUES (?, ?, ?, ?)
                        """, (nome_fantasia, cnpj, telefone, email))
                        conn.commit()
                        st.toast(f"Fornecedor {nome_fantasia} cadastrado!", icon="✅")
                        time.sleep(1)
                    except Exception as e:
                        st.error(f"Erro: {e}")
        conn.close()


def rotina_332_cadastro_produto():
    st.header("Rotina 332 · Cadastrar Produto")
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

            if st.form_submit_button("Salvar Produto (F8)"):
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


def rotina_333_consulta_produtos():
    st.header("Rotina 333 · Consulta de Produtos")
    conn = get_connection()
    if conn:
        try:
            termo = st.text_input("Buscar por descrição ou código", placeholder="Digite parte do nome, EAN ou cód. ERP...")

            query = """
                SELECT p.codigo_erp as [Cód. ERP], p.nome as [Descrição], p.sku as [EAN],
                       p.preco as [Preço], f.nome_fantasia as [Fornecedor]
                FROM produtos p
                LEFT JOIN fornecedores f ON p.id_fornecedor = f.id
            """
            params = None
            if termo:
                query += " WHERE p.nome LIKE ? OR p.sku LIKE ? OR CAST(p.codigo_erp AS VARCHAR) LIKE ?"
                params = (f"%{termo}%", f"%{termo}%", f"%{termo}%")
            query += " ORDER BY p.nome"

            df = pd.read_sql(query, conn, params=params)
            st.caption(f"{len(df)} produto(s) encontrado(s)")
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao consultar produtos: {e}")
        finally:
            conn.close()


def rotina_336_pedido_venda():
    st.header("Rotina 336 · Pedido de Venda")
    conn = get_connection()
    if conn:
        df_vend = pd.read_sql("SELECT c.id, c.nome FROM colaboradores c JOIN rcas r ON c.id_rca = r.id WHERE c.id_cargo = (SELECT id FROM cargos WHERE descricao='Vendedor')", conn)
        lista_vend = dict(zip(df_vend['nome'], df_vend['id']))

        df_prod = pd.read_sql("SELECT id, nome, preco, codigo_erp FROM produtos", conn)
        lista_prod = {f"{row['codigo_erp']} - {row['nome']} (R$ {row['preco']:.2f})": row['id'] for i, row in df_prod.iterrows()}

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

            if st.form_submit_button("Fechar Pedido (F8)"):
                if lista_cli.get(cliente_key) == 0:
                    st.error("Cadastre um cliente primeiro!")
                else:
                    try:
                        cursor = conn.cursor()
                        id_vend = lista_vend[vendedor_key]
                        id_prod = lista_prod[prod_key]

                        preco = df_prod[df_prod['id'] == id_prod]['preco'].values[0]
                        total = float(preco) * qtd

                        cursor.execute("INSERT INTO pedidos (id_vendedor, valor_total) VALUES (?, ?)", (id_vend, total))
                        cursor.execute("SELECT @@IDENTITY")
                        id_pedido = cursor.fetchone()[0]

                        cursor.execute("INSERT INTO pedidos_itens (id_pedido, id_produto, qtd, total_item) VALUES (?, ?, ?, ?)",
                                       (id_pedido, id_prod, qtd, total))
                        conn.commit()
                        st.balloons()
                        st.success(f"Pedido Nº {id_pedido} gerado! Total: R$ {total:.2f}")
                    except Exception as e:
                        st.error(f"Erro: {e}")
        conn.close()


def rotina_301_cadastrar_funcionario():
    st.header("Rotina 301 · Cadastrar Funcionário")
    conn = get_connection()
    if conn:
        try:
            df_cargos = pd.read_sql("SELECT id, descricao FROM cargos", conn)
            lista_cargos = dict(zip(df_cargos['descricao'], df_cargos['id']))
        except Exception as e:
            st.error(f"Erro ao carregar cargos: {e}")
            conn.close()
            return

        with st.form("form_301"):
            c1, c2 = st.columns([2, 1])
            nome = c1.text_input("Nome completo")
            cargo_key = c2.selectbox("Cargo", list(lista_cargos.keys()))

            eh_vendedor = st.checkbox("Este funcionário é vendedor (RCA)?")
            meta_inicial = None
            if eh_vendedor:
                meta_inicial = st.number_input("Meta mensal inicial (R$)", min_value=0.0, format="%.2f")

            if st.form_submit_button("Salvar Funcionário (F8)"):
                if not nome.strip():
                    st.error("Informe o nome do funcionário.")
                else:
                    try:
                        cursor = conn.cursor()
                        id_rca = None

                        if eh_vendedor:
                            cursor.execute("INSERT INTO rcas DEFAULT VALUES")
                            cursor.execute("SELECT @@IDENTITY")
                            id_rca = cursor.fetchone()[0]

                        cursor.execute(
                            "INSERT INTO colaboradores (nome, id_cargo, id_rca) VALUES (?, ?, ?)",
                            (nome, lista_cargos[cargo_key], id_rca)
                        )
                        cursor.execute("SELECT @@IDENTITY")
                        id_colaborador = cursor.fetchone()[0]

                        if eh_vendedor and meta_inicial:
                            cursor.execute(
                                "INSERT INTO metas (id_colaborador, valor) VALUES (?, ?)",
                                (id_colaborador, meta_inicial)
                            )

                        conn.commit()
                        st.toast(f"Funcionário {nome} cadastrado!", icon="✅")
                        time.sleep(1)
                    except Exception as e:
                        st.error(f"Erro: {e}")
        conn.close()


def rotina_338_consulta_vendas():
    st.header("Rotina 338 · Consulta de Vendas")
    conn = get_connection()
    if conn:
        try:
            df_vend = pd.read_sql("SELECT id, nome FROM colaboradores", conn)
            opcoes_vend = {"Todos os vendedores": None}
            opcoes_vend.update(dict(zip(df_vend['nome'], df_vend['id'])))

            c1, c2, c3 = st.columns(3)
            vendedor_key = c1.selectbox("Vendedor", list(opcoes_vend.keys()))
            data_ini = c2.date_input("Data inicial", value=None)
            data_fim = c3.date_input("Data final", value=None)

            query = """
                SELECT p.id as [Nº Pedido], p.data_emissao as [Data],
                       c.nome as [Vendedor], p.valor_total as [Total R$]
                FROM pedidos p
                JOIN colaboradores c ON p.id_vendedor = c.id
                WHERE 1=1
            """
            params = []
            id_vend_filtro = opcoes_vend[vendedor_key]
            if id_vend_filtro:
                query += " AND p.id_vendedor = ?"
                params.append(id_vend_filtro)
            if data_ini:
                query += " AND p.data_emissao >= ?"
                params.append(data_ini)
            if data_fim:
                query += " AND p.data_emissao <= ?"
                params.append(data_fim)
            query += " ORDER BY p.id DESC"

            df = pd.read_sql(query, conn, params=params if params else None)

            m1, m2, m3 = st.columns(3)
            m1.metric("Pedidos encontrados", len(df))
            m2.metric("Total vendido", f"R$ {df['Total R$'].sum():,.2f}" if not df.empty else "R$ 0,00")
            m3.metric("Ticket médio", f"R$ {df['Total R$'].mean():,.2f}" if not df.empty else "R$ 0,00")

            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao consultar vendas: {e}")
        finally:
            conn.close()


def rotina_1450_relatorio_faturamento():
    st.header("Rotina 1450 · Relatório de Faturamento")
    conn = get_connection()
    if conn:
        try:
            c1, c2 = st.columns(2)
            data_ini = c1.date_input("Período - de", value=None, key="fat_ini")
            data_fim = c2.date_input("Período - até", value=None, key="fat_fim")

            query = """
                SELECT p.id, p.data_emissao, p.valor_total, c.nome as vendedor
                FROM pedidos p
                JOIN colaboradores c ON p.id_vendedor = c.id
                WHERE 1=1
            """
            params = []
            if data_ini:
                query += " AND p.data_emissao >= ?"
                params.append(data_ini)
            if data_fim:
                query += " AND p.data_emissao <= ?"
                params.append(data_fim)

            df = pd.read_sql(query, conn, params=params if params else None)

            total_faturado = df['valor_total'].sum() if not df.empty else 0
            qtd_pedidos = len(df)
            ticket_medio = df['valor_total'].mean() if not df.empty else 0

            m1, m2, m3 = st.columns(3)
            m1.metric("Total Faturado", f"R$ {total_faturado:,.2f}")
            m2.metric("Pedidos no Período", qtd_pedidos)
            m3.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")

            st.divider()

            if not df.empty:
                st.subheader("Faturamento por Vendedor")
                df_por_vendedor = df.groupby('vendedor')['valor_total'].sum().sort_values(ascending=False)
                st.bar_chart(df_por_vendedor, color="#1565C0", horizontal=True)
            else:
                st.info("Nenhum faturamento encontrado no período selecionado.")

        except Exception as e:
            st.error(f"Erro ao gerar relatório: {e}")
        finally:
            conn.close()


def rotina_1452_faturamento():
    st.header("Rotina 1452 · Emissão NFe")
    conn = get_connection()
    if conn:
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
                col1, col2 = st.columns([3, 1])
                n_ped = col1.number_input("Nº Pedido para Faturar", min_value=1)
                if col2.button("Emitir Nota (F8)"):
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
# 3. LOGIN E NAVEGAÇÃO
# ==============================================================================

def tela_login():
    """Tela de login estilo ERP corporativo: usuário, senha e seleção de filial."""
    st.markdown("""
        <div style="max-width:420px;margin:60px auto 0;background:#fff;border:1px solid #C7D0DC;
                    border-radius:6px;overflow:hidden;box-shadow:0 8px 24px rgba(12,45,87,0.15);">
          <div style="background:linear-gradient(180deg,#0C2D57,#081F3D);padding:22px 24px;color:#fff;">
            <div style="font-size:20px;font-weight:700;">🗂️ ZenERP</div>
            <div style="font-size:12.5px;opacity:.75;">Sistema de Gestão Empresarial</div>
          </div>
        </div>
    """, unsafe_allow_html=True)

    _, col_center, _ = st.columns([1, 1.3, 1])
    with col_center:
        with st.container(border=True):
            usuario_correto = os.getenv("ZENERP_APP_USER", "admin")
            senha_correta = os.getenv("ZENERP_APP_PASSWORD", "")

            u = st.text_input("Usuário")
            p = st.text_input("Senha", type="password")
            filial = st.selectbox("Filial", ["01 - Matriz (Santarém/PA)", "02 - Filial (Belém/PA)"])
            st.caption("Ambiente: Produção")

            if st.button("Entrar", use_container_width=True):
                if not senha_correta:
                    st.error("ZENERP_APP_PASSWORD não configurada. Veja .env.example.")
                elif u == usuario_correto and p == senha_correta:
                    st.session_state['logado'] = True
                    st.session_state['usuario_logado'] = u
                    st.session_state['filial'] = filial
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")

    st.markdown(
        "<div style='text-align:center;color:#5B6B7C;font-size:11.5px;margin-top:10px;'>ZenERP v2.4 · Build 2026</div>",
        unsafe_allow_html=True
    )


def main():
    if 'logado' not in st.session_state: st.session_state['logado'] = False
    if 'pagina_atual' not in st.session_state: st.session_state['pagina_atual'] = "Dashboard"

    if not st.session_state['logado']:
        tela_login()
        return

    render_topbar()

    with st.sidebar:
        st.markdown("#### Navegação")
        busca = st.text_input("Ir para rotina...", placeholder="Ex: 336")
        if busca:
            if "301" in busca: st.session_state['pagina_atual'] = "301"
            elif "303" in busca: st.session_state['pagina_atual'] = "303"
            elif "302" in busca: st.session_state['pagina_atual'] = "302"
            elif "310" in busca: st.session_state['pagina_atual'] = "310"
            elif "333" in busca: st.session_state['pagina_atual'] = "333"
            elif "338" in busca: st.session_state['pagina_atual'] = "338"
            elif "336" in busca: st.session_state['pagina_atual'] = "336"
            elif "332" in busca: st.session_state['pagina_atual'] = "332"
            elif "1450" in busca: st.session_state['pagina_atual'] = "1450"
            elif "1452" in busca: st.session_state['pagina_atual'] = "1452"

        st.divider()
        st.button("000 · Dashboard", on_click=navegar_para, args=("Dashboard",), use_container_width=True)

        with st.expander("Vendas / Clientes", expanded=True):
            st.button("336 · Pedido de Venda", on_click=navegar_para, args=("336",), use_container_width=True)
            st.button("338 · Consulta de Vendas", on_click=navegar_para, args=("338",), use_container_width=True)
            st.button("302 · Cadastrar Cliente", on_click=navegar_para, args=("302",), use_container_width=True)
            st.button("303 · Consulta de Clientes", on_click=navegar_para, args=("303",), use_container_width=True)

        with st.expander("Produtos / Fornecedores"):
            st.button("332 · Cadastrar Produto", on_click=navegar_para, args=("332",), use_container_width=True)
            st.button("333 · Consulta de Produtos", on_click=navegar_para, args=("333",), use_container_width=True)
            st.button("310 · Cadastrar Fornecedor", on_click=navegar_para, args=("310",), use_container_width=True)

        with st.expander("Financeiro"):
            st.button("1450 · Relatório de Faturamento", on_click=navegar_para, args=("1450",), use_container_width=True)
            st.button("1452 · Emissão NFe", on_click=navegar_para, args=("1452",), use_container_width=True)

        with st.expander("Recursos Humanos"):
            st.button("301 · Cadastrar Funcionário", on_click=navegar_para, args=("301",), use_container_width=True)

        st.divider()
        if st.button("Sair"):
            st.session_state['logado'] = False
            st.rerun()

    pagina = st.session_state['pagina_atual']
    if pagina == "Dashboard": dashboard_home()
    elif pagina == "301": rotina_301_cadastrar_funcionario()
    elif pagina == "302": rotina_302_cadastrar_cliente()
    elif pagina == "303": rotina_303_consulta_clientes()
    elif pagina == "310": rotina_310_cadastrar_fornecedor()
    elif pagina == "332": rotina_332_cadastro_produto()
    elif pagina == "333": rotina_333_consulta_produtos()
    elif pagina == "336": rotina_336_pedido_venda()
    elif pagina == "338": rotina_338_consulta_vendas()
    elif pagina == "1450": rotina_1450_relatorio_faturamento()
    elif pagina == "1452": rotina_1452_faturamento()

    render_statusbar()


if __name__ == "__main__":
    main()
