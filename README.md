# Projetos Pessoais

Coleção de projetos e estudos desenvolvidos de forma independente, cobrindo automação, integração de sistemas, bancos de dados e monitoramento de infraestrutura.

## Projetos com repositório próprio

Os projetos mais completos foram migrados para repositórios individuais — cada um com README, `.gitignore` e configuração de credenciais via variáveis de ambiente:

| Projeto | Descrição | Stack principal |
|---|---|---|
| [`cnpj-analytics`](https://github.com/MaraparaXD/cnpj-analytics) | API de análise de crédito: cruza dados públicos de CNPJ com histórico financeiro interno (ERP) e recomenda ação de crédito | Python, FastAPI, Oracle, Docker |
| [`wizard-api`](https://github.com/MaraparaXD/wizard-api) | Normalização de relatórios de vendas em CSV desestruturado, cruzamento com estoque e detecção de anomalias de preço | Python, FastAPI, SQL Server, Streamlit |
| [`monitor-rede`](https://github.com/MaraparaXD/monitor-rede) | Monitoramento de rede em tempo real com alerta para dispositivos não identificados | Python, Flask, sockets/threading |
| [`zenerp`](https://github.com/MaraparaXD/zenerp) | Sistema ERP com múltiplas rotinas (cadastros, vendas, faturamento), inspirado na navegação por código de rotina do WinThor | Python, Streamlit, Azure SQL |

*(Links acima assumem esses nomes de repositório — ajuste se você nomeou diferente ao publicar.)*

## Projetos e estudos que continuam aqui

| Pasta | Descrição | Stack principal |
|---|---|---|
| [`RE-MAID`](./RE-MAID) | Modelagem de banco de dados (PostgreSQL) para inventário de TI e service desk, com dashboards em Power BI | SQL, Power BI |
| [`Doc Requesitos RE-MAID`](./Doc%20Requesitos%20RE-MAID) | Levantamento de requisitos do projeto RE-MAID | — |
| [`Gerenciador de Tabelas(AzureSQL)`](./Gerenciador%20de%20Tabelas(AzureSQL)) | Ferramenta CLI para administrar tabelas em Azure SQL por menu interativo | Python |
| [`POWER GIT`](./POWER%20GIT) | Script Bash que guia o fluxo de commit/push seguindo o padrão Conventional Commits | Bash |
| [`COD PYTHON`](./COD%20PYTHON) | Exercícios de lógica de programação e fundamentos de Python | Python |
| [`Scripts LINUX UBUNTU`](./Scripts%20LINUX%20UBUNTU) | Scripts Bash de automação e administração básica de servidores Linux | Bash |

## Sobre este repositório

Este repositório reúne estudos e utilitários pessoais que não justificam (ainda) um repositório próprio. Os projetos com escopo e maturidade maiores ganharam repositório individual — veja a tabela acima.

**Nota de segurança:** nenhum destes projetos deve ser usado em produção sem revisão prévia de segurança — em particular, revisar autenticação, CORS e gestão de credenciais antes de qualquer deploy real. Nunca deixe usuário/senha escritos diretamente no código-fonte; use variáveis de ambiente (veja o padrão `.env.example` usado nos repositórios individuais).
