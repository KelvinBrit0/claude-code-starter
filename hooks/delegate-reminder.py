"""Hook de lembrete: trabalho longo da sessão principal vai para Agent em segundo plano.

Regra de trabalho: tarefa que leva mais que alguns comandos vai para `Agent` com
`run_in_background` e `model` explícito; a sessão principal fica livre para conversar. O assistente
esquecia e fazia sozinho correções de ~15 chamadas. Regra esquecida mais de uma vez vira código.

É LEMBRETE, não bloqueio. Um script serve a dois eventos:
  - UserPromptSubmit : zera o contador (mensagem nova do usuário = turno novo).
  - PreToolUse       : `Agent`/`Task` zera; ferramenta de trabalho soma 1. Ao passar do limite,
                       injeta UMA vez por turno um aviso em additionalContext.

Por que PreToolUse e não PostToolUse: o `Agent` zera o contador na hora em que é chamado (o
PostToolUse de um agente em primeiro plano só dispararia quando ele terminasse) e o aviso chega junto
da chamada que passou do limite. Chamada que falha também conta, o que é o certo: é trabalho feito.

Subagente: a entrada do hook traz `agent_id` quando dispara dentro de subagente (docs oficiais,
"Common input fields"). `agent_type` NÃO serve de teste: também vem na sessão principal aberta com
`--agent`. Então só `agent_id` decide, e subagente sai sem contar nem avisar.

Estado por sessão em hooks/state/delegate-<session_id>.json. Variáveis de ambiente:
  CLAUDE_DELEGATE_THRESHOLD  limite de chamadas seguidas (padrão 8; o aviso sai na seguinte)
  CLAUDE_SKIP_DELEGATE_REMINDER=1  desliga o lembrete

Qualquer erro: sai 0 em silêncio, nunca trava a sessão.
"""
import json
import os
import re
import sys
import time

DEFAULT_THRESHOLD = 8
STATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state")
STATE_TTL_S = 7 * 24 * 3600  # limpa estado de sessão com mais de 7 dias

WORK_TOOLS = {"Bash", "Edit", "Write", "MultiEdit", "Read", "Grep", "Glob", "NotebookEdit"}
RESET_TOOLS = {"Agent", "Task"}  # "Task" é o nome antigo da ferramenta Agent


def is_work_tool(name):
    return name in WORK_TOOLS or name.startswith("mcp__playwright__")


def threshold():
    try:
        return max(1, int(os.environ.get("CLAUDE_DELEGATE_THRESHOLD", DEFAULT_THRESHOLD)))
    except ValueError:
        return DEFAULT_THRESHOLD


def state_file(session_id):
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)[:64]
    return os.path.join(STATE_DIR, f"delegate-{safe}.json")


def read_state(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            st = json.load(f)
        return int(st.get("count", 0)), bool(st.get("warned", False))
    except Exception:
        return 0, False


def write_state(path, count, warned):
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"count": count, "warned": warned}, f)
    except Exception:
        pass


def cleanup_old():
    try:
        now = time.time()
        for name in os.listdir(STATE_DIR):
            if name.startswith("delegate-"):
                p = os.path.join(STATE_DIR, name)
                if now - os.path.getmtime(p) > STATE_TTL_S:
                    os.remove(p)
    except Exception:
        pass


def remind(n):
    # ensure_ascii deixa os acentos como \uXXXX: o stdout do Python no Windows não é UTF-8.
    msg = (f"Já são {n} chamadas seguidas nesta sessão. Pela regra de trabalho, trabalho longo vai "
           "para Agent em segundo plano (run_in_background), com model explícito (Sonnet por "
           "padrão). Se o que falta passa de alguns comandos, delegue agora.")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "additionalContext": msg}}))


def main():
    if os.environ.get("CLAUDE_SKIP_DELEGATE_REMINDER") == "1":
        return
    data = json.load(sys.stdin)
    if data.get("agent_id"):
        return  # dentro de subagente: não conta, não avisa
    session_id = str(data.get("session_id") or "")
    if not session_id:
        return
    path = state_file(session_id)
    event = data.get("hook_event_name")

    if event == "UserPromptSubmit":
        write_state(path, 0, False)
        cleanup_old()
        return
    if event != "PreToolUse":
        return

    tool = str(data.get("tool_name") or "")
    if tool in RESET_TOOLS:
        write_state(path, 0, False)
        return
    if not is_work_tool(tool):
        return

    count, warned = read_state(path)
    count += 1
    if count > threshold() and not warned:
        warned = True
        write_state(path, count, warned)
        remind(count)
    else:
        write_state(path, count, warned)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)  # lembrete quebrado não pode travar o trabalho
