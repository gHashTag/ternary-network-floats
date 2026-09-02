#!/usr/bin/env python3
"""Conformance test for the direct TNF weight-apply + accumulate RTL.

The oracle is intentionally outside the RTL.  It decodes to an exact Fraction,
adds there, and re-encodes with round-to-nearest-even.  The circuit receives only
packed TNF words and a two-bit ternary weight code.
"""

from fractions import Fraction
from pathlib import Path
import random
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "oracle"))
import tnf_ref  # noqa: E402


RTL = [
    ROOT / "rtl" / "tnf_weight_apply.v",
    ROOT / "rtl" / "tnf_add_full.v",
    ROOT / "rtl" / "tnf_mac.v",
    ROOT / "rtl" / "tnf_mac_e4m8_top.v",
]
TB = ROOT / "tests" / "tnf_mac_e4m8_tb.v"
FMT = tnf_ref.TNFFormat(exp_trits=4, mant_bits=8)


def apply_weight(raw, weight):
    if weight in (0, 3):
        return 0
    if weight == 1:
        return raw
    if weight == 2:
        return raw ^ (1 << FMT.sign_shift)
    raise AssertionError(weight)


def expected_mac(acc, sample, weight):
    return tnf_ref.tef_add(FMT, acc, apply_weight(sample, weight))


def encoded_finite(rng):
    sign = rng.randrange(2)
    offset = rng.randrange(1, FMT.offset_max)
    mantissa = rng.randrange(1 << FMT.mant_bits)
    return ((sign << FMT.sign_shift)
            | (offset << FMT.exp_shift)
            | mantissa)


def vectors():
    one = tnf_ref.encode(FMT, Fraction(1))
    minus_one = tnf_ref.encode(FMT, Fraction(-1))
    inf = FMT.offset_max << FMT.exp_shift
    invalid = ((1 << FMT.exp_bits) - 1) << FMT.exp_shift

    directed = [
        (0, one, 0),
        (0, one, 1),
        (0, one, 2),
        (one, one, 1),
        (one, one, 2),
        (minus_one, one, 1),
        (one, inf, 0),
        (one, inf, 1),
        (one, invalid, 1),
        (inf, one, 1),
        (invalid, one, 1),
        (one, minus_one, 3),
    ]

    rng = random.Random(0x544E46)
    out = list(directed)
    for _ in range(4988):
        acc = 0 if rng.random() < 0.03 else encoded_finite(rng)
        sample = 0 if rng.random() < 0.03 else encoded_finite(rng)
        out.append((acc, sample, rng.randrange(4)))
    return [(a, x, w, expected_mac(a, x, w)) for a, x, w in out]


def main():
    missing = [str(path.relative_to(ROOT)) for path in RTL if not path.is_file()]
    if missing:
        print("FAIL: direct TNF RTL is missing: " + ", ".join(missing))
        return 1

    with tempfile.TemporaryDirectory(prefix="tnf-direct-") as tmp_name:
        tmp = Path(tmp_name)
        vec = tmp / "vectors.txt"
        sim = tmp / "tnf_mac.vvp"
        vec.write_text("".join(
            f"{a:04x} {x:04x} {w:x} {want:04x}\n"
            for a, x, w, want in vectors()
        ), encoding="ascii")

        compile_cmd = [
            "iverilog", "-g2012", "-Wall", "-s", "tnf_mac_e4m8_tb",
            "-o", str(sim), *(str(path) for path in RTL), str(TB),
        ]
        subprocess.run(compile_cmd, cwd=ROOT, check=True)
        run = subprocess.run(
            ["vvp", str(sim), f"+VECTORS={vec}"],
            cwd=ROOT, check=False, text=True, capture_output=True,
        )
        sys.stdout.write(run.stdout)
        sys.stderr.write(run.stderr)
        return run.returncode


if __name__ == "__main__":
    raise SystemExit(main())
