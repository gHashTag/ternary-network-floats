#!/usr/bin/env python3
"""Check that regenerating the corpus reproduces what is committed.

gen_all_formats.py used to read its catalog from /tmp/catalog_lines.txt, which was
never in the repository: on a clean checkout it raised FileNotFoundError, so the
corpus could be read but not regenerated. It now reads the committed SSOT,
specs/numeric/formats_catalog.t27, whose `// CATALOG:` rows are the same lines
catalog-count-gate.yml counts.

This script is the falsifiable half of that claim. If the SSOT and the generator
had drifted apart in any field, the regenerated packs would not match the SHA-256
digests already recorded in INDEX_all_formats.json.

Run from a clean checkout:

    python3 gen_all_formats.py        # regenerate from the SSOT
    python3 verify_regeneration.py    # digests still match

Exit 0 if every pack's digest and tier is unchanged. Exit 1 naming what moved.

What this does NOT establish: that any format is specified correctly -- only that
the pipeline runs from committed inputs and lands where it landed before.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "INDEX_all_formats.json")


def committed_index() -> dict:
    """The index as of HEAD, so a regenerated working tree can be compared to it."""
    rel = os.path.relpath(INDEX, subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], cwd=HERE, text=True).strip())
    blob = subprocess.check_output(["git", "show", f"HEAD:{rel}"], cwd=HERE)
    return json.loads(blob)


def main() -> int:
    live = json.load(open(INDEX))
    try:
        base = committed_index()
    except subprocess.CalledProcessError:
        print("cannot read the committed index from git; run inside a checkout")
        return 2

    base_by_id = {e["id"]: e for e in base["packs"]}
    live_by_id = {e["id"]: e for e in live["packs"]}

    moved, missing, retiered = [], [], []
    for cid, be in base_by_id.items():
        le = live_by_id.get(cid)
        if le is None:
            missing.append(cid)
            continue
        # digest of the file on disk now, not the recorded one
        path = os.path.join(HERE, le["file"])
        if not os.path.exists(path):
            missing.append(cid)
            continue
        disk = hashlib.sha256(open(path, "rb").read()).hexdigest()
        if disk != be.get("sha256"):
            moved.append((cid, be.get("sha256", "")[:12], disk[:12]))
        if le.get("kind") != be.get("kind"):
            retiered.append((cid, be.get("kind"), le.get("kind")))

    added = sorted(set(live_by_id) - set(base_by_id))

    print(f"packs compared: {len(base_by_id)}")
    print(f"  digests unchanged : {len(base_by_id) - len(moved) - len(missing)}")
    print(f"  digests changed   : {len(moved)}")
    print(f"  missing on disk   : {len(missing)}")
    print(f"  tier changed      : {len(retiered)}")
    print(f"  new packs         : {len(added)}")

    for cid, was, now in moved:
        print(f"    CHANGED {cid}: {was}... -> {now}...")
    for cid in missing:
        print(f"    MISSING {cid}")
    for cid, was, now in retiered:
        print(f"    RETIERED {cid}: {was} -> {now}")
    for cid in added:
        print(f"    NEW {cid}")

    ok = not (moved or missing or retiered)
    print("\n" + ("OK: regeneration reproduces the committed corpus."
                  if ok else
                  "FAIL: regeneration does not reproduce the committed corpus."))
    if ok:
        print("The committed SSOT is sufficient to rebuild the corpus from scratch.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
