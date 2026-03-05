#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, json, re, shutil, textwrap
from dataclasses import dataclass
from pathlib import Path

DEFAULT_GLOBAL_RULES = "~/.codex/GLOBAL_ENGINEERING_RULES.md"
DEFAULT_OWNER = "self"
DEFAULT_STATUS = "in_progress"
VALID_STATUSES = {"todo", "in_progress", "blocked", "done"}
DOCS_MEMORY = "docs/memory.md"
TASK_INDEX = "docs/tasks/index.md"
TASK_DIR = "docs/tasks"
TASK_ARCHIVE = "docs/tasks/archive"
REPORT_DIR = "docs/reports"
LEGACY_MEMORY = "DEVELOPMENT_MEMORY.md"

@dataclass
class Task:
    task_id: str
    title: str
    status: str
    updated: str
    owner: str
    task_file: str

def now() -> dt.datetime: return dt.datetime.now().astimezone()
def today() -> str: return now().date().isoformat()
def stamp() -> str: return now().strftime("%Y-%m-%d %H:%M %z")
def p(path: str) -> Path: return Path(path).expanduser().resolve()
def ensure_parent(path: Path) -> None: path.parent.mkdir(parents=True, exist_ok=True)

def paths(root: Path) -> dict[str, Path]:
    return {
        "memory": root / DOCS_MEMORY,
        "index": root / TASK_INDEX,
        "task_dir": root / TASK_DIR,
        "archive": root / TASK_ARCHIVE,
        "report": root / REPORT_DIR,
        "legacy": root / LEGACY_MEMORY,
    }

def norm_status(value: str | None) -> str:
    s = (value or DEFAULT_STATUS).strip().lower()
    if s not in VALID_STATUSES: raise ValueError(f"Invalid status '{value}'. Allowed: {', '.join(sorted(VALID_STATUSES))}")
    return s

def slugify(text: str) -> str: return re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
def items(vals: list[str] | None) -> list[str]:
    out: list[str] = []
    for raw in vals or []:
        out.extend([x.strip() for x in raw.split(";") if x.strip()])
    return out

def bullets(vals: list[str]) -> str: return "- (none)" if not vals else "\n".join(f"- {x}" for x in vals)
def preview(text: str, n: int) -> str:
    lines = text.splitlines();
    return text.rstrip() if len(lines) <= n else "\n".join(lines[:n]).rstrip() + "\n...[truncated]"
def trunc(text: str, n: int) -> str: return text if len(text) <= n else text[: n - 40].rstrip() + "\n\n...[truncated]"

def set_bullet(text: str, label: str, value: str) -> str:
    pat = re.compile(rf"(^- {re.escape(label)}:\s*).*$", re.MULTILINE)
    return pat.sub(lambda m: f"{m.group(1)}{value}", text, count=1) if pat.search(text) else text

def ensure_section(text: str, heading: str) -> str:
    if heading in text: return text
    if not text.endswith("\n"): text += "\n"
    return text + f"\n{heading}\n"

def tpl_global() -> str:
    return """# Global Engineering Rules

## Coding Preferences
- Prefer clear naming and small functions with single responsibility.
- Avoid hidden side effects and surprising control flow.
- Add tests for behavior changes and bug fixes.

## Architecture Preferences
- Favor composition over inheritance.
- Keep domain logic separate from framework glue code.
- Minimize coupling across modules.

## Workflow Rules
- Start by summarizing context before implementation.
- Record decisions that affect future implementation.
- End each session with a short handoff.

## Communication Preferences
- Keep responses direct and technical.
- Surface tradeoffs and risks explicitly.
- Ask for confirmation only when assumptions are high risk.

## Hard Constraints
- Do not run destructive commands without explicit approval.
- Preserve unrelated local changes in the working tree.
"""

