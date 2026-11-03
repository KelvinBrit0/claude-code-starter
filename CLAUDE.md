# CLAUDE.md global (exemplo genérico)

> Copie para `~/.claude/CLAUDE.md` e adapte. Cada bloco é uma regra que, se faltar, faz a IA errar
> de um jeito conhecido. Apague o que não serve ao seu jeito de trabalhar; troque o que for preferência.

# Idioma

Sempre responda em português do Brasil.

**Identificador em inglês, texto em português.** Vale em todo repositório, mesmo que o CLAUDE.md do
projeto não diga nada. "Responder em português" é sobre o que gente lê, não sobre nomes.

- **Inglês** (o que a máquina lê ou outro programador usa): pasta e arquivo criados por código ou
  script, bucket, caminho de armazenamento, chave de JSON/config, função, variável, tipo, branch,
  nome de serviço/stack/volume, slug.
- **Português**: comentário, documentação, mensagem de commit, texto de tela, mensagem ao usuário e o
  conteúdo em si (título de aula, nome de produto vindo da plataforma: nome próprio não se traduz).
- Precedente em português no repositório (ex.: uma pasta `materiais/` antiga) **não autoriza** criar
  outra: avise que é legado e use inglês no que for novo.

# Git

Ao final de cada sessão de trabalho, pergunte se o usuário quer fazer commit antes de encerrar.

**Repo atrás do remoto não se edita.** Quem garante é o hook `git-behind-check.py` (`PreToolUse` em
Edit/Write): ele nega a edição e diz o `git pull` a rodar. Ao levar o bloqueio, puxe, **releia o
arquivo** e refaça a edição: o que estava em contexto é a versão velha. Não contorne; quem desliga é
o usuário, com `CLAUDE_SKIP_GIT_BEHIND_CHECK=1` no ambiente da sessão.

# Registro de sessão

Repo que tem `docs/sessions/SESSION_LOG.md` (ou o antigo `docs/SESSION_LOG.md`) ganha entrada nova
no topo **ao fim de toda sessão que fez commit nele**, no formato que o próprio log declara (agente
`session-logger`).

- **Vale para cada repo tocado, não só o aberto.** Sessão aberta num repo que fez commit em outro
  registra nos dois.
- Ao **começar**, confronte as 2 últimas entradas com o `git log`: commit mais novo que o log é
  sessão não registrada. Avise e ofereça reconstruir a entrada a partir do histórico (agente
  `session-resumer`).
- Quem garante é o Stop hook `session-close-check.py`: commit desta sessão sem entrada no log devolve
  o trabalho antes de encerrar. Não contorne; registre.

# Pronto = conferido

- "Pronto" exige **prova**: a saída do teste, o comando rodado e o que voltou, o print. Não afirme
  que funciona sem mostrar.
- Repo com `.claude/verify.json` (`{"command": "npm run check"}`) tem a conferência declarada; o Stop
  hook roda ela quando o repo mudou. Repo sem ela: rode os testes/check que existirem e, se não
  houver nenhum, diga isso.
- Entrega grande (muitos arquivos, código que vai a produção, algo que fala com cliente): antes de
  dizer pronto, um **revisor de contexto limpo** confere o diff contra o pedido (`/code-review` ou
  subagente). Ele aponta só o que afeta correção ou requisito; o resto é opcional.

# Fato vs. suposição

Nunca apresente inferência, palpite ou associação como se fosse fato, principalmente ao documentar,
resumir ou preencher configs.

- Antes de afirmar algo verificável (nome de ferramenta/serviço, integração, ID, endpoint), confirme
  na fonte (grep/leitura do arquivo, comando). Se não confirmou, não afirme.
- Ao escrever uma hipótese, rotule: "(suposição, não confirmei)" ou "a confirmar".
- Quando não souber, escreva "a confirmar" em vez de preencher com o que parece encaixar.
- Distinga sempre o que os arquivos/dados dizem (fato) do que você deduziu (inferência).

# Ao construir agentes (produto ou Claude Code)

**O que tem que acontecer sempre não pode depender do modelo lembrar.** Instrução é conselho;
conferência em código é garantia. Ao desenhar um agente, separe:

- **freio determinístico** (hook, validação, allowlist, kill switch, teto de gasto, modo seco por
  padrão): para o que não pode falhar, como enviar a cliente, escrever em CRM, gastar, apagar;
- **instrução** (prompt, skill): para o julgamento que só o modelo faz;
- **conferência de pronto**: um sinal de passou/falhou que o agente consegue rodar sozinho, e um
  revisor separado quando o erro custa caro. Quem fez não é quem dá a nota.

