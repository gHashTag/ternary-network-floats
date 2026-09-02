`timescale 1ns/1ps
`default_nettype none

// Complete combinational TNF adder.
//
// Packed layout: [sign | balanced-ternary-derived offset | binary mantissa].
// The offset occupies ceil(E_t*log2(3)) binary cells and names only the rows
// 0..OFFSET_MAX.  Rows above OFFSET_MAX have no E_t-trit preimage and are
// treated as special, matching oracle/tnf_ref.py.
//
// This module descends from fpga/tef/tef_add_full.v in gHashTag/trinity-fpga.
// The artifact version closes three boundaries left undefined there: zero
// operands, the reserved special row, and unencodable offset rows.
module tnf_add_full #(
    parameter integer MANT_W     = 8,
    parameter integer OFF_W      = 7,
    parameter integer TOTAL      = 1 + OFF_W + MANT_W,
    parameter [31:0]  OFFSET_MAX = 80
) (
    input  wire [TOTAL-1:0] a,
    input  wire [TOTAL-1:0] b,
    output wire [TOTAL-1:0] y
);
    localparam integer SIG_W = MANT_W + 1;
    localparam integer EXT_W = SIG_W + 3;
    localparam integer SH_W  = (OFF_W > 5) ? OFF_W : 5;
    localparam [SH_W-1:0] EXT_LIMIT = EXT_W[SH_W-1:0];

    wire                    a_sign = a[TOTAL-1];
    wire [OFF_W-1:0]        a_off  = a[TOTAL-2:MANT_W];
    wire [MANT_W-1:0]       a_mant = a[MANT_W-1:0];
    wire                    b_sign = b[TOTAL-1];
    wire [OFF_W-1:0]        b_off  = b[TOTAL-2:MANT_W];
    wire [MANT_W-1:0]       b_mant = b[MANT_W-1:0];

    wire a_zero = (a_off == {OFF_W{1'b0}});
    wire b_zero = (b_off == {OFF_W{1'b0}});
    wire a_special = ({1'b0, a_off} >= {1'b0, OFFSET_MAX[OFF_W-1:0]});
    wire b_special = ({1'b0, b_off} >= {1'b0, OFFSET_MAX[OFF_W-1:0]});

    // The exact oracle maps every operation involving a special or unencodable
    // operand to one canonical quiet-NaN word.
    wire [TOTAL-1:0] canonical_nan = {
        1'b0,
        OFFSET_MAX[OFF_W-1:0],
        {(MANT_W-1){1'b0}}, 1'b1
    };

    // Order finite non-zero operands by magnitude.
    wire a_bigger = (a_off > b_off)
                 || ((a_off == b_off) && (a_mant >= b_mant));
    wire                    hi_sign = a_bigger ? a_sign : b_sign;
    wire [OFF_W-1:0]        hi_off  = a_bigger ? a_off  : b_off;
    wire [MANT_W-1:0]       hi_mant = a_bigger ? a_mant : b_mant;
    wire                    lo_sign = a_bigger ? b_sign : a_sign;
    wire [OFF_W-1:0]        lo_off  = a_bigger ? b_off  : a_off;
    wire [MANT_W-1:0]       lo_mant = a_bigger ? b_mant : a_mant;

    wire subtract = hi_sign ^ lo_sign;
    wire [SH_W-1:0] distance =
        {{(SH_W-OFF_W){1'b0}}, hi_off}
      - {{(SH_W-OFF_W){1'b0}}, lo_off};

    // Align with guard, round, and sticky positions.
    wire [EXT_W-1:0] hi_ext = {1'b1, hi_mant, 3'b000};
    wire [EXT_W-1:0] lo_ext = {1'b1, lo_mant, 3'b000};
    wire [EXT_W-1:0] lo_shifted =
        (distance >= EXT_LIMIT) ? {EXT_W{1'b0}} : (lo_ext >> distance);
    wire sticky = (distance == 0) ? 1'b0
                : (distance >= EXT_LIMIT) ? |lo_ext
                : |(lo_ext & ~({EXT_W{1'b1}} << distance));
    wire [EXT_W-1:0] lo_aligned = {
        lo_shifted[EXT_W-1:1], lo_shifted[0] | sticky
    };

    wire [EXT_W:0] raw = subtract
        ? ({1'b0, hi_ext} - {1'b0, lo_aligned})
        : ({1'b0, hi_ext} + {1'b0, lo_aligned});

    // Addition shifts right by at most one position.  Subtraction may cancel
    // through the whole significand, so it needs full leading-zero normalize.
    integer i;
    reg [EXT_W:0] norm;
    reg [OFF_W+1:0] exponent;
    always @* begin
        i = 0;
        norm = raw;
        exponent = {2'b00, hi_off};
        if (raw[EXT_W]) begin
            norm = (raw >> 1) | {{EXT_W{1'b0}}, raw[0]};
            exponent = exponent + 1'b1;
        end else begin
            for (i = 0; i < SIG_W; i = i + 1) begin
                if (!norm[EXT_W-1] && (exponent != 0)) begin
                    norm = norm << 1;
                    exponent = exponent - 1'b1;
                end
            end
        end
    end

    // RNE on the three low positions.
    wire guard = norm[2];
    wire round_bit = norm[1];
    wire stick_bit = norm[0];
    wire [MANT_W:0] kept = norm[EXT_W-1 -: (MANT_W+1)];
    wire round_up = guard & (round_bit | stick_bit | kept[0]);
    wire [MANT_W+1:0] rounded =
        {1'b0, kept} + {{(MANT_W+1){1'b0}}, round_up};
    wire renormalize = rounded[MANT_W+1];
    wire [OFF_W+1:0] final_exponent =
        renormalize ? (exponent + 1'b1) : exponent;

    wire exact_zero = (raw == 0);
    wire underflow = !exact_zero && (exponent == 0);
    wire [EXT_W:0] half_min_normal = {
        1'b0, 1'b1, {(EXT_W-1){1'b0}}
    };
    wire underflow_rounds_up = underflow && (norm > half_min_normal);
    wire overflow = (final_exponent
                   >= {2'b00, OFFSET_MAX[OFF_W-1:0]});

    wire [MANT_W-1:0] rounded_mantissa = renormalize
        ? rounded[MANT_W -: MANT_W]
        : rounded[MANT_W-1:0];

    wire [TOTAL-1:0] finite_result = exact_zero
        ? {TOTAL{1'b0}}
        : underflow_rounds_up
            ? {hi_sign, {{(OFF_W-1){1'b0}}, 1'b1}, {MANT_W{1'b0}}}
        : underflow
            ? {hi_sign, {(TOTAL-1){1'b0}}}
        : overflow
            ? {hi_sign, OFFSET_MAX[OFF_W-1:0], {MANT_W{1'b0}}}
        : {hi_sign, final_exponent[OFF_W-1:0], rounded_mantissa};

    assign y = (a_special || b_special) ? canonical_nan
             : (a_zero && b_zero) ? {TOTAL{1'b0}}
             : a_zero ? b
             : b_zero ? a
             : finite_result;
endmodule

`default_nettype wire
