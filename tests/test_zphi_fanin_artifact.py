#!/usr/bin/env python3
"""Exact integer-oracle regression for the Z[phi] pair dot tree."""

from pathlib import Path
import random
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / "rtl" / "zphi_dot_tree.v"
FANINS = (8, 16, 32, 64)
COORD_W = 16
CASES = 96


def packed(values, width):
    out = 0
    mask = (1 << width) - 1
    for index, value in enumerate(values):
        out |= (value & mask) << (index * width)
    return out


def transform(a, b, weight):
    if weight in (0, 3):
        return 0, 0
    out_a, out_b = b, a + b
    return (out_a, out_b) if weight == 1 else (-out_a, -out_b)


def rows(fanin):
    rng = random.Random(0x5A504849 + fanin)
    lo, hi = -(1 << (COORD_W-1)), (1 << (COORD_W-1)) - 1
    out = [
        ([hi] * fanin, [hi] * fanin, [1] * fanin),
        ([lo] * fanin, [lo] * fanin, [2] * fanin),
        ([hi if i & 1 else lo for i in range(fanin)],
         [lo if i & 1 else hi for i in range(fanin)], [1] * fanin),
        ([1] * fanin, [0] * fanin, [i % 4 for i in range(fanin)]),
    ]
    while len(out) < CASES:
        out.append(([rng.randint(lo, hi) for _ in range(fanin)],
                    [rng.randint(lo, hi) for _ in range(fanin)],
                    [rng.randrange(4) for _ in range(fanin)]))
    return out


def write_vectors(path, fanin):
    out_w = COORD_W + 1 + (fanin.bit_length() - 1)
    mask = (1 << out_w) - 1
    lines = []
    for aa, bb, ww in rows(fanin):
        pairs = [transform(a, b, w) for a, b, w in zip(aa, bb, ww)]
        ra = sum(x for x, _ in pairs)
        rb = sum(y for _, y in pairs)
        lines.append(
            f"{packed(aa, COORD_W):0{fanin*COORD_W//4}x} "
            f"{packed(bb, COORD_W):0{fanin*COORD_W//4}x} "
            f"{packed(ww, 2):0{(fanin*2+3)//4}x} "
            f"{ra & mask:0{(out_w+3)//4}x} "
            f"{rb & mask:0{(out_w+3)//4}x}\n"
        )
    path.write_text("".join(lines), encoding="ascii")


def run_arm(tmp, fanin):
    vectors = tmp / f"zphi-f{fanin}.txt"
    executable = tmp / f"zphi-f{fanin}.vvp"
    write_vectors(vectors, fanin)
    subprocess.run([
        "iverilog", "-g2012", "-Wall", "-s", "zphi_fanin_tb",
        f"-Pzphi_fanin_tb.FANIN={fanin}", "-o", str(executable),
        str(RTL), str(ROOT / "tests" / "zphi_fanin_tb.v"),
    ], cwd=ROOT, check=True)
    run = subprocess.run(["vvp", str(executable), f"+VECTORS={vectors}"],
                         cwd=ROOT, text=True, capture_output=True)
    print(run.stdout, end="")
    if run.returncode:
        raise SystemExit(run.returncode)


def main():
    if not RTL.is_file():
        print("FAIL: exact Z[phi] RTL is missing: rtl/zphi_dot_tree.v")
        return 1
    with tempfile.TemporaryDirectory(prefix="zphi-fanin-test-") as name:
        for fanin in FANINS:
            run_arm(Path(name), fanin)
    print("PASS: 384 exact-Zphi checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
