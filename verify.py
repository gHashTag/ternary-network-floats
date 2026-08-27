#!/usr/bin/env python3
"""Recompute the numbers this paper reports, from the oracle, and fail loudly.

Every check below corresponds to a claim in the paper. Run it and the paper's
matched-width table is either reproduced or the script exits non-zero. There is
no third outcome and nothing is quoted from a record file.
"""
import math, bisect, dataclasses, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "oracle"))
import tnf_ref as m

FAIL = []

def check(name, got, want, tol=0):
    ok = abs(got - want) <= tol if isinstance(want, (int, float)) else got == want
    print(f"  [{'ok ' if ok else 'FAIL'}] {name}: {got} (expected {want})")
    if not ok:
        FAIL.append(name)

def rung(exp_trits, mant_bits):
    """Enumerate a rung and return (values, binades, step_at_unity_pct)."""
    base = m.LADDER[{2: 4, 3: 8, 4: 16}[exp_trits]]
    f = dataclasses.replace(base, mant_bits=mant_bits)
    width = 1 + f.exp_bits + f.mant_bits
    seen = set()
    for raw in range(1 << width):
        v = m.decode(f, raw)
        if v is None:
            continue
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            continue
        if v != 0:
            seen.add(v)
    pos = sorted(x for x in seen if x > 0)
    i = bisect.bisect_left(pos, 1)
    lo, hi = pos[max(0, i - 1)], pos[min(len(pos) - 1, i)]
    return len(seen), math.log2(float(pos[-1]) / float(pos[0])), float(hi - lo) * 100

print("Table: matched physical width (paper, Section 'The result is negative')")
v19, b19, s19 = rung(4, 11)
check("TNF16 (4t,11m) values", v19, 323584)
check("TNF16 (4t,11m) binades", round(b19, 1), 79.0)
check("TNF16 (4t,11m) step at 1.0 (%)", round(s19, 3), 0.024)
check("TNF16 unreachable of 2^19", 2**19 - v19, 200704)

v10, b10, s10 = rung(3, 4)
check("TNF8 (3t,4m) values", v10, 800)
check("TNF8 (3t,4m) binades", round(b10, 1), 25.0)

v6, b6, s6 = rung(2, 1)
check("TNF4 (2t,1m) values", v6, 28)

print("\nRatios the paper states (posit19 es=1 steps 0.002%, posit10 0.781%, posit6 12.5%)")
check("posit finer at 19 bits, times", round(s19 / 0.002), 12)
check("posit finer at 10 bits, times", round(s10 / 0.781), 4)
check("posit finer at 6 bits, times", round(s6 / 12.5), 2)

print("\nThe exponent field: four trits name 81 of the 128 codes 7 bits hold")
f16 = m.LADDER[16]
check("offset_max is 3^4 - 1", f16.offset_max, 3**4 - 1)
check("exponent field width", f16.exp_bits, 7)
check("codes the field holds", 2**f16.exp_bits, 128)

print("\nOne-adder family: the roots of r^d = r+1 descend towards 1")
def root(d, lo=1.000001, hi=3.0):
    f = lambda r: r**d - r - 1
    for _ in range(300):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2
check("root at degree 9", round(root(9), 7), 1.0850702)
check("root at degree 27", round(root(27), 7), 1.0265049)
check("degree 27 within 0.05% of 1.026159",
      round(100 * abs(root(27) - 1.026159) / 1.026159, 3) < 0.05, True)

print("\nNode area (paper, Table 'A complete ternary neuron')")
node = [(8, 82.5, 28.0, 109.35, 87.29), (16, 87.1, 33.1, 91.43, 73.42),
        (32, 119.0, 33.2, 66.53, 58.22)]
area = [a0 / a1 for _, a0, a1, _, _ in node]
tput = [(q1 / a1) / (q0 / a0) for _, a0, a1, q0, q1 in node]
check("area falls, min times", round(min(area), 1), 2.6)
check("area falls, max times", round(max(area), 1), 3.6)
check("throughput per area, min times", round(min(tput), 1), 2.1)
check("throughput per area, max times", round(max(tput), 1), 3.1)

print()
if FAIL:
    print(f"FAILED: {len(FAIL)} check(s): {', '.join(FAIL)}")
    sys.exit(1)
print("All checks reproduce the paper.")
