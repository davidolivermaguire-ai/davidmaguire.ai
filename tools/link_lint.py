#!/usr/bin/env python3
"""link_lint.py - flag internal-link gaps in the Quarto source.

Targets the specific bug the site's link audit found: inside an *enumeration*
(a table cell, or a comma/middot-separated list of methods) that already links
at least one method, a sibling method that has its own page is left as plain
text. Scoping to enumerations keeps it high-signal - ordinary prose mentions of
a concept are not flagged, only lists where a peer is already linked.

Reads tools/link_map.json. Standard library only (no pip installs), so it runs
in the same pass that verifies the site's numbers.

Usage:
    python tools/link_lint.py                 # scan the whole site, warn
    python tools/link_lint.py --strict        # exit 1 if any gaps (for CI)
    python tools/link_lint.py phd/index.qmd   # scan specific files
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MAP = os.path.join(HERE, "link_map.json")
LINK_RE = re.compile(r"\[[^\]]*\]\([^)]*\)")  # a markdown [text](url) link


def load_entries():
    data = json.load(open(MAP, encoding="utf-8"))
    ents = []
    for e in data["entries"]:
        e["_res"] = [
            (re.compile(r"(?<![\w-])" + re.escape(a) + r"(?![\w-])", re.I), a)
            for a in e["aliases"]
        ]
        ents.append(e)
    return ents


def _frontmatter_end(lines):
    if lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            if lines[j].strip() == "---":
                return j + 1
    return 0


def check_file(path, ents):
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    text = open(path, encoding="utf-8").read()
    lines = text.split("\n")
    start = _frontmatter_end(lines)

    # Blank every link span across the WHOLE file (link text can wrap across lines),
    # keeping newlines so line numbers and offsets are preserved.
    chars = list(text)
    spans = []
    for m in LINK_RE.finditer(text):
        spans.append((m.start(), m.end()))
        for k in range(m.start(), m.end()):
            if chars[k] != "\n":
                chars[k] = " "
    blines = "".join(chars).split("\n")

    offs, o = [], 0
    for ln in lines:
        offs.append(o)
        o += len(ln) + 1

    def has_link(i):
        a, b = offs[i], offs[i] + len(lines[i])
        return any(sa < b and sb > a for sa, sb in spans)

    issues = []
    in_code = False
    for idx in range(start, len(lines)):
        line = lines[idx]
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not s or s.startswith("#"):
            continue
        if set(s) <= set("|:- "):          # table separator row
            continue
        if not has_link(idx):               # must already link something
            continue
        seps = line.count(",") + line.count("·") + line.count(";")
        if not (s.startswith("|") or seps >= 2):
            continue                        # only enumerations: table cells / method lists
        plain = blines[idx]                 # link text blanked out, wraps included
        for e in ents:
            if rel == e["qmd"] or e["url"] in line:
                continue                    # its own page, or already linked on this line
            for rgx, alias in e["_res"]:
                if rgx.search(plain):
                    issues.append((idx + 1, alias, e["url"]))
                    break
    return rel, issues


def default_files():
    fs = glob.glob(os.path.join(ROOT, "*.qmd"))
    fs += glob.glob(os.path.join(ROOT, "**", "index.qmd"), recursive=True)
    out = []
    for f in sorted(set(fs)):
        p = f.replace("\\", "/")
        if "/_site/" in p or "/.quarto/" in p or "/_freeze/" in p:
            continue
        out.append(f)
    return out


def main(argv):
    strict = "--strict" in argv
    paths = [a for a in argv[1:] if not a.startswith("--")]
    files = [os.path.join(ROOT, p) for p in paths] if paths else default_files()
    ents = load_entries()
    total = 0
    for f in files:
        rel, issues = check_file(f, ents)
        if issues:
            print(rel)
            for ln, alias, url in issues:
                print(f"  line {ln}: '{alias}' is plain text but has a page -> {url}")
            total += len(issues)
    print(f"\n{total} candidate link gap(s) across {len(files)} files.")
    return 1 if (strict and total) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
