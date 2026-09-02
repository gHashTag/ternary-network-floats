# Exact Z[phi] fan-in benchmark contract

## Question

What does the paper's proved two-coordinate arithmetic cost when implemented
directly as an unrolled dot product, without packed exponents, alignment,
normalization, or rounding?

## Representation

Each input is a pair of signed 16-bit integers `(a,b)` denoting `a+b*phi`.
The weight alphabet is `{0,+phi,-phi}` with codes `00/11`, `01`, and `10`.

```text
+phi: (a,b) -> (b, a+b)
-phi: (a,b) -> (-b, -(a+b))
zero:          (0,0)
```

The transformed coordinates are sign-extended and accumulated independently in
the same balanced tree. With fan-in `N`, output width is
`16 + 1 + log2(N)` bits per coordinate, so fan-in 64 produces two 23-bit
coordinates without overflow for every possible input pair and weight.

## Protocol

- fan-in 8, 16, 32, and 64;
- fully unrolled balanced combinational tree;
- all pair coordinates and weights visible at top-level ports;
- exact Python integer oracle, 96 deterministic cases per arm;
- Yosys xc7, `-flatten -nodsp`, and the same bounded `share -fast` staged flow;
- post-synthesis cell counts with compressed raw logs and hashes.

## Acceptance criteria

1. The test fails first because `rtl/zphi_dot_tree.v` is absent.
2. All 384 pair results match the exact integer oracle, including coordinate
   extremes, cancellation, zero, and both signs of phi.
3. Verilator lint is clean at fan-in 64.
4. Synthesis reports zero DSP, no latch, and full operand visibility.
5. The result index compares exact Z[phi] against direct packed TNF, deferred
   TNF, int4, and int8 while recording that widths and numerical contracts are
   not matched.

## Non-claims

The pair design does not include conversion to or from packed TNF, nonlinear
activation, saturation, memory traffic, registers, timing, or place and route.
Its 34 input bits per lane are not storage-matched to packed TNF's 18, int8's 16,
or int4's 8. Logic ratios are architecture facts, not an end-to-end winner.
