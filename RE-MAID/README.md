# RE-MAID — Gestão de Inventário e Service Desk

Modelagem de banco de dados relacional (PostgreSQL) para controle de inventário de equipamentos de TI e atendimento de chamados internos, com dashboards de visualização em Power BI.

## O que o projeto cobre

**Modelo de dados** (`Query RE-MAID/CREATE TABLE RE-MAID.sql`):
- `DEPARTAMENTO`, `COLABORADOR`, `TECNICO` — estrutura organizacional
- `DISPOSITIVO` — inventário de equipamentos, vinculado a um colaborador
- `CHAMADOS` — chamados de suporte, com solicitante, técnico responsável e status
- `HISTORICO_DE_COLABORADOR` — histórico de posse de dispositivo por colaborador ao longo do tempo

**Consultas** (`Query RE-MAID/SELECTS RE-MAID.sql` e demais arquivos):
- Inventário ativo (quem tem qual dispositivo)
- Relatório de chamados atendidos, com técnico responsável
- Volume de chamados por departamento
- Consultas de apoio para os dashboards abaixo

**Dashboards** (Power BI):
- `Service Desk Dashboard.pbix` — indicadores de chamados (volume, status, técnico responsável)
- `Gestão de Inventário Dashboard.pbix` — visão do inventário de dispositivos por colaborador/departamento

## Stack

- PostgreSQL (schema e queries)
- Power BI (dashboards)

## Como usar

1. Rode o script `CREATE TABLE RE-MAID.sql` em um banco PostgreSQL para criar o schema.
2. Popule com os dados de exemplo em `INSER INTO RE-MAID.sql`.
3. Explore as consultas prontas em `SELECT RE-MAID.sql` e `SELECTS RE-MAID.sql`.
4. Abra os arquivos `.pbix` no Power BI Desktop e aponte a conexão de dados para o seu banco.

## Documento de requisitos

A pasta irmã `Doc Requesitos RE-MAID/` tem o levantamento de requisitos original do projeto — útil para entender o problema de negócio que motivou esse modelo de dados antes de mexer no schema.
