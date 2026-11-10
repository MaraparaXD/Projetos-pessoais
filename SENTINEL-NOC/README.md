# SENTINEL NOC

Plataforma independente de laboratório para transformar eventos de monitoramento em incidentes rastreáveis. Backend Python/FastAPI, frontend React/TypeScript e PostgreSQL. Nenhuma afiliação oficial com Checkmk ou empresas; somente dados sintéticos na demonstração.

O MVP inclui autenticação, RBAC, ingestão HMAC, idempotência, correlação, flapping, recuperação e reabertura de incidentes, auditoria e simulador. O painel permite consultar métricas, filtrar eventos, atribuir incidentes, adicionar comentários e acompanhar a investigação.

## Stack

| Camada | Tecnologias |
| --- | --- |
| Backend | Python 3.12+, FastAPI, Pydantic 2, SQLAlchemy 2 e Alembic |
| Frontend | React, TypeScript, Vite, Tailwind CSS e TanStack Query |
| Persistência | PostgreSQL 17; SQLite para desenvolvimento e testes |
| Infraestrutura | Docker Compose, Redis e Nginx |
| Testes | pytest, HTTPX, Vitest e Playwright |

## Obter o projeto

```bash
git clone https://github.com/MaraparaXD/Projetos-pessoais.git
cd Projetos-pessoais/SENTINEL-NOC
```

## Executar com Docker

Requisitos: Python 3.12+ para gerar a configuração; Docker Engine/Desktop **em execução**, com Compose v2; portas locais 8000 e 8080 livres.

```powershell
python scripts/setup_local.py
docker compose up --build
```

