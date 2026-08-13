"""
Scripts utilitários de manutenção do banco (criação e correção de tabelas).
Execute com: python criar_tabela.py criar   |   python criar_tabela.py corrigir

As credenciais de conexão vêm de variáveis de ambiente (ver .env.example) —
nunca deixe usuário/senha escritos diretamente neste arquivo.
"""

import os
import sys
import pyodbc
from dotenv import load_dotenv

load_dotenv()

SERVER = os.getenv("ZENERP_DB_SERVER", "")
DATABASE = os.getenv("ZENERP_DB_NAME", "")
USERNAME = os.getenv("ZENERP_DB_USER", "")
SENHA = os.getenv("ZENERP_DB_PASSWORD", "")
DRIVER = "{ODBC Driver 18 for SQL Server}"


def _conectar():
    if not all([SERVER, DATABASE, USERNAME, SENHA]):
        print("❌ Variáveis de ambiente ZENERP_DB_* não configuradas. Veja .env.example.")
        sys.exit(1)
    conn_str = f"DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={SENHA};Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=30;"
    return pyodbc.connect(conn_str)


def criar_tabelas():
    print("⏳ Conectando no Azure...")
    try:
        conn = _conectar()
        cursor = conn.cursor()
        print("✅ Conectado! Criando tabelas...")

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

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def corrigir_tabela():
    print("⏳ Conectando para corrigir a tabela...")
    try:
        conn = _conectar()
        cursor = conn.cursor()

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
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    acao = sys.argv[1] if len(sys.argv) > 1 else "criar"
    if acao == "corrigir":
        corrigir_tabela()
    else:
        criar_tabelas()
