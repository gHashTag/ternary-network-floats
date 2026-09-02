#!/usr/bin/env python3
"""
Generate a bit-precise MXFP4 E2M1 conformance vector pack in the SAME row
schema as the GF16 / FP8 packs.

E2M1 (OCP Microscaling MXFP4 element format) semantics:
  * 1 sign, 2 exponent, 1 mantissa bit. 4 bits total -> only 16 codes.
  * bias = 1.
  * NO inf, NO NaN (the MX *element* format carries neither; the block scale
    handles dynamic range, the element is a pure finite 4-bit value).
  * Subnormals: exponent field 0. value = (M/2) * 2^(1-1) = (M/2) * 1 = M*0.5
    -> the only subnormal magnitude is 0.5 (M=1, E=0).
  * Normals: value = (1 + M/2) * 2^(E-1).
  * Full positive value set: 0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0 (and signed).
  * Max finite magnitude = 6.0 (S, E=11=3, M=1 -> 1.5 * 2^2).

The issue #7085 clamps to +/-7. Note 7.0 is NOT representable in E2M1; the
largest representable magnitude is 6.0. So a clamp bound of 7 is one E2M1 step
WIDER than the format max -- any pre-quantization clamp at +/-7 still leaves a
gap to the nearest grid point 6.0. This pack enumerates the full 16-code grid
so the clamp-vs-grid relationship is explicit. 3.0 (the anchor) is an exact
grid point at bits 0x6.
"""
import json, struct

def f64_hex(x):
    return "0x" + struct.pack(">d", x).hex().upper()

def decode_e2m1(bits):
    """bits: int 0..15 -> (value, category)"""
    s = (bits >> 3) & 1
    e = (bits >> 1) & 0x3
    m = bits & 0x1
    sign = -1.0 if s else 1.0
    if e == 0:
        if m == 0:
            return (sign * 0.0, "zero")
        return (sign * 0.5, "subnormal")     # (1/2)*2^0
    val = sign * (1.0 + m / 2.0) * (2.0 ** (e - 1))
    return (val, "normal")

def make_vector(name, bits):
    val, cat = decode_e2m1(bits)
    return {
        "name": name,
        "input_f64": val,
        "input_f64_hex": f64_hex(val),
        "mxfp4_bits_hex": "0x%X" % bits,
        "mxfp4_bits_int": bits,
        "decoded_f64": val,
        "decoded_f64_hex": f64_hex(val),
        "abs_error": 0.0,
        "category": cat,
    }

# Enumerate the full 16-code grid (4-bit format -> exhaustive is tiny + ideal).
labels = {
    0x0: "pos_zero",   0x1: "pos_half",  0x2: "pos_one",   0x3: "pos_onehalf",
    0x4: "pos_two",    0x5: "pos_three", 0x6: "pos_four",  0x7: "pos_six",
    0x8: "neg_zero",   0x9: "neg_half",  0xA: "neg_one",   0xB: "neg_onehalf",
    0xC: "neg_two",    0xD: "neg_three", 0xE: "neg_four",  0xF: "neg_six",
}
vectors = [make_vector(labels[b], b) for b in range(16)]

# Anchor 3.0: bits 0x5 (E=10=2, M=1 -> 1.5*2 = 3.0).
three = decode_e2m1(0x5)[0]
anchor_ok = (three == 3.0)
maxfinite = decode_e2m1(0x7)[0]  # 6.0

pack = {
    "schema": "t27-conformance/v0.1",
    "format": "MXFP4_E2M1",
    "format_notes": "OCP Microscaling element format. 1s2e1m, bias 1, 16 codes, no inf, no NaN. Value grid +/-{0,0.5,1.0,1.5,2.0,3.0,4.0,6.0}. Max finite 6.0 at bits 0x7.",
    "ssot": "https://github.com/gHashTag/t27/blob/master/conformance/FORMAT-SPEC-001.json",
    "preprint": "https://arxiv.org/abs/2606.05017",
    "anchor_identity": "phi^2 + 1/phi^2 = 3",
    "anchor_check": {
        "value": three,
        "expected": 3.0,
        "ieee754_exact": anchor_ok,
        "mxfp4_bits_hex": "0x5",
    },
    "clamp_note": "tt-mlir#7085 clamps to +/-7. E2M1 max finite is 6.0; 7.0 is NOT a grid point. A clamp bound of 7 sits one step above the format max, so values in (6,7] still round to the 6.0 grid point under round-nearest. The clamp bound and the representable max are not the same number -- this enumeration makes that explicit.",
    "round_trip_policy": "decode: exact bits->f64 (all 16 codes, abs_error 0). encode: round-nearest-ties-even onto the 8-magnitude grid; there is no inf/NaN, so out-of-range maps to nearest finite grid point (+/-6.0).",
    "n_vectors": len(vectors),
    "max_finite": maxfinite,
    "vectors": vectors,
}

with open("vectors/mxfp4_e2m1_conformance_v0.json", "w") as f:
    json.dump(pack, f, indent=2)

print("Wrote vectors/mxfp4_e2m1_conformance_v0.json")
print("n_vectors:", len(vectors), "(full 4-bit grid)")
print("anchor 3.0 exact:", anchor_ok, "at bits 0x5")
print("max finite:", maxfinite, "at bits 0x7 (clamp bound 7 > grid max 6.0)")
print("full positive grid:", sorted(set(decode_e2m1(b)[0] for b in range(8))))
