`timescale 1ns/1ps
`default_nettype none

module int_fanin_tb #(
    parameter integer FANIN = 8,
    parameter integer WIDTH = 8
);
    reg  [FANIN*WIDTH-1:0] samples;
    reg  [FANIN*WIDTH-1:0] weights;
    wire [31:0] result;
    reg  [31:0] expected;
    reg  [1023:0] vector_path;
    integer fd;
    integer scan;
    integer checks;
    integer errors;

    signed_int_dot #(.FANIN(FANIN), .WIDTH(WIDTH), .ACC_W(32)) dut (
        .samples(samples), .weights(weights), .result(result)
    );

    initial begin
        checks = 0;
        errors = 0;
        if (!$value$plusargs("VECTORS=%s", vector_path))
            $finish_and_return(2);
        fd = $fopen(vector_path, "r");
        if (fd == 0)
            $finish_and_return(2);
        while (!$feof(fd)) begin
            scan = $fscanf(fd, "%h %h %h\n", samples, weights, expected);
            if (scan == 3) begin
                #1;
                checks = checks + 1;
                if (result !== expected) begin
                    errors = errors + 1;
                    if (errors <= 8)
                        $display("int%0d mismatch fanin=%0d case=%0d got=%h want=%h",
                                 WIDTH, FANIN, checks, result, expected);
                end
            end
        end
        $fclose(fd);
        if (errors != 0)
            $finish_and_return(1);
        $display("PASS int%0d fanin=%0d checks=%0d", WIDTH, FANIN, checks);
        $finish_and_return(0);
    end
endmodule

`default_nettype wire
