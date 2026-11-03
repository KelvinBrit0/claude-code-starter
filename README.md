# Pacote de fluxo de trabalho para o Claude Code

Este pacote é para o **seu Claude Code** ler e dizer o que vale aproveitar, e também para você
entender, sem ser técnico. Nada aqui é obrigatório: são peças soltas. Cada uma
resolve um problema que aparece quando se trabalha todo dia com um assistente de código.

Analogia: o Claude Code é um funcionário muito rápido que **esquece o que não está escrito** e **às
vezes diz que terminou sem ter conferido**. Este pacote é o conjunto de regras na parede (CLAUDE.md),
de travas na porta (hooks) e de ajudantes especializados (agents) que reduz esses dois defeitos.

## Os princípios (valem para qualquer pessoa, com ou sem estas peças)

1. **Pronto = conferido.** O Claude só diz "pronto" mostrando prova: a saída do teste, o comando
   rodado e o que voltou, um print. Em entrega grande (muitos arquivos, algo que vai para produção ou
   fala com cliente), um segundo Claude de contexto limpo (o "revisor") confere o diff contra o
   pedido. Quem fez não é quem dá a nota.
2. **O que tem que acontecer sempre vira hook, não instrução.** Instrução ("lembre de X") é conselho
   e o modelo esquece. Hook é um programa pequeno que o Claude Code roda sozinho em certos momentos
   (antes de editar, ao encerrar...) e pode barrar a ação. Regra que o Claude esqueceu mais de uma
   vez vira hook. Esse é o freio determinístico: serve para o que não pode falhar (enviar a cliente,
   gastar, apagar, sobrescrever trabalho de outro).
3. **Pendência vira tarefa.** Tudo que fica para depois (pergunta sem resposta, ideia, "a confirmar")
   vai para a sua ferramenta de tarefas, com o porquê, de onde veio e um "Pronto quando". Nada fica só
   na conversa, que some.
4. **Modelo do agente pelo tamanho da tarefa.** Modelo maior custa mais. Sonnet é o padrão; Haiku para
   buscar, ler e conferir; Opus só com motivo dito. Ver a seção "Custo (tokens)".
5. **Registro de sessão (SESSION_LOG).** Cada repositório guarda em `docs/sessions/SESSION_LOG.md` o
   que foi feito, o que ficou pendente e o próximo passo. Quem abre uma sessão nova lê as duas últimas
   entradas e confere com o `git log`; quem fecha uma sessão com commit escreve a entrada.
6. **Nome de sessão.** Toda sessão ganha um nome no padrão `AAAA-MM · assunto — última coisa feita`
   para achar depois no histórico.
7. **Fato não é suposição.** O Claude confirma na fonte antes de afirmar; o que não confirmou vai
   rotulado "a confirmar".

## O que tem aqui

| Peça | O que é | Problema que resolve |
|---|---|---|
| `CLAUDE.md` | Regras globais de exemplo (idioma, git, registro de sessão, pronto = conferido, fato vs. suposição, agentes, nome de sessão) | O Claude não sabe seu jeito de trabalhar; sem regra escrita ele improvisa |
| `hooks/git-behind-check.py` | Antes de editar arquivo, confere se o repositório está atrás do remoto; se estiver, nega e manda dar `git pull` | Editar um clone desatualizado sobrescreve trabalho já publicado (caso real no setup de origem: clone 249 commits atrás do `origin/main`) |
| `hooks/session-close-check.py` | Ao encerrar, confere se o commit da sessão tem entrada no SESSION_LOG e roda a conferência do repo (`.claude/verify.json`) | Sessão que termina sem registro e sem teste |
| `hooks/delegate-reminder.py` | Depois de ~8 chamadas seguidas na sessão principal, lembra (uma vez por turno) de mandar o trabalho longo para um agente em segundo plano | Contexto da conversa cheio e custo alto |
| `hooks/compact-clickup-resume.py` | Depois que o contexto é compactado, lembra de reler a tarefa do assunto na sua ferramenta de tarefas antes de continuar | A compactação perde o detalhe do trabalho em andamento |
| `agents/commit-writer.md` | Propõe a mensagem de commit (português, foco no porquê); nunca commita sozinho | Mensagem de commit ruim ou em padrão misturado |
| `agents/session-logger.md` | Escreve a entrada nova no SESSION_LOG ao fim da sessão | Esquecer de registrar |
| `agents/session-resumer.md` | No começo da sessão, lê o log, confere com o git e diz onde paramos (só leitura) | Recomeçar sem contexto |
| `agents/planejador-estrategico.md` | Quebra uma demanda grande em plano com etapas, dependências e riscos | Começar a codar sem plano |
| `skills/session-name/` + `scripts/session-title.py` | Dá e atualiza o nome da sessão no padrão acima | Histórico de sessões ilegível |
| `vscode/` | Settings e extensões do VS Code (bypass de permissões, notificações) | Configuração do editor que "some" sem aviso |
| `settings.example.json` | O que vai no `settings.json`: idioma, esforço, permissões, plugins, a compactação aos 200 mil tokens, os agentes em Sonnet e o bloco `hooks` que liga as quatro peças de `hooks/` | Hook copiado mas não ligado não faz nada; conversa e agente gastando mais que o necessário |

