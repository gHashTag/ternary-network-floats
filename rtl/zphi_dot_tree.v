`timescale 1ns/1ps
`default_nettype none

// Exact fully unrolled dot product over Z[phi].
// A pair (a,b) denotes a+b*phi. Multiplication by +phi is (b,a+b);
// -phi negates both transformed coordinates. No rounding or normalization.
module zphi_dot_tree #(
    parameter integer FANIN  = 8,
    parameter integer COORD_W = 16,
    parameter integer OUT_W = COORD_W + 1 + $clog2(FANIN)
) (
    input  wire [FANIN*COORD_W-1:0] a_values,
    input  wire [FANIN*COORD_W-1:0] b_values,
    input  wire [FANIN*2-1:0]       weights,
    output wire [OUT_W-1:0]         result_a,
    output wire [OUT_W-1:0]         result_b
);
    localparam integer LEVELS = $clog2(FANIN);
    /* verilator lint_off UNOPTFLAT */
    wire signed [OUT_W-1:0] tree_a [0:LEVELS][0:FANIN-1];
    wire signed [OUT_W-1:0] tree_b [0:LEVELS][0:FANIN-1];
    /* verilator lint_on UNOPTFLAT */

    genvar lane;
    generate
        for (lane = 0; lane < FANIN; lane = lane + 1) begin : g_weight
            wire signed [COORD_W-1:0] a_in =
                a_values[lane*COORD_W +: COORD_W];
            wire signed [COORD_W-1:0] b_in =
                b_values[lane*COORD_W +: COORD_W];
            wire signed [OUT_W-1:0] a_ext =
                {{(OUT_W-COORD_W){a_in[COORD_W-1]}}, a_in};
            wire signed [OUT_W-1:0] b_ext =
                {{(OUT_W-COORD_W){b_in[COORD_W-1]}}, b_in};
            wire signed [OUT_W-1:0] phi_b = a_ext + b_ext;
            wire positive = (weights[lane*2 +: 2] == 2'b01);
            wire negative = (weights[lane*2 +: 2] == 2'b10);

            assign tree_a[0][lane] = positive ? b_ext
                : negative ? -b_ext : {OUT_W{1'b0}};
            assign tree_b[0][lane] = positive ? phi_b
                : negative ? -phi_b : {OUT_W{1'b0}};
        end
    endgenerate

    genvar level;
    genvar node;
    generate
        for (level = 0; level < LEVELS; level = level + 1) begin : g_level
            for (node = 0; node < (FANIN >> (level + 1));
                 node = node + 1) begin : g_node
                assign tree_a[level + 1][node] =
                    tree_a[level][node*2] + tree_a[level][node*2 + 1];
                assign tree_b[level + 1][node] =
                    tree_b[level][node*2] + tree_b[level][node*2 + 1];
            end
        end
    endgenerate

    assign result_a = tree_a[LEVELS][0];
    assign result_b = tree_b[LEVELS][0];
endmodule

`default_nettype wire
