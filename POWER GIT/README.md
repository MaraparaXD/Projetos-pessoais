# Power Git — Assistente de Commit Guiado

Script Bash que guia o fluxo `add → commit → push` do Git por um menu interativo, no padrão de mensagens do [Conventional Commits](https://www.conventionalcommits.org/) (`FEAT`, `FIX`, `REFACTOR`, `DOCS`, etc.).

## O que o script faz

1. Verifica se você está na raiz de um repositório Git e mostra o branch atual.
2. Se houver alterações, mostra o status resumido (`git status -s`).
3. Pergunta se quer adicionar tudo (`git add .`) ou entrar no modo interativo (`git add -p`), arquivo por arquivo.
4. Monta a mensagem de commit de forma guiada:
   - Escolha do tipo (`FEAT`, `FIX`, `REFACTOR`, `DOCS`, `STYLE`, `TEST`, `CHORE`, `PERF`, `CI`, `BUILD`)
   - Escopo opcional (ex: `login`, `api`)
   - Título obrigatório
   - Corpo opcional, com descrição mais detalhada
5. Mostra a mensagem final para revisão antes de confirmar o commit.
6. Depois do commit, pergunta se quer fazer `git push` na hora — detecta automaticamente se o branch já tem upstream configurado ou se precisa criar um novo (`--set-upstream`).

## Como usar

1. Copie o script para dentro de um repositório Git local (ou adicione ao `PATH` do seu sistema para usar em qualquer repositório).
2. Dê permissão de execução:
   ```bash
   chmod +x powergit.sh
   ```
3. Rode dentro de um repositório com alterações pendentes:
   ```bash
   ./powergit.sh
   ```

## Por que existe

Escrever mensagens de commit consistentes é fácil de negligenciar no dia a dia. Este script existe para tornar o padrão (tipo + escopo + descrição) o caminho mais rápido, não o mais trabalhoso.