Todos os agentes são genéricos.

### Decisões de empacotamento

- **Backlog:** não incluí uma skill de backlog. A original é presa ao ClickUp e a IDs de um
  workspace específico; generalizar daria uma skill vazia. O princípio 3 e o hook
  `compact-clickup-resume.py` já cobrem o essencial. Se quiser, o seu Claude escreve uma skill
  `task-backlog` para a ferramenta que você usa (ClickUp, Notion, Linear, Trello).
- **Exemplo de padrão não incluído:** existe, no setup de origem, um hook que **só deixa o Claude
  chamar a ferramenta de tarefas se a chamada trouxer o ID do workspace certo** (uma allowlist por
  workspace). Serve para quem tem duas contas/workspaces e não pode misturar. Como é específico do
  ambiente de lá, não vai no pacote; o padrão é: hook `PreToolUse` com `matcher` no nome das
  ferramentas daquele MCP, que nega quando o parâmetro de workspace falta ou é de outro. Se você tem
  mais de um workspace, peça ao seu Claude para escrever o equivalente.

## Como instalar

Os caminhos usam `<HOME>` para a sua pasta pessoal. Troque por ela com barras normais, por exemplo
`C:/Users/seunome` no Windows ou `/Users/seunome` no Mac.

1. **Hooks, agentes, skill e script.** Copie as pastas para dentro de `<HOME>/.claude/`:
   `hooks/` para `<HOME>/.claude/hooks/`, `agents/` para `<HOME>/.claude/agents/`,
   `skills/session-name/` para `<HOME>/.claude/skills/session-name/` e `scripts/session-title.py`
   para `<HOME>/.claude/scripts/`. Não sobrescreva o que você já tem sem comparar.
2. **CLAUDE.md.** Se você não tem `<HOME>/.claude/CLAUDE.md`, copie o deste pacote. Se tem, junte só
   os blocos que quiser.
3. **settings.json.** Abra `<HOME>/.claude/settings.json` e mescle o conteúdo de
   `settings.example.json` (idioma, esforço, compactação, `env`, permissões, plugins e `hooks`), trocando `<HOME>`. Se já existir uma chave `hooks`, **acrescente** as
   entradas dentro dela em vez de substituir. Reinicie o Claude Code.
4. **Python.** Os hooks e o script são Python 3.9 ou mais novo (só biblioteca padrão). Confira com `python --version`; em Mac
   ou Linux o comando costuma ser `python3` (troque no `command` do settings).
5. **Teste cada hook** antes de confiar: peça ao Claude para editar um arquivo num repositório que
   você sabe estar atrás do remoto (o `git-behind-check` deve negar) e encerre uma sessão com um
   commit sem entrada no log (o `session-close-check` deve devolver o trabalho).

## O que você precisa adaptar

