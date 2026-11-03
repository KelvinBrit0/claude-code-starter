---
name: session-name
description: Dá ou atualiza o nome da sessão atual do Claude Code no padrão "ano-mês · assunto — última coisa feita" ("AAAA-MM · assunto — última coisa feita"), para achar a sessão depois no histórico. Usar quando o usuário pedir nome para a sessão, "nomeia a sessão", "atualiza o nome", ou digitar /session-name.
---

# Nome da sessão

Quem abre muitas sessões se perde no histórico. Esta skill dá o nome e o aplica.

## O padrão

```
AAAA-MM · <assunto> — <última coisa feita>
```

- **`AAAA-MM`**: ano e mês em que a sessão **começou** (a data da primeira mensagem, se aparecer no
  contexto; senão, a de hoje). ISO 8601, que ordena certo no histórico: `2026-10`.
- **`<assunto>`**: a coisa principal da sessão, pelo nome que o usuário reconhece. Repositório,
  cliente ou produto vão como são (`site-vendas`, `lancamento-black`, `tracking`). **Fica fixo** depois de
  dado.
- **`<última coisa feita>`**: a entrega mais recente, em poucas palavras, em português. **Muda** ao
  longo da sessão.
- **No máximo 70 caracteres no total** (o script recusa acima disso). O histórico corta nome longo.
- Nada genérico ("ajustes", "várias coisas", "continuação").

Exemplos:
- `2026-10 · site-vendas — Stape fora, Pixel com cidade`
- `2026-10 · lancamento — monitor de SLA no WhatsApp`
- `2026-09 · tracking — GTM server revisado`

## Como aplicar

O ID da sessão é a **última pasta do caminho do scratchpad** que aparece nas instruções do sistema
(`…\<projeto>\<ID-da-sessão>\scratchpad`). Com ele:

```bash
python -I -X utf8 ~/.claude/scripts/session-title.py --session <ID> --show            # o título atual
python -I -X utf8 ~/.claude/scripts/session-title.py --session <ID> --title "<AAAA-MM · assunto — fim>"
python -I -X utf8 ~/.claude/scripts/session-title.py --session <ID> --outcome "<novo fim>"
```

- Sessão **sem** título no padrão → `--title` com o nome completo.
- Sessão **com** título no padrão → `--outcome`, que troca só o fim e mantém o assunto.

**Limite (visto em 17/10/2026):** se o usuário **já deu nome à mão** (botão Rename) e a aba está
aberta, a extensão guarda esse nome na memória e o regrava no arquivo por cima do nosso. Sinal: no
`--show`, o título é um nome fora do padrão que ele digitou. Nesse caso, não grave: passe o nome
para ele colar no **Rename**, ou peça para fechar a aba e então grave. Sessão só com título
automático aceita o nome pelo script normalmente.

O script acrescenta uma linha `custom-title` no arquivo da sessão
(`~/.claude/projects/<projeto>/<ID>.jsonl`), e a extensão do VS Code mostra o nome novo no
histórico. É formato interno do Claude Code (testado em 17/10/2026), não documentado: se um dia
parar de funcionar, o caminho oficial é o botão **Rename** no histórico de sessões, ou `/rename`
no terminal.

## O que responder

Uma linha só, com o nome aplicado. Sem explicar o padrão de novo.
