# Gerenciador de Tabelas — Azure SQL

Ferramenta de linha de comando (CLI) para administrar um banco Azure SQL sem precisar escrever SQL manualmente para tarefas do dia a dia: criar tabela, consultar dados, inserir, atualizar e excluir — tudo por menu interativo no terminal.

## O que a ferramenta faz

Um menu no terminal com 5 opções:

1. **Criar Tabela** — monta um `CREATE TABLE` de forma guiada: você digita `nome tipo` linha por linha (ex: `id INT PRIMARY KEY IDENTITY`) até finalizar.
2. **Ler Dados (Select)** — lista as tabelas existentes no banco e mostra o conteúdo de qualquer uma, formatado em tabela no terminal.
3. **Inserir Dados** — detecta as colunas da tabela escolhida e pede o valor de cada uma, uma a uma.
4. **Atualizar (Update)** — pede a coluna a alterar, o novo valor, e a condição do `WHERE`, com confirmação antes de executar.
5. **Excluir (Drop)** — remove uma tabela inteira, com confirmação explícita antes.

A interface usa a biblioteca `rich` para formatar tabelas, cores e painéis no terminal.

## Stack

- Python
- `pyodbc` (conexão com Azure SQL)
- `rich` (interface de terminal)

## Como rodar localmente

1. Instale as dependências:
   ```bash
   pip install pyodbc rich
   ```
2. Abra `gerenciador.py` e preencha `SERVER`, `DATABASE`, `USERNAME` e `SENHA` — ou, melhor, adapte o script para ler essas informações de variáveis de ambiente (veja o padrão usado nos outros projetos deste perfil, como o `contabil_api`).
3. Execute:
   ```bash
   python gerenciador.py
   ```

## Observações

- Os nomes de tabela e coluna são montados diretamente na string SQL (não dá para parametrizar identificadores de tabela/coluna em SQL, é uma limitação da linguagem, não do código). Isso é aceitável para uma ferramenta de uso pessoal via terminal, mas **não deve ser exposta como serviço/API** sem antes validar e sanitizar esses nomes contra uma lista de tabelas/colunas conhecidas.
- Assim como nos demais projetos, nunca deixe usuário/senha escritos diretamente no arquivo — use variáveis de ambiente.
