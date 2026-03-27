import io
import time
import pyodbc
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.responses import StreamingResponse

app = FastAPI(
    title="A Visão do Mago",
    
)

API_KEY_LOCAL = "1234"

def get_db_connection():
    return pyodbc.connect("Driver={ODBC Driver 17 for SQL Server};Server=localhost;Database=ENGINE;Trusted_Connection=yes;")

def registrar_pendencias(df_alertas: pd.DataFrame):
    if df_alertas.empty: return
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ReposicaoPrioritaria' AND xtype='U')
            CREATE TABLE ReposicaoPrioritaria (
                id_log INT IDENTITY(1,1) PRIMARY KEY,
                id_produto INT,
                nome_produto VARCHAR(255),
                quantidade_pedida INT,
                estoque_atual INT,
                deficit INT,
                data_solicitacao DATETIME DEFAULT GETDATE(),
                vendedor_origem VARCHAR(100)
            )
        ''')
        
        for _, row in df_alertas.iterrows():
            deficit = int(row['quantidade'] - row['estoque_atual'])
            cursor.execute("""
                INSERT INTO ReposicaoPrioritaria (id_produto, nome_produto, quantidade_pedida, estoque_atual, deficit, vendedor_origem)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (int(row['id']), row['produto'], int(row['quantidade']), int(row['estoque_atual']), deficit, row['vendedor']))
        conn.commit()
    except Exception as e:
        print(f"⚠️ Erro no SQL: {e}")
    finally:
        if 'conn' in locals(): conn.close()

def pipeline_wizard(df_csv: pd.DataFrame):
    # 1. Carrega a Fonte da Verdade
    conn = get_db_connection()
    df_sql = pd.read_sql("SELECT id_oficial, nome_produto, preco_tabela, estoque_atual FROM ProdutosMestre", conn)
    conn.close()

    # --- O SCANNER INTELIGENTE ---
    produtos_validos = set(df_sql['nome_produto'].astype(str).str.lower().str.strip())
    
    coluna_produto_descoberta = None
    maior_intersecao = 0

    for col in df_csv.columns:
        valores_csv = set(df_csv[col].astype(str).str.lower().str.strip())
        matches = len(valores_csv.intersection(produtos_validos))
        
        if matches > maior_intersecao:
            maior_intersecao = matches
            coluna_produto_descoberta = col

    if not coluna_produto_descoberta or maior_intersecao == 0:
        raise ValueError("O Mago escaneou o CSV inteiro e não reconheceu nenhum produto cadastrado no banco de dados!")

    df_csv.rename(columns={coluna_produto_descoberta: 'produto'}, inplace=True)
    
    df_csv['produto'] = df_csv['produto'].astype(str).str.strip()
    df_sql['nome_produto'] = df_sql['nome_produto'].astype(str).str.strip()

    df_final = pd.merge(df_csv, df_sql, left_on=df_csv['produto'].str.lower(), right_on=df_sql['nome_produto'].str.lower(), how='left')
    
    if 'key_0' in df_final.columns:
        df_final.drop('key_0', axis=1, inplace=True)

    # 3. Tratamento Seguro (Correção do Erro 'str' e 'int')
    df_final['id'] = df_final['id_oficial'].fillna(df_final.get('id', 0)).astype(int)
    df_final['preco'] = df_final['preco_tabela'].fillna(df_final.get('preco', 0)).astype(float)
    df_final['estoque_atual'] = df_final['estoque_atual'].fillna(0).astype(int)
    
    # Validação blindada para colunas que podem não existir no CSV
    if 'vendedor' in df_final.columns:
        df_final['vendedor'] = df_final['vendedor'].fillna("DESCONHECIDO")
    else:
        df_final['vendedor'] = "DESCONHECIDO"

    if 'quantidade' in df_final.columns:
        df_final['quantidade'] = df_final['quantidade'].fillna(1).astype(int)
    else:
        df_final['quantidade'] = 1

    # Preenche preços zerados com a média
    if df_final['preco'].isnull().any() or (df_final['preco'] == 0).any():
        media_precos = df_final['preco'][df_final['preco'] > 0].mean()
        df_final['preco'] = df_final['preco'].replace(0, media_precos).fillna(media_precos if not pd.isna(media_precos) else 0.0)

    # 4. Status Logístico e Z-Score
    df_final['status_logistico'] = df_final.apply(
        lambda x: 'ESTOQUE_INSUFICIENTE' if x['quantidade'] > x['estoque_atual'] else 'LIBERADO', axis=1
    )

    std_p = df_final['preco'].std()
    df_final['z_score'] = 0.0 if pd.isna(std_p) or std_p == 0 else (df_final['preco'] - df_final['preco'].mean()) / std_p

    df_final['produto'] = df_final['nome_produto'].fillna(df_final['produto']) 
    colunas_saida = ['id', 'produto', 'preco', 'quantidade', 'estoque_atual', 'status_logistico', 'vendedor', 'z_score']
    
    colunas_saida = [c for c in colunas_saida if c in df_final.columns]
    return df_final[colunas_saida].drop_duplicates()

@app.post("/v1/analyze")
async def analyze_endpoint(file: UploadFile = File(...), x_api_key: str = Header(None)):
    if x_api_key != API_KEY_LOCAL:
        raise HTTPException(status_code=403, detail="Chave de API inválida.")

    start = time.time()
    try:
        conteudo = await file.read()
        df_bruto = pd.read_csv(io.BytesIO(conteudo), sep=None, engine='python')
        
        df_limpo = pipeline_wizard(df_bruto)
        
        df_alertas = df_limpo[df_limpo['status_logistico'] == 'ESTOQUE_INSUFICIENTE']
        registrar_pendencias(df_alertas)
        
        resumo = df_limpo.describe().to_dict()
        tempo_total = round(time.time() - start, 4)

        return {
            "metadata": {
                "tempo": f"{tempo_total}s",
                "total_itens": len(df_limpo),
                "alertas_gerados": len(df_alertas)
            },
            "statistics": resumo,
            "data": df_limpo.to_dict(orient="records")
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)