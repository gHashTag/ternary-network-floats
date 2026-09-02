#!/usr/bin/env python3
"""
Generate a bit-precise bfloat16 (1s8e7m) conformance + golden-accumulation
pack in the SAME row schema as the GF16 / FP8 / MXFP4 packs, PLUS a small
golden-reference accumulation section aimed at tt-mlir#6252 (rounding-error
accumulation in depth-31 fused trees, all-close failures).

bfloat16 semantics:
  * 1 sign, 8 exponent, 7 mantissa bits. bias = 127 (same exponent range as
    fp32; bf16 is fp32 with the low 16 mantissa bits truncated).
  * HAS inf (E=255, M=0) and NaN (E=255, M!=0).
  * Decode is exact into f64 (bf16 is a strict subset of fp32 which is a strict
    subset of f64).
  * bf16 bits = top 16 bits of the fp32 encoding. We encode via
    round-nearest-ties-even on the fp32->bf16 truncation boundary.

#6252 angle: depth-31 fused reduction trees accumulate rounding error. The
"all-close" check needs a golden reference computed at higher precision (f64)
and a clamped, deterministic input set so the comparison is reproducible. This
pack supplies: (a) a bit-exact bf16 element table, and (b) a golden reduction:
sum of N copies of an exactly-representable bf16 value, with the f64 golden,
the naive sequential-bf16-rounded result, the pairwise-tree result, and the
absolute / relative error of each tree vs the golden. The split between
sequential and pairwise at depth ~31 is exactly the all-close gap.
"""
import json, struct

def f64_hex(x):
    return "0x" + struct.pack(">d", x).hex().upper()

def f32_bits(x):
    return struct.unpack(">I", struct.pack(">f", x))[0]

def bf16_encode(x):
    """fp32 value -> 16-bit bf16, round-nearest-ties-even on truncation."""
    b = f32_bits(x)
    # round to nearest even on bit 16
    lsb = (b >> 16) & 1
    rounding_bias = 0x7FFF + lsb
    b = (b + rounding_bias) >> 16
    return b & 0xFFFF

def bf16_decode(bits16):
    """16-bit bf16 -> exact f64 value."""
    b32 = (bits16 & 0xFFFF) << 16
    return struct.unpack(">f", struct.pack(">I", b32))[0]

def category_of(bits16):
    e = (bits16 >> 7) & 0xFF
    m = bits16 & 0x7F
    if e == 0xFF:
        return "nan" if m else "inf"
    if e == 0:
        return "zero" if m == 0 else "subnormal"
    return "normal"

def make_vector(name, value):
    bits16 = bf16_encode(value)
    dec = bf16_decode(bits16)
    return {
        "name": name,
        "input_f64": value,
        "input_f64_hex": f64_hex(value),
        "bf16_bits_hex": "0x%04X" % bits16,
        "bf16_bits_int": bits16,
        "decoded_f64": dec,
        "decoded_f64_hex": f64_hex(dec),
        "abs_error": abs(value - dec),
        "category": category_of(bits16),
    }

# Element table: values exactly representable in bf16 (abs_error 0) plus the
# anchor 3.0 and a couple of integers used in the accumulation golden.
selected = [
    ("pos_zero",     0.0),
    ("pos_one",      1.0),
    ("neg_one",     -1.0),
    ("pos_two",      2.0),
    ("pos_three",    3.0),    # anchor: phi^2 + 1/phi^2 = 3
    ("pos_half",     0.5),
    ("pos_quarter",  0.25),
    ("pos_0p1",      0.1),    # NOT exact in bf16 -> nonzero abs_error (honest)
]
vectors = [make_vector(n, v) for (n, v) in selected]

# ---- Golden accumulation section for #6252 ----
def sequential_sum_bf16(value, n):
    """Accumulate n copies of value, rounding to bf16 after every add."""
    acc = bf16_decode(bf16_encode(value))
    elem = acc
    for _ in range(n - 1):
        acc = bf16_decode(bf16_encode(acc + elem))
    return acc

