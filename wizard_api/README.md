# Wizard API — Normalização e Auditoria de Estoque

API + dashboard para validar relatórios de vendas em CSV desestruturado, cruzar com o cadastro oficial de produtos em SQL Server, e sinalizar rupturas de estoque e anomalias de preço automaticamente.

## O que o sistema faz

1. Recebe um CSV de movimentação de vendas (formato e cabeçalhos não padronizados — vendedores diferentes exportam de jeitos diferentes).
2. Identifica automaticamente qual coluna do CSV corresponde a "produto", comparando os valores de cada coluna com a lista de produtos cadastrados no banco (a coluna com mais correspondências é escolhida) — isso evita depender de um nome de cabeçalho fixo.
3. Cruza os dados do CSV com o cadastro oficial (`ProdutosMestre` no SQL Server): preço de tabela, estoque atual.
4. Preenche lacunas nos dados (preços zerados ou ausentes recebem a média dos preços válidos do lote).
5. Calcula, por item:
   - **Status logístico**: `ESTOQUE_INSUFICIENTE` quando a quantidade pedida excede o estoque atual.
   - **Z-score do preço**: desvio em relação à média do lote, para sinalizar preços fora do padrão (possível erro de digitação ou fraude).
6. Registra automaticamente no banco os itens com estoque insuficiente, para acompanhamento de reposição.
7. O dashboard (Streamlit) exibe os resultados com gráficos e permite exportar para `.xlsx`/`.csv`.

## Stack

- **Backend:** Python, FastAPI, Pandas
- **Banco de dados:** Microsoft SQL Server (via `pyodbc`)
- **Frontend:** Streamlit, Plotly

## Autenticação

O endpoint de análise exige uma chave via header `x-api-key`, definida na variável de ambiente `WIZARD_API_KEY` — a aplicação recusa iniciar se essa variável não estiver configurada.

## Como rodar localmente

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Copie `.env.example` para `.env` e preencha `WIZARD_API_KEY` com uma chave forte.
3. Ajuste `WIZARD_DB_SERVER`/`WIZARD_DB_NAME` no `.env` se necessário (usa autenticação do Windows por padrão).
4. Inicie a API:
   ```bash
   python main.py
   ```
5. Em outro terminal, inicie o dashboard:
   ```bash
   streamlit run interface_wizard.py
   ```
6. Acesse o Streamlit no navegador, cole a mesma chave definida em `WIZARD_API_KEY` no campo lateral, e envie um CSV de teste (veja `gerar_csv_teste.py` para gerar um exemplo).

## Observações

- Projeto de estudo, construído para resolver um problema real de padronização de relatórios de vendas.
