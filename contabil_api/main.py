from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta
from services import LedgerService
import os

# Nome da API 
app = FastAPI(title="CNPJ Analytics API", version="3.0 Master")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key_header = APIKeyHeader(name="X-API-Token", auto_error=True)

def verificar_token(api_key: str = Security(api_key_header)):
   
    token_correto = os.getenv("API_TOKEN", "Admin2026")
    if api_key != token_correto:
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
