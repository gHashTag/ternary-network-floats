# Deferred-normalization TNF fan-in contract

## Question

Does moving exponent alignment to the leaves and performing only one packed-TNF
normalization/rounding operation at the dot-product root materially reduce the
cost of the direct RNE-at-every-node architecture?

## Representation and exact domain

Inputs are packed 16-bit `TNF(E_t=4,M=8)` values. For a finite non-zero word
with offset `o` and mantissa `m`, the exact integer-domain magnitude is

```text
(256 + m) << (o - 1)
```

with common scale `2^-47`. Fan-in 64 therefore fits in a signed 94-bit
accumulator. A ternary weight is applied as zero, identity, or negation. All
leaf integers are reduced by a balanced tree with no intermediate
normalization or rounding. The root is encoded once to packed TNF with
round-to-nearest-even. An active special/unencodable input produces canonical
NaN; a special input multiplied by zero contributes zero.

## Matched protocol

- fan-in 8, 16, 32, and 64;
- fully unrolled balanced reduction;
- every sample and weight visible through top-level input ports;
- Yosys xc7 mapping with DSP inference disabled;
- the same bounded `share -fast` staged `synth_xilinx` policy as the frozen
  direct fan-in campaign;
- post-synthesis logical cell counts only.

## Acceptance criteria

1. The deterministic test fails first because `rtl/tnf_deferred_dot.v` and
   `rtl/tnf_exact_to_packed.v` do not exist.
2. At least 96 cases at each fan-in match `encode(sum(weight*decode(sample)))`
   exactly, including cancellation, underflow, overflow, zero, and special rows.
3. Verilator lint is clean for fan-in 64 apart from any narrowly justified
   generated-array waiver.
4. Every synthesis arm has zero `DSP48E1`, no latch, full operand visibility,
   a raw compressed log, and hashes for sources, wrappers, and logs.
5. Results are compared directly with commit `d7d13e9`'s RNE-at-every-node TNF
   counts under the same synthesis policy.

## Non-claims

This experiment is not matched to int4/int8 for numerical accuracy, range,
storage width, model quality, timing, power, or physical I/O. It does not
implement the separate `Z[phi]` representation. It tests one specific packed
TNF microarchitecture and one final-rounding contract.
