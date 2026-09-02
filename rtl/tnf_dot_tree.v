`timescale 1ns/1ps
`default_nettype none

// Fully unrolled direct packed-TNF dot product.
// FANIN must be a power of two. Each lane applies one ternary weight by
// sign-select/zero; each internal node performs one packed TNF RNE addition.
module tnf_dot_tree #(
    parameter integer FANIN = 8
) (
    input  wire [FANIN*16-1:0] samples,
    input  wire [FANIN*2-1:0]  weights,
    output wire [15:0]          result
);
    localparam integer LEVELS = $clog2(FANIN);
    // The linter tracks this generated array as one signal and reports a false
    // UNOPTFLAT cycle. Every driver below is strictly level -> level+1.
    /* verilator lint_off UNOPTFLAT */
    wire [15:0] tree [0:LEVELS][0:FANIN-1];
    /* verilator lint_on UNOPTFLAT */

    genvar lane;
    generate
        for (lane = 0; lane < FANIN; lane = lane + 1) begin : g_weight
            tnf_weight_apply #(.TOTAL(16)) apply_weight (
                .in_value(samples[lane*16 +: 16]),
                .weight(weights[lane*2 +: 2]),
                .out_value(tree[0][lane])
            );
        end
    endgenerate

    genvar level;
    genvar node;
    generate
        for (level = 0; level < LEVELS; level = level + 1) begin : g_level
            for (node = 0; node < (FANIN >> (level + 1));
                 node = node + 1) begin : g_node
                tnf_add_full #(
                    .MANT_W(8), .OFF_W(7), .TOTAL(16), .OFFSET_MAX(80)
                ) add (
                    .a(tree[level][node*2]),
                    .b(tree[level][node*2 + 1]),
                    .y(tree[level + 1][node])
                );
            end
        end
    endgenerate

    assign result = tree[LEVELS][0];
endmodule

`default_nettype wire
