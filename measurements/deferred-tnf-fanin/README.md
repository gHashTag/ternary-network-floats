# Deferred-normalization TNF result

The experiment removes intermediate packed-float rounding: every TNF input is
lifted to a common exact 96-bit integer domain, the balanced tree adds exactly,
and the result is normalized and rounded once at the root.

Functional result: **384 deterministic oracle checks, zero errors**.

| fan-in | RNE at every node | deferred TNF | direct/deferred | deferred/int8 |
|---:|---:|---:|---:|---:|
| 8  | 3,397  | 5,382  | 0.63x | 3.53x |
| 16 | 7,394  | 10,674 | 0.69x | 3.43x |
| 32 | 15,459 | 25,007 | 0.62x | 3.88x |
| 64 | 31,274 | 48,265 | 0.65x | 4.02x |

All rows have zero DSP. Deferring normalization improves arithmetic semantics
but not logic area in this implementation. The repeated packed adders disappear,
yet each leaf now needs a variable shift into a 96-bit common-scale domain, and
the entire reduction tree is 96 bits wide. That exchange costs 1.44--1.62x more
LUT than the already expensive direct packed-RNE tree.

This closes one proposed optimization path with a negative result. It suggests
that a useful exact accumulator must avoid both repeated normalization and
per-leaf wide barrel alignment; the two-coordinate `Z[phi]` representation is
the next directly measured candidate.

Reproduce with:

```bash
python3 tests/test_deferred_tnf_artifact.py
python3 measure_deferred_tnf.py
```
