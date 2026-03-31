# 👁️‍🗨️ CNPJ Analytics - O Oráculo de Crédito (Motor de Risco & Vidência Financeira)

"Nas encruzilhadas do mercado, onde falsos mercadores ocultam suas dívidas e moedas desaparecem, este Oráculo foi forjado para revelar a verdadeira face de cada guilda."

Bem-vindo ao **CNPJ Analytics**, um artefato implacável de inteligência financeira e logística. Desenvolvido para cruzar pergaminhos públicos em tempo real com os cofres da sua guilda, gerando um "Risk Score" automático e blindando a concessão de ouro (crédito) contra maus pagadores.

## 🏰 Arquitetura do Artefato

A magia deste projeto acontece em duas camadas perfeitamente sincronizadas, aprisionadas dentro de uma dimensão de bolso (Docker):

* **O Motor das Sombras (Backend - FastAPI):** O núcleo assíncrono do sistema. Uma API de altíssima velocidade conectada aos cofres ancestrais de um banco de dados Oracle. Responsável por receber invocações, consultar oráculos externos e calcular o destino do crédito.
* **O Espelho da Verdade (Frontend - HTML & Tailwind):** Um Dashboard interativo e elegante, desenhado com runas visuais (Chart.js) para que a alta liderança compreenda os vereditos financeiros sem precisar decifrar códigos.

## ✨ Feitiços e Encantamentos (Features Avançadas)

👁️ **Visão Verdadeira (Consumo de APIs em Tempo Real):** Integração mística com os oráculos do governo (BrasilAPI e ViaCEP) para desmascarar CNPJs, validar status cadastrais e mapear territórios de logística num piscar de olhos.

⚡ **Celeridade Arcana (Cache em Memória):** Um feitiço de retenção de conhecimento. Consultas repetidas de um mesmo CNPJ são respondidas instantaneamente pela memória espiritual da aplicação, poupando a mana (processamento) do banco de dados principal.

🛡️ **Abjuração de Intrusos (Autenticação via Token):** Barreira de proteção intransponível. Apenas magos portando o amuleto sagrado (`X-API-Token` no header) podem cruzar os portões da API e solicitar vidências.

⚖️ **Julgamento Neural (Risk Score Automático):** Algoritmo que cruza faturamento, histórico de inadimplência e o status da Receita Federal para ditar o destino do mercador: Manter Crédito, Bloquear Operações ou Expandir Limites.

🐳 **Magia de Isolamento (Containerização Docker):** Todo o ecossistema vive isolado dentro de um container. Imune às pragas do ambiente externo e pronto para ser invocado em qualquer reino (máquina Windows, Linux ou Mac) sem quebrar dependências.

## 📖 Grimório de Tecnologias

Para invocar este sistema, os seguintes conhecimentos foram combinados:

* **Linguagem Anciã:** Python 3.11+
* **Cofre de Dados:** OracleDB (com integração nativa)
* **Estrutura Backend:** FastAPI, Uvicorn (Assíncrono)
* **Círculo de Invocação (Infra):** Docker & Docker Compose
* **Pergaminhos de Clarividência:** Integração REST com BrasilAPI e ViaCEP
* **Ilusionismo Visual:** HTML5, TailwindCSS, Chart.js

## ⚙️ Ritual de Invocação (Como rodar localmente)

1. Clone este repositório para o seu inventário local:
```bash
git clone [https://github.com/MaraparaXD/Projetos-pessoais.git](https://github.com/MaraparaXD/Projetos-pessoais.git)
Forje o seu amuleto de conexão:
Copie o pergaminho dados.env.example e renomeie-o para dados.env. Grave as suas verdadeiras runas de poder dentro dele (Tokens, Usuário e Senha do Oracle).

Desperte o leviatã mágico (Docker):
No seu terminal, dentro da pasta do projeto, entoe o cântico de invocação:

Bash
docker compose up -d --build
Contemple a Vidência:
Abra o seu portal local no navegador:

🔮 Espelho da Verdade (Dashboard): http://localhost:8000

📜 Grimório Interativo (Swagger UI): http://localhost:8000/docs para testar as feitiçarias da API diretamente.


***

Pronto! Só jogar no seu GitHub agora. O repositório vai ficar lendário! ⚔️🚀
