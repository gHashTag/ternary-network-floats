#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tnf_ladder_versions.py — versioned TNF ladder definitions.

Why this file exists
--------------------
`tnf_ref.py` shipped a single `LADDER` dictionary whose mantissa widths came
from the research note.  Seven of its nine rungs do not satisfy the width rule
the specification states, `1 + E_t + M = N`:

    rung      shipped (E_t, M)   1+E_t+M    N
    TNF16     (4,  9)            14         16
    TNF32     (5, 21)            27         32
    TNF64     (7, 52)            60         64
    TNF128    (8, 115)          124        128
    TNF256    (9, 242)          252        256
    TNF512    (10, 497)         508        512
    TNF1024   (11, 1006)       1018       1024

Silently repairing the dictionary would change every conformance vector and
therefore every published SHA-256 digest, so the repair is a *versioned* change
and both ladders stay addressable by name:

    LADDER_V1_RESEARCH  frozen, byte-compatible with what shipped
    LADDER_V2_SPEC      derived from the width rule, not typed in by hand

A conformance transcript is only meaningful together with the ladder version and
the digest of the vector file it was produced from.  `VECTOR_SPEC_VERSION` below
is what a transcript must quote.
"""

from dataclasses import dataclass

# The trit budget per nominal width is the design choice; the mantissa is then
# forced.  Nothing here is a free parameter, which is the point: a typo in a
# mantissa column cannot survive.
TRIT_BUDGET = {4: 2, 8: 3, 16: 4, 32: 6, 64: 7, 128: 8, 256: 9, 512: 10, 1024: 11}


def mantissa_from_rule(width: int, trits: int) -> int:
    """M = N - 1 - E_t.  One sign slot, E_t trit slots, the rest is mantissa."""
    return width - 1 - trits


def spec_ladder():
    """(width -> (E_t, M)) with every row satisfying 1 + E_t + M = N."""
    out = {}
    for w, t in TRIT_BUDGET.items():
        m = mantissa_from_rule(w, t)
        assert 1 + t + m == w, (w, t, m)
        assert m >= 1, (w, t, m)
        out[w] = (t, m)
    return out


# Frozen: exactly the widths the first oracle shipped with.  Do not repair.
LADDER_V1_RESEARCH = {
    4: (2, 1), 8: (3, 4), 16: (4, 9), 32: (5, 21), 64: (7, 52),
    128: (8, 115), 256: (9, 242), 512: (10, 497), 1024: (11, 1006),
}

LADDER_V2_SPEC = spec_ladder()

LADDER_VERSIONS = {"v1-research": LADDER_V1_RESEARCH, "v2-spec": LADDER_V2_SPEC}

DEFAULT_LADDER_VERSION = "v2-spec"

# Bump whenever the generator, the encoding, or a ladder row changes.
VECTOR_SPEC_VERSION = "tnf-vectors-3"


def width_rule_report():
    """Which v1 rows violate the rule, and by how much."""
    rows = []
    for w in sorted(LADDER_V1_RESEARCH):
        t1, m1 = LADDER_V1_RESEARCH[w]
        t2, m2 = LADDER_V2_SPEC[w]
        rows.append({
            "width": w,
            "v1": (t1, m1), "v1_sum": 1 + t1 + m1, "v1_ok": (1 + t1 + m1) == w,
            "v2": (t2, m2), "v2_sum": 1 + t2 + m2,
            "mantissa_delta": m2 - m1, "trit_delta": t2 - t1,
        })
    return rows


if __name__ == "__main__":
    print(f"vector spec version: {VECTOR_SPEC_VERSION}")
    print(f"{'rung':>8} {'v1 (Et,M)':>12} {'sum':>5} {'rule':>5} "
          f"{'v2 (Et,M)':>12} {'sum':>5} {'dM':>5} {'dEt':>4}")
    for r in width_rule_report():
        print(f"TNF{r['width']:<5} {str(r['v1']):>12} {r['v1_sum']:>5} "
              f"{('ok' if r['v1_ok'] else 'VIOL'):>5} {str(r['v2']):>12} "
              f"{r['v2_sum']:>5} {r['mantissa_delta']:>+5} {r['trit_delta']:>+4}")

# ---------------------------------------------------------------------------
# W995: THE LADDER NAME IS A SYMBOL COUNT, NOT A BIT COUNT.
#
# `spec_ladder` asserts `1 + E_t + M == N`, where E_t counts TRITS. So "TNF16"
# means one sign, four trits and eleven mantissa bits -- sixteen storage
# ELEMENTS. Packed into binary, four trits need seven bits, and the format is
# nineteen bits wide.
#
# The name is therefore correct in a unit nobody else uses and wrong in the unit
# every comparison is made in. That is worse than an arbitrary label: it is
# self-consistent, so it never trips, and the sequence 4/8/16/32/64 is exactly
# the IEEE width sequence, so "TNF16 vs binary16" reads as matched and is not.
# The gap grows with the rung: +2, +2, +3, +4, +5 bits.
#
# Measured cost of this confusion: `structural_w942` had to record
# `physical_bits: 19` as a separate field; T614 exists as a standing rule
# ("a rung's NAME is not its object") after it cost two sign-flipped results;
# and in W991 `tri compare` put TNF16 in a 16-bit table and reported 516096
# values from a "16-bit" format -- 2**19 codes -- catching itself only because
# the count was arithmetically impossible.
#
# CANONICAL NAME IS NOW THE BINARY WIDTH. The symbol-count names are kept as
# aliases, not deleted: every committed record, die word, referee row and
# derived check cites them, and a rename that makes history unreadable trades
# one defect for a worse one.
# ---------------------------------------------------------------------------

def ladder_names():
    """symbol-count name -> (binary width, exp_trits, mant_bits)."""
    import math
    out = {}
    for sym, (t, m) in spec_ladder().items():
        exp_bits = math.ceil(t * math.log2(3))
        out[sym] = (1 + exp_bits + m, t, m)
    return out


def canonical(name):
    """'TNF4' or 4 -> 'TNF6'. The binary width, which is the unit of comparison."""
    n = int(str(name).upper().removeprefix("TNF"))
    tbl = ladder_names()
    if n in tbl:
        return f"TNF{tbl[n][0]}"
    if n in {w for w, _, _ in tbl.values()}:
        return f"TNF{n}"
    raise KeyError(f"no ladder rung named or sized {name}")


def legacy(name):
    """'TNF6' or 6 -> 'TNF4'. The symbol count, for reading older records."""
    n = int(str(name).upper().removeprefix("TNF"))
    for sym, (w, _, _) in ladder_names().items():
        if w == n:
            return f"TNF{sym}"
    if n in ladder_names():
        return f"TNF{n}"
    raise KeyError(f"no ladder rung named or sized {name}")


# The table a reader needs to move between the two, in one place.
LADDER_RENAME = {f"TNF{sym}": f"TNF{w}" for sym, (w, _, _) in ladder_names().items()}