O script cria `.env` com senhas aleatórias e não sobrescreve um arquivo existente. Não copie `.env.example` sem substituir os marcadores. Abra [painel local](http://localhost:8080), entre com `admin@sentinel.local` e a senha `BOOTSTRAP_ADMIN_PASSWORD` do `.env`. Não existe senha padrão de produção.

Migrations executam em um contêiner separado antes da API; os healthchecks aguardam PostgreSQL, Redis e readiness. Redis serve ao rate limiting compartilhado nesta fase. O worker Celery será acrescentado na fase 4.

- Painel: `http://localhost:8080`
- OpenAPI/Swagger: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
- Liveness: `http://localhost:8000/health`
- Readiness: `http://localhost:8000/ready`

## Demonstrar eventos

Entre em **Integrações**, copie o UUID da integração **Laboratório Checkmk**, e execute na raiz:

```powershell
python scripts/simulate_checkmk.py --integration SEU_UUID --save output/demo.json
python scripts/simulate_checkmk.py --integration SEU_UUID --replay output/demo.json
python scripts/simulate_checkmk.py --integration SEU_UUID --scenario flapping
python scripts/simulate_checkmk.py --integration SEU_UUID --scenario recovery
```

O primeiro cenário envia 6 eventos únicos e 1 replay exato: em banco vazio, são 6 incidentes e 6 eventos persistidos. Repetir o arquivo salvo devolve `duplicate=True` e não aumenta contagens. O dashboard consulta a API a cada 10 segundos. Abra um incidente para reconhecer, investigar, atribuir, comentar, resolver e encerrar. **Auditoria** registra as ações.

A integração inicial usa `BOOTSTRAP_WEBHOOK_SECRET` do `.env`. Para integrações criadas no painel, configure `SENTINEL_WEBHOOK_SECRET` no ambiente com o segredo exibido uma única vez. Nunca coloque esse segredo no frontend. O simulador não acessa um Checkmk real.

## Desenvolvimento sem Docker

SQLite é um fallback de desenvolvimento e testes; PostgreSQL é o banco do Compose. Execute o backend dentro de `backend/` para resolver corretamente o arquivo SQLite. Exemplo Windows/PowerShell com [uv](https://docs.astral.sh/uv/):

```powershell
python scripts/setup_local.py
uv venv .venv --python 3.12
uv pip install --python .venv/Scripts/python.exe -r backend/requirements-dev.lock
cd backend
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Em outro terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Abra `http://localhost:5173`. O proxy do Vite direciona `/api` para o backend. Alternativa sem uv: `python -m venv .venv`, depois `.venv\Scripts\python -m pip install -r backend/requirements-dev.lock`. No Linux, substitua `.venv/Scripts/python.exe` por `.venv/bin/python` e os caminhos PowerShell por `/`.

## Validação

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest -q
..\.venv\Scripts\python.exe -m ruff check app tests
..\.venv\Scripts\python.exe -m alembic check
cd ../frontend
npm test
npm run build
npx playwright install chromium
npm run test:e2e
```

Os testes do backend aplicam migrations reais em bancos temporários. Para executar os mesmos testes no PostgreSQL, defina `TEST_DATABASE_URL` para um banco descartável cujo nome termine em `_test`. **Esse banco de testes é limpo entre testes.** A CI faz essa verificação com PostgreSQL 17, além de verificar Compose e frontend. A execução na CI não é presumida como concluída localmente.

Com o Compose ativo, a alternativa pronta é `python scripts/test_postgres.py`: cria/usa o banco dedicado `sentinel_test` e executa a suíte em um contêiner temporário, preservando o banco de demonstração. `python scripts/smoke_demo.py` valida login, simulador, replay e dashboard no Compose e deixa seis eventos sintéticos disponíveis no painel.

Playwright inicia API em 8001 e Vite em 5174 com SQLite temporário e credenciais exclusivas de teste, sem tocar no banco da demonstração. Capturas desktop/mobile ficam em `output/playwright/`. `SENTINEL_PYTHON` permite selecionar o executável Python dos testes de navegador.

## Estrutura

```text
backend/
  app/
    domain/           # estados e regras puras
    application/      # ingestão, ciclo de incidentes, bootstrap e auditoria
    infrastructure/   # SQLAlchemy, segurança, rate limiting e Checkmk REST
    interfaces/       # FastAPI, schemas, RBAC e middleware
    core/             # configuração validada
  migrations/         # Alembic, schema explícito
  tests/              # unidade, API, integração e concorrência
frontend/
  src/                # React, TanStack Query, páginas e temas
  e2e/                # fluxos reais de navegador
scripts/              # setup, simulador e notificação Checkmk
compose.yaml
```

O workflow do projeto fica em `.github/workflows/sentinel-noc.yml`, na raiz do repositório de projetos pessoais.

## Arquitetura e regras de correlação

Monólito modular com separação entre domínio, aplicação, infraestrutura e interfaces. O evento, a atualização do incidente e a auditoria são persistidos na mesma transação. A ingestão só confirma sucesso depois do commit.

- A chave de correlação combina integração, host, serviço e tipo HOST/SERVICE.
- Um incidente ativo recebe os novos eventos do mesmo recurso. Uma constraint no banco impede dois incidentes ativos para a mesma chave.
- `external_id` é único por integração. Um replay exato retorna o evento existente; conteúdo diferente com o mesmo ID retorna HTTP 409.
- `OK` e `RECOVERY` resolvem o incidente ativo. Um novo problema até 900 segundos após a resolução reabre o incidente; depois desse prazo, cria outro.
- `CLOSED` é terminal. A sequência de triagem permite reconhecer, investigar, resolver e encerrar.
- Eventos com horário anterior ou igual ao último observado ficam no histórico como `out_of_order`, sem alterar o estado atual.
- Flapping é detectado com pelo menos 4 transições em 600 segundos. Os parâmetros são configuráveis; a flag é recalculada a cada novo evento.

O dashboard usa dados da API e identifica eventos sintéticos. Tendência e severidade usam uma janela móvel de 24 horas por horário de recebimento. As médias de reconhecimento e resolução usam o tempo desde a criação original do incidente; sem amostra, retornam null. Uma janela móvel pode ocupar 25 intervalos de hora, com o primeiro e o último parciais.

## Perfis e segurança

| Perfil | Permissões |
| --- | --- |
| Admin | Gerenciar usuários e integrações, operar incidentes e consultar auditoria |
| Analyst | Consultar o workspace, atribuir, comentar e conduzir incidentes |
| Viewer | Consultar o workspace sem alterar registros |

Senhas usam Argon2. Tokens são opacos e revogáveis, com validade padrão de 8 horas; somente seu hash é armazenado no banco. O navegador mantém o token em memória, portanto recarregar exige novo login.

Webhooks usam HMAC SHA-256 por integração, assinatura com timestamp e tolerância de 300 segundos. Há limite de 64 KiB por requisição, validação de payload, rate limiting e CORS com origens explícitas. Segredos de integração são cifrados com Fernet; a chave fica em `INTEGRATION_ENCRYPTION_KEY`. Guarde essa chave para conseguir restaurar as integrações existentes.

O Compose publica apenas as portas locais da API e do painel. PostgreSQL e Redis permanecem na rede interna. O workspace atual é único e compartilhado conforme RBAC; não há isolamento multi-tenant. A demonstração é local e requer revisão adicional antes de exposição remota.

Para criar outros operadores, execute na raiz do projeto:

```bash
docker compose exec api python -m app.cli create-user --email analyst@sentinel.local --name Analista --role Analyst
docker compose exec api python -m app.cli create-user --email viewer@sentinel.local --name Observador --role Viewer
```

A CLI solicita e confirma a senha sem exibi-la. O bootstrap cria contas apenas quando ainda não existem; alterar a senha no `.env` não redefine uma conta existente.

## Integração com Checkmk

O Checkmk precisa de um método e de uma regra de notificação configurados para enviar os eventos desejados. A API REST não é uma assinatura automática de alertas.

O adaptador `backend/app/infrastructure/checkmk.py` consulta inventário em modo somente leitura, com HTTPS, allowlist de host, verificação TLS, IP de destino validado e proteção contra SSRF. O mock é explicitamente sintético. Esse adaptador não é executado automaticamente e não alimenta o painel como se estivesse conectado a um ambiente real.

Para testar o encaminhamento em um Checkmk próprio de laboratório:

1. Instale `scripts/checkmk_notification.py` e `scripts/simulate_checkmk.py` no diretório `~/local/share/check_mk/notifications` do site. O segundo fornece a função de assinatura; apenas o primeiro é selecionado como método.
2. Torne o script de notificação executável e configure `SENTINEL_WEBHOOK_URL` com uma URL HTTPS fixa terminada em `/api/webhooks/checkmk/UUID`, além de `SENTINEL_WEBHOOK_SECRET`, no ambiente efetivo do processo de notificação.
3. Crie e ative uma regra para problemas e recuperações dos hosts/serviços de laboratório. Confirme as variáveis `NOTIFY_*` na documentação da versão instalada.
4. Valide com uma notificação de teste e consulte os logs do laboratório. Tipos suportados: PROBLEM, RECOVERY, FLAPPINGSTART e FLAPPINGSTOP. Não direcione outros tipos sem estender o contrato.

Nenhuma conexão a Checkmk real foi validada. O simulador local funciona sem Checkmk e é o caminho recomendado para reproduzir a demonstração. Referências oficiais: [REST API](https://docs.checkmk.com/latest/en/rest_api.html) e [notificações](https://docs.checkmk.com/latest/en/notifications.html).

## Operação e retenção

```bash
docker compose ps
docker compose logs --tail 100 api
docker compose exec api alembic current
docker compose exec api python -m app.cli retention
docker compose down
```

O comando de retenção remove eventos anteriores a 90 dias, preservando os vinculados a incidentes ativos, além de sessões expiradas e auditoria anterior a 365 dias. O agendamento deve ser configurado pelo operador. Incidentes, comentários e inventário são preservados. `docker compose down` mantém os volumes.

Logs JSON incluem correlation ID, rota, status e duração. `/metrics` expõe métricas Prometheus com autenticação Admin. `/ready` verifica banco, revisão Alembic e Redis.

## Resultados de validação

| Verificação local | Resultado |
| --- | --- |
| Backend com SQLite | 41 testes passaram |
| Mesma suíte com PostgreSQL | 41 testes passaram |
| Vitest | 5 testes passaram |
| Playwright Chromium | 2 fluxos passaram, com verificação desktop e mobile |
| Build TypeScript/Vite e Docker Compose | Concluídos |
| Simulador e replay no Compose | 6 eventos persistidos, sem duplicação no replay |

O cliente de testes HTTPX emite um aviso de depreciação do Starlette sobre a futura migração para HTTPX2; ele não foi suprimido. O workflow GitHub Actions valida o projeto em ambientes próprios. Os resultados acima descrevem a execução local, não substituem os resultados de cada execução da CI.

## Próximos passos

Celery, automações, retry com dead-letter, Telegram e webhook de saída, tickets simulados, playbooks, análise por IA, exportação OpenTelemetry e Grafana ainda não estão implementados. Nenhuma remediação automática é executada em servidores.
