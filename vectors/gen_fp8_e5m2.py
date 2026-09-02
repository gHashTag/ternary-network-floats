#!/usr/bin/env python3
"""
Generate a bit-precise FP8 E5M2 conformance vector pack in the SAME row
schema as the GF16 / E4M3FN packs.

E5M2 (OCP / torch.float8_e5m2) semantics:
  * 1 sign, 5 exponent, 2 mantissa bits. bias = 15.
  * IEEE-754-style: HAS infinity (E=11111, M=00 -> +/-Inf).
  * NaN: E=11111, M != 00 (so 0x7D/0x7E/0x7F and signed copies are NaN).
  * Max finite magnitude = 57344.0 (S=0, E=11110=30, M=11 -> 1.75 * 2^15).
  * Subnormals: exponent field 0, value = (M/4) * 2^(1-15) = (M/4) * 2^-14.
  * Smallest positive subnormal = 2^-16 = 1.52587890625e-05.
  * Smallest positive normal = 2^-14 = 6.103515625e-05.

Decode is exact into f64. Encode (reference) is round-nearest-ties-even with
overflow to +/-Inf (true IEEE behaviour for E5M2, in contrast to the E4M3FN
saturate-to-448 policy). That overflow-to-Inf vs saturate difference between
the two FP8 variants is the practical round-trip gotcha for host construction.
"""
import json, struct, math

def f64_hex(x):
    return "0x" + struct.pack(">d", x).hex().upper()

def decode_e5m2(bits):
    """bits: int 0..255 -> (value_or_special, category)"""
    s = (bits >> 7) & 1
    e = (bits >> 2) & 0x1F
    m = bits & 0x3
    sign = -1.0 if s else 1.0
    if e == 0x1F:
        if m == 0:
            return (sign * math.inf, "inf")
        return (math.nan, "nan")
    if e == 0:
        if m == 0:
            return (sign * 0.0, "zero")
        val = sign * (m / 4.0) * (2.0 ** -14)   # subnormal
        return (val, "subnormal")
    val = sign * (1.0 + m / 4.0) * (2.0 ** (e - 15))
    return (val, "normal")

def make_vector(name, bits, category_override=None):
    val, cat = decode_e5m2(bits)
    if category_override:
        cat = category_override
    is_nan = isinstance(val, float) and math.isnan(val)
    is_inf = isinstance(val, float) and math.isinf(val)
    if is_nan:
        input_f64 = "NaN"; decoded_f64 = "NaN"
        input_hex = "0x7FF8000000000000"; decoded_hex = "0x7FF8000000000000"
        abs_err = "NaN"
    elif is_inf:
        sign_txt = "-Inf" if val < 0 else "Inf"
        input_f64 = sign_txt; decoded_f64 = sign_txt
        input_hex = f64_hex(val); decoded_hex = f64_hex(val)
        abs_err = 0.0
    else:
        input_f64 = val; decoded_f64 = val
        input_hex = f64_hex(val); decoded_hex = f64_hex(val)
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

# Curated set covering the E5M2 failure surfaces: signed zeros, subnormal
# flush boundary, smallest normal, unit + small ints, max finite vs Inf vs
# NaN, sign symmetry. 3.0 anchor lands at bits 0x42.
selected = [
    ("pos_zero",            0x00),
    ("neg_zero",            0x80),
    ("min_pos_subnormal",   0x01),  # 2^-16
    ("max_pos_subnormal",   0x03),  # (3/4)*2^-14
    ("min_pos_normal",      0x04),  # 2^-14
    ("pos_half",            0x38),  # 0.5
    ("pos_one",             0x3C),  # 1.0
    ("neg_one",             0xBC),  # -1.0
    ("pos_two",             0x40),  # 2.0
    ("pos_three",           0x42),  # 3.0 (anchor: phi^2 + 1/phi^2 = 3)
    ("pos_six",             0x46),  # 6.0
    ("max_finite_pos",      0x7B),  # 57344.0 (E=11110, M=11)
    ("max_finite_neg",      0xFB),  # -57344.0
    ("pos_inf",             0x7C),  # +Inf (E=11111, M=00)
    ("neg_inf",             0xFC),  # -Inf
    ("nan",                 0x7D),  # NaN (E=11111, M!=00)
]

vectors = [make_vector(n, b) for (n, b) in selected]

three = decode_e5m2(0x42)[0]
anchor_ok = (three == 3.0)

pack = {
    "schema": "t27-conformance/v0.1",
    "format": "FP8_E5M2",
    "format_notes": "OCP / torch.float8_e5m2. 1s5e2m, bias 15, HAS inf (E=11111,M=00), NaN (E=11111,M!=00), max finite 57344.0 at 0x7B. Subnormal min 2^-16, normal min 2^-14.",
    "ssot": "https://github.com/gHashTag/t27/blob/master/conformance/FORMAT-SPEC-001.json",
    "preprint": "https://arxiv.org/abs/2606.05017",
    "anchor_identity": "phi^2 + 1/phi^2 = 3",
    "anchor_check": {
        "value": three,
        "expected": 3.0,
        "ieee754_exact": anchor_ok,
        "fp8_bits_hex": "0x42",
    },
    "round_trip_policy": "decode: exact bits->f64. encode (reference): round-nearest-ties-even, overflow goes to +/-Inf (IEEE), NOT saturate. This is the variant-level divergence from E4M3FN (which saturates to 448.0). The overflow-to-Inf vs saturate split is the practical round-trip gotcha across the two FP8 variants.",
    "n_vectors": len(vectors),
    "vectors": vectors,
}

with open("vectors/fp8_e5m2_conformance_v0.json", "w") as f:
    json.dump(pack, f, indent=2)

print("Wrote vectors/fp8_e5m2_conformance_v0.json")
print("n_vectors:", len(vectors))
print("anchor 3.0 exact:", anchor_ok, "decoded:", three)
for n, b in [("min_pos_subnormal",0x01),("max_pos_subnormal",0x03),
             ("min_pos_normal",0x04),("max_finite_pos",0x7B),
             ("pos_inf",0x7C),("nan",0x7D)]:
    v,c = decode_e5m2(b)
    print(f"  {n}: bits=0x{b:02X} -> {v} ({c})")
