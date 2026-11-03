"""Stop hook: o Claude só encerra quando o que ele fez está registrado e conferido.

Roda ao fim de cada resposta. Olha só os repositórios em que ESTA sessão fez commit ou mexeu em
arquivo (o sha do commit aparece na conversa; outras sessões abertas não contam) e devolve o
trabalho ao Claude quando:

1. o repo tem SESSION_LOG e há commit desta sessão depois do último commit que tocou o log;
2. o repo declara uma conferência em .claude/verify.json ({"command": "npm run check"}) e ela
   falha. A conferência só roda quando o estado do repo mudou desde a última aprovação.

Devolve uma vez por rodada (stop_hook_active): se o Claude não puder resolver, ele explica ao
usuário em vez de entrar em laço. Falha do próprio hook nunca bloqueia (sai 0).
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# Pasta onde ficam os seus repositórios. Troque aqui ou defina CLAUDE_PROJECTS_ROOT no ambiente.
# É por ela que o hook acha, na conversa, os repositórios em que a sessão mexeu (além da pasta
# em que a sessão foi aberta, que sempre entra).
ROOT = Path(os.environ.get("CLAUDE_PROJECTS_ROOT") or (Path.home() / "projects"))
LOGS = ["docs/sessions/SESSION_LOG.md", "docs/SESSION_LOG.md"]
STATE = Path.home() / ".claude" / "hooks" / "state"
_SEP = r"(?:\\\\|\\|/)+"  # barra normal, invertida, ou invertida escapada (como aparece na transcrição)
_root_segs = [x for x in re.split(r"[\\/]+", str(ROOT)) if x]
# caminho da raiz + até 3 níveis de pasta abaixo dela
PATH_RE = re.compile(
    r"(?i)" + _SEP.join(re.escape(x) for x in _root_segs) + r"((?:" + _SEP + r"[a-z0-9._-]+){1,3})"
)
# sem \b: na transcrição o sha vem colado em "\n" escrito como texto ("\n20a29d5")
SHA_RE = re.compile(r"(?<![0-9a-f])[0-9a-f]{7,40}(?![0-9a-f])")


def git(repo, *args, timeout=30):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    return r.stdout.strip() if r.returncode == 0 else ""


def read_transcript(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def session_start(text):
    m = re.search(r'"timestamp"\s*:\s*"([^"]+)"', text)
    return m.group(1) if m else None


def candidate_repos(text, cwd):
    found = set()
    parts_list = [m.group(1) for m in PATH_RE.finditer(text)]
    for parts in parts_list:
        segs = [s for s in re.split(r"[\\/]+", parts) if s]
        for n in range(1, len(segs) + 1):
            d = ROOT.joinpath(*segs[:n])
            if (d / ".git").exists():
                found.add(d.resolve())
                break
    if cwd:
        top = git(cwd, "rev-parse", "--show-toplevel")
        if top:
            found.add(Path(top).resolve())
    return found


def session_commits(repo, since, shas_in_text):
    out = git(repo, "log", f"--since={since}", "--format=%H")
    return [h for h in out.splitlines() if h and h[:7] in shas_in_text]


def unlogged(repo, commits):
    log = next((l for l in LOGS if (repo / l).exists()), None)
    if not log or not commits:
        return None, []
    last = git(repo, "log", "-1", "--format=%H", "--", log)
    after = set(git(repo, "rev-list", f"{last}..HEAD").splitlines()) if last else None
    pending = [c for c in commits if after is None or c in after]
    return log, pending


def dirty_since(repo, start_epoch):
    out = git(repo, "status", "--porcelain")
    for line in out.splitlines():
        p = repo / line[3:].strip().strip('"')
        try:
            if p.exists() and p.stat().st_mtime >= start_epoch:
                return True
        except OSError:
            pass
    return False


def run_verify(repo):
    cfg = repo / ".claude" / "verify.json"
    if not cfg.exists():
        return None
    try:
        conf = json.loads(cfg.read_text(encoding="utf-8"))
    except ValueError:
        return f"{cfg} não é JSON válido"
    key_src = git(repo, "rev-parse", "HEAD") + git(repo, "diff", "HEAD")
    key = hashlib.sha256(key_src.encode()).hexdigest()[:16]
    mark = STATE / f"verify-{hashlib.sha256(str(repo).encode()).hexdigest()[:12]}.txt"
    if mark.exists() and mark.read_text() == key:
        return None
    cwd = repo / conf.get("cwd", ".")
    try:
        r = subprocess.run(conf["command"], shell=True, cwd=cwd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=conf.get("timeout", 300))
    except subprocess.TimeoutExpired:
        return f"`{conf['command']}` passou do tempo limite"
    if r.returncode == 0:
        STATE.mkdir(parents=True, exist_ok=True)
        mark.write_text(key)
        return None
    tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-15:])
    return f"`{conf['command']}` falhou (código {r.returncode}):\n{tail}"


def main():
    data = json.load(sys.stdin)
    if data.get("stop_hook_active"):
        return
    text = read_transcript(data.get("transcript_path", ""))
    start = session_start(text)
    if not start:
        return
    start_epoch = time.mktime(time.strptime(start[:19], "%Y-%m-%dT%H:%M:%S")) - time.timezone
    shas = {s[:7] for s in SHA_RE.findall(text)}
    problems = []
    for repo in sorted(candidate_repos(text, data.get("cwd"))):
        commits = session_commits(repo, start, shas)
        log, pending = unlogged(repo, commits)
        if pending:
            short = ", ".join(c[:7] for c in pending[:8])
            problems.append(
                f"- {repo}: {len(pending)} commit(s) desta sessão sem entrada em {log} ({short}). "
                "Registre (agente session-logger ou à mão, no formato do próprio log) e commite o log; "
                "se a sessão continua, acrescente à entrada de hoje.")
        if commits or dirty_since(repo, start_epoch):
            fail = run_verify(repo)
            if fail:
                problems.append(f"- {repo}: a conferência do repo falhou. {fail}\n"
                                "Corrija a causa; se a falha não veio desta sessão, diga isso ao usuário.")
    if problems:
        print(json.dumps({"decision": "block",
                          "reason": "Antes de encerrar:\n" + "\n".join(problems)}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
