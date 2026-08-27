# Ternary Network Floats — artefacts

Everything needed to check the claims in *Ternary Network Floats: a datapath with
no multiplier anywhere*. One command reproduces the paper's numbers; one command
checks its proofs. Neither quotes a stored record.

```bash
python3 verify.py          # recomputes the paper's tables from the oracle
coqc -Q proofs Trinity proofs/CorePhi.v   # checks the algebra
```

`verify.py` exits non-zero if any number moves. `coqc` returns 0 on a file with
twenty-two theorems, twenty-two `Qed`, and no `Admitted` or `Axiom`.

## What is here

| path | what it settles |
|---|---|
| `oracle/tnf_ref.py` | the reference decoder for every rung TNF4..TNF1024 |
| `proofs/CorePhi.v` | the φ identities and the closure of Z[φ], machine-checked |
| `data/compare_w991.json` | the matched-width comparison against posit and takum |
| `rtl/` | the formal-equivalence modules for the multiply-free datapath |
| `verify.py` | every table in the paper, recomputed and asserted |

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

## Requirements

Python 3.9+ (no third-party packages) and Rocq/Coq 9.x for the proofs. The
FPGA numbers in the paper were produced with Yosys 0.65, nextpnr-xilinx
1743d0f and Icarus Verilog 13.0 — all open-source, none requiring a licence.

## Provenance

Extracted from the [t27](https://github.com/gHashTag/t27) monorepo, where this
work was developed. That repository remains the origin; this one exists so the
paper's artefacts can be checked without cloning everything around them.

## Licence

MIT. See `LICENSE`.