- **`hooks/session-close-check.py`**: no topo do arquivo, `ROOT` é a pasta onde ficam seus
  repositórios (padrão `<HOME>/projects`). Troque ali ou defina a variável de ambiente
  `CLAUDE_PROJECTS_ROOT`. Sem isso o hook só enxerga o repositório da pasta onde a sessão foi aberta.
  Para a conferência automática, crie em cada repo `.claude/verify.json` com
  `{"command": "npm run check"}` (ou o seu comando de teste).
- **`hooks/compact-clickup-resume.py`**: o texto fala em "a ferramenta de tarefas que você usa".
  Se quiser, troque pelo nome da sua e diga qual ferramenta/skill do Claude mexe nela. O nome do
  arquivo ficou com "clickup" só por origem; pode renomear (e ajustar o settings).
- **`hooks/git-behind-check.py`**: precisa de `git` no PATH e de credencial que permita `git fetch`
  sem pedir senha. Sem rede ou sem credencial ele deixa passar e avisa. Desliga com
  `CLAUDE_SKIP_GIT_BEHIND_CHECK=1` no ambiente da sessão.
- **`hooks/delegate-reminder.py`**: limite em `CLAUDE_DELEGATE_THRESHOLD` (padrão 8); desliga com
  `CLAUDE_SKIP_DELEGATE_REMINDER=1`.
- **Os hooks guardam estado** em `<HOME>/.claude/hooks/state/` (criado sozinho). Não versionar.
- **`agents/commit-writer.md`** termina o commit com `Co-Authored-By: Claude ...`; ajuste o texto do
  modelo se quiser.
- **`session-name`**: o ID da sessão vem do caminho do scratchpad que o Claude Code mostra nas
  instruções do sistema. O script mexe num formato interno do Claude Code (não documentado, testado
  em 17/10/2026): se parar de funcionar, o botão Rename do histórico faz o mesmo.

## O resto do setup de origem (configurações, VS Code, plugins, MCPs)

Além das peças acima, o setup de onde este pacote saiu tem:

- **`settings.example.json` completo**: idioma (`language`), esforço padrão (`effortLevel: medium`; ver "Custo"),
  histórico por 180 dias (`cleanupPeriodDays`), compactação aos 200 mil tokens, agentes em Sonnet,
  permissões (comandos só de leitura liberados; `git push --force` bloqueado), plugins e hooks.
  Mescle no seu `~/.claude/settings.json`; não substitua o arquivo inteiro.
- **VS Code** (`vscode/`): `settings.example.jsonc` com as duas chaves do bypass (que só funcionam
  juntas) e exclusões de desempenho; `extensions.txt` com as extensões. Instale com
  `code --install-extension <id>`. A `singularityinc.claude-notifier` avisa no Windows quando o Claude
  termina, pede permissão ou faz uma pergunta; ela cria os próprios hooks no `settings.json`.
- **Plugins** (`/plugin` no Claude Code, catálogo `claude-plugins-official`): `code-review` (revisor
  de diff, usado no "pronto = conferido"), `frontend-design` (direção visual de tela) e
  `typescript-lsp` (o Claude entende tipos do TypeScript). Ligue só os que usar: plugin ligado gasta
  contexto.
- **MCPs genéricos** (`claude mcp add --scope user ...`): `context7` (documentação atual de
  biblioteca), `playwright` (navegador), `github` (PR, issue), `brave-search` (pesquisa web; precisa
  de chave da Brave). Ligue só os que o projeto usa (ver "Custo").

**Ficou de fora de propósito**, por ser da empresa de origem e não servir a outra pessoa: a conexão
com a base de conhecimento interna, o CRM e o ClickUp dela, as contas Cloudflare, o hook que trava
o ClickUp num workspace só e a skill de backlog presa a esse ClickUp. O padrão de cada um está
descrito acima quando vale copiar.

## Custo (tokens)

Resumo do que o setup de origem já faz para gastar menos, com o porquê. **Não há medição de quanto
isso economizou**; são escolhas feitas por raciocínio, não resultado comprovado. Meça no seu uso
antes de tratar como verdade.

