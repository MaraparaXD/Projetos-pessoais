from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta
from services import LedgerService
import os
import sys

# Nome da API
app = FastAPI(title="CNPJ Analytics API", version="3.1")

# --- CORS ---
# Nunca combine allow_origins=["*"] com allow_credentials=True: é uma
# configuração insegura (e a maioria dos navegadores já rejeita essa
# combinação). As origens permitidas vêm de uma variável de ambiente,
# separadas por vírgula — em desenvolvimento local, defina
# CORS_ALLOWED_ORIGINS=http://localhost:8000 (ou a porta do seu frontend).
origens_permitidas = [
    o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origens_permitidas,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Token", "Content-Type"],
)

api_key_header = APIKeyHeader(name="X-API-Token", auto_error=True)

# --- Token de API ---
# Sem valor padrão: se API_TOKEN não estiver definido, a aplicação recusa
# subir. Um token "de fábrica" hardcoded (como havia antes) é uma senha
# fraca e previsível — qualquer pessoa que leia o código consegue acessar
# a API em qualquer ambiente onde a variável não tenha sido trocada.
TOKEN_CORRETO = os.getenv("API_TOKEN")
if not TOKEN_CORRETO:
    sys.exit("ERRO: variável de ambiente API_TOKEN não definida. Veja dados.env.example.")


def verificar_token(api_key: str = Security(api_key_header)):
    if api_key != TOKEN_CORRETO:
        raise HTTPException(status_code=403, detail="Acesso negado. Token inválido.")
    return api_key

class ConsultaRequest(BaseModel):
    cnpj: str = Field(..., description="CNPJ numérico")
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None

memoria_cache = {}
CACHE_MINUTOS = 60

@app.get("/")
def home():
    return FileResponse("index.html")

@app.get("/api/v1/auth/validate")
def validar_acesso(token: str = Depends(verificar_token)):
    return {"status": "Autorizado"}

@app.post("/api/v1/contabilidade/unificar")
async def consultar_hub(item: ConsultaRequest, token: str = Depends(verificar_token)):
    try:
        hoje = datetime.now().strftime('%Y-%m-%d')
        um_ano_atras = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        inicio = item.data_inicio if item.data_inicio else um_ano_atras
        fim = item.data_fim if item.data_fim else hoje

        chave_cache = f"{item.cnpj}_{inicio}_{fim}"
        agora = datetime.now()

        if chave_cache in memoria_cache:
            dados_salvos = memoria_cache[chave_cache]
            if agora < dados_salvos["expira_em"]:
                print(f"⚡ [CACHE HIT] {item.cnpj} carregado da memória!")
                return dados_salvos["dados"]

        print(f"🔍 [ORACLE] Buscando dados novos para {item.cnpj}...")
        resultado = await LedgerService.buscar_dados_unificados(item.cnpj, inicio, fim)

        if "erro" in resultado:
            raise HTTPException(status_code=404, detail=resultado["erro"])

        memoria_cache[chave_cache] = {
            "dados": resultado,
            "expira_em": agora + timedelta(minutes=CACHE_MINUTOS)
        }
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