def tpl_memory(project: str, date: str) -> str:
    return f"""# Project Memory

## Project Snapshot
- Project: {project}
- Current Goal:
- Current Phase:
- Last Updated: {date}

## Active Context
- Current Task: (none)
- Why This Matters:
- Constraints:

## Last Session Handoff
- Completed:
- In Progress:
- Next First Action:
- Blockers:
- Files Touched:

## Decision Log
| Date | Decision | Reason | Impact |
| --- | --- | --- | --- |

## Session Log
"""

def tpl_index() -> str:
    return """# Task Index

| id | title | status | updated | owner | task_file |
| --- | --- | --- | --- | --- | --- |
"""

def tpl_task(tid: str, title: str, status: str, created: str, updated: str) -> str:
    return f"""# {title}

## Metadata
- id: {tid}
- status: {status}
- created: {created}
- updated: {updated}

## Context

## Progress Log

## Next Action
- (pending)

## Blockers
- (none)

## Related Files
- (none)
"""

def ensure_global(path: Path) -> bool:
    if path.exists(): return False
    ensure_parent(path); path.write_text(tpl_global(), encoding="utf-8"); return True

def ensure_project(root: Path, date: str) -> dict[str, Path]:
    ps = paths(root); ps["task_dir"].mkdir(parents=True, exist_ok=True); ps["report"].mkdir(parents=True, exist_ok=True)
    if not ps["memory"].exists():
        ensure_parent(ps["memory"])
        if ps["legacy"].exists():
            legacy = ps["legacy"].read_text(encoding="utf-8")
            ps["memory"].write_text(tpl_memory(root.name, date) + "\n## Migrated Legacy Notes\n\n" + legacy.strip() + "\n", encoding="utf-8")
        else:
            ps["memory"].write_text(tpl_memory(root.name, date), encoding="utf-8")
    if not ps["index"].exists():
        ensure_parent(ps["index"]); ps["index"].write_text(tpl_index(), encoding="utf-8")
    txt = set_bullet(ps["memory"].read_text(encoding="utf-8"), "Last Updated", date)
    ps["memory"].write_text(txt, encoding="utf-8")
    return ps

def parse_index(path: Path) -> list[Task]:
    if not path.exists(): return []
    out: list[Task] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s.startswith("|"): continue
        cols = [x.strip() for x in s.strip("|").split("|")]
        if len(cols) != 6 or cols[0].lower() == "id": continue
        if all(re.fullmatch(r"[-:]+", c or "") for c in cols): continue
        out.append(Task(cols[0], cols[1], cols[2], cols[3], cols[4], cols[5]))
    return out

def sort_tasks(tasks: list[Task]) -> list[Task]: return sorted(tasks, key=lambda x: x.updated, reverse=True)
def write_index(path: Path, tasks: list[Task]) -> None:
    rows = ["# Task Index", "", "| id | title | status | updated | owner | task_file |", "| --- | --- | --- | --- | --- | --- |"]
    for t in sort_tasks(tasks):
        row = f"| {t.task_id.replace('|','/')} | {t.title.replace('|','/')} | {t.status} | {t.updated} | {t.owner} | {t.task_file.replace('|','/')} |"
        rows.append(row)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")

def find(tasks: list[Task], tid: str) -> Task | None:
    for t in tasks:
        if t.task_id == tid: return t
    return None

def next_id(tasks: list[Task], date: str) -> str:
    pre = f"{date}-"; seq = 1
    for t in tasks:
        if t.task_id.startswith(pre):
            suf = t.task_id[len(pre):]
            if suf.isdigit(): seq = max(seq, int(suf) + 1)
    return f"{pre}{seq:02d}"

def choose_id(tasks: list[Task], title: str | None, date: str) -> str:
    if title:
        base = slugify(title)
        if base:
            ids = {t.task_id for t in tasks}; cand = base; n = 2
            while cand in ids: cand, n = f"{base}-{n}", n + 1
            return cand
    return next_id(tasks, date)

def get_created(task_path: Path) -> str | None:
    if not task_path.exists(): return None
    m = re.search(r"^- created:\s*(.+)$", task_path.read_text(encoding="utf-8"), re.MULTILINE)
    return m.group(1).strip() if m else None

