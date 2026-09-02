`timescale 1ns/1ps
`default_nettype none

// Register-to-register boundary used only for post-route timing and area
// measurement. The measured design includes both register banks and package I/O.
module tnf_mac_e4m8_pnr_top (
    input  wire        clk,
    input  wire        rst,
    input  wire        in_valid,
    input  wire [15:0] acc,
    input  wire [15:0] sample,
    input  wire [1:0]  weight,
    output reg         out_valid,
    output reg  [15:0] result
);
    reg  [15:0] acc_reg;
    reg  [15:0] sample_reg;
    reg  [1:0]  weight_reg;
    reg         in_valid_reg;
    wire [15:0] next_result;

    tnf_mac_e4m8_top datapath (
        .acc(acc_reg),
        .sample(sample_reg),
        .weight(weight_reg),
        .result(next_result)
    );

    always @(posedge clk) begin
        if (rst) begin
            acc_reg <= 16'd0;
            sample_reg <= 16'd0;
            weight_reg <= 2'b00;
            in_valid_reg <= 1'b0;
            result <= 16'd0;
            out_valid <= 1'b0;
        end else begin
            acc_reg <= acc;
            sample_reg <= sample;
            weight_reg <= weight;
            in_valid_reg <= in_valid;
            result <= next_result;
            out_valid <= in_valid_reg;
        end
    end
endmodule

`default_nettype wire
