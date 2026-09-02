`timescale 1ns/1ps
`default_nettype none

// Apply one ternary weight to one packed TNF value.
//
// Weight codes are the repository convention:
//   2'b00 = 0, 2'b01 = +1, 2'b10 = -1, 2'b11 = 0.
//
// A negative weight flips only the sign bit.  A zero weight emits canonical
// +0.  There is no multiplication operator and no magnitude datapath.
module tnf_weight_apply #(
    parameter integer TOTAL = 16
) (
    input  wire [TOTAL-1:0] in_value,
    input  wire [1:0]       weight,
    output wire [TOTAL-1:0] out_value
);
    wire is_positive = (weight == 2'b01);
    wire is_negative = (weight == 2'b10);
    wire [TOTAL-1:0] negated = in_value ^ {1'b1, {(TOTAL-1){1'b0}}};

    assign out_value = is_positive ? in_value
                     : is_negative ? negated
                     : {TOTAL{1'b0}};
endmodule

`default_nettype wire