1. **Modelo do agente pelo tamanho da tarefa.** Sonnet é o padrão (pesquisa, estudo, código seguindo
   padrão); Haiku para buscar, ler, resumir e conferir saída de comando; Opus só com o motivo dito
   (arquitetura, decisão difícil, bug que o Sonnet não resolveu). Por quê: modelo maior custa mais
   por token e a maior parte do trabalho não precisa dele. Configurar: a regra já está no
   `CLAUDE.md` deste pacote; ao chamar o subagente, passe sempre `model`.
2. **`CLAUDE_CODE_SUBAGENT_MODEL=sonnet` e `model:` nos agentes.** Por quê: subagente sem `model`
   herda o modelo da sessão (por exemplo Opus) e gasta mais sem ninguém decidir. Configurar no
   `settings.json`: `"env": { "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet" }`. Os agentes deste pacote já
   trazem `model: sonnet` no cabeçalho (front matter).
3. **`autoCompactWindow` 200000.** Por quê: compacta a conversa num ponto fixo em vez de deixar o
   contexto crescer sem limite. Configurar no `settings.json`: `"autoCompactWindow": 200000`. O hook
   `compact-clickup-resume.py` devolve o fio do trabalho depois da compactação.
4. **Desligar plugin que não se usa.** Por quê: plugin ligado carrega suas skills e ferramentas no
   contexto de toda sessão. Exemplo: um plugin de memória que quase não é usado. Configurar no `settings.json`: `"enabledPlugins": { "nome@origem": false }`.
5. **Hook `delegate-reminder`.** Por quê: trabalho longo feito na sessão principal enche o contexto
   dela; um agente em segundo plano gasta o dele e devolve só o resultado. O hook avisa uma vez por
   turno, depois de ~8 chamadas seguidas.
6. **Só os MCPs que o projeto usa.** Por quê: cada servidor MCP ligado põe a descrição de todas as
   suas ferramentas no contexto. Configurar: em `<HOME>/.claude.json`, na chave
   `projects` → `"<caminho do projeto>"` → `disabledMcpServers`, uma lista com os nomes a desligar
   naquele projeto (chave conferida no arquivo de origem em 02/11/2026). Cuidado: o caminho tem de
   estar escrito igual ao que o Claude Code registrou para aquele projeto (no Windows, a letra do
   drive em maiúscula ou minúscula pode importar: a confirmar no seu arquivo).
7. **Esforço (`effortLevel`) em `medium` no dia a dia.** Por quê: o esforço é o quanto o modelo
   pensa antes de responder (`low`, `medium`, `high`, `xhigh`, `max`). Mais alto erra menos em
   problema difícil, mas gasta mais tokens e demora mais; junto com o modelo, é o que mais pesa no
   gasto. Suba para `high` ou `xhigh` só na tarefa difícil (bug complicado, arquitetura) pelo seletor
   de esforço e volte depois. Configurar no `settings.json`: `"effortLevel": "medium"`. Atenção: vale
   também por modelo, em `"modelSettings": { "<id do modelo>": { "effortLevel": "..." } }`, e essa
   linha ganha da geral; o seletor do VS Code grava ali. Se o esforço que aparece não bate com o
   arquivo, procure essa chave.

## Perguntas para o seu Claude analisar

Leia tudo e responda ao dono deste setup, em português simples, uma lista curta:

1. Quais destas peças encaixam no meu fluxo de trabalho de hoje e quais não fazem sentido para mim?
   (Por peça: aproveitar, adaptar ou ignorar, com o motivo.)
2. O que eu já tenho instalado em `<HOME>/.claude/` (CLAUDE.md, hooks, agentes, skills, plugins, MCPs)
   que faz o mesmo que alguma peça daqui? Há conflito entre o que existe e o que o pacote traz?
3. Que erros repetidos do Claude no meu trabalho mereciam virar
   hook em vez de instrução? Proponha no máximo três.
4. Qual ferramenta de tarefas eu uso, e como ficaria o hook `compact-clickup-resume.py` e a regra
   "pendência vira tarefa" para ela?
5. Dos itens da seção "Custo (tokens)", quais já estão ligados no meu setup e quais faltam?
   Proponha uma forma simples de medir o gasto antes e depois, já que não há medição.

Responda só com análise; **não instale nem altere nada** sem eu aprovar peça por peça.
