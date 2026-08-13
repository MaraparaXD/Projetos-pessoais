# CNPJ Analytics — Motor de Análise de Crédito

API assíncrona que consolida dados públicos de CNPJ com o histórico financeiro interno de um cliente (ERP WinThor / Oracle) e gera uma recomendação automática de crédito, com base em regras de negócio configuráveis.

## O que o sistema faz

1. Recebe um CNPJ e um período de consulta.
2. Busca a situação cadastral da empresa em tempo real na **BrasilAPI** (Receita Federal) e enriquece o endereço via **ViaCEP**.
3. Cruza esses dados com o histórico interno no Oracle (limite de crédito, vendas no período, títulos em atraso).
4. Aplica um conjunto de regras de negócio (situação cadastral, % de atraso sobre o limite, volume de compras vs. limite aprovado) e retorna uma recomendação: manter crédito, bloquear, reduzir limite, aumentar limite ou liberar crédito — com o motivo explícito.
5. Resultado é cacheado em memória por 60 minutos, para evitar reprocessar a mesma consulta repetidamente.

## Stack

- **Backend:** Python 3.11+, FastAPI, Uvicorn (assíncrono)
- **Banco de dados:** Oracle (via `oracledb`), consultando uma base ERP (WinThor)
- **APIs externas:** BrasilAPI (dados de CNPJ), ViaCEP (endereço)
- **Frontend:** HTML5, TailwindCSS, Chart.js (dashboard simples de visualização)
- **Infra:** Docker e Docker Compose

## Autenticação

Todos os endpoints (exceto o dashboard estático) exigem um token no header `X-API-Token`, validado contra uma variável de ambiente.

## Como rodar localmente

1. Clone o repositório.
2. Copie `dados.env.example` para `dados.env` (crie esse arquivo se ainda não existir) e preencha:
   ```
   ORACLE_USER=...
   ORACLE_PASSWORD=...
   ORACLE_CONNECT_STRING=...
   API_TOKEN=...
   ```
3. Suba o ambiente:
   ```bash
   docker compose up -d --build
   ```
4. Acesse:
   - Dashboard: http://localhost:8000
   - Documentação interativa (Swagger UI): http://localhost:8000/docs

## Observações

- A query SQL em `services.py` foi escrita para o schema de um ERP específico (WinThor/Oracle) — para reutilizar em outro banco, ajuste as tabelas/colunas na consulta.
- Este é um projeto pessoal de estudo, construído para resolver um caso real de análise de crédito. Não recomendado para uso em produção sem revisão de segurança (ver observação abaixo).

## Melhorias conhecidas (próximos passos)

- Restringir `allow_origins` do CORS em vez do wildcard `*` atual.
- Remover o valor padrão hardcoded do token de API (hoje há um fallback fraco caso a variável de ambiente não esteja definida).
- Mover a lógica de regras de crédito para uma configuração externa (hoje os limiares estão fixos no código).
