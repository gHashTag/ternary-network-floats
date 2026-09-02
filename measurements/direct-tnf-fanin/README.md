# Direct packed-TNF fan-in sweep

This directory answers the previously open implementation question with raw,
recomputable evidence. `TNF(E_t=4,M=8)`, signed int4, and signed int8 are each
implemented as a fully unrolled balanced dot-product tree at fan-in 8, 16, 32,
and 64. All operands enter through top-level ports and every arm uses the same
Yosys xc7, no-DSP, bounded-share policy defined in `BENCHMARK_CONTRACT.md`.

## Frozen result

The simulation regression checks 96 deterministic vectors in each of 12 arms:
**1,152 checks, zero errors**. Post-synthesis counts are:

| fan-in | direct TNF LUT | int4 LUT | int8 LUT | TNF/int4 | TNF/int8 |
|---:|---:|---:|---:|---:|---:|
| 8  | 3,397  | 370   | 1,524  | 9.18x | 2.23x |
| 16 | 7,394  | 777   | 3,113  | 9.52x | 2.38x |
| 32 | 15,459 | 1,426 | 6,443  | 10.84x | 2.40x |
| 64 | 31,274 | 3,048 | 12,003 | 10.26x | 2.61x |

Every arm has zero `DSP48E1`, zero inferred flip-flops, and no latch cell. The
full cell-type counts, wall times, source hashes, generated-wrapper hashes,
deterministically gzipped raw-log hashes, tool versions, exact command, and
negative-result fields are in `result.json`.

## Interpretation

The direct packed TNF path is real and functionally checked, but this particular
architecture is not area-competitive. Applying a ternary weight is still a
sign-select; the cost comes from placing a complete alignment, normalization,
exception-handling, and RNE packed-TNF adder at every internal tree node. The
direct TNF tree uses 9.18--10.84x the LUTs of native int4 and 2.23--2.61x the
LUTs of native int8 in this synthesis-only experiment.

This falsifies an unqualified “TNF is smaller” statement for the direct fully
unrolled RNE tree. It does not falsify the exact `Z[phi]` closure theorem, the
low cost of ternary weight application, or architectures that defer
normalization/rounding, use a wide exact accumulator, serialize the adder, or
keep the two-coordinate representation through the layer. Those are now the
specific next designs to measure.

## Reproduce

```bash
python3 tests/test_tnf_fanin_artifact.py
python3 measure_tnf_fanin.py
```

No place-and-route result is claimed. The fan-in-64 TNF interface alone has
1,152 input bits, so it cannot be exposed through the selected sbg484 package;
a physical comparison requires a registered streaming or on-chip-memory harness
with matched throughput and I/O.
