#!/usr/bin/env python3
"""Write or check SHA-256 digests for the conformance vector set.

The paper tells a reader to check a transcript's digests against a published
manifest. Until this script existed there was no manifest to check against, and
the version names the paper used named nothing. This produces the manifest and
verifies it, so the instruction in the paper is executable.

    python3 conformance/make_vector_manifest.py           # write SHA256SUMS
    python3 conformance/make_vector_manifest.py --check    # verify, exit 1 on drift
"""
import argparse
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VECTORS = os.path.join(HERE, "vectors")
SUMS = os.path.join(VECTORS, "SHA256SUMS")


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def vector_files():
    out = []
    for fn in sorted(os.listdir(VECTORS)):
        p = os.path.join(VECTORS, fn)
        if os.path.isfile(p) and fn not in ("SHA256SUMS", "MANIFEST.md"):
            out.append(fn)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify instead of writing")
    args = ap.parse_args()

    files = vector_files()
    if not files:
        print(f"no vector files under {VECTORS}", file=sys.stderr)
        return 2

    if not args.check:
        with open(SUMS, "w", encoding="utf-8") as fh:
            for fn in files:
                fh.write(f"{digest(os.path.join(VECTORS, fn))}  {fn}\n")
        print(f"wrote {len(files)} digests to {os.path.relpath(SUMS, os.path.dirname(HERE))}")
        return 0

    if not os.path.exists(SUMS):
        print(f"no manifest at {SUMS}; run without --check first", file=sys.stderr)
        return 2

    recorded = {}
    for line in open(SUMS, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        d, _, fn = line.partition("  ")
        recorded[fn] = d

    bad = []
    for fn in files:
        want = recorded.pop(fn, None)
        if want is None:
            bad.append(f"present but unlisted: {fn}")
            continue
        got = digest(os.path.join(VECTORS, fn))
        if got != want:
            bad.append(f"digest drift: {fn}\n    recorded {want}\n    actual   {got}")
    for fn in recorded:
        bad.append(f"listed but missing: {fn}")

    if bad:
        print(f"FAILED: {len(bad)} problem(s)")
        for b in bad:
            print(f"  {b}")
        return 1
    print(f"all {len(files)} vector files match the manifest")
    return 0


if __name__ == "__main__":
    sys.exit(main())