def upsert(tasks: list[Task], tid: str, title: str, status: str, updated: str, owner: str, task_file: str) -> Task:
    t = find(tasks, tid)
    if t: t.title, t.status, t.updated, t.owner, t.task_file = title, status, updated, owner, task_file; return t
    t = Task(tid, title, status, updated, owner, task_file); tasks.append(t); return t

def update_meta(text: str, tid: str, status: str, created: str, updated: str, title: str) -> str:
    lines = text.splitlines();
    if lines and lines[0].startswith("# "): lines[0] = f"# {title}"
    text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    for k, v in {"id": tid, "status": status, "created": created, "updated": updated}.items():
        pat = re.compile(rf"(^- {re.escape(k)}:\s*).*$", re.MULTILINE)
        if pat.search(text): text = pat.sub(lambda m: f"{m.group(1)}{v}", text, count=1)
    return text

def append_progress(text: str, c: list[str], ip: list[str], nxt: list[str], bl: list[str], files: list[str]) -> str:
    text = ensure_section(text, "## Progress Log")
    e = f"\n### {stamp()}\n- Completed:\n{bullets(c)}\n- In Progress:\n{bullets(ip)}\n- Next First Action:\n{bullets(nxt)}\n- Blockers:\n{bullets(bl)}\n- Files Touched:\n{bullets(files)}\n"
    if not text.endswith("\n"): text += "\n"
    return text + e

def ensure_task_file(task_path: Path, tid: str, title: str, status: str, updated: str, c: list[str], ip: list[str], nxt: list[str], bl: list[str], files: list[str]) -> None:
    if task_path.exists():
        txt = task_path.read_text(encoding="utf-8")
        created = get_created(task_path) or updated
        txt = update_meta(txt, tid, status, created, updated, title)
    else:
        ensure_parent(task_path); txt = tpl_task(tid, title, status, updated, updated)
    task_path.write_text(append_progress(txt, c, ip, nxt, bl, files), encoding="utf-8")

def sync_memory(mem: Path, project: str, current_task: str, c: list[str], ip: list[str], nxt: list[str], bl: list[str], files: list[str], note: str) -> None:
    date = today()
    txt = mem.read_text(encoding="utf-8") if mem.exists() else tpl_memory(project, date)
    txt = set_bullet(txt, "Last Updated", date)
    txt = set_bullet(txt, "Current Task", current_task)
    txt = set_bullet(txt, "Completed", ", ".join(c) if c else "")
    txt = set_bullet(txt, "In Progress", ", ".join(ip) if ip else "")
    txt = set_bullet(txt, "Next First Action", ", ".join(nxt) if nxt else "")
    txt = set_bullet(txt, "Blockers", ", ".join(bl) if bl else "")
    txt = set_bullet(txt, "Files Touched", ", ".join(files) if files else "")
    txt = ensure_section(txt, "## Session Log")
    e = f"\n### {stamp()}\n- Note: {note}\n- Current Task: {current_task}\n- Completed:\n{bullets(c)}\n- In Progress:\n{bullets(ip)}\n- Next First Action:\n{bullets(nxt)}\n- Blockers:\n{bullets(bl)}\n- Files Touched:\n{bullets(files)}\n"
    if not txt.endswith("\n"): txt += "\n"
    mem.write_text(txt + e, encoding="utf-8")

def latest(tasks: list[Task]) -> Task | None: return sort_tasks(tasks)[0] if tasks else None

