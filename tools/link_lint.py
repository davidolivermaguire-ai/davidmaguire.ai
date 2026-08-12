#!/usr/bin/env python3
"""link_lint.py - internal-link checks for the Quarto source.

Two checks, run together by default:

  broken links  - every internal [text](url) / ![](img) points at a file that
                  exists (dead targets are hard errors). Code fences and inline
                  `code` spans are skipped, so JS like run[f](x.input) is ignored.

  gap candidates - inside an *enumeration* (a table cell, or a comma/middot
                  list of methods) that already links one method, a sibling
                  method with its own page left as plain text. Advisory only.
                  Headings, code and figure captions are skipped; links are
                  resolved to a canonical path so an already-linked term via any
                  relative path is not re-flagged.

Reads tools/link_map.json. Standard library only.

Usage:
    python tools/link_lint.py                 # both checks, whole site
    python tools/link_lint.py --broken        # broken-link check only
    python tools/link_lint.py --siblings      # gap-candidate check only
    python tools/link_lint.py --strict        # exit 1 if any BROKEN links
    python tools/link_lint.py phd/index.qmd   # specific files
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MAP = os.path.join(HERE, "link_map.json")
LINK_RE = re.compile(r"\[[^\]]*\]\([^)]*\)")   # a markdown [text](url) link
URL_RE = re.compile(r"\]\(([^)]+)\)")          # the url inside a link
INLINE_CODE = re.compile(r"`[^`]*`")           # an inline `code` span


def canon(path):
    p = path.replace("\\", "/").split("#")[0].split("?")[0]
    if p.endswith("index.qmd"):
        p = p[:-len("index.qmd")]
    return p.rstrip("/")


def resolve(url, file_dir):
    u = url.strip()
    if not u or u.startswith(("http://", "https://", "mailto:", "#")):
        return None
    full = os.path.normpath(os.path.join(file_dir, u)).replace("\\", "/")
    return canon(full)


def target_exists(url, file_dir):
    """Does an internal link target exist on disk? External/anchor links pass."""
    u = url.split("#")[0].split("?")[0].strip()
    if not u or u.startswith(("http://", "https://", "mailto:", "#")):
        return True
    tgt = os.path.normpath(os.path.join(ROOT, file_dir, u))
    ext = os.path.splitext(u)[1]
    if u.endswith("/"):
        return os.path.exists(os.path.join(tgt, "index.qmd")) or os.path.isdir(tgt)
    if ext == ".html":
        return os.path.exists(tgt[:-5] + ".qmd") or os.path.exists(tgt)
    if ext:
        return os.path.exists(tgt)
    return (os.path.exists(os.path.join(tgt, "index.qmd"))
            or os.path.isdir(tgt) or os.path.exists(tgt + ".qmd"))


def load_entries():
    data = json.load(open(MAP, encoding="utf-8"))
    ents = []
    for e in data["entries"]:
        e["_canon"] = canon(e["url"])
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


def check_broken(path):
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    file_dir = os.path.dirname(rel)
    lines = open(path, encoding="utf-8").read().split("\n")
    start = _frontmatter_end(lines)
    out = []
    in_code = False
    for i in range(start, len(lines)):
        s = lines[i].strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        line = INLINE_CODE.sub("", lines[i])   # drop inline code spans
        for u in URL_RE.findall(line):
            if not target_exists(u, file_dir):
                out.append((i + 1, u))
    return rel, out


def check_siblings(path, ents):
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    file_dir = os.path.dirname(rel)
    text = open(path, encoding="utf-8").read()
    lines = text.split("\n")
    start = _frontmatter_end(lines)

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
        if in_code or not s or s.startswith("#") or s.startswith("!["):
            continue
        if set(s) <= set("|:- "):
            continue
        if not has_link(idx):
            continue
        seps = line.count(",") + line.count("·") + line.count(";")
        if not (s.startswith("|") or seps >= 2):
            continue
        targets = {resolve(u, file_dir) for u in URL_RE.findall(line)}
        plain = blines[idx]
        for e in ents:
            if rel == e["qmd"] or e["_canon"] in targets:
                continue
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
    broken_only = "--broken" in argv
    siblings_only = "--siblings" in argv
    paths = [a for a in argv[1:] if not a.startswith("--")]
    files = [os.path.join(ROOT, p) for p in paths] if paths else default_files()

    n_broken = n_sib = 0
    if not siblings_only:
        print("== broken internal links ==")
        for f in files:
            rel, out = check_broken(f)
            for ln, u in out:
                print(f"  {rel}:{ln}  ->  {u}   (target missing)")
                n_broken += 1
        print(f"  {n_broken} broken link(s).\n")

    if not broken_only:
        ents = load_entries()
        print("== link-gap candidates (plain sibling in an enumeration) ==")
        for f in files:
            rel, issues = check_siblings(f, ents)
            if issues:
                print(f"  {rel}")
                for ln, alias, url in issues:
                    print(f"    line {ln}: '{alias}' -> {url}")
                    n_sib += 1
        print(f"  {n_sib} candidate(s).")

    return 1 if (strict and n_broken) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
