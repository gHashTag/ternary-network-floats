`timescale 1ns/1ps
`default_nettype none

module tnf_deferred_fanin_tb #(
    parameter integer FANIN = 8
);
    localparam integer CASES = 96;
    reg  [FANIN*16-1:0] samples;
    reg  [FANIN*2-1:0]  weights;
    wire [15:0]          result;
    reg  [15:0]          expected;
    integer              fd;
    integer              count;
    integer              code;
    reg [1023:0]         vector_path;

    tnf_deferred_dot #(.FANIN(FANIN)) dut (
        .samples(samples), .weights(weights), .result(result)
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
            code = $fscanf(fd, "%h %h %h\n", samples, weights, expected);
            if (code == 3) begin
                #1;
                if (result !== expected) begin
                    $display("FAIL fanin=%0d case=%0d got=%h expected=%h",
                             FANIN, count, result, expected);
                    $finish(1);
                end
                count = count + 1;
            end
        end
        $fclose(fd);
        if (count != CASES) begin
            $display("FAIL fanin=%0d count=%0d expected=%0d",
                     FANIN, count, CASES);
            $finish(1);
        end
        $display("PASS deferred-TNF fanin=%0d checks=%0d", FANIN, count);
        $finish(0);
    end
endmodule

`default_nettype wire
