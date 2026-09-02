# Exact Z[phi] pair result

This is the direct RTL realization of the paper's closure theorem. A signed
16-bit pair `(a,b)` denotes `a+b*phi`; applying `+phi` is `(b,a+b)`, applying
`-phi` negates that pair, and accumulation is componentwise integer addition.
There is no exponent alignment, normalization, rounding, or multiplier.

Functional result: **384 deterministic exact-integer checks, zero errors**.

| fan-in | exact Z[phi] LUT | direct packed LUT | packed/Z[phi] | Z[phi]/int8 |
|---:|---:|---:|---:|---:|
| 8  | 1,177  | 3,397  | 2.89x | 0.77x |
| 16 | 2,490  | 7,394  | 2.97x | 0.80x |
| 32 | 6,152  | 15,459 | 2.51x | 0.95x |
| 64 | 13,144 | 31,274 | 2.38x | 1.10x |

Every row maps at zero DSP. Against the packed TNF RNE tree, the exact pair is
2.38--2.97x smaller; against the 96-bit deferred-normalization tree it is
3.67--4.57x smaller. It is also smaller than the native int8 structural baseline
at fan-in 8, 16, and 32, then crosses to 1.095x int8 at fan-in 64.

The int8 comparison is not a format ranking. Z[phi] presents 34 input bits per
lane (two 16-bit coordinates and a two-bit weight), while int8 presents 16.
Conversion, storage, memory traffic, timing, and model accuracy are not included.
The defensible result is narrower and stronger: implementing the theorem's
closed coordinate domain avoids the packed format's dominant alignment and
rounding cost.

Reproduce with:

```bash
python3 tests/test_zphi_fanin_artifact.py
python3 measure_zphi_fanin.py
```
