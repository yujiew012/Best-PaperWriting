#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""Validate this skill's packaging (maintainers / CI). Stdlib only.

Checks:
  S001  SKILL.md starts with YAML frontmatter containing name and description   error
  S002  name: 1-64 chars, lowercase letters/digits/hyphens, equals folder name   error
  S003  description: single line, <= 1024 chars                                 error
  S004  every scripts/ references/ assets/ path mentioned in SKILL.md exists    error
  S005  every script has a PEP 723 header and compiles                          error
  S006  SKILL.md body <= 500 lines                                              warning
  S007  description <= 600 chars (index-layer budget)                           warning
  S008  file in references/ or assets/ not mentioned in SKILL.md (orphan)       warning

    python3 validate_skill.py            # validates the skill this script belongs to
    python3 validate_skill.py path/to/skill

Exit codes: 0 valid, 1 errors.
"""
import os
import re
import sys


def frontmatter(text):
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end < 0:
        return None, text
    raw = text[4:end]
    body = text[end + 4:].lstrip("\n")
    fields, cur = {}, None
    for line in raw.splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            cur = m.group(1)
            fields[cur] = m.group(2).strip()
        elif cur and line.startswith((" ", "\t")):
            fields[cur] += "\n" + line.strip()   # nested map or folded text
    return fields, body


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("skill", nargs="?", help="skill folder (default: the one containing this script)")
    args = ap.parse_args(argv)
    skill = os.path.abspath(args.skill or os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    errors, warns = [], []
    md_path = os.path.join(skill, "SKILL.md")
    if not os.path.isfile(md_path):
        print(f"[error] no SKILL.md in {skill}")
        return 1
    text = open(md_path, encoding="utf-8").read()
    fm, body = frontmatter(text)
    if not fm or "name" not in fm or "description" not in fm:
        errors.append("S001 SKILL.md needs YAML frontmatter with name and description")
        fm = fm or {}
    name = fm.get("name", "").strip("'\"")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
        errors.append(f"S002 invalid name '{name}'")
    if name != os.path.basename(skill):
        errors.append(f"S002 name '{name}' != folder '{os.path.basename(skill)}'")
    desc = fm.get("description", "")
    if desc[:1] in "'\"":
        desc = desc[1:-1] if desc[-1:] == desc[:1] else desc
    if "\n" in desc or desc.startswith((">", "|")):
        errors.append("S003 description must be a single line (no folded/literal block)")
    if len(desc) > 1024:
        errors.append(f"S003 description is {len(desc)} chars (> 1024)")
    elif len(desc) > 600:
        warns.append(f"S007 description is {len(desc)} chars; keep the always-loaded index short (<= 600)")
    n_body = body.count("\n") + 1
    if n_body > 500:
        warns.append(f"S006 SKILL.md body has {n_body} lines (> 500); move detail to references/")

    mentioned = set(re.findall(r"(?<![\w/.])((?:scripts|references|assets)/[\w./-]+\w)", text))
    for rel in sorted(mentioned):
        if "*" in rel or "<" in rel:
            continue
        if not os.path.exists(os.path.join(skill, rel)):
            errors.append(f"S004 SKILL.md mentions missing path: {rel}")
    for sub in ("references", "assets"):
        d = os.path.join(skill, sub)
        for root, _, files in os.walk(d):
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), skill).replace(os.sep, "/")
                if rel not in mentioned and not any(rel.startswith(m.rstrip("/") + "/") for m in mentioned):
                    warns.append(f"S008 {rel} is not referenced from SKILL.md (unreachable for the agent)")
    sdir = os.path.join(skill, "scripts")
    for f in sorted(os.listdir(sdir)) if os.path.isdir(sdir) else []:
        if not f.endswith(".py"):
            continue
        p = os.path.join(sdir, f)
        src = open(p, encoding="utf-8").read()
        if f != "pubstyle.py" and "# /// script" not in src:
            errors.append(f"S005 scripts/{f} has no PEP 723 header (needed for `uv run`)")
        try:
            compile(src, p, "exec")      # syntax check in memory, no .pyc written
        except SyntaxError as e:
            errors.append(f"S005 scripts/{f} does not compile: line {e.lineno}: {e.msg}")

    for e in errors:
        print(f"[error] {e}")
    for w in warns:
        print(f"[warn]  {w}")
    print(f"\n{os.path.basename(skill)}: {len(errors)} error(s), {len(warns)} warning(s); "
          f"description {len(desc)} chars, SKILL.md body {n_body} lines")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
