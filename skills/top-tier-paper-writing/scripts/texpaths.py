#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""Resolve \\input / \\include file names the way LaTeX does (shared by the .tex readers).

LaTeX opens the file of an \\input relative to the directory it runs in -- the directory of the
main file -- not relative to the file that contains the \\input. A section file
sections/results.tex that says \\input{tables/main} therefore reads <main dir>/tables/main.tex.
The including file's own directory is tried second (packages such as import/subfiles use it).
"""
import os


def resolve_input(name, including, root):
    """Absolute path of the file `name` input from `including`, with `root` the main file's dir."""
    name = name.strip()
    candidates = []
    for base in (root, os.path.dirname(os.path.abspath(including))):
        path = os.path.join(base, name)
        candidates += [path] if path.endswith(".tex") else [path + ".tex", path]
    for path in candidates:
        if os.path.isfile(path):
            return os.path.abspath(path)
    return os.path.abspath(candidates[0])          # missing: report it under the LaTeX path


def expand_simple_macros(tex):
    """Replace argument-free macros defined in the document (\\newcommand{\\M}{Name}) by their text.

    Prose checks would otherwise drop a method name such as \\M{} and miscount the sentence."""
    import re
    macros = {}
    for m in re.finditer(r"\\(?:re)?newcommand\*?\{?\\([A-Za-z]+)\}?\s*\{((?:[^{}]|\{[^{}]*\})*)\}", tex):
        body = m.group(2)
        if "#" not in body and "\\" not in body.replace("\\ ", ""):    # plain text only
            macros[m.group(1)] = body
    if not macros:
        return tex
    names = "|".join(sorted(map(re.escape, macros), key=len, reverse=True))
    # not inside the definitions themselves (\newcommand{\M} / \newcommand\M)
    return re.sub(r"(?<!newcommand\{)(?<!newcommand\*\{)(?<!newcommand)\\(" + names + r")(?![A-Za-z])(?:\{\})?",
                  lambda m: macros[m.group(1)], tex)


def refs_to_text(t, ref_word="Section 1"):
    """Cross-references as the reader sees them: \\cref/\\Cref/\\autoref print a name and a number."""
    import re
    t = re.sub(r"(?:Fig|Tab|Sec|Eq)\.?~?\\(?:c|C|auto)?ref\*?\{[^}]*\}", "Figure 1", t)
    t = re.sub(r"\\(?:cref|Cref|autoref|labelcref)\*?\{[^}]*\}", ref_word, t)
    t = re.sub(r"\\eqref\{[^}]*\}", "(1)", t)
    return re.sub(r"\\(?:v|V|page|name)?ref\*?\{[^}]*\}", "1", t)
