`timescale 1ns/1ps
`default_nettype none

// Fully unrolled packed-TNF dot product with one final normalization/RNE.
// Every finite input is lifted into a common exact integer domain; the balanced
// tree performs signed integer additions only.
module tnf_deferred_dot #(
    parameter integer FANIN      = 8,
    parameter integer ACC_W      = 96,
    parameter integer MANT_W     = 8,
    parameter integer OFF_W      = 7,
    parameter integer TOTAL      = 16,
    parameter [31:0]  OFFSET_MAX = 80
) (
    input  wire [FANIN*TOTAL-1:0] samples,
    input  wire [FANIN*2-1:0]     weights,
    output wire [TOTAL-1:0]       result
);
    localparam integer LEVELS = $clog2(FANIN);
    /* verilator lint_off UNOPTFLAT */
    wire signed [ACC_W-1:0] tree [0:LEVELS][0:FANIN-1];
    /* verilator lint_on UNOPTFLAT */
    wire [FANIN-1:0] active_special;

    genvar lane;
    generate
        for (lane = 0; lane < FANIN; lane = lane + 1) begin : g_leaf
            wire [TOTAL-1:0] sample = samples[lane*TOTAL +: TOTAL];
            wire [1:0] weight = weights[lane*2 +: 2];
            wire sample_sign = sample[TOTAL-1];
            wire [OFF_W-1:0] sample_offset =
                sample[TOTAL-2:MANT_W];
            wire [MANT_W-1:0] sample_mantissa = sample[MANT_W-1:0];
            wire weight_active = (weight == 2'b01) || (weight == 2'b10);
            wire weight_negative = (weight == 2'b10);
            wire sample_zero = (sample_offset == {OFF_W{1'b0}});
            wire sample_special =
                ({1'b0, sample_offset} >=
                 {1'b0, OFFSET_MAX[OFF_W-1:0]});
            wire [OFF_W-1:0] shift_amount = sample_zero
                ? {OFF_W{1'b0}} : sample_offset - 1'b1;
            wire [ACC_W-1:0] unsigned_leaf =
                {{(ACC_W-MANT_W-1){1'b0}}, 1'b1, sample_mantissa}
                << shift_amount;
            wire effective_sign = sample_sign ^ weight_negative;
            wire signed [ACC_W-1:0] signed_leaf = effective_sign
                ? -$signed(unsigned_leaf) : $signed(unsigned_leaf);

            assign active_special[lane] = weight_active && sample_special;
            assign tree[0][lane] = (!weight_active || sample_zero
                                    || sample_special)
                ? {ACC_W{1'b0}} : signed_leaf;
        end
    endgenerate

    genvar level;
    genvar node;
    generate
        for (level = 0; level < LEVELS; level = level + 1) begin : g_level
            for (node = 0; node < (FANIN >> (level + 1));
                 node = node + 1) begin : g_node
                assign tree[level + 1][node] =
                    tree[level][node*2] + tree[level][node*2 + 1];
            end
        end
    endgenerate

    tnf_exact_to_packed #(
        .ACC_W(ACC_W), .MANT_W(MANT_W), .OFF_W(OFF_W),
        .TOTAL(TOTAL), .OFFSET_MAX(OFFSET_MAX)
    ) encode_root (
        .exact_value(tree[LEVELS][0]),
        .special(|active_special),
        .out_value(result)
    );
endmodule

`default_nettype wire
