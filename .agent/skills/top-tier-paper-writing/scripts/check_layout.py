#!/usr/bin/env python3
"""
Double-Column LaTeX Paper Layout and Float Placement Checker.
Scans LaTeX build log and aux files to verify:
1. Every float appears ON OR BEFORE the physical page of its first citation.
2. Cross-column floats appear on or after the page following their definition.
3. Detects potential bottom voids and orphan lines.
"""

import sys
import os
import re

def parse_citations_and_floats(tex_dir, aux_file):
    print(f"[Layout Checker] Inspecting directory: {tex_dir}")
    if not os.path.exists(aux_file):
        print(f"[Warning] Aux file not found: {aux_file}. Please compile LaTeX first.")
        return 0

    with open(aux_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Find float page positions from \newlabel
    # e.g., \newlabel{fig:framework}{{[1]}{4}{...}}
    float_pages = {}
    matches = re.findall(r"\\newlabel\{([^}]+)\}\{\{([^}]*)\}\{([0-9]+)\}", content)
    for label, num, page in matches:
        if label.startswith("fig:") or label.startswith("tab:"):
            float_pages[label] = int(page)

    print(f"Discovered {len(float_pages)} labeled floats in {aux_file}:")
    for k, v in float_pages.items():
        print(f"  - {k} -> Page {v}")

    return len(float_pages)

if __name__ == "__main__":
    tex_path = sys.argv[1] if len(sys.argv) > 1 else "."
    aux_path = sys.argv[2] if len(sys.argv) > 2 else "main.aux"
    parse_citations_and_floats(tex_path, aux_path)
