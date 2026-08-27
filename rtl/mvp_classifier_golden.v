`default_nettype none

// mvp_classifier_golden.v -- golden reference for the IGLA RACE MVP classifier.
//
// WRITTEN FROM THE SPEC HEADER, NOT FROM THE GENERATED RTL.  Every constant and
// every rule below is transcribed from the comment block and the weight
// constants at the top of specs/igla/race/mvp_ternary_classifier.t27, where the
// reference table was computed independently BEFORE any implementation existed.
// Reading the generated Verilog to write this file would make the proof
// circular: it would show the compiler agrees with itself.
//
// The point of this model is that it MULTIPLIES.  Each contribution is a real
// `*` on a signed weight in {-1, 0, +1} and an activation bit.  Proving the
// shipped RTL equivalent to it therefore establishes that the multiplier-free
// implementation computes exactly the integer correlation the spec describes --
// for ALL 256 inputs simultaneously, symbolically, not for the ten the
// on-silicon sweep compares against a table.
//
// Weight codes (specs/numeric/gfternary.t27, pinned by three invariants in the
// spec): 0 = GFT_ZERO, 1 = GFT_POS (+1), 2 = GFT_NEG (-1).  Code 3 does not
// occur in the three templates but is decoded as zero, matching `contrib`,
// whose final else-branch returns 0 for any code that is neither POS nor NEG.
//
// Tie rule: argmax returns the FIRST maximal class.  The spec states this
// explicitly and tests it at x=0 and x=255 where all three scores are equal,
// because an implicit tie rule is where a reference and an implementation
// disagree while both look correct.
//
// Used by fpga/formal/prove_mvp_classifier.ys.
// Refs #1959

module mvp_classifier_golden (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       en,
    input  wire [7:0] x,
    output wire       ready,
    output wire [7:0] result
);
    // ---- The model, transcribed from the spec's constants ----
    //   A: + + + - - 0 0 0     "left"
    //   B: 0 - + + + - 0 0     "middle"
    //   C: 0 0 0 - - + + +     "right"
    localparam [15:0] W_A = 16'b0000001010010101;
    localparam [15:0] W_B = 16'b0000100101011000;
    localparam [15:0] W_C = 16'b0101011010000000;

    // ---- The correlation, computed with a real multiplier ----
    function signed [31:0] score;
        input [15:0] tmpl;
        input [7:0]  xv;
        integer i;
        reg [1:0] code;
        reg signed [31:0] w;
        reg signed [31:0] bit_val;
        begin
            score = 32'sd0;
            for (i = 0; i < 8; i = i + 1) begin
                code    = (tmpl >> (i * 2)) & 2'b11;
                w       = (code == 2'd1) ?  32'sd1 :
                          (code == 2'd2) ? -32'sd1 :
                                            32'sd0;
                bit_val = {31'd0, xv[i]};
                score   = score + (w * bit_val);   // <-- the real `*`
            end
        end
    endfunction

    wire signed [31:0] score_a = score(W_A, x);
    wire signed [31:0] score_b = score(W_B, x);
    wire signed [31:0] score_c = score(W_C, x);

    // ---- argmax, first-maximal wins ----
    assign result = ((score_a >= score_b) && (score_a >= score_c)) ? 8'd0 :
                     (score_b >= score_c)                          ? 8'd1 :
                                                                     8'd2;

    // The spec's port surface is combinational: `ready` is tied high and the
    // clock, reset and enable are unused.  They are present so the miter pairs
    // port-for-port with the generated module.
    assign ready = 1'b1;

    wire _unused = &{1'b0, clk, rst_n, en};
endmodule

`default_nettype wire
