`timescale 1ns/1ps
`default_nettype none

// Black-box conformance harness for the direct TNF linear datapath.
// The expected words are generated independently by oracle/tnf_ref.py.
module tnf_mac_e4m8_tb;
    reg  [15:0] acc;
    reg  [15:0] sample;
    reg  [1:0]  weight;
    wire [15:0] result;

    integer fd;
    integer scan;
    integer checks;
    integer errors;
    reg [15:0] expected;
    reg [1023:0] vector_path;

    tnf_mac_e4m8_top dut (
        .acc(acc),
        .sample(sample),
        .weight(weight),
        .result(result)
    );

    initial begin
        checks = 0;
        errors = 0;
        if (!$value$plusargs("VECTORS=%s", vector_path)) begin
            $display("FAIL: missing +VECTORS=<path>");
            $finish_and_return(2);
        end
        fd = $fopen(vector_path, "r");
        if (fd == 0) begin
            $display("FAIL: cannot open %0s", vector_path);
            $finish_and_return(2);
        end

        while (!$feof(fd)) begin
            scan = $fscanf(fd, "%h %h %h %h\n", acc, sample, weight, expected);
            if (scan == 4) begin
                #1;
                checks = checks + 1;
                if (result !== expected) begin
                    errors = errors + 1;
                    if (errors <= 12)
                        $display("MISMATCH #%0d acc=%h sample=%h weight=%h got=%h expected=%h",
                                 checks, acc, sample, weight, result, expected);
                end
            end
        end
        $fclose(fd);

        if (errors != 0) begin
            $display("FAIL: %0d checks, %0d errors", checks, errors);
            $finish_and_return(1);
        end
        $display("PASS: %0d direct TNF MAC checks, 0 errors", checks);
        $finish_and_return(0);
    end
endmodule

`default_nettype wire
