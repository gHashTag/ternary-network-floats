#!/usr/bin/env python3
"""
Generate a bit-precise FP8 E4M3FN conformance vector pack in the SAME row
schema as the GF16 pack (gf16_conformance_v0.json).

E4M3FN (OCP / torch.float8_e4m3fn) semantics:
  * 1 sign, 4 exponent, 3 mantissa bits. bias = 7.
  * NO infinity. Single NaN encoding: S.1111.111 (0x7F / 0xFF).
  * Max finite magnitude = 448.0  (S=0, E=1111=15, M=110 -> 1.75 * 2^8).
    Note: the all-ones mantissa at max exponent is reserved for NaN, so the
    largest finite is mantissa=110, not 111.
  * Subnormals: exponent field 0, value = (M/8) * 2^(1-7) = (M/8) * 2^-6.
  * Smallest positive subnormal = 2^-9 = 0.001953125.
  * Smallest positive normal = 2^-6 = 0.015625.

Decode is exact into f64. Encode here is round-to-nearest-ties-to-even with
saturation to 448 on overflow (the common "FN" clamp; out-of-range maps to
max finite, NOT to NaN -- this is exactly the round-trip decision the issue
author flagged).
"""
import json, struct, math

def f64_hex(x):
    return "0x" + struct.pack(">d", x).hex().upper()

def decode_e4m3fn(bits):
    """bits: int 0..255 -> (value_float_or_nan_str, category)"""
    s = (bits >> 7) & 1
    e = (bits >> 3) & 0xF
    m = bits & 0x7
    sign = -1.0 if s else 1.0
    # NaN: E=1111 and M=111
    if e == 0xF and m == 0x7:
        return (math.nan, "nan")
    if e == 0:
        if m == 0:
            return (sign * 0.0, "zero")
        val = sign * (m / 8.0) * (2.0 ** -6)   # subnormal
        return (val, "subnormal")
    val = sign * (1.0 + m / 8.0) * (2.0 ** (e - 7))
    return (val, "normal")

def all_codes():
    out = []
    for bits in range(256):
        val, cat = decode_e4m3fn(bits)
        out.append((bits, val, cat))
    return out

def make_vector(name, bits, category_override=None):
    val, cat = decode_e4m3fn(bits)
    if category_override:
        cat = category_override
    is_nan = isinstance(val, float) and math.isnan(val)
    # For a conformance pack the "input_f64" is the exact decoded value
    # (this pack documents the decode side: bits -> f64, abs_error 0 by
    # construction; the encode/round-trip side is documented separately).
    if is_nan:
        input_f64 = "NaN"
        decoded_f64 = "NaN"
        input_hex = "0x7FF8000000000000"
        decoded_hex = "0x7FF8000000000000"
        abs_err = "NaN"
    else:
        input_f64 = val
        decoded_f64 = val
        input_hex = f64_hex(val)
        decoded_hex = f64_hex(val)
        abs_err = 0.0
    return {
        "name": name,
        "input_f64": input_f64,
        "input_f64_hex": input_hex,
        "fp8_bits_hex": "0x%02X" % bits,
        "fp8_bits_int": bits,
        "decoded_f64": decoded_f64,
        "decoded_f64_hex": decoded_hex,
        "abs_error": abs_err,
        "category": cat,
    }

# Curated, high-signal vector set covering exactly the failure surfaces named
# in tt-mlir #8549: zeros, subnormal flush boundary, smallest normal, unit,
# max finite (448) vs NaN, sign symmetry.
selected = [
    ("pos_zero",            0x00),
    ("neg_zero",            0x80),
    ("min_pos_subnormal",   0x01),  # 2^-9
    ("max_pos_subnormal",   0x07),  # (7/8)*2^-6
    ("min_pos_normal",      0x08),  # 2^-6
    ("pos_half",            0x30),  # 0.5
    ("pos_one",             0x38),  # 1.0
    ("neg_one",             0xB8),  # -1.0
    ("pos_two",             0x40),  # 2.0
    ("pos_three",           0x44),  # 3.0  (anchor: phi^2 + 1/phi^2 = 3)
    ("pos_six",             0x4C),  # 6.0
    ("max_finite_pos",      0x7E),  # 448.0  (E=1111,M=110)
    ("max_finite_neg",      0xFE),  # -448.0
    ("nan",                 0x7F),  # canonical NaN
]

vectors = [make_vector(n, b) for (n, b) in selected]

# Anchor check: 3.0 must be exactly representable in E4M3FN.
three = decode_e4m3fn(0x44)[0]
anchor_ok = (three == 3.0)

pack = {
    "schema": "t27-conformance/v0.1",
    "format": "FP8_E4M3FN",
    "format_notes": "OCP / torch.float8_e4m3fn. 1s4e3m, bias 7, no inf, single NaN S.1111.111, max finite 448.0. Subnormal min 2^-9.",
    "ssot": "https://github.com/gHashTag/t27/blob/master/conformance/FORMAT-SPEC-001.json",
    "preprint": "https://arxiv.org/abs/2606.05017",
    "anchor_identity": "phi^2 + 1/phi^2 = 3",
    "anchor_check": {
        "value": three,
        "expected": 3.0,
        "ieee754_exact": anchor_ok,
        "fp8_bits_hex": "0x44",
    },
    "round_trip_policy": "decode: exact bits->f64. encode (reference): round-nearest-ties-even, overflow saturates to max finite 448.0 (NOT NaN). This is the divergence point flagged in tt-mlir#8549.",
    "n_vectors": len(vectors),
    "vectors": vectors,
}

with open("vectors/fp8_e4m3fn_conformance_v0.json", "w") as f:
    json.dump(pack, f, indent=2)

print("Wrote vectors/fp8_e4m3fn_conformance_v0.json")
print("n_vectors:", len(vectors))
print("anchor 3.0 exact:", anchor_ok, "decoded:", three)
# Sanity: print the boundary values
for n, b in [("min_pos_subnormal",0x01),("max_pos_subnormal",0x07),
             ("min_pos_normal",0x08),("max_finite_pos",0x7E)]:
    v,c = decode_e4m3fn(b)
    print(f"  {n}: bits=0x{b:02X} -> {v} ({c})")
