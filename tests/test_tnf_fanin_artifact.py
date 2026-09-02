#!/usr/bin/env python3
"""Conformance test for direct TNF, int4, and int8 unrolled dot trees."""

from fractions import Fraction
from pathlib import Path
import random
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "oracle"))
import tnf_ref  # noqa: E402


FANINS = (8, 16, 32, 64)
CASES = 96
FMT = tnf_ref.TNFFormat(exp_trits=4, mant_bits=8)
TNF_RTL = ROOT / "rtl" / "tnf_dot_tree.v"
INT_RTL = ROOT / "rtl" / "signed_int_dot.v"


def packed(values, width):
    out = 0
    mask = (1 << width) - 1
    for index, value in enumerate(values):
        out |= (value & mask) << (index * width)
    return out


def apply_weight(raw, weight):
    if weight in (0, 3):
        return 0
    if weight == 1:
        return raw
    return raw ^ (1 << FMT.sign_shift)


def tnf_tree(samples, weights):
    level = [apply_weight(x, w) for x, w in zip(samples, weights)]
    while len(level) > 1:
        level = [tnf_ref.tef_add(FMT, level[i], level[i + 1])
                 for i in range(0, len(level), 2)]
    return level[0]


def random_tnf(rng):
    sign = rng.randrange(2)
    offset = rng.randrange(1, FMT.offset_max)
    mantissa = rng.randrange(1 << FMT.mant_bits)
    return ((sign << FMT.sign_shift)
            | (offset << FMT.exp_shift) | mantissa)


def signed(raw, width):
    return raw - (1 << width) if raw & (1 << (width - 1)) else raw


def write_tnf_vectors(path, fanin):
    rng = random.Random(0x544E4600 + fanin)
    rows = []
    one = tnf_ref.encode(FMT, Fraction(1))
    directed_samples = [one] * fanin
    directed_weights = [1 if i % 3 else 2 for i in range(fanin)]
    rows.append((directed_samples, directed_weights))
    rows.append((directed_samples, [0] * fanin))
    rows.append((directed_samples, [3] * fanin))
    for _ in range(CASES - len(rows)):
        samples = [0 if rng.random() < 0.05 else random_tnf(rng)
                   for _ in range(fanin)]
        weights = [rng.randrange(4) for _ in range(fanin)]
        rows.append((samples, weights))
    path.write_text("".join(
        f"{packed(xs, 16):0{fanin*4}x} "
        f"{packed(ws, 2):0{(fanin*2+3)//4}x} "
        f"{tnf_tree(xs, ws):04x}\n"
        for xs, ws in rows
    ), encoding="ascii")


def write_int_vectors(path, fanin, width):
    rng = random.Random(0x1A700000 + 256 * width + fanin)
    rows = []
    lo, hi = -(1 << (width - 1)), (1 << (width - 1)) - 1
    rows.append(([hi] * fanin, [hi] * fanin))
    rows.append(([lo] * fanin, [lo] * fanin))
    rows.append(([lo if i & 1 else hi for i in range(fanin)], [1] * fanin))
    for _ in range(CASES - len(rows)):
        rows.append(([rng.randint(lo, hi) for _ in range(fanin)],
                     [rng.randint(lo, hi) for _ in range(fanin)]))
    mask = (1 << 32) - 1
    path.write_text("".join(
        f"{packed(xs, width):0{(fanin*width+3)//4}x} "
        f"{packed(ws, width):0{(fanin*width+3)//4}x} "
        f"{sum(x*w for x, w in zip(xs, ws)) & mask:08x}\n"
        for xs, ws in rows
    ), encoding="ascii")


def simulate(tmp, *, kind, fanin, width=None):
    vector_file = tmp / f"{kind}-f{fanin}.txt"
    executable = tmp / f"{kind}-f{fanin}.vvp"
    if kind == "tnf":
        write_tnf_vectors(vector_file, fanin)
        command = [
            "iverilog", "-g2012", "-Wall", "-s", "tnf_fanin_tb",
            f"-Ptnf_fanin_tb.FANIN={fanin}", "-o", str(executable),
            str(ROOT / "rtl" / "tnf_weight_apply.v"),
            str(ROOT / "rtl" / "tnf_add_full.v"), str(TNF_RTL),
            str(ROOT / "tests" / "tnf_fanin_tb.v"),
        ]
    else:
        write_int_vectors(vector_file, fanin, width)
        command = [
            "iverilog", "-g2012", "-Wall", "-s", "int_fanin_tb",
            f"-Pint_fanin_tb.FANIN={fanin}",
            f"-Pint_fanin_tb.WIDTH={width}", "-o", str(executable),
            str(INT_RTL), str(ROOT / "tests" / "int_fanin_tb.v"),
        ]
    subprocess.run(command, cwd=ROOT, check=True)
    run = subprocess.run(["vvp", str(executable), f"+VECTORS={vector_file}"],
                         cwd=ROOT, text=True, capture_output=True)
    sys.stdout.write(run.stdout)
    sys.stderr.write(run.stderr)
    if run.returncode:
        raise SystemExit(run.returncode)


def main():
    missing = [p.relative_to(ROOT) for p in (TNF_RTL, INT_RTL) if not p.is_file()]
    if missing:
        print("FAIL: fan-in RTL is missing: " + ", ".join(map(str, missing)))
        return 1
    with tempfile.TemporaryDirectory(prefix="tnf-fanin-test-") as name:
        tmp = Path(name)
        for fanin in FANINS:
            simulate(tmp, kind="tnf", fanin=fanin)
            simulate(tmp, kind="int4", fanin=fanin, width=4)
            simulate(tmp, kind="int8", fanin=fanin, width=8)
    print(f"PASS: {len(FANINS)*3*CASES} fan-in checks across 12 arms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
