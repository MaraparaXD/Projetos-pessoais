# 🧙‍♂️ Wizard Tech - O Oráculo de Suprimentos (BI Logístico & Data Engine)

*"Nas profundezas do caos logístico, onde pergaminhos se perdem e estoques desaparecem, este Oráculo foi forjado para trazer a verdade aos olhos dos gestores."*

Bem-vindo ao **Wizard Tech**, um artefato completo de inteligência logística, validação de dados e auditoria de estoque. Desenvolvido para otimizar setores de compras, bloquear rupturas de estoque e identificar anomalias financeiras em tempo real.

---

## 🏰 Arquitetura do Artefato
A magia deste projeto acontece em duas camadas perfeitamente sincronizadas:
1. **O Motor (Backend - FastAPI):** O núcleo da engrenagem. Uma API robusta conectada diretamente às masmorras de um banco de dados SQL Server. Responsável por receber dados caóticos, purificá-los e gravar logs de proteção.
2. **O Espelho da Verdade (Frontend - Streamlit):** Um Dashboard interativo de Business Intelligence, desenhado com uma interface elegante e filtros implacáveis para a alta liderança.

---

## ✨ Feitiços e Encantamentos (Features Avançadas)

* 👁️ **Visão Verdadeira (Inferência de Schema):** O motor possui um scanner inteligente que varre planilhas despadronizadas. Usando a Teoria dos Conjuntos, ele identifica produtos e reestrutura colunas automaticamente, ignorando cabeçalhos bagunçados.
* 🛡️ **Escudo Anti-Excel:** Resiliência total contra arquivos corrompidos ou delimitadores trocados (vírgulas e pontos-e-vírgulas).
* ⚖️ **Detector de Ilusões (Análise Z-Score):** Um algoritmo estatístico embutido para detectar anomalias de preços (fraudes ou erros de digitação mortais) calculando o Desvio Padrão de cada item do inventário.
* ⚔️ **Guardião do Estoque (Cálculo de Ruptura):** Cruzamento em tempo real do volume de pedidos com o estoque oficial do SQL Server. Se o estoque quebrar, o sistema emite alertas vermelhos e grava a necessidade de reposição automaticamente no banco.
* 📊 **Dashboard Premium (Plotly & Streamlit):** Gráficos interativos renderizando na velocidade da luz, com cálculos de impacto financeiro (Custo de Reposição) e exportação nativa formatada para `.xlsx` e `.csv`.

---

## 📖 Grimório de Tecnologias
Para invocar este sistema, os seguintes conhecimentos foram combinados:
* **Linguagem Anciã:** Python 3.10+
* **Cofre de Dados:** Microsoft SQL Server (com `pyodbc`)
* **Estrutura Backend:** FastAPI, Uvicorn
* **Alquimia de Dados:** Pandas, Estatística Matemática
* **Interface Mágica:** Streamlit, Plotly Express

---

## ⚙️ Ritual de Invocação (Como rodar localmente)

1. Clone este repositório para o seu inventário local.
2. Instale as dependências mágicas: 
   ```bash
   pip install -r requirements.txt
Desperte o Motor da API:

3. Bash
python main.py
Em um novo terminal, abra o Espelho da Verdade:

4. Bash
streamlit run interface_wizard.py
Acesse seu portal local no navegador e inicie a auditoria!