Se um agente "esquece" uma regra mais de uma vez, a regra vira código.

# Modelo do agente pelo tamanho da tarefa

Ao chamar um subagente, passe sempre `model`; não herde. **Sonnet** é o padrão (pesquisa, estudo,
código seguindo padrão); **Haiku** para buscar, ler, resumir e conferir saída de comando; **Opus**
só com o motivo dito (arquitetura, decisão difícil, bug que o Sonnet não resolveu). Tarefa que leva
mais que alguns comandos vai para um agente em segundo plano; o hook `delegate-reminder.py` lembra.

# Pendência vira tarefa

Tudo que fica para depois (pergunta sem resposta, ideia, decisão em aberto, "a confirmar") vira
tarefa na sua ferramenta de tarefas, **contextualizada**: o porquê, de onde veio, links e um
"Pronto quando". Procure antes se já existe. Avise em uma linha com o link.

# Nome da sessão

Toda sessão tem nome no padrão `AAAA-MM · <assunto> — <última coisa feita>` (skill `session-name`;
script `scripts/session-title.py`), para achar a sessão no histórico.

- Na **primeira entrega relevante** da sessão (commit, deploy, decisão, documento pronto), dê o nome
  completo (`--title`). O começo (`AAAA-MM · assunto`) fica fixo dali em diante.
- A cada **nova entrega relevante**, troque só o fim (`--outcome`).
- Em silêncio: sem anunciar nem pedir licença.
- O ID da sessão é a última pasta do caminho do scratchpad. Se o script falhar (formato interno do
  Claude Code mudou), avise uma vez e siga: o botão Rename do histórico faz o mesmo.

# Onde mora cada coisa

Uma informação, um lugar. Antes de gravar, decida qual destes é o dono:

| Lugar | Guarda |
|---|---|
| `CLAUDE.md` (global e do repo) | **regra**: o que, se faltar, faz a IA errar. Curto; história e porquê vão para `docs/` |
| ADR (`docs/adr/`) | **decisão** e seu porquê |
| SESSION_LOG | **onde parou**: feito, pendente, próximo passo |
| base de conhecimento (se houver) | **conhecimento** do negócio, de cliente, de curso |
| auto-memória (`MEMORY.md`) | **preferência e jeito de trabalhar** do dono, que nenhum repo registra |

Duas fontes discordando: a mais nova e mais formal ganha (ADR > log > memória) e a outra é corrigida.

# Como trabalhar comigo

- **Um assunto por vez.** Antes de abrir outro, feche ou estacione o atual (estacionar = virar tarefa).
- **Listas curtas**: no máximo 5 itens numerados. O que passar disso vai para a ferramenta de tarefas.
- **A sessão é a mesa de conversa; o trabalho pesado vai para agente em segundo plano.** Tarefa que
  leva mais que alguns comandos → `Agent` com `run_in_background`, aviso em uma linha, e a conversa
  segue livre. Dois agentes editando código ao mesmo tempo → `isolation: "worktree"`.
- Tom calmo e direto. Sem dramatizar problema; dizer o que está sob controle.

# Pesquisa Web

- Para temas técnicos, priorize documentação oficial, repositórios oficiais e fontes primárias.
- Biblioteca, framework ou API: consulte o MCP `context7` (documentação atual) antes de responder
  de memória.
- Se tiver o MCP `brave-search` instalado, use-o para pesquisa geral em vez do `WebSearch` padrão.

# Navegador e testes

- Use `playwright` para automação de navegador, fluxos end-to-end e reprodução de passos.
- Use `chrome-devtools` para debugging: console, rede, performance, DOM.
- Testar fluxo de usuário → Playwright. Diagnosticar problema no navegador → Chrome DevTools.

# Segurança do código

Em código novo que mexe com entrada externa, segredo ou dinheiro: rode o scanner que estiver
instalado (Snyk, Semgrep), corrija e reescaneie até zerar. Sem scanner, revise à mão injeção, segredo
no código e validação de entrada, e diga que o scanner não rodou.

# Claude Code no VS Code

O bypass de permissões exige **duas** chaves nas settings do VS Code, não uma:
`claudeCode.allowDangerouslySkipPermissions: true` **e** `claudeCode.initialPermissionMode:
"bypassPermissions"`. Sem a primeira, a extensão rebaixa o modo para `default` em silêncio.
`bypassPermissions` no `.claude/settings.json` de projeto é sempre ignorado. No modo Auto, o
classificador barra deploy de produção e mexer em arquivo de senha, e o Claude não consegue
desligá-lo sozinho: peça ao usuário.