def context_payload(root: Path, rules: Path, ensure: bool) -> dict[str, str]:
    if ensure:
        try: ensure_global(rules)
        except PermissionError: pass
    ps = ensure_project(root, today())
    rules_txt = rules.read_text(encoding="utf-8") if rules.exists() else "(missing global rules file)"
    mem_txt = ps["memory"].read_text(encoding="utf-8") if ps["memory"].exists() else "(missing docs/memory.md)"
    tasks = parse_index(ps["index"]); lt = latest(tasks)
    latest_summary, task_txt = "(no task selected)", "(no task file yet)"
    if lt:
        latest_summary = f"{lt.task_id} | {lt.status} | {lt.updated}"
        tp = root / lt.task_file
        if tp.exists(): task_txt = tp.read_text(encoding="utf-8")
    terminal = textwrap.dedent(f"""
    === GLOBAL RULES: {rules} ===
    {preview(rules_txt,40)}

    === PROJECT MEMORY: {ps['memory']} ===
    {preview(mem_txt,30)}

    === LATEST TASK ===
    {latest_summary}
    {preview(task_txt,20)}
    """).strip()
    prompt = textwrap.dedent(f"""
    [GLOBAL RULES]
    {trunc(rules_txt.strip(),6000)}

    [PROJECT MEMORY]
    {trunc(mem_txt.strip(),5000)}

    [ACTIVE TASK]
    {trunc(task_txt.strip(),4000)}
    """).strip()
    return {"terminal_summary": terminal, "prompt_payload": prompt}

def save_op(root: Path, rules: Path, mode: str, tid: str | None, title: str | None, status: str, owner: str, c: list[str], ip: list[str], nxt: list[str], bl: list[str], files: list[str]) -> dict[str, str]:
    try: ensure_global(rules)
    except PermissionError: pass
    ps = ensure_project(root, today())
    tasks = parse_index(ps["index"])
    sid = tid or (choose_id(tasks, title, today()) if title else (latest(tasks).task_id if latest(tasks) else choose_id(tasks, None, today())))
    old = find(tasks, sid)
    final_title = (title or (old.title if old else sid)).strip() or sid
    final_status = norm_status(status)
    rel = f"docs/tasks/{sid}.md"
    rec = upsert(tasks, sid, final_title, final_status, stamp(), owner or DEFAULT_OWNER, rel)
    write_index(ps["index"], tasks)
    tpath = root / rec.task_file
    if mode == "task": ensure_task_file(tpath, rec.task_id, rec.title, rec.status, rec.updated, c, ip, nxt, bl, files)
    sync_memory(ps["memory"], root.name, rec.task_id, c, ip, nxt, bl, files, f"quick-save ({mode})")
    return {"mode": mode, "task_id": rec.task_id, "title": rec.title, "status": rec.status, "task_file": str(tpath), "index_file": str(ps['index']), "memory_file": str(ps['memory'])}

def latest_session(mem_txt: str) -> list[str]:
    cur, all_entries = [], []
    for line in mem_txt.splitlines():
        if line.startswith("### "):
            if cur: all_entries.append(cur)
            cur = [line]; continue
        if cur: cur.append(line)
    if cur: all_entries.append(cur)
    return all_entries[-1] if all_entries else []

def cmd_init(a):
    root, rules = p(a.project_path), p(a.global_rules)
    try: created = ensure_global(rules)
    except PermissionError: created = False
    ps = ensure_project(root, today())
    print("Initialization complete.")
    print(f"Project root: {root}")
    print(f"Global rules: {rules} ({'created' if created else 'existing'})")
    print(f"Project memory: {ps['memory']}")
    print(f"Task index: {ps['index']}")
    print(f"Task dir: {ps['task_dir']}")
    return 0

def cmd_context(a):
    out = context_payload(p(a.project_path), p(a.global_rules), not a.skip_init)
    if a.json: print(json.dumps(out, ensure_ascii=False)); return 0
    printed = False
    if a.print_summary or (not a.print_summary and not a.print_prompt): print(out["terminal_summary"]); printed = True
    if a.print_prompt:
        if printed: print("")
        print(out["prompt_payload"])
    return 0

