#!/usr/bin/env python3
"""Strict provenance registry for the one quantity with the widest seed spread.

The general traceability gate matches a literal as a substring of a data file
with separators stripped, so a short literal passes whenever its digits happen to
sit inside a longer unrelated number: 307.69 passes because 30769 occurs inside a
conformance-vector column. That is weak evidence for short literals and none at
all for frequencies.

This registry is narrower and stricter:

  * it reads only prose and script files -- *.md and *.py under research/, fpga/,
    conformance/, docs/ and the repository root -- the places where a measurement
    is actually written down, rather than every data file in the tree;
  * it requires a DELIMITED match. A literal counts as sourced only when it
    appears bounded by non-digit, non-dot characters, so 307.69 is not sourced by
    30769123 and 48.20 is not sourced by 148.204.

Usage:
    python3 tools/freq_provenance.py [--paper PATH] [--json OUT]

Exit status is 0 whether or not literals are untraced: this reports, it does not
gate. The count it prints is quoted in the paper, so it must be reproducible.
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEARCH_DIRS = ["research", "fpga", "conformance", "docs"]
SEARCH_EXTS = (".md", ".py")

# A frequency literal in the paper: a number attached to MHz, in either the prose
# form "$307.69$\,MHz" or a table cell in an Fmax column. Captured without the
# TeX thousands separator.
FREQ_PATTERNS = [
    re.compile(r"\$?([0-9]{1,3}(?:\{,\})?[0-9]*\.[0-9]+)\$?(?:\\,|~|\s)*MHz"),
    re.compile(r"MHz[^\n]{0,40}?\$([0-9]{1,3}\.[0-9]{1,2})\$"),
]


def paper_frequency_literals(paper_path):
    """Every distinct frequency literal the paper prints."""
    text = open(paper_path, encoding="utf-8", errors="replace").read()
    # Drop the bibliography: arXiv identifiers and page ranges are not measurements.
    cut = text.find("\\begin{thebibliography}")
    if cut > 0:
        text = text[:cut]
    found = set()
    for pat in FREQ_PATTERNS:
        for m in pat.finditer(text):
            lit = m.group(1).replace("{,}", "").replace(",", "")
            # A frequency, not a ratio or a percentage.
            if "." in lit and 1.0 <= float(lit) <= 100000.0:
                found.add(lit)
    return sorted(found, key=float)


def record_files():
    """Prose and script files, the places a measurement is written down."""
    out = []
    for d in SEARCH_DIRS:
        base = os.path.join(ROOT, d)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [x for x in dirnames if x not in (".git", "node_modules", "target", "__pycache__")]
            for fn in filenames:
                if fn.endswith(SEARCH_EXTS):
                    out.append(os.path.join(dirpath, fn))
    for fn in os.listdir(ROOT):
        if fn.endswith(SEARCH_EXTS) and os.path.isfile(os.path.join(ROOT, fn)):
            out.append(os.path.join(ROOT, fn))
    return sorted(out)


def delimited(literal, text):
    """True when the literal appears bounded by non-digit, non-dot characters."""
    return re.search(r"(?<![0-9.])" + re.escape(literal) + r"(?![0-9])", text) is not None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", default=os.path.join(ROOT, "arxiv_submission", "tnf_paper.tex"))
    ap.add_argument("--json", default=os.path.join(ROOT, "research", "arxiv_tnf", "freq_provenance.json"))
    args = ap.parse_args()

    if not os.path.exists(args.paper):
        print(f"paper not found: {args.paper}", file=sys.stderr)
        return 2

    literals = paper_frequency_literals(args.paper)
    files = record_files()
    blobs = []
    for f in files:
        try:
            blobs.append((os.path.relpath(f, ROOT), open(f, encoding="utf-8", errors="replace").read()))
        except OSError:
            continue

    traced, untraced = {}, []
    for lit in literals:
        hits = [rel for rel, txt in blobs if delimited(lit, txt)]
        if hits:
            traced[lit] = hits[:4]
        else:
            untraced.append(lit)

    print(f"record files searched: {len(blobs)}  ({', '.join(SEARCH_DIRS)} and the root, {'/'.join(SEARCH_EXTS)})")
    print(f"frequency literals in the paper: {len(literals)}")
    print(f"  stated in a record file: {len(traced)}")
    print(f"  stated in no record file: {len(untraced)}")
    if untraced:
        print("\nuntraced:")
        for lit in untraced:
            print(f"  {lit}")

    out = {
        "paper": os.path.relpath(args.paper, ROOT),
        "record_files_searched": len(blobs),
        "search_dirs": SEARCH_DIRS,
        "search_exts": list(SEARCH_EXTS),
        "match": "delimited, not substring",
        "frequency_literals": len(literals),
        "traced": len(traced),
        "untraced": len(untraced),
        "untraced_literals": untraced,
        "traced_literals": traced,
    }
    os.makedirs(os.path.dirname(args.json), exist_ok=True)
    with open(args.json, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(f"\nwritten: {os.path.relpath(args.json, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
