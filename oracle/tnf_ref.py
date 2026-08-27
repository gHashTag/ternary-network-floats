#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tnf_ref.py — parameterized bit-exact oracle for the WHOLE TNF ladder.

One oracle for every rung (TNF4 .. TNF1024): a GoldenFloat whose exponent is a
balanced-ternary number of `exp_trits` trits (offset in [0, 3^Et - 1], balanced
exponent e = offset - (3^Et-1)/2) and a `mant_bits` binary mantissa. No regime
decode; add/mul are decode -> exact Fraction -> re-encode (round-to-nearest-even).

Off-path conformance oracle (like gf_ref.py / tekum_ref.py). Supersedes the
single-width tnf16_ref.py (TNF16 == TNFFormat(4, 9)).

WIDTH NOTICE (2026-08-18, measured in conformance/true_width_ladder.py):
the LADDER keys below are NAMES, not stored widths. The exponent field needs
ceil(Et*log2 3) bits, so the stored widths are:

    TNF4=6b(+2)  TNF8=10b(+2)  TNF16=17b(+1)  TNF32=30b(-2)  TNF64=65b(+1)
    TNF128=129b  TNF256=258b   TNF512=514b    TNF1024=1025b

Not one rung stores the width in its name. Use stored_width(fmt) before any
"at N bits" comparison, or construct the stored-width-exact rungs directly:
TNFFormat(2,3) stores 8 bits, TNFFormat(4,8) 16, TNFFormat(4,24) 32. (The
TRUE_LADDER dictionary that once held them was retired by the versioned
ladders in tnf_ladder_versions.py, which version the NOMINAL budget instead.) Measured consequence of the misnaming: the sign of the advantage
over takum followed the sign of the width excess (+2 bits: 484x; +1: 2x;
-2: 0.08x), and at true width with range to spare the advantage is 1.00x.
"""

from fractions import Fraction
from dataclasses import dataclass
import math


def _floor_log2(fr: Fraction) -> int:
    # pure-integer floor(log2) for a positive Fraction (no float -> no overflow
    # even for the >1000-decade wide rungs).
    e = fr.numerator.bit_length() - fr.denominator.bit_length()
    if (Fraction(1) * (1 << e) if e >= 0 else Fraction(1, 1 << -e)) > fr:
        e -= 1
    while (Fraction(1) * (1 << (e + 1)) if e + 1 >= 0 else Fraction(1, 1 << -(e + 1))) <= fr:
        e += 1
    return e


def _pow2(e: int) -> Fraction:
    return Fraction(1) * (1 << e) if e >= 0 else Fraction(1, 1 << -e)


@dataclass(frozen=True)
class TNFFormat:
    exp_trits: int
    mant_bits: int

    @property
    def offset_max(self): return 3 ** self.exp_trits - 1          # reserved special row
    @property
    def exp_offset(self): return (3 ** self.exp_trits - 1) // 2   # balanced zero point
    @property
    def mant(self): return 1 << self.mant_bits
    @property
    def exp_bits(self):
        """Bits the offset field actually occupies."""
        return self.offset_max.bit_length()

    @property
    def sign_shift(self):
        # Derived, not fixed. This was hardcoded to 24 — "room for wide exp/mant" —
        # which holds only while the payload stays below that bit. At mant_bits of
        # 21 or 25 the exponent field reaches bit 24 and the sign lands inside the
        # payload: encoding 1.5 through TNF32 returned -1.5. Wider mantissas were
        # corrupted too, silently, whenever bit 24 of the significand happened to
        # be set — which is why a spot check on 1.5 passed at mant_bits=52.
        #
        # The commutativity check the ladder relies on cannot see this: an inverted
        # sign survives on both sides of a + b == b + a. A round-trip assertion
        # catches it in one line.
        return self.mant_bits + self.exp_bits
    @property
    def exp_shift(self): return self.mant_bits
    @property
    def inf(self): return self.offset_max << self.exp_shift
    def range_decades(self): return 2 * self.exp_offset * math.log10(2)


def encode(fmt: TNFFormat, value) -> int:
    if value == 0:
        return 0
    sign = 1 if value < 0 else 0
    av = abs(Fraction(value))
    e = _floor_log2(av)
    offset = e + fmt.exp_offset
    if offset >= fmt.offset_max:
        return (sign << fmt.sign_shift) | fmt.inf
    if offset < 1:
        # Underflow.  There are no subnormals in this encoding: the only two
        # representable neighbours of an underflowing magnitude are zero and the
        # smallest normal 2^(1-exp_offset).  Round to nearest between them, ties
        # to zero, and keep the sign.  Clamping the offset and continuing (as an
        # earlier revision did) makes `frac` negative, which produces a negative
        # code word and therefore a silently wrong sign and magnitude on decode.
        min_normal = _pow2(1 - fmt.exp_offset)
        if av * 2 <= min_normal:
            return sign << fmt.sign_shift
        return (sign << fmt.sign_shift) | (1 << fmt.exp_shift)
    frac = av / _pow2(e) - 1
    scaled = frac * fmt.mant
    fl = int(scaled)
    rem = scaled - fl
    if rem > Fraction(1, 2) or (rem == Fraction(1, 2) and (fl & 1)):
        fl += 1
    if fl == fmt.mant:
        fl = 0
        offset += 1
        if offset >= fmt.offset_max:
            return (sign << fmt.sign_shift) | fmt.inf
    return (sign << fmt.sign_shift) | (offset << fmt.exp_shift) | fl


def is_special(fmt: TNFFormat, raw: int) -> bool:
    # >= rather than ==: the exponent field is ceil(Et*log2 3) bits wide, so it can
    # hold offsets the Et trits cannot name. Offsets above offset_max have no
    # balanced-ternary preimage and are not members of the format.
    return ((raw >> fmt.exp_shift) & ((1 << fmt.exp_bits) - 1)) >= fmt.offset_max


def decode(fmt: TNFFormat, raw: int):
    sign = (raw >> fmt.sign_shift) & 1
    offset = (raw >> fmt.exp_shift) & ((1 << fmt.exp_bits) - 1)
    m = raw & (fmt.mant - 1)
    if offset > fmt.offset_max:
        # Unencodable: four trits reach 81 of the 128 codes a 7-bit field holds, and
        # decoding the other 47 as normal numbers is what inflated the value counts
        # and the binade span of every TNF row in the matched-width comparison.
        return math.nan
    if offset == fmt.offset_max:
        return math.nan if m else (-math.inf if sign else math.inf)
    if offset == 0:
        return Fraction(0)
    val = (Fraction(1) + Fraction(m, fmt.mant)) * _pow2(offset - fmt.exp_offset)
    return -val if sign else val


def tef_add(fmt: TNFFormat, a: int, b: int) -> int:
    if is_special(fmt, a) or is_special(fmt, b):
        return (fmt.offset_max << fmt.exp_shift) | 1
    return encode(fmt, decode(fmt, a) + decode(fmt, b))


def tef_mul(fmt: TNFFormat, a: int, b: int) -> int:
    if is_special(fmt, a) or is_special(fmt, b):
        return (fmt.offset_max << fmt.exp_shift) | 1
    return encode(fmt, decode(fmt, a) * decode(fmt, b))


# Ladder rungs (exp_trits, mant_bits) per nominal width, by version.
#
# The dictionary that shipped first used the research-note mantissas, seven of
# which do not satisfy the width rule the specification states, 1+E_t+M=N.
# Repairing it in place would change every conformance vector and every
# published digest, so both ladders stay addressable and the caller says which
# one it means.  See tnf_ladder_versions.py for the table and the deltas.
from tnf_ladder_versions import (  # noqa: E402
    LADDER_V1_RESEARCH, LADDER_V2_SPEC, DEFAULT_LADDER_VERSION,
    VECTOR_SPEC_VERSION, width_rule_report,
)


def _mk(table):
    return {w: TNFFormat(t, m) for w, (t, m) in table.items()}


LADDER_RESEARCH = _mk(LADDER_V1_RESEARCH)   # frozen, byte-compatible with v1
LADDER_SPEC = _mk(LADDER_V2_SPEC)           # satisfies 1+E_t+M=N on every rung

LADDERS = {"v1-research": LADDER_RESEARCH, "v2-spec": LADDER_SPEC}


def get_ladder(version: str = DEFAULT_LADDER_VERSION):
    if version not in LADDERS:
        raise KeyError(f"unknown ladder version {version!r}; "
                       f"have {sorted(LADDERS)}")
    return LADDERS[version]


# `LADDER` keeps pointing at the research widths so that existing transcripts
# stay reproducible.  New work should call get_ladder() explicitly.
LADDER = LADDER_RESEARCH


def _selftest():
    import random
    rnd = random.Random(1)
    print(f"{'rung':>6} {'Et':>3} {'M':>5} {'range(dec)':>11} {'add/mul commute (5k pairs)':>28}")
    for w, f in LADDER.items():
        bad = 0
        klim = max(1, int(f.exp_offset * 0.29))
        def rv():
            k = rnd.randint(-klim, klim)
            m = Fraction(rnd.randint(0, f.mant if f.mant_bits < 30 else (1 << 30)), (f.mant if f.mant_bits < 30 else (1 << 30)))
            s = 1 if rnd.random() < .5 else -1
            return s * (Fraction(1) + m) * (Fraction(2) ** k)
        for _ in range(3000):
            x, y = rv(), rv()
            if tef_add(f, encode(f, x), encode(f, y)) != tef_add(f, encode(f, y), encode(f, x)):
                bad += 1
            if tef_mul(f, encode(f, x), encode(f, y)) != tef_mul(f, encode(f, y), encode(f, x)):
                bad += 1
        print(f"TNF{w:<4} {f.exp_trits:>3} {f.mant_bits:>5} {f.range_decades():11.0f} {('%d violations' % bad):>28}")
    F16 = LADDER[16]
    assert abs(float(decode(F16, tef_mul(F16, encode(F16, 1.5), encode(F16, 2.0)))) - 3.0) < 1e-2
    print("TNF16 1.5*2.0 =", float(decode(F16, tef_mul(F16, encode(F16, 1.5), encode(F16, 2.0)))))
    _width_rule_check()
    _roundtrip_check()


def _width_rule_check():
    """Print the rule per rung.  v2 must satisfy it everywhere; v1 must not be
    silently claimed to."""
    print("\nwidth rule 1+E_t+M=N")
    for r in width_rule_report():
        assert r["v2_sum"] == r["width"]
        print(f"  TNF{r['width']:<5} v1 sum {r['v1_sum']:>5} "
              f"{'ok' if r['v1_ok'] else 'VIOLATES'};  v2 sum {r['v2_sum']:>5} ok")


def _roundtrip_check():
    """Sign survival and encode->decode->encode fixpoint on both ladders.

    The commutativity check cannot see an inverted sign: it survives on both
    sides of a+b == b+a.  This one line is what caught the hardcoded sign_shift.
    """
    print("\nround-trip (sign survival + encode fixpoint)")
    from fractions import Fraction as F
    probes = [F(3, 2), F(-3, 2), F(1), F(-1), F(5, 4), F(-5, 4), F(7, 8), F(-7, 8)]
    for name, lad in LADDERS.items():
        bad = 0
        for w, f in lad.items():
            for v in probes:
                r = encode(f, v)
                d = decode(f, r)
                if (d < 0) != (v < 0):
                    bad += 1
                if encode(f, d) != r:
                    bad += 1
        print(f"  {name:<12} {bad} violations over "
              f"{len(lad) * len(probes)} probes")
        assert bad == 0, (name, bad)
    print(f"\nvector spec version: {VECTOR_SPEC_VERSION}")


if __name__ == "__main__":
    _selftest()