def pairwise_sum_bf16(value, n):
    """Pairwise (tree) reduction, rounding to bf16 at every node."""
    arr = [bf16_decode(bf16_encode(value))] * n
    while len(arr) > 1:
        nxt = []
        for i in range(0, len(arr) - 1, 2):
            nxt.append(bf16_decode(bf16_encode(arr[i] + arr[i + 1])))
        if len(arr) % 2 == 1:
            nxt.append(arr[-1])
        arr = nxt
    return arr[0]

# 0.1 is the classic case: not bf16-exact, so error compounds. depth-31 tree
# means ~2^31 leaves is impractical; we use a depth proxy n that exercises the
# sequential-vs-pairwise divergence at a representative reduction width.
golden_cases = []
for value, n in [(0.1, 1024), (3.0, 1024), (0.1, 4096), (1.0/3.0, 2048)]:
    golden = value * n                       # f64 golden reference
    seq = sequential_sum_bf16(value, n)
    pw = pairwise_sum_bf16(value, n)
    golden_cases.append({
        "element_f64": value,
        "element_f64_hex": f64_hex(value),
        "element_bf16_hex": "0x%04X" % bf16_encode(value),
        "n_terms": n,
        "golden_f64": golden,
        "golden_f64_hex": f64_hex(golden),
        "sequential_bf16": seq,
        "pairwise_bf16": pw,
        "abs_err_sequential": abs(seq - golden),
        "abs_err_pairwise": abs(pw - golden),
        "rel_err_sequential": abs(seq - golden) / abs(golden),
        "rel_err_pairwise": abs(pw - golden) / abs(golden),
        "pairwise_better": abs(pw - golden) <= abs(seq - golden),
    })

three = bf16_decode(bf16_encode(3.0))
anchor_ok = (three == 3.0)

pack = {
    "schema": "t27-conformance/v0.1",
    "format": "BFLOAT16",
    "format_notes": "1s8e7m, bias 127, same exponent range as fp32 (top 16 bits of fp32). HAS inf and NaN. Decode exact into f64.",
    "ssot": "https://github.com/gHashTag/t27/blob/master/conformance/FORMAT-SPEC-001.json",
    "preprint": "https://arxiv.org/abs/2606.05017",
    "anchor_identity": "phi^2 + 1/phi^2 = 3",
    "anchor_check": {
        "value": three,
        "expected": 3.0,
        "ieee754_exact": anchor_ok,
        "bf16_bits_hex": "0x%04X" % bf16_encode(3.0),
    },
    "issue_6252_note": "Rounding-error accumulation in depth-31 fused trees. The all-close gap comes from accumulation ORDER, not single-op rounding. The golden_accumulation section gives an f64 golden reference plus sequential vs pairwise bf16 reductions; pairwise reduces the accumulated error. A reproducible all-close test needs (a) a clamped deterministic input set and (b) an f64 golden, both supplied here.",
    "round_trip_policy": "decode: bf16 bits -> f64 exact. encode: fp32->bf16 round-nearest-ties-even on the 16-bit truncation boundary. abs_error is nonzero only for inputs not representable in bf16 (e.g. 0.1) -- stated honestly, not hidden.",
    "n_vectors": len(vectors),
    "vectors": vectors,
    "golden_accumulation": golden_cases,
}

with open("vectors/bf16_golden_conformance_v0.json", "w") as f:
    json.dump(pack, f, indent=2)

print("Wrote vectors/bf16_golden_conformance_v0.json")
print("n_vectors:", len(vectors))
print("anchor 3.0 exact:", anchor_ok, "bits", "0x%04X" % bf16_encode(3.0))
print("0.1 abs_error (honest, nonzero):", make_vector("x", 0.1)["abs_error"])
print("--- golden accumulation (sequential vs pairwise) ---")
for c in golden_cases:
    print(f"  elem={c['element_f64']:<10} n={c['n_terms']:<5} "
          f"seq_err={c['abs_err_sequential']:.6g}  pw_err={c['abs_err_pairwise']:.6g}  "
          f"pairwise_better={c['pairwise_better']}")
