# Monitor de Rede e Inventário Ativo

Sistema de monitoramento de rede em tempo real, construído para unificar a visibilidade de dispositivos em duas redes distintas (TI e Logística) de uma distribuidora, com alerta automático para dispositivos não identificados.

## O que o sistema faz

O sistema roda em duas partes que se comunicam entre si:

1. **Coletor (`recebe_logs.py`)** — processo em background que:
   - Faz varredura ativa (ping multithread) na rede de TI para mapear dispositivos conectados.
   - Autentica na interface administrativa de um roteador Intelbras via requisição HTTP para listar os dispositivos conectados na rede de Logística (contorna a ausência de API oficial do roteador).
   - Mantém um servidor Syslog (UDP, porta 514) escutando por mensagens DHCP, para detectar em tempo real quando um novo dispositivo entra na rede.
   - Persiste o estado atual em `dados/estado_atual.json`.

2. **Dashboard (`dashboard_duraes.py`)** — interface web (Flask) que:
   - Exibe os dispositivos ativos, atualizando via polling a cada poucos segundos.
   - Sinaliza com um alerta visual qualquer dispositivo cujo identificador não conste em uma lista de dispositivos conhecidos (`dados/dispositivos.json`).

## Stack

- Python 3.10+
- Flask (dashboard web)
- `requests` (autenticação/consulta ao roteador)
- Sockets nativos + threading (varredura de rede e servidor Syslog)

## Como rodar localmente

Pré-requisito: acesso à rede local (ou VPN) onde os dispositivos estão.

1. Configure `dados/dispositivos.json` com os IPs e nomes dos dispositivos já conhecidos — sem isso, tudo aparece como "novo".
2. Em `recebe_logs.py`, preencha as constantes de configuração (URL do roteador, usuário/senha, prefixo da rede de TI). **Não deixe credenciais reais hardcoded no código-fonte** — use variáveis de ambiente ou um arquivo `.env` ignorado pelo Git.
3. Em dois terminais separados:
   ```bash
   python recebe_logs.py      # inicia a coleta/varredura
   python dashboard_duraes.py # sobe o painel web
   ```
4. Acesse `http://localhost:5000`.

## Observações

- Projeto construído para um cenário real (rede de uma distribuidora), com IPs e nomes de host específicos removidos/generalizados no código publicado.
- O acesso ao roteador via requisição HTTP direta é um contorno específico do modelo/firmware usado — não é uma técnica genérica de "bypass".
- Como boa prática, nenhuma credencial deve permanecer no código-fonte; use variáveis de ambiente.