def cmd_summary(a):
    root = p(a.project_path); ps = ensure_project(root, today())
    mem = ps["memory"].read_text(encoding="utf-8")
    entry = latest_session(mem); lt = latest(parse_index(ps["index"]))
    print(f"Project memory: {ps['memory']}")
    if entry:
        print("Latest session:")
        for line in entry: print(line)
    else: print("Latest session: (none)")
    print("")
    if lt:
        print("Latest task:")
        print(f"- id: {lt.task_id}")
        print(f"- title: {lt.title}")
        print(f"- status: {lt.status}")
        print(f"- updated: {lt.updated}")
    else: print("Latest task: (none)")
    return 0

def cmd_save(a):
    res = save_op(p(a.project_path), p(a.global_rules), a.mode, a.task_id, a.title, a.status, a.owner, items(a.completed), items(a.in_progress), items(a.next_steps), items(a.blockers), items(a.files))
    print("Save complete.")
    for k in ["mode", "task_id", "title", "status", "task_file", "index_file", "memory_file"]: print(f"{k}: {res[k]}")
    return 0

def cmd_list(a):
    root = p(a.project_path); records = sort_tasks(parse_index(ensure_project(root, today())["index"]))
    data = [{"task_id": r.task_id, "title": r.title, "status": r.status, "updated": r.updated, "task_file": r.task_file} for r in records]
    if a.json: print(json.dumps(data, ensure_ascii=False)); return 0
    if not data: print("No tasks found."); return 0
    for i, it in enumerate(data, 1): print(f"{i}. {it['task_id']} | {it['status']} | {it['updated']} | {it['title']}")
    return 0

def cmd_activate(a):
    root = p(a.project_path); ps = ensure_project(root, today()); records = parse_index(ps["index"]); rec = find(records, a.task_id)
    if not rec: print(f"Task not found: {a.task_id}"); return 1
    rec.status, rec.updated = "in_progress", stamp(); write_index(ps["index"], records)
    tp = root / rec.task_file
    if tp.exists():
        txt = tp.read_text(encoding="utf-8")
        tp.write_text(update_meta(txt, rec.task_id, rec.status, get_created(tp) or rec.updated, rec.updated, rec.title), encoding="utf-8")
    sync_memory(ps["memory"], root.name, rec.task_id, [], [f"manual pick: {rec.title}"], [], [], [rec.task_file], "manual-pick-task")
    print(f"Activated task: {rec.task_id}")
    print(f"Status set to: {rec.status}")
    print(f"Task file: {tp}")
    return 0

def cmd_archive(a):
    root = p(a.project_path); ps = ensure_project(root, today()); records = parse_index(ps["index"]); keep, n = [], 0; ps["archive"].mkdir(parents=True, exist_ok=True)
    for rec in records:
        if rec.status != "done": keep.append(rec); continue
        tp = root / rec.task_file
        if tp.exists():
            dst = ps["archive"] / tp.name; ensure_parent(dst); shutil.move(str(tp), str(dst))
        n += 1
    write_index(ps["index"], keep)
    print(f"Archived tasks: {n}")
    print(f"Archive dir: {ps['archive']}")
    return 0

def cmd_stats(a):
    records = parse_index(ensure_project(p(a.project_path), today())["index"])
    counts = {s: 0 for s in sorted(VALID_STATUSES)}
    for r in records: counts[r.status] = counts.get(r.status, 0) + 1
    print(f"Project: {p(a.project_path).name}")
    print(f"Total tasks: {len(records)}")
    for s in sorted(counts): print(f"- {s}: {counts[s]}")
    return 0

