`timescale 1ns/1ps
`default_nettype none

module zphi_fanin_tb #(
    parameter integer FANIN = 8,
    parameter integer COORD_W = 16,
    parameter integer OUT_W = COORD_W + 1 + $clog2(FANIN)
);
    localparam integer CASES = 96;
    reg  [FANIN*COORD_W-1:0] a_values;
    reg  [FANIN*COORD_W-1:0] b_values;
    reg  [FANIN*2-1:0]       weights;
    wire [OUT_W-1:0]         result_a;
    wire [OUT_W-1:0]         result_b;
    reg  [OUT_W-1:0]         expected_a;
    reg  [OUT_W-1:0]         expected_b;
    integer fd;
    integer count;
    integer code;
    reg [1023:0] vector_path;

    zphi_dot_tree #(.FANIN(FANIN), .COORD_W(COORD_W)) dut (
        .a_values(a_values), .b_values(b_values), .weights(weights),
        .result_a(result_a), .result_b(result_b)
    );

    initial begin
        if (!$value$plusargs("VECTORS=%s", vector_path)) begin
            $display("FAIL: missing +VECTORS");
            $finish(2);
        end
        fd = $fopen(vector_path, "r");
        if (fd == 0) begin
            $display("FAIL: cannot open vectors");
            $finish(2);
        end
        count = 0;
        while (!$feof(fd)) begin
            code = $fscanf(fd, "%h %h %h %h %h\n", a_values, b_values,
                           weights, expected_a, expected_b);
            if (code == 5) begin
                #1;
                if (result_a !== expected_a || result_b !== expected_b) begin
                    $display("FAIL zphi fanin=%0d case=%0d got=(%h,%h) expected=(%h,%h)",
                             FANIN, count, result_a, result_b,
                             expected_a, expected_b);
                    $finish(1);
                end
                count = count + 1;
            end
        end
        $fclose(fd);
        if (count != CASES) begin
            $display("FAIL zphi fanin=%0d count=%0d expected=%0d",
                     FANIN, count, CASES);
            $finish(1);
        end
        $display("PASS exact-Zphi fanin=%0d checks=%0d", FANIN, count);
        $finish(0);
    end
endmodule

`default_nettype wire
