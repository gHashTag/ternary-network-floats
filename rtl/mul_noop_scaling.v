`default_nettype none

// mul_noop_scaling.v -- the compiler's multiplication helper, parameterised by
// width, and the `*` it replaces.
//
// WHY.  t27c emits `__mul_noop(a, b)` into EVERY generated Verilog module in
// place of the `*` operator (bootstrap/src/compiler.rs:9734), because `*` is not
// accepted on the synthesis path.  Measured 2026-08-14: 130 of 200 specs emit
// it.  It is the single most load-bearing piece of arithmetic in the project,
// it is shared by two thirds of the corpus, and NOTHING tests it directly --
// the Zig backend does not use this lowering, so the cross-backend disagreement
// that catches most defects is blind here by construction.
//
// The body below is the shipped algorithm with 64 replaced by W.  It must stay
// a transcription: if compiler.rs changes, this file is wrong and the proof it
// supports is about something that is no longer emitted.
//
// W  is the activation width (the wide operand).
// WB is the WEIGHT width (the narrow one).  Setting WB < W is the whole point:
// a ternary weight is TWO bits, so the multiplication a ternary network performs
// is 64x2, not 64x64 -- and those sit on opposite sides of what SAT can do.
// Measured: 64x2 proves in 0.16 s, 64x5 in 119.92 s, 64x6 not at all.
//
// Proving these equivalent is the classic hard case for SAT -- multiplier
// equivalence is exponential in the operand width -- so this file exists as much
// to MEASURE THE WALL as to check the algorithm.  Where the wall sits bounds
// what "prove the corpus" can ever mean.
//
// Refs #1959

module mul_noop #(parameter integer W = 8, parameter integer WB = 8) (
    input  wire [W-1:0]  a,
    input  wire [WB-1:0] b,
    output wire [W-1:0]  y
);
    function [W-1:0] noop;
        input [W-1:0]  fa;
        input [WB-1:0] fb;
        integer i;
        reg [2*W-1:0] acc;
        begin
            acc = {(2*W){1'b0}};
            for (i = 0; i < WB; i = i + 1) begin
                if (fb[i]) acc = acc + ({{W{1'b0}}, fa} << i);
            end
            noop = acc[W-1:0];
        end
    endfunction

    assign y = noop(a, b);
endmodule

module mul_golden #(parameter integer W = 8, parameter integer WB = 8) (
    input  wire [W-1:0]  a,
    input  wire [WB-1:0] b,
    output wire [W-1:0]  y
);
    // The operator the helper exists to avoid. Truncating, like the helper:
    // the helper returns acc[W-1:0], so the reference must also keep only the
    // low W bits, or the miter would report a disagreement that is a width
    // convention rather than a defect.
    assign y = a * b;
endmodule

`default_nettype wire