def cmd_weekly(a):
    root = p(a.project_path); ps = ensure_project(root, today()); records = sort_tasks(parse_index(ps["index"]))
    cutoff = now() - dt.timedelta(days=7)
    recent = [r for r in records if ((dt.datetime.strptime(r.updated, "%Y-%m-%d %H:%M %z") if re.match(r"^\d{4}-\d{2}-\d{2}", r.updated) else dt.datetime(1970,1,1,tzinfo=now().tzinfo)) >= cutoff)]
    counts = {s: 0 for s in sorted(VALID_STATUSES)}
    for r in records: counts[r.status] = counts.get(r.status, 0) + 1
    label = now().strftime("%Y-W%W"); rp = ps["report"] / f"weekly-{label}.md"
    lines = [f"# Weekly Report ({label})", "", f"- Generated: {stamp()}", f"- Project: {root.name}", "", "## Status Snapshot"]
    for s in sorted(counts): lines.append(f"- {s}: {counts[s]}")
    lines.extend(["", "## Tasks Updated In Last 7 Days"])
    lines.extend([f"- {r.task_id} | {r.status} | {r.updated} | {r.title}" for r in recent] or ["- (none)"])
    rp.write_text("\n".join(lines) + "\n", encoding="utf-8"); print(f"Weekly report written: {rp}")
    return 0

def ask(prompt: str, default: str = "") -> str:
    if default:
        v = input(f"{prompt} [{default}]: ").strip(); return v or default
    return input(f"{prompt}: ").strip()

def cmd_menu(a):
    root, rules = p(a.project_path), p(a.global_rules); ensure_project(root, today())
    while True:
        print("\n/mem Menu\n1) Fast Read\n2) Fast Save\n3) Pick Task Manually\n4) Advanced\n0) Exit")
        ch = input("Select: ").strip()
        if ch in {"0", "q", "quit", "exit"}: return 0
        if ch == "1": print(context_payload(root, rules, True)["terminal_summary"]); continue
        if ch == "2":
            print("\nFast Save\n1) Save Local Task Index\n2) Save Task File In docs/tasks")
            sub = input("Select: ").strip()
            if sub not in {"1", "2"}: print("Invalid selection."); continue
            title, status = ask("Task name (optional)"), ask("Status", DEFAULT_STATUS)
            if sub == "1":
                nxt = ask("Next action (optional)")
                res = save_op(root, rules, "index", None, title or None, status, DEFAULT_OWNER, [], [], [nxt] if nxt else [], [], [])
            else:
                c = items([ask("Completed (use ';' between items)")]); ip = items([ask("In progress (use ';' between items)")])
                nx = items([ask("Next actions (use ';' between items)")]); bl = items([ask("Blockers (use ';' between items)")]); fs = items([ask("Files touched (use ';' between items)")])
                res = save_op(root, rules, "task", None, title or None, status, DEFAULT_OWNER, c, ip, nx, bl, fs)
            print("Saved:"); print(json.dumps(res, ensure_ascii=False, indent=2)); continue
        if ch == "3":
            arr = sort_tasks(parse_index(paths(root)["index"]))
            if not arr: print("No tasks available to pick."); continue
            print("\nSelect task:")
            for i, r in enumerate(arr, 1): print(f"{i}) {r.task_id} | {r.status} | {r.updated} | {r.title}")
            pick = input("Pick number: ").strip()
            if not pick.isdigit() or int(pick) < 1 or int(pick) > len(arr): print("Invalid selection."); continue
            cmd_activate(argparse.Namespace(project_path=str(root), task_id=arr[int(pick)-1].task_id)); continue
        if ch == "4":
            print("\nAdvanced\n1) Archive done tasks\n2) Status stats\n3) Export weekly report")
            adv = input("Select: ").strip()
            if adv == "1": cmd_archive(argparse.Namespace(project_path=str(root)))
            elif adv == "2": cmd_stats(argparse.Namespace(project_path=str(root)))
            elif adv == "3": cmd_weekly(argparse.Namespace(project_path=str(root)))
            else: print("Invalid selection.")
            continue
        print("Invalid selection.")

