"""PreToolUse hook: não editar arquivo de repositório que está atrás do remoto.

Caso real (no setup de origem deste pacote): o Claude editou um repositório cujo clone estava 249 commits atrás do origin/main. Leu
470 linhas de um arquivo que no remoto tinha 841 e quase sobrescreveu trabalho já publicado. A regra
geral: o que tem que acontecer sempre não pode depender do modelo lembrar — instrução é conselho,
conferência em código é garantia.

Por que PreToolUse e não SessionStart: a sessão abriu num repo e, no meio do caminho,
passou a editar outro. Aviso na largada não pegaria o repo que deu problema.

Como decide:
  - arquivo fora de repositório git, ou ignorado pelo .gitignore  -> passa
  - branch sem upstream (local, ainda não publicada)              -> passa
  - fetch falhou (sem rede, sem credencial, timeout)              -> passa, com aviso ao usuário
  - atrás do upstream                                             -> NEGA, com o comando para sair disso

Custo: duas chamadas git por edição no caso comum. O `git fetch` só roda uma vez a cada
FETCH_TTL_S por repositório; o quanto está atrás é recalculado sempre, com as refs já em disco,
para que um `git pull` destrave na hora em vez de esperar o cache vencer.

Válvula de escape: a variável de ambiente CLAUDE_SKIP_GIT_BEHIND_CHECK=1 desliga o freio. Ela só
pega em sessão aberta com ela no ambiente — de propósito: quem decide contornar é a pessoa, não a
sessão que está sendo barrada.
"""
import hashlib
import json
import os
import subprocess
import sys
import time

FETCH_TTL_S = 900  # 15 min entre fetches do mesmo repositório
GIT_TIMEOUT_S = 12
STATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state", "git-behind")

FILE_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}

# Sem isto o git trava esperando senha num processo que ninguém vê.
GIT_ENV = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="Never", GIT_ASKPASS="echo")


def git(cwd, *args, timeout=GIT_TIMEOUT_S):
    """Devolve (ok, saída). Nunca levanta: erro de git aqui significa 'deixa passar'."""
    try:
        p = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True,
                           timeout=timeout, env=GIT_ENV,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return p.returncode == 0, (p.stdout or "").strip()
    except Exception:
        return False, ""


def deny(reason):
    # ensure_ascii deixa os acentos como \uXXXX: o stdout do Python no Windows não é UTF-8.
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason}}))


def warn(message):
    print(json.dumps({"systemMessage": message, "suppressOutput": True}))


def state_path(repo):
    slug = hashlib.sha1(os.path.normcase(repo).encode("utf-8", "replace")).hexdigest()[:16]
    return os.path.join(STATE_DIR, slug + ".json")


def read_state(repo):
    try:
        with open(state_path(repo), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def write_state(repo, data):
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(state_path(repo), "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def nearest_existing_dir(path):
    """O arquivo do Write pode ainda não existir; a pasta dele, às vezes, também não."""
    d = os.path.dirname(os.path.abspath(path))
    for _ in range(40):
        if os.path.isdir(d):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent
    return None


def main():
    if os.environ.get("CLAUDE_SKIP_GIT_BEHIND_CHECK") == "1":
        return

    data = json.load(sys.stdin)
    if data.get("tool_name") not in FILE_TOOLS:
        return

    args = data.get("tool_input") or {}
    target = args.get("file_path") or args.get("notebook_path")
    if not target:
        return

    start_dir = nearest_existing_dir(target)
    if not start_dir:
        return

    ok, repo = git(start_dir, "rev-parse", "--show-toplevel", timeout=8)
    if not ok or not repo:
        return  # fora de repositório git

    # Contar vem antes de buscar: é barato, não toca a rede, e já descarta a branch sem upstream.
    # --left-right conta os dois lados numa chamada só: "<atrás>\t<à frente>".
    def contagem():
        ok, counts = git(repo, "rev-list", "--count", "--left-right", "@{u}...HEAD", timeout=10)
        if not ok:
            return None  # branch sem upstream (ainda não publicada)
        try:
            behind, ahead = (int(n) for n in counts.split())
        except ValueError:
            return None
        return behind, ahead

    placar = contagem()
    if placar is None:
        return

    st = read_state(repo)
    now = time.time()
    if st.get("fetched_at", 0) < now - FETCH_TTL_S:
        fetch_ok, _ = git(repo, "fetch", "--quiet")
        # Grava o carimbo mesmo quando falha: offline, não adianta tentar a cada edição.
        write_state(repo, {"fetched_at": now, "fetch_ok": fetch_ok})
        if not fetch_ok:
            warn(f"git fetch falhou em {os.path.basename(repo)} — não dá para saber se o repo está "
                 "atrás do remoto. Seguindo sem a conferência.")
            return
        placar = contagem()  # refaz com as refs recém-buscadas
        if placar is None:
            return

    behind, ahead = placar
    if behind == 0:
        return

    # Arquivo que o git ignora não corre risco de sobrescrever trabalho de ninguém.
    ignored, _ = git(repo, "check-ignore", "-q", os.path.abspath(target), timeout=8)
    if ignored:
        return

    name = os.path.basename(repo)
    _, branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD", timeout=8)
    plural = "commit" if behind == 1 else "commits"
    if ahead:
        deny(f"O repositório {name} divergiu do remoto: {behind} {plural} atrás e {ahead} à frente "
             f"na branch {branch or 'atual'}. Editar agora cria conflito ou apaga trabalho que já "
             "está publicado. Confira o que são os dois lados (git log --oneline HEAD..@{u} e "
             "@{u}..HEAD) e combine com o usuário como juntar antes de mexer no código.")
    else:
        deny(f"O repositório {name} está {behind} {plural} atrás do remoto na branch "
             f"{branch or 'atual'}. O arquivo que você vai editar pode já ter mudado lá. Rode "
             f"`git -C \"{repo}\" pull` e releia o arquivo antes de editar — editar um clone "
             "desatualizado pode sobrescrever trabalho já publicado.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)  # freio quebrado não pode travar o trabalho
