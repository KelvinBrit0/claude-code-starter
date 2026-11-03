"""Dá ou atualiza o título de uma sessão do Claude Code.

O título fica no próprio arquivo da sessão (~/.claude/projects/<projeto>/<id>.jsonl), numa linha
{"type":"custom-title",...}. Vale a última linha desse tipo; a extensão do VS Code relê o arquivo
(testado em 17/10/2026). É formato interno do Claude Code, não documentado: pode mudar numa
atualização. O jeito oficial continua sendo o Rename do histórico de sessões.

Padrão sugerido:  AAAA-MM · <assunto> — <última coisa feita>
O começo (até o " — ") é fixo; o fim muda ao longo da sessão.

Uso:
  python session-title.py --session <id> --show
  python session-title.py --session <id> --title "2026-10 · site-vendas — sai o Stape"
  python session-title.py --session <id> --outcome "Pixel com cidade"   # troca só o fim
Sem --session, usa a variável CLAUDE_SESSION_ID, se existir.
"""
import argparse, glob, json, os, sys

SEP = " — "
MAX_LEN = 70


def find_file(session_id: str) -> str:
    base = os.path.join(os.path.expanduser("~"), ".claude", "projects")
    hits = glob.glob(os.path.join(base, "*", f"{session_id}.jsonl"))
    if not hits:
        sys.exit(f"nenhum arquivo para a sessão {session_id}")
    # Sessão que mudou de projeto (ex.: mudou de pasta de trabalho) deixa uma
    # cópia antiga na pasta de origem; a viva é a gravada por último.
    return max(hits, key=os.path.getmtime)


def current_title(path: str) -> tuple[str, str]:
    custom = auto = ""
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            if '"custom-title"' in line or '"ai-title"' in line:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if d.get("type") == "custom-title":
                    custom = d.get("customTitle", "")
                elif d.get("type") == "ai-title":
                    auto = d.get("aiTitle", "")
    return custom, auto


def append_title(path: str, session_id: str, title: str) -> None:
    with open(path, "rb") as f:
        f.seek(-1, os.SEEK_END)
        ends_nl = f.read(1) == b"\n"
    line = json.dumps({"type": "custom-title", "customTitle": title, "sessionId": session_id},
                      ensure_ascii=False, separators=(",", ":"))
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(("" if ends_nl else "\n") + line + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default=os.environ.get("CLAUDE_SESSION_ID"))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--show", action="store_true")
    g.add_argument("--title")
    g.add_argument("--outcome")
    a = ap.parse_args()
    if not a.session:
        sys.exit("falta --session (o ID da sessão)")

    path = find_file(a.session)
    custom, auto = current_title(path)

    if a.show:
        print(f"título: {custom or auto or '(nenhum)'}" + ("" if custom else "  [automático]"))
        print(f"arquivo: {path}")
        return

    if a.title:
        title = a.title.strip()
    else:
        if SEP not in custom:
            sys.exit(f"a sessão ainda não tem título no padrão (atual: {custom or auto!r}); use --title")
        title = custom.split(SEP, 1)[0] + SEP + a.outcome.strip()

    if len(title) > MAX_LEN:
        sys.exit(f"título com {len(title)} caracteres (máximo {MAX_LEN}): encurte o fim")
    if title == custom:
        print(f"sem mudança: {title}")
        return
    append_title(path, a.session, title)
    print(f"título: {title}")


if __name__ == "__main__":
    main()
