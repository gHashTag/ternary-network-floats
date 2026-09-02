`timescale 1ns/1ps
`default_nettype none

// One direct TNF multiply-accumulate step for a ternary network.
// Multiplication by {-1,0,+1} is sign-select; accumulation is a TNF RNE add.
module tnf_mac #(
    parameter integer MANT_W     = 8,
    parameter integer OFF_W      = 7,
    parameter integer TOTAL      = 1 + OFF_W + MANT_W,
    parameter [31:0]  OFFSET_MAX = 80
) (
    input  wire [TOTAL-1:0] acc,
    input  wire [TOTAL-1:0] sample,
    input  wire [1:0]       weight,
    output wire [TOTAL-1:0] result
);
    wire [TOTAL-1:0] weighted_sample;

    tnf_weight_apply #(.TOTAL(TOTAL)) apply_weight (
        .in_value(sample),
        .weight(weight),
        .out_value(weighted_sample)
    );

    tnf_add_full #(
        .MANT_W(MANT_W),
        .OFF_W(OFF_W),
        .TOTAL(TOTAL),
        .OFFSET_MAX(OFFSET_MAX)
    ) accumulate (
        .a(acc),
        .b(weighted_sample),
        .y(result)
    );
endmodule

`default_nettype wire
