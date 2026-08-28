# Ternary Network Floats — artefacts

Everything needed to check the claims in *Ternary Network Floats: a datapath with
no multiplier anywhere*. One command reproduces the paper's numbers; one command
checks its proofs. Neither quotes a stored record — both recompute.

```bash
python3 verify.py                          # recomputes the paper's tables from the oracle
coqc -Q proofs Trinity proofs/CorePhi.v    # checks the algebra
python3 make_vector_manifest.py --check    # verifies the conformance vector digests
```

`verify.py` exits non-zero if any number moves. `coqc` returns 0 on a file with
twenty-two theorems, twenty-two `Qed`, and no `Admitted` or `Axiom`.

---

## The result in one line

A ternary neuron costs **28 LUT per weight at fan-in 8 and no DSP at any fan-in**
on an XC7A200T, because the multiplier is removed rather than cheapened: with a
two-bit `{-φ, 0, +φ}` alphabet, `Z[φ]` is closed under weight application and
accumulation, so applying a weight is the Fibonacci step `(a,b) → (b, a+b)` —
one addition, no multiplier — and a layer's linear path is **exact**.

What it costs: **precision per bit**. Posit holds more representable values and a
finer step at unity at every matched physical width. That is the paper's own
second negative result and it is not hedged.

---

## Format comparison

One ternary-neuron datapath, XC7A200T, `-nodsp`, median of five placement seeds,
harness subtracted. **DSP = 0 in every row.**

| format | base | stored width | LUT | MHz\* | MHz/LUT\* | decode LUT | decode MHz | kind | conformance |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| **GFTernary** (ours) | ternary | 2 bits | 463 | 83.19 | **0.1797** | **66** | **974.66** | fixed | all 4 codes |
| **TNF16** (ours) | ternary | 17 bits† | 565 | 66.28 | 0.1173 | 101 | 407.66 | fixed | all 131,072 |
| **TNF32** (ours) | ternary | 36 bits | 569 | 66.91 | 0.1176 | — | — | fixed | 9,997 sampled, 0 wrong |
| **TNF8** (ours) | ternary | 10 bits | 545 | 62.13 | 0.1140 | — | — | fixed | all 1,024, 0 wrong |
| **BNF16** (ours) | binary | 17 bits | 571 | 67.13 | 0.1176 | 97 | 388.35 | fixed | all 131,072, 0 wrong |
| binary32 | binary | 32 bits | 472 | 77.00 | 0.1631 | 112 | 886.52 | fixed | not swept |
| binary16 | binary | 16 bits | 522 | 63.30 | 0.1213 | 164 | 235.18 | fixed | all 65,536 |
| fp8 e5m2 | binary | 8 bits | 480 | 67.06 | 0.1397 | — | — | fixed | **6 of 256 wrong** |
| fp8 e4m3 | binary | 8 bits | 485 | 67.02 | 0.1382 | — | — | fixed | **14 of 256 wrong** |
| minifloat | binary | 8 bits | 558 | 67.06 | 0.1202 | — | — | fixed | not swept |
| VAX F | binary | 32 bits | 527 | 73.51 | 0.1395 | 100 | 311.14 | fixed | not swept |
| posit8 | binary | 8 bits | 540 | 44.33 | 0.0821 | 214 | 77.75 | tapered | not swept |
| posit16 | binary | 16 bits | 712 | 40.38 | 0.0567 | 302 | 62.39 | tapered | 4 of 65,536 wrong |
| posit32 | binary | 32 bits | 953 | 28.16 | 0.0295 | **517** | **49.05** | tapered | not swept |
| takum16 | binary | 16 bits | 789 | 58.96 | 0.0747 | — | — | tapered | not swept |
| LNS16 | binary | 16 bits | 658 | 43.04 | 0.0654 | 270 | 93.17 | logarithmic | not swept |
| IBM hex32 | binary | 32 bits | 687 | 46.78 | 0.0681 | 243 | 111.10 | fixed | not swept |

