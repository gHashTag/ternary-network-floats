# Direct TNF fan-in benchmark contract

## Question

Does the packed TNF representation have a directly executable dot-product RTL
implementation, and how does its post-synthesis logic scale at fan-in 8, 16,
32, and 64 beside int4 and int8 under one hardware protocol?

## Matched protocol

Every arm is:

- a fully unrolled combinational dot product;
- reduced by the same balanced binary-tree topology;
- driven through top-level operand ports so synthesis cannot replace operands
  with constants;
- synthesized by the same Yosys executable for `xc7` with `-flatten -nodsp`;
- passed through the documented `synth_xilinx` coarse sequence with
  `share -fast` before the standard script resumes at `map_memory`; this bounded
  policy is identical for every arm and replaces the stock exhaustive `share`
  pass, which did not finish the TNF fan-in-64 arm within 35 minutes;
- reported from the synthesized JSON, with deterministically gzipped raw logs
  and SHA-256 retained.

The direct TNF arm uses packed `TNF(E_t=4,M=8)` values: 1 sign bit, a 7-bit
offset field naming four-trit rows, and 8 binary mantissa bits. Each two-bit
ternary weight is applied by zero/sign-select, then every internal tree node is
the full TNF RNE adder. Its oracle performs the same balanced sequence of packed
RNE additions.

The int4 and int8 arms multiply signed native-width samples by signed
native-width weights, sign-extend products, and reduce them in a 32-bit signed
tree. DSP inference is disabled, so those products map into logic.

## Acceptance criteria

1. A test written before the RTL must fail because the fan-in modules are absent.
2. Deterministic simulation must cover all 12 `(format, fan-in)` arms and match
   independent Python oracles with zero errors.
3. Verilator lint must produce no warnings for the measured sources.
4. Every Yosys arm must complete with zero `DSP48E1` and no latch cell.
5. The result index must record tool identity, exact commands, source hashes,
   per-arm raw-log hashes, topology, word widths, and negative-result fields.

## Non-claims

`matched` means topology, fan-in, unrolling, operand visibility, synthesis tool,
target family, and DSP policy. It does not mean equal accuracy, equal dynamic
range, equal storage width, equal model quality, or equal throughput after
pipelining. The experiment is post-synthesis only. It establishes no timing,
power, energy, ASIC, board, or universal-superiority claim. The direct TNF arm
is the proposed packed representation, not the separate two-coordinate
`Z[phi]` construction used by the closure theorem.
