`timescale 1ns/1ps
`default_nettype none

// Physical-width-exact 16-bit TNF point:
//   E_t=4 trits -> OFF_W=ceil(4*log2(3))=7 bits
//   M=8 bits, plus one sign bit: 1+7+8=16.
module tnf_mac_e4m8_top (
    input  wire [15:0] acc,
    input  wire [15:0] sample,
    input  wire [1:0]  weight,
    output wire [15:0] result
);
    tnf_mac #(
        .MANT_W(8),
        .OFF_W(7),
        .TOTAL(16),
        .OFFSET_MAX(80)
    ) datapath (
        .acc(acc),
        .sample(sample),
        .weight(weight),
        .result(result)
    );
endmodule

`default_nettype wire
