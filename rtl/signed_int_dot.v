`timescale 1ns/1ps
`default_nettype none

// Fully unrolled signed integer dot product with a balanced 32-bit add tree.
// FANIN must be a power of two. DSP inference is controlled by the synthesis
// invocation; the benchmark uses synth_xilinx -nodsp.
module signed_int_dot #(
    parameter integer FANIN = 8,
    parameter integer WIDTH = 8,
    parameter integer ACC_W = 32
) (
    input  wire [FANIN*WIDTH-1:0] samples,
    input  wire [FANIN*WIDTH-1:0] weights,
    output wire [ACC_W-1:0]       result
);
    localparam integer LEVELS = $clog2(FANIN);
    localparam integer PROD_W = WIDTH * 2;
    // Each generated assignment advances exactly one level. Verilator treats
    // the complete array as one signal and otherwise reports a false cycle.
    /* verilator lint_off UNOPTFLAT */
    wire signed [ACC_W-1:0] tree [0:LEVELS][0:FANIN-1];
    /* verilator lint_on UNOPTFLAT */

    genvar lane;
    generate
        for (lane = 0; lane < FANIN; lane = lane + 1) begin : g_product
            wire signed [WIDTH-1:0] sample_lane;
            wire signed [WIDTH-1:0] weight_lane;
            wire signed [PROD_W-1:0] product;
            assign sample_lane = samples[lane*WIDTH +: WIDTH];
            assign weight_lane = weights[lane*WIDTH +: WIDTH];
            assign product = sample_lane * weight_lane;
            assign tree[0][lane] = {
                {(ACC_W-PROD_W){product[PROD_W-1]}}, product
            };
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

    assign result = tree[LEVELS][0];
endmodule

`default_nettype wire
