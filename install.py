#!/usr/bin/env python3
"""Install the top-tier-paper-writing skill for one or more coding agents.

The skill lives in one place (skills/top-tier-paper-writing/) and follows the
Agent Skills format (a folder with SKILL.md + scripts/ + references/), which
Claude Code, OpenAI Codex and Google Antigravity all read. This script links
(default) or copies that folder into each agent's skills directory.

    python3 install.py                          # all agents, user level (symlink)
    python3 install.py --agent claude codex     # only some agents
    python3 install.py --project ~/my-paper     # project level, inside a repo
    python3 install.py --copy                   # copy instead of symlink
    python3 install.py --dest ~/somewhere/skills  # any other skills directory
    python3 install.py --status                 # show what is installed where
    python3 install.py --uninstall              # remove what this script installed

Symlinks keep every agent on the same files, so `git pull` updates all of them.
On systems where symlinks are not permitted (e.g. Windows without developer
mode) the script falls back to copying.
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

SKILL_NAME = "top-tier-paper-writing"
SOURCE = Path(__file__).resolve().parent / "skills" / SKILL_NAME

# User-level skills directories.
USER_DIRS = {
    "claude": "~/.claude/skills",                          # Claude Code
    "codex": "~/.agents/skills",                           # OpenAI Codex (legacy: ~/.codex/skills)
    "antigravity": "~/.gemini/antigravity/skills",         # Antigravity app (global)
    "antigravity-cli": "~/.gemini/antigravity-cli/skills", # Antigravity CLI (global)
}
# Project-level skills directories (relative to the project root).
# Codex and Antigravity both read .agents/skills, so they share one install.
PROJECT_DIRS = {
    "claude": ".claude/skills",
    "codex": ".agents/skills",
    "antigravity": ".agents/skills",
    "antigravity-cli": ".agents/skills",
}
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", "session_domain_profile.json")


def skill_name_of(path: Path):
    """Return the `name:` from a SKILL.md frontmatter, or None."""
    md = path / "SKILL.md"
    if not md.is_file():
        return None
    try:
        lines = md.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip("'\"")
    return None


def state(target: Path) -> str:
    if target.is_symlink():
        try:
            same = target.resolve() == SOURCE
        except OSError:
            same = False
        return "linked" if same else "foreign-link"
    if target.is_dir():
        return "copied" if skill_name_of(target) == SKILL_NAME else "foreign-dir"
    if target.exists():
        return "foreign-file"
    return "absent"


def remove(target: Path):
    if target.is_symlink() or target.is_file():
        target.unlink()
    else:
        shutil.rmtree(target)


def install_one(target: Path, copy: bool, force: bool, dry: bool) -> str:
    st = state(target)
    if st == "linked" and not copy:
        return "already linked"
    if st.startswith("foreign") and not force:
        return f"SKIPPED: {target} exists and is not this skill (use --force to replace)"
    if dry:
        return f"would {'copy' if copy else 'link'} (current: {st})"
    target.parent.mkdir(parents=True, exist_ok=True)
    if st != "absent":
        remove(target)
    if not copy:
        try:
            target.symlink_to(SOURCE, target_is_directory=True)
            return "linked"
        except (OSError, NotImplementedError) as e:
            print(f"  [note] symlink failed ({e}); copying instead")
    shutil.copytree(SOURCE, target, ignore=IGNORE)
    return "copied"


def uninstall_one(target: Path, force: bool, dry: bool) -> str:
    st = state(target)
    if st == "absent":
        return "not installed"
    if st.startswith("foreign") and not force:
        return f"SKIPPED: {target} is not this skill (use --force to remove anyway)"
    if dry:
        return f"would remove ({st})"
    remove(target)
    return f"removed ({st})"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agent", nargs="+", choices=sorted(USER_DIRS) + ["all"], default=["all"],
                    help="which agents to install for (default: all)")
    where = ap.add_mutually_exclusive_group()
    where.add_argument("--project", metavar="DIR", help="install into a project instead of the user profile")
    where.add_argument("--dest", metavar="DIR", action="append",
                       help="install into this skills directory (repeatable; overrides --agent)")
    ap.add_argument("--copy", action="store_true", help="copy files instead of creating a symlink")
    ap.add_argument("--force", action="store_true", help="replace/remove an unrelated existing entry")
    ap.add_argument("--uninstall", action="store_true", help="remove the skill from the selected locations")
    ap.add_argument("--status", action="store_true", help="only report the current state")
    ap.add_argument("--dry-run", action="store_true", help="show what would happen")
    args = ap.parse_args(argv)

    if skill_name_of(SOURCE) != SKILL_NAME:
        print(f"[error] skill source not found or invalid: {SOURCE}", file=sys.stderr)
        return 2

    if args.dest:
        targets = {Path(d).expanduser() / SKILL_NAME: ["custom"] for d in args.dest}
    else:
        agents = sorted(USER_DIRS) if "all" in args.agent else args.agent
        targets = {}
        for a in agents:
            base = (Path(args.project).expanduser() / PROJECT_DIRS[a]) if args.project else Path(USER_DIRS[a]).expanduser()
            targets.setdefault(base / SKILL_NAME, []).append(a)

    print(f"source: {SOURCE}")
    failed = False
    for target, agents in targets.items():
        label = ", ".join(agents)
        if args.status:
            msg = state(target)
        elif args.uninstall:
            msg = uninstall_one(target, args.force, args.dry_run)
        else:
            msg = install_one(target, args.copy, args.force, args.dry_run)
        failed |= msg.startswith("SKIPPED")
        print(f"  [{label}] {target}: {msg}")

    if not (args.status or args.uninstall or args.dry_run):
        print("\nNext: install the script dependencies once, then restart the agent so it rescans skills:")
        print(f"  python3 -m pip install -r {SOURCE / 'requirements.txt'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
