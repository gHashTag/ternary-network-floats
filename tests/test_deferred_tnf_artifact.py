#!/usr/bin/env python3
"""Exact-oracle regression for a one-rounding packed-TNF dot product."""

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
RTL = (ROOT / "rtl" / "tnf_deferred_dot.v",
       ROOT / "rtl" / "tnf_exact_to_packed.v")


def packed(values, width):
    word = 0
    mask = (1 << width) - 1
    for index, value in enumerate(values):
        word |= (value & mask) << (index * width)
    return word


def random_finite(rng):
    if rng.random() < 0.06:
        return 0
    return ((rng.randrange(2) << FMT.sign_shift)
            | (rng.randrange(1, FMT.offset_max) << FMT.exp_shift)
            | rng.randrange(1 << FMT.mant_bits))


def expected(samples, weights):
    total = Fraction(0)
    for raw, weight in zip(samples, weights):
        if weight in (0, 3):
            continue
        if tnf_ref.is_special(FMT, raw):
            return (FMT.offset_max << FMT.exp_shift) | 1
        value = tnf_ref.decode(FMT, raw)
        total += value if weight == 1 else -value
    return tnf_ref.encode(FMT, total)


def rows(fanin):
    rng = random.Random(0x44454600 + fanin)
    one = tnf_ref.encode(FMT, Fraction(1))
    min0 = (1 << FMT.exp_shift)
    min1 = min0 | 1
    special = (FMT.offset_max << FMT.exp_shift) | 7
    out = [
        ([one] * fanin, [1 if i & 1 else 2 for i in range(fanin)]),
        ([one] * fanin, [1] * fanin),
        ([min1, min0] + [0] * (fanin - 2),
         [1, 2] + [0] * (fanin - 2)),
        ([special] + [0] * (fanin - 1), [1] + [0] * (fanin - 1)),
        ([special] + [0] * (fanin - 1), [0] * fanin),
    ]
    while len(out) < CASES:
        out.append(([random_finite(rng) for _ in range(fanin)],
                    [rng.randrange(4) for _ in range(fanin)]))
    return out


def run_arm(tmp, fanin):
    vector_file = tmp / f"deferred-f{fanin}.txt"
    executable = tmp / f"deferred-f{fanin}.vvp"
    vector_file.write_text("".join(
        f"{packed(xs, 16):0{fanin*4}x} "
        f"{packed(ws, 2):0{(fanin*2+3)//4}x} "
        f"{expected(xs, ws):04x}\n"
        for xs, ws in rows(fanin)
    ), encoding="ascii")
    subprocess.run([
        "iverilog", "-g2012", "-Wall", "-s", "tnf_deferred_fanin_tb",
        f"-Ptnf_deferred_fanin_tb.FANIN={fanin}", "-o", str(executable),
        *(str(path) for path in RTL),
        str(ROOT / "tests" / "tnf_deferred_fanin_tb.v"),
    ], cwd=ROOT, check=True)
    result = subprocess.run(
        ["vvp", str(executable), f"+VECTORS={vector_file}"],
        cwd=ROOT, text=True, capture_output=True
    )
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    if result.returncode:
        raise SystemExit(result.returncode)


def main():
    missing = [path.relative_to(ROOT) for path in RTL if not path.is_file()]
    if missing:
        print("FAIL: deferred TNF RTL is missing: " +
              ", ".join(map(str, missing)))
        return 1
    with tempfile.TemporaryDirectory(prefix="tnf-deferred-test-") as name:
        tmp = Path(name)
        for fanin in FANINS:
            run_arm(tmp, fanin)
    print(f"PASS: {len(FANINS)*CASES} deferred-TNF checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
