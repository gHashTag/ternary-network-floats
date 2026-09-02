`timescale 1ns/1ps
`default_nettype none

// Encode one exact common-scale signed integer into packed TNF(E_t=4,M=8).
// exact_value has LSB weight 2^(1-EXP_OFFSET-MANT_W), which is 2^-47 for
// the measured configuration. Normalization and RNE occur exactly once here.
module tnf_exact_to_packed #(
    parameter integer ACC_W      = 96,
    parameter integer MANT_W     = 8,
    parameter integer OFF_W      = 7,
    parameter integer TOTAL      = 16,
    parameter [31:0]  OFFSET_MAX = 80
) (
    input  wire signed [ACC_W-1:0] exact_value,
    input  wire                    special,
    output reg  [TOTAL-1:0]        out_value
);
    wire sign = exact_value[ACC_W-1];
    wire [ACC_W-1:0] magnitude = sign
        ? (~exact_value + {{(ACC_W-1){1'b0}}, 1'b1})
        : exact_value;

    integer i;
    integer msb_index;
    integer offset;
    integer shift_amount;
    reg found;
    reg [MANT_W:0] kept;
    reg guard;
    reg sticky;
    reg round_up;
    reg [MANT_W+1:0] rounded;
    reg [MANT_W-1:0] mantissa;

    always @* begin
        out_value = {TOTAL{1'b0}};
        found = 1'b0;
        msb_index = 0;
        offset = 0;
        shift_amount = 0;
        kept = {(MANT_W+1){1'b0}};
        guard = 1'b0;
        sticky = 1'b0;
        round_up = 1'b0;
        rounded = {(MANT_W+2){1'b0}};
        mantissa = {MANT_W{1'b0}};

        for (i = ACC_W-1; i >= 0; i = i - 1) begin
            if (!found && magnitude[i]) begin
                found = 1'b1;
                msb_index = i;
            end
        end

        if (special) begin
            out_value = {1'b0, OFFSET_MAX[OFF_W-1:0],
                      {(MANT_W-1){1'b0}}, 1'b1};
        end else if (!found) begin
            out_value = {TOTAL{1'b0}};
        end else if (msb_index < MANT_W) begin
            // Half the smallest normal is integer magnitude 2^(MANT_W-1).
            // Ties round to zero because zero is the even endpoint.
            if (magnitude > ({{(ACC_W-1){1'b0}}, 1'b1}
                             << (MANT_W-1)))
                out_value = {sign, {{(OFF_W-1){1'b0}}, 1'b1},
                          {MANT_W{1'b0}}};
        end else begin
            offset = msb_index + 1'b1 - MANT_W;
            if (offset >= OFFSET_MAX) begin
                out_value = {sign, OFFSET_MAX[OFF_W-1:0],
                          {MANT_W{1'b0}}};
            end else begin
                shift_amount = msb_index - MANT_W;
                // The shifted value is intentionally truncated to the leading
                // one plus MANT_W retained bits; guard/sticky are read below.
                /* verilator lint_off WIDTHTRUNC */
                kept = magnitude >> shift_amount;
                /* verilator lint_on WIDTHTRUNC */
                if (shift_amount > 0) begin
                    guard = magnitude[shift_amount-1];
                    if (shift_amount > 1)
                        sticky = |(magnitude &
                                   ~({ACC_W{1'b1}} << (shift_amount-1)));
                end
                round_up = guard & (sticky | kept[0]);
                rounded = {1'b0, kept}
                        + {{(MANT_W+1){1'b0}}, round_up};
                if (rounded[MANT_W+1]) begin
                    offset = offset + 1'b1;
                    mantissa = {MANT_W{1'b0}};
                end else begin
                    mantissa = rounded[MANT_W-1:0];
                end
                if (offset >= OFFSET_MAX)
                    out_value = {sign, OFFSET_MAX[OFF_W-1:0],
                              {MANT_W{1'b0}}};
                else
                    out_value = {sign, offset[OFF_W-1:0], mantissa};
            end
        end
    end
endmodule

`default_nettype wire
