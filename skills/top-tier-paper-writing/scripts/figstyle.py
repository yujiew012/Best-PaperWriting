"""Figure style profiles for gen_architecture_diagram.py (and evolve.py).

A profile lives in references/figure_styles/<name>.json:
    {"domain": ..., "notes": ..., "base": {...}, "provisional": {"font.badge": {"value": 8, "rule": "S-0003"}}}
`base` holds established values; `provisional` holds overrides added by the figure-evolution
loop (one exemplar paper so far). The effective style = base with provisional overrides applied.
Every value must stay inside references/figure_styles/_bounds.json.
"""
import copy
import json
import os

STYLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "figure_styles")
OKABE = {"blue": "#0072B2", "orange": "#E69F00", "bluish_green": "#009E73", "vermilion": "#D55E00",
         "reddish_purple": "#CC79A7", "sky_blue": "#56B4E9", "black": "#000000", "grey": "#555555",
         "yellow": "#F0E442"}
TINT = {"none": 1.0, "light": 0.90, "medium": 0.78}      # share of white mixed into the fill


def bounds():
    with open(os.path.join(STYLE_DIR, "_bounds.json"), encoding="utf-8") as f:
        return {k: v for k, v in json.load(f).items() if not k.startswith("$")}


def get(d, path):
    for part in path.split("."):
        d = d[part]
    return d


def set_path(d, path, value):
    parts = path.split(".")
    for part in parts[:-1]:
        d = d.setdefault(part, {})
    d[parts[-1]] = value


def check_value(path, value, b=None):
    """Return an error string if `value` is not allowed for `path`, else None."""
    b = b or bounds()
    if path not in b:
        return f"unknown style parameter '{path}' (allowed: {', '.join(sorted(b))})"
    rule = b[path]
    if "enum" in rule and value not in rule["enum"]:
        return f"{path}={value!r} not in {rule['enum']}"
    if "min" in rule:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return f"{path} must be a number"
        if not rule["min"] <= value <= rule["max"]:
            return f"{path}={value} outside [{rule['min']}, {rule['max']}]"
    return None


def load(name_or_path):
    """Load a profile by domain name or path; returns (profile_dict, path)."""
    path = name_or_path if name_or_path.endswith(".json") else os.path.join(STYLE_DIR, f"{name_or_path}.json")
    if not os.path.exists(path):
        path = os.path.join(STYLE_DIR, "default.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f), path


def effective(profile):
    style = copy.deepcopy(profile["base"])
    for p, entry in profile.get("provisional", {}).items():
        set_path(style, p, entry["value"] if isinstance(entry, dict) else entry)
    return style


def validate(profile):
    """List of errors for base and provisional values."""
    b = bounds()
    errs = []
    for p in b:
        try:
            v = get(profile["base"], p)
        except (KeyError, TypeError):
            errs.append(f"base is missing '{p}'")
            continue
        e = check_value(p, v, b)
        if e:
            errs.append("base: " + e)
    for p, entry in profile.get("provisional", {}).items():
        v = entry["value"] if isinstance(entry, dict) else entry
        e = check_value(p, v, b)
        if e:
            errs.append("provisional: " + e)
    return errs


def mix(hex_color, white_share):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    m = lambda c: round(c + (255 - c) * white_share)
    return f"#{m(r):02X}{m(g):02X}{m(b):02X}"


def role_colors(style, role, group=False):
    """(fill, edge) for a role; groups use a lighter fill."""
    edge = OKABE[style["roles"].get(role, style["roles"]["neutral"])]
    if group:
        fill = mix(edge, 0.96) if style["group"]["fill"] else "none"
    elif role == "neutral":
        fill = "#FFFFFF"
    else:
        fill = mix(edge, TINT[style["block"]["fill"]])
    return fill, edge