\* **Do not rank by these.** Every frequency in this table is stated in no record
file in the repository, no place-and-route log for any row is in the tree, and
`Fmax` through this flow is a size proxy (see below). The columns are printed
because they were measured, not because they support a conclusion.

† TNF16 here is the pre-reconciliation module at `M=9`, 17 bits. The specified
rung is `M=11` at 19 bits and has not been placed. Read the row by its stored
width, not by its name.

**What this table does support.** Decode cost, which needed no frequency to
measure: GFTernary decodes in **66 LUT** against posit32's **517** — a factor of
**7.8**. A fixed field is decoded by slicing it; a tapered format is decoded by
counting leading zeros and then shifting by the count. That is the axis this
format is for.

---

## Precision at matched physical width — the negative result

Computed from the reference decoder, not quoted. `verify.py` reproduces every
cell.

| bits | format | values | binades | step at 1.0 |
|---:|---|---:|---:|---:|
| 19 | TNF16 (4t, 11m) | 323,584 | 79.0 | 0.024% |
| 19 | **posit19 es=1** | **524,286** | 68.0 | **0.002%** |
| 19 | **posit19 es=2** | **524,286** | **136.0** | **0.003%** |
| 19 | **takum19** | **524,286** | **510.0** | **0.003%** |
| 10 | TNF8 (3t, 4m) | 800 | 25.0 | 3.125% |
| 10 | **posit10 es=1** | **1,022** | **32.0** | **0.781%** |
| 6 | TNF4 (2t, 1m) | 28 | 6.6 | 25.0% |
| 6 | **posit6 es=1** | **62** | **16.0** | **12.5%** |

Posit is **12× / 4× / 2×** finer at unity at 19, 10 and 6 bits, and `es=2` weakly
dominates on both range and precision at all three. The case for this format was
never precision per bit.

**How much of that deficit is structural.** One value of the 19-bit rung carries
`log₂(2·3⁴·2¹¹) = 18.340` bits in a 19-bit word — **63.3% utilisation**. The
waste is a rounding-up paid once per value. Paying it once per block instead:

| packing | bits/value | utilisation | decode cost |
|---|---:|---:|---|
| per word (as published) | 19.000 | 63.3% | field slice |
| **5 trits in 8 bits** | **18.400** | **95.9%** | one 256×8 lookup per five values |
| base-3 over K=32 | 18.344 | 99.7% | division chain — not worth it |
| information floor | 18.340 | 100% | — |

Spending the recovered 0.6 bits on the mantissa moves the step at unity from
0.024% to about 0.015%, narrowing the gap to posit19 from 12× to roughly 7.6×.
**It does not close it.** Half the published deficit was our own choice of
packing; the rest is real.

---

## Two findings about the toolchain, not about ternary

These cost us published numbers and they are properties of the flow. Anyone
benchmarking through Yosys + nextpnr-xilinx is exposed to both.

**Synthesis deletes the checks whose area you are measuring.** We embedded
assertion logic so a wrong result could not be produced silently, then measured
area. **Fifteen of twenty-eight on-die clauses were folded to constants and
removed**, so every area figure we had published measured a design with its
checks already gone — and the bias runs with design size, which is exactly what
an area table compares. *Detection:* synthesise twice, with the checks and with
them cut by hand, and compare cell counts. If they agree, they were folded.

**MHz/LUT through this flow is a size proxy.** Across a 41× span of area,

```
Fmax ≈ 3174 · LUT^(-0.648),   R² = 0.92
```

so size explains 92% of frequency and a ranking by MHz per LUT is close to a
ranking by smallness. Residuals span a factor of two, and that factor is the only
part of the frequency column carrying design information. *Detection:* fit `Fmax`
against area over your own rows before reporting frequency per area.

Four more of the same kind — a proof base with no admitted lemmas that never
type-checked, a decoder accepting codes its format cannot name, substring
provenance matching, and a provenance chain ending at a restatement — are in the
paper's methodology section. None was caught by review; all six were caught by
re-running something that had already passed.

---

## What is here

