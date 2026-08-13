# ZenERP

ERP simples construído em Streamlit, inspirado na navegação por número de rotina do WinThor (ERP real usado pela Distribuidora Durães) — cada tela do sistema é acessada por um código (302, 332, 336, 1452...), igual ao padrão que profissionais de suporte/implantação desse tipo de sistema já conhecem.

## Rotinas implementadas

| Código | Nome | Função |
|---|---|---|
| 000 | Dashboard | Visão geral: total de clientes, mix de produtos, ranking de metas por vendedor |
| 301 | Cadastrar Funcionário | Cadastro de colaborador, com opção de vinculá-lo como vendedor (RCA) e definir meta inicial |
| 302 | Cadastrar Cliente | Cadastro com busca automática de endereço por CEP (BrasilAPI) |
| 303 | Consulta de Clientes | Busca por nome ou CPF/CNPJ na base de clientes já cadastrados |
| 310 | Cadastrar Fornecedor | Cadastro de fornecedor (nome fantasia, CNPJ, contato) |
| 332 | Cadastrar Produto | Cadastro de produto vinculado a um fornecedor |
| 333 | Consulta de Produtos | Busca por descrição, EAN ou código ERP na base de produtos |
| 336 | Pedido de Venda | Lançamento de pedido (vendedor + cliente + item), grava pedido e item no banco |
| 338 | Consulta de Vendas | Lista pedidos com filtro por vendedor e período, com total vendido e ticket médio |
| 1450 | Relatório de Faturamento | Faturamento total no período, ticket médio e gráfico de faturamento por vendedor |
| 1452 | Emissão de NFe | Lista os últimos pedidos e simula a emissão de nota fiscal |

**Nota sobre a rotina 310:** o INSERT assume que a tabela `fornecedores` já tem as colunas `cnpj`, `telefone` e `email`, além da `nome_fantasia` que já era usada. Se seu banco ainda não tiver essas colunas, rode um `ALTER TABLE fornecedores ADD cnpj VARCHAR(20), telefone VARCHAR(20), email VARCHAR(100);` antes de usar essa rotina (ou remova os campos extras do formulário).

## Interface

A navegação por código de rotina (inclusive a busca rápida "Ir para rotina...") e o layout com barra de rotina no topo e barra de atalhos (F5/F8/F2/ESC) no rodapé foram desenhados para lembrar a experiência de um ERP corporativo tradicional.

## Stack

- Python, Streamlit
- Azure SQL (via `pyodbc`)
- BrasilAPI (consulta de CEP)

## Como rodar localmente

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Copie `.env.example` para `.env` e preencha com suas credenciais reais (banco e login da aplicação).
3. Rode o script de criação de tabelas (uma vez, para preparar o schema):
   ```bash
   python criar_tabela.py criar
   ```
4. Inicie o sistema:
   ```bash
   streamlit run ERP.py
   ```

## Observações

- Projeto de estudo — a emissão de NFe é simulada (não integra com SEFAZ de verdade).
- Todas as credenciais são lidas de variáveis de ambiente; nunca edite `ERP.py` ou `criar_tabela.py` para colocar usuário/senha diretamente no código.
