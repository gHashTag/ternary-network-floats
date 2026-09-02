# Direct TNF MAC E4M8 measurement

This directory records a fresh measurement of the RTL in `rtl/tnf_mac.v`, not a
reconstruction of a number printed in the paper.

## Contract

- Format: TNF with four exponent trits and eight binary mantissa bits.
- Physical word: 16 bits (`1 sign + 7 offset + 8 mantissa`).
- Operation: `acc + weight * sample`, where the two-bit weight is `0`, `+1`,
  `-1`, or the second zero code.
- Weight application: sign-select only; no magnitude multiplier.
- Addition: full packed-TNF alignment, add/subtract, normalization, and RNE.
- Timing boundary: input registers, direct TNF combinational MAC, output
  registers, and package I/O.
- Target: `xc7a200tsbg484-1`, 50 MHz requested, five seeds.
- Claim gate: no `DSP48E1` and no synthesized latch cells.

## Results

- RTL/oracle: 5,000 vectors, 0 errors.
- Yosys: 452 LUT, 46 CARRY4, 52 FF, 0 DSP48E1.
- nextpnr: 854 SLICE_LUTX, 46 CARRY4, 52 FF, 0 DSP48E1 for every seed.
- Fmax: 22.24, 23.14, 22.31, 23.90, and 23.23 MHz; median 23.14 MHz.
- The requested 50 MHz constraint was not met in any seed.

`result.json` is the machine-readable index. The raw logs are retained beside
it, and every log SHA-256 is embedded in the result. The design, verification,
and XDC digests, tool versions, chip database path, and chip database SHA-256
are also embedded.

The chip database used here was generated from nextpnr-xilinx commit
`7037c948048a8a61ab281bfb8db3e2e7a898927a`, Project X-Ray database commit
`0a0addedd73e7e4139d52a6d8db4258763e0f1f3`, and nextpnr metadata commit
`a4af910cac907f2cbd3a545f26f8e26573e860de`. Its recorded SHA-256 is the
identity check; a speed-grade label alone is not sufficient provenance.

## Non-claims

This is one MAC step, not a fan-in dot product, a complete neuron, or a complete
network. It has no matched binary, posit, or legacy-TNF baseline in this run.
Therefore it supports implementation, conformance, zero-DSP, area, and timing
claims only for this boundary. It does not validate the historical neuron table
or establish that TNF outperforms another format.
