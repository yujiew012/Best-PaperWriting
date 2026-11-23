#!/usr/bin/env python3
"""Mirror the canonical skill (skills/) into .agent/skills/.

skills/top-tier-paper-writing/ is the only place to edit. .agent/skills/ is a
copy for tools that read skills from .agent/ (e.g. Antigravity).

    python3 tools/sync_skill.py          # copy skills/ -> .agent/skills/
    python3 tools/sync_skill.py --check  # exit 1 if the two differ
"""
import argparse
import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "skills"
DST = ROOT / ".agent" / "skills"
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")


def diff(a: Path, b: Path, rel=Path()):
    """Yield relative paths that differ between two trees."""
    if not b.exists():
        yield rel or Path(".")
        return
    cmp = filecmp.dircmp(a, b, ignore=["__pycache__", ".DS_Store"])
    for name in cmp.left_only + cmp.right_only + cmp.funny_files:
        yield rel / name
    _, mismatch, errors = filecmp.cmpfiles(a, b, cmp.common_files, shallow=False)
    for name in mismatch + errors:
        yield rel / name
    for sub in cmp.common_dirs:
        yield from diff(a / sub, b / sub, rel / sub)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="only report differences")
    args = ap.parse_args()
    changed = sorted(set(diff(SRC, DST)))
    if args.check:
        for p in changed:
            print(f"differs: {p}")
        print("in sync" if not changed else f"{len(changed)} path(s) out of sync; run tools/sync_skill.py")
        return 1 if changed else 0
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=IGNORE)
    print(f"synced {SRC.relative_to(ROOT)} -> {DST.relative_to(ROOT)} ({len(changed)} path(s) updated)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