def cmd_slash(a):
    c = a.slash_command.strip().lower()
    if c in {"/init", "init"}: return cmd_init(a)
    if c in {"/load", "load"}: return cmd_context(argparse.Namespace(project_path=a.project_path, global_rules=a.global_rules, print_summary=True, print_prompt=False, json=False, skip_init=False))
    if c in {"/summary", "summary"}: return cmd_summary(a)
    if c in {"/save", "save"}: return cmd_save(argparse.Namespace(project_path=a.project_path, global_rules=a.global_rules, mode="task", task_id=a.task_id, title=a.title, status=a.status, owner=a.owner, completed=a.completed, in_progress=a.in_progress, next_steps=a.next_steps, blockers=a.blockers, files=a.files))
    if c in {"/menu", "menu"}: return cmd_menu(argparse.Namespace(project_path=a.project_path, global_rules=a.global_rules))
    print(f"Unsupported slash command: {a.slash_command}")
    print("Supported: /init, /load, /summary, /save, /menu")
    return 1

def add_common(prs):
    prs.add_argument("--project-path", default=".", help="Project root path. Default: current directory.")
    prs.add_argument("--global-rules", default=DEFAULT_GLOBAL_RULES, help="Global rules file path.")

def add_save(prs):
    prs.add_argument("--mode", choices=["index", "task"], default="task", help="Save mode.")
    prs.add_argument("--task-id", help="Target task id.")
    prs.add_argument("--title", help="Task title. Creates slug id when task-id is omitted.")
    prs.add_argument("--status", default=DEFAULT_STATUS, help="Task status.")
    prs.add_argument("--owner", default=DEFAULT_OWNER, help="Task owner.")
    prs.add_argument("--completed", action="append", help="Completed item(s), ';' separated allowed.")
    prs.add_argument("--in-progress", action="append", help="In-progress item(s), ';' separated allowed.")
    prs.add_argument("--next", dest="next_steps", action="append", help="Next step item(s), ';' separated allowed.")
    prs.add_argument("--blockers", action="append", help="Blocker item(s), ';' separated allowed.")
    prs.add_argument("--files", action="append", help="Touched file item(s), ';' separated allowed.")

def parser() -> argparse.ArgumentParser:
    prs = argparse.ArgumentParser(description="Project memory and global rules manager.")
    sub = prs.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("init", help="Initialize global and project memory files."); add_common(p1); p1.set_defaults(func=cmd_init)
    p2 = sub.add_parser("context", help="Build context payload for shell/codex startup."); add_common(p2); p2.add_argument("--skip-init", action="store_true"); p2.add_argument("--print-summary", action="store_true"); p2.add_argument("--print-prompt", action="store_true"); p2.add_argument("--json", action="store_true"); p2.set_defaults(func=cmd_context)
    p3 = sub.add_parser("summary", help="Print latest memory session and task summary."); add_common(p3); p3.set_defaults(func=cmd_summary)
    p4 = sub.add_parser("save", help="Save index/task updates and sync docs/memory.md."); add_common(p4); add_save(p4); p4.set_defaults(func=cmd_save)
    p5 = sub.add_parser("list-tasks", help="List tasks from docs/tasks/index.md."); add_common(p5); p5.add_argument("--json", action="store_true"); p5.set_defaults(func=cmd_list)
    p6 = sub.add_parser("activate-task", help="Activate task and set status=in_progress."); add_common(p6); p6.add_argument("--task-id", required=True); p6.set_defaults(func=cmd_activate)
    p7 = sub.add_parser("archive-done", help="Archive done tasks and clean index."); add_common(p7); p7.set_defaults(func=cmd_archive)
    p8 = sub.add_parser("stats", help="Show status counts."); add_common(p8); p8.set_defaults(func=cmd_stats)
    p9 = sub.add_parser("weekly-report", help="Export weekly report under docs/reports."); add_common(p9); p9.set_defaults(func=cmd_weekly)
    p10 = sub.add_parser("menu", help="Interactive /mem menu."); add_common(p10); p10.set_defaults(func=cmd_menu)
    p11 = sub.add_parser("slash", help="Compatibility slash commands."); add_common(p11); p11.add_argument("slash_command"); add_save(p11); p11.set_defaults(func=cmd_slash)
    return prs

def main() -> int:
    a = parser().parse_args()
    try: return a.func(a)
    except ValueError as e: print(str(e)); return 1

if __name__ == "__main__": raise SystemExit(main())
