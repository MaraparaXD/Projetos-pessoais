'''
import pyodbc
import time

# --- CONFIGURAÇÃO ---
SERVER = ''
DATABASE = ''
USERNAME = ''
SENHA    = '' 
DRIVER   = '{ODBC Driver 18 for SQL Server}'

def criar_tabelas():
    print("⏳ Conectando no Azure...")
    conn_str = f'DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={SENHA};Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=30;'
    
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        print("✅ Conectado! Criando tabelas...")

        # 1. TABELA CLIENTES
        print(" > Criando tabela 'clientes'...")
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='clientes' AND xtype='U')
            CREATE TABLE clientes (
                id INT IDENTITY(1,1) PRIMARY KEY,
                cpf_cnpj VARCHAR(20),
                nome VARCHAR(100),
                cep VARCHAR(10),
                logradouro VARCHAR(100),
                numero VARCHAR(20),
                bairro VARCHAR(50),
                cidade VARCHAR(50),
                uf VARCHAR(2)
            )
        """)

        # 2. TABELA PEDIDOS (Para a rotina 336 não dar erro depois)
        print(" > Criando tabela 'pedidos'...")
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='pedidos' AND xtype='U')
            CREATE TABLE pedidos (
                id INT IDENTITY(1,1) PRIMARY KEY,
                id_vendedor INT,
                data_emissao DATETIME DEFAULT GETDATE(),
                valor_total DECIMAL(10,2)
            )
        """)

        # 3. TABELA ITENS DO PEDIDO
        print(" > Criando tabela 'pedidos_itens'...")
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='pedidos_itens' AND xtype='U')
            CREATE TABLE pedidos_itens (
                id INT IDENTITY(1,1) PRIMARY KEY,
                id_pedido INT,
                id_produto INT,
                qtd INT,
                total_item DECIMAL(10,2)
            )
        """)

        conn.commit()
        print("\n🎉 SUCESSO! Todas as tabelas foram criadas.")
        print("Agora pode voltar pro Streamlit e cadastrar à vontade.")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
    finally:
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    criar_tabelas()
    '''

import pyodbc

# --- CONFIGURAÇÃO ---
SERVER = 'zendarerp.database.windows.net'
DATABASE = 'zendatabase'
USERNAME = 'zendar'
SENHA    = 'Tiago23072004!' # <--- COLOCA A SENHA AQUI PFVR
DRIVER   = '{ODBC Driver 18 for SQL Server}'

def corrigir_tabela():
    print("⏳ Conectando para corrigir a tabela...")
    conn_str = f'DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={SENHA};Encrypt=yes;TrustServerCertificate=yes;'
    
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # COMANDO MÁGICO: ALTER TABLE
        # Ele adiciona a coluna 'numero' na tabela que já existe
        print(" > Adicionando coluna 'numero' na tabela clientes...")
        cursor.execute("ALTER TABLE clientes ADD numero VARCHAR(20)")
        
        conn.commit()
        print("✅ SUCESSO! A coluna 'numero' foi criada.")
        
    except Exception as e:
        if "Column names in each table must be unique" in str(e):
            print("⚠️ A coluna já existia, não precisou fazer nada.")
        else:
            print(f"❌ Erro: {e}")
    finally:
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    corrigir_tabela()
