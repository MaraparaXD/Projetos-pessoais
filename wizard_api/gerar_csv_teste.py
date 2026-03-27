import pandas as pd
import pyodbc
import random

def gerar_carga_teste_150():
    # Conecta no banco para pegar os nomes REAIS dos produtos
    conn_str = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=localhost;"
        "Database=ENGINE;"
        "Trusted_Connection=yes;"
    )
    
    try:
        conn = pyodbc.connect(conn_str)
        # Pegamos os nomes que o setup_db.py criou
        df_db = pd.read_sql("SELECT nome_produto FROM ProdutosMestre", conn)
        conn.close()

        # Criamos a massa de teste baseada nesses nomes
        dados_teste = []
        vendedores = ["Zendar", "Tiago", "Ludmila", "Estagiario_Duraes"]

        for i, nome in enumerate(df_db['nome_produto']):
            dados_teste.append({
                "id": random.randint(1, 99), # IDs errados (o banco vai corrigir para 1000+)
                "produto": nome,
                "preco": None,               # Preço vazio (o banco vai preencher)
                "quantidade": random.randint(1, 20),
                "vendedor": random.choice(vendedores)
            })

        df_final = pd.DataFrame(dados_teste)
        df_final.to_csv("carga_tech_150.csv", index=False)
        print("✨ Arquivo 'carga_tech_150.csv' conjurado com sucesso!")

    except Exception as e:
        print(f"❌ Erro ao gerar teste: {e}")

if __name__ == "__main__":
    gerar_carga_teste_150()