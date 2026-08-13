# Guia de publicação — repositórios separados

Este pacote tem 4 pastas, cada uma pronta para virar um repositório próprio no
seu GitHub. Todas já têm: código corrigido, README direto, `.gitignore` e
arquivo `.env.example` (ou `dados.env.example`) documentando as variáveis
necessárias.

| Pasta | Vira o repositório | Topic sugerida |
|---|---|---|
| `contabil_api/` | `cnpj-analytics` (ou o nome que preferir) | `backend` |
| `wizard_api/` | `wizard-api` | `backend` |
| `mapeamento-de-rede/` | `monitor-rede` | `soc` |
| `zenerp/` | `zenerp` | `automacao` |

A topic é o que faz cada repositório aparecer sozinho na seção "Deployments"
do seu portfólio — é só marcar exatamente esse texto (sem acento, minúsculo)
em Settings → Topics de cada repo no GitHub.

---

## Passo 1 — Criar cada repositório no GitHub

Para cada uma das 4 pastas:

1. Vá em [github.com/new](https://github.com/new).
2. Dê o nome sugerido na tabela acima (ou outro de sua preferência).
3. **Não** marque "Add a README" nem "Add .gitignore" — a pasta já tem os
   dois, e marcar isso no GitHub cria conflito na hora do primeiro push.
4. Clique em "Create repository" e deixe a página aberta — ela mostra a URL
   que você vai usar no passo 2.

## Passo 2 — Publicar cada pasta

Abra um terminal, entre em cada pasta e rode (trocando `SEU_USUARIO` e
`NOME_DO_REPO` pelos valores reais):

```bash
cd contabil_api
git init
git add .
git commit -m "Versão inicial"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/NOME_DO_REPO.git
git push -u origin main
```

Repita para `wizard_api/`, `mapeamento-de-rede/` e `zenerp/`.

## Passo 3 — Marcar a topic

Em cada repositório recém-criado no GitHub: clique na engrenagem ao lado de
"About" (barra lateral direita) → campo "Topics" → digite a topic da tabela
acima → Enter → Save changes.

## Passo 4 — Antes de rodar de verdade

Cada pasta tem um `.env.example` (ou `dados.env.example`). Copie para `.env`
(ou `dados.env`) **fora do controle do Git** — o `.gitignore` já está
configurado para nunca deixar esse arquivo ser commitado — e preencha com
suas credenciais reais.

---

## E o repositório antigo (`Projetos-pessoais`), com a senha vazada?

A senha do Azure que identifiquei já deve ter sido trocada (isso é o mais
importante e não pode esperar, se ainda não fez). Sobre o repositório em si,
duas opções:

### Opção A — recomendada, mais simples

Torne o repositório `Projetos-pessoais` **privado**:
Settings → General → Danger Zone → "Change repository visibility" → Private.

Isso tira a senha vazada de circulação pública imediatamente, e você mantém
o histórico de commits (e a contagem de contribuições no seu perfil, se a
opção "Include private contributions on my profile" estiver ativada em
Settings → Profile). Os 4 repositórios novos passam a ser sua vitrine
pública; o antigo vira só um arquivo pessoal.

### Opção B — mais trabalhosa, mantém tudo público

Se você quiser manter esse repositório específico público mas com a senha
removida também do **histórico** (não só do arquivo atual), é preciso
reescrever o histórico do Git. Isso exige rodar localmente (não dá pra fazer
pelo site do GitHub):

```bash
# instala a ferramenta (uma vez só)
pip install git-filter-repo

# dentro de uma cópia local do repositório antigo
git filter-repo --replace-text <(echo "Tiago23072004!==>SENHA_REMOVIDA")

# depois, força o push da história reescrita
git push origin --force --all
```

**Atenção:** isso reescreve o hash de todos os commits do repositório — se
alguém já clonou ou deu fork antes disso, a cópia dela fica dessincronizada.
Como é um repositório pessoal de estudo, isso não costuma ser problema, mas
é bom saber.

**Minha recomendação:** Opção A. É mais simples, resolve o problema de
exposição imediatamente, e você não perde nada do seu histórico de
contribuições.