| path | what it settles |
|---|---|
| `oracle/tnf_ref.py` | the reference decoder for every rung TNF4..TNF1024 |
| `proofs/CorePhi.v` | the φ identities and the closure of Z[φ], machine-checked |
| `data/compare_w991.json` | the matched-width comparison against posit and takum |
| `rtl/` | the formal-equivalence modules for the multiply-free datapath |
| `verify.py` | every table in the paper, recomputed and asserted |
| `freq_provenance.py` | which frequency literals in the paper are stated in no record file |
| `data/freq_provenance.json` | that registry's output on the cited revision |
| `make_vector_manifest.py` | writes and checks SHA-256 over the conformance vectors |
| `vectors/SHA256SUMS` | one digest per vector file |

## Claim to file

| claim in the paper | where to check it |
|---|---|
| applying a weight is the Fibonacci step `(a,b) → (b,a+b)` | `proofs/CorePhi.v`, `fib_step_is_phi_mul` |
| accumulation is componentwise, so Z[φ] is closed | `zphi_add_closed`, `zphi_opp_closed`, `zphi_zero` |
| a layer's linear path is exact | `dot_exact` |
| φ² = φ + 1 and φ² + φ⁻² = 3 | `phi_square`, `trinity_identity` |
| φⁿ = F(n)·φ + F(n−1) | `phi_cubed_fib`, `phi_fourth_fib`, `phi_fifth_fib` |
| TNF16 (4t,11m) holds 323,584 values across 79 binades | `verify.py`, first block |
| 200,704 of the 2¹⁹ words are unreachable | `verify.py`, first block |
| posit is 12× / 4× / 2× finer at unity | `verify.py`, second block |
| the one-adder family reaches 1.0265 at degree 27 | `verify.py`, fourth block |
| area falls 2.6–3.6×, throughput per area 2.1–3.1× | `verify.py`, fifth block |
| 12 of 44 frequency literals are unsourced | `freq_provenance.py`, run against the paper |
| conformance vector digests | `make_vector_manifest.py --check` |

## Two corrections this repository carries

**The oracle counted the wrong format.** A TNF exponent of `Et` trits is stored
in `ceil(Et·log₂3)` bits, so the field holds more codes than the trits name: at
`Et=4` it holds 128 and the trits reach 81. `decode` used to mask to the field
and treat the other 47 as ordinary normals, which put TNF16 at 516,096 values
and 127.0 binades — and 127.0 is 2⁷−1, the span of a *binary* seven-bit
exponent. Against the trits it is 323,584 values and 79.0 binades. The step at
unity is unaffected, so the precision ratios against posit are unchanged; the
value deficit grows.

**The proof base was never checked.** `CorePhi.v` closed every lemma with `Qed`
and contained no `Admitted`, so it audited clean — while failing to compile at
all. It also stated three falsehoods: `phi^3 = 2·√5 + 3` is 7.472 where φ³ is
4.236, and two further powers carried the same error, the Fibonacci form written
as `F(n)·√5 + F(n+1)`. Statements corrected, proofs rewritten so each power
follows from `phi_square` by one Fibonacci step, and the numeric bracket proved
by strict monotonicity of `sqrt` rather than by evaluating it.

Both are described in the paper rather than quietly repaired.

## What is not here

The paper marks, in place, the claims a reader cannot check: the downstream
experiment's generator and JSON record, the withdrawal note said to be under
`research/frontier/`, and the `tnf-vectors-2` / `tnf-vectors-3` tags, which never
existed on any remote — all vector files carry the `_v0` suffix and the manifest
above names the one set that exists. Quote the commit, never a version name.

## Requirements

Python 3.9+ (no third-party packages) and Rocq/Coq 9.x for the proofs. The
FPGA numbers were produced with Yosys 0.65, nextpnr-xilinx 1743d0f, Icarus
Verilog 13.0 and Python 3.14 — all open-source, none requiring a licence, which
is the point: a result nobody can reproduce without buying something is not a
public result.

## Provenance

Extracted from the [t27](https://github.com/gHashTag/t27) monorepo, where this
work was developed. That repository remains the origin; this one exists so the
paper's artefacts can be checked without cloning everything around them.

## Licence

MIT. See `LICENSE`.
