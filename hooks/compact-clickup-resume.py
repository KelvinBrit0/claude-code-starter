# SessionStart (matcher "compact"): depois que o contexto é compactado, o detalhe do trabalho em
# andamento se perde, e a retomada só sai certa quando a tarefa registrada na sua ferramenta de
# tarefas é lida de novo. Instrução esquece; este hook injeta o passo toda vez.
#
# ADAPTAR: o texto abaixo fala em "a ferramenta de tarefas que você usa" (ClickUp, Notion, Linear,
# Trello, arquivo de TODO...). Se quiser, troque pelo nome da sua e pela habilidade/skill que
# explica como mexer nela.
import json

aviso = (
    "O contexto acabou de ser compactado. Antes de continuar o trabalho:\n"
    "1. Procure, na ferramenta de tarefas que você usa, a tarefa do assunto em andamento "
    "e leia a descrição e os comentários. Se não existir, crie com contexto completo "
    "(o porquê, de onde veio e um 'Pronto quando').\n"
    "2. Retome pelo que a tarefa diz, não pelo resumo; se o resumo e a tarefa discordarem, a tarefa ganha "
    "e o que mudou vira comentário nela.\n"
    "3. Ideia ou pendência nova do usuário daqui em diante vira tarefa com descrição detalhada "
    "(contexto, palavras dele, dependências, Pronto quando)."
)

print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": aviso}},
                 ensure_ascii=False))
