#!/usr/bin/env python3
"""Measure exact fully unrolled Z[phi] pair dot trees."""

import collections
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "measurements" / "exact-zphi-fanin"
DIRECT = ROOT / "measurements" / "direct-tnf-fanin" / "result.json"
DEFERRED = ROOT / "measurements" / "deferred-tnf-fanin" / "result.json"
FANINS = (8, 16, 32, 64)
COORD_W = 16
SOURCES = [
    ROOT / "rtl" / "zphi_dot_tree.v",
    ROOT / "tests" / "zphi_fanin_tb.v",
    ROOT / "tests" / "test_zphi_fanin_artifact.py",
    ROOT / "measure_zphi_fanin.py",
    OUT / "BENCHMARK_CONTRACT.md",
    DIRECT,
    DEFERRED,
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wrapper(fanin):
    out_w = COORD_W + 1 + (fanin.bit_length() - 1)
    return f"""module bench_top (
  input wire [{fanin*COORD_W-1}:0] a_values,
  input wire [{fanin*COORD_W-1}:0] b_values,
  input wire [{fanin*2-1}:0] weights,
  output wire [{out_w-1}:0] result_a,
  output wire [{out_w-1}:0] result_b
);
  zphi_dot_tree #(.FANIN({fanin}), .COORD_W({COORD_W})) u (.*);
endmodule
"""


def synthesize(fanin, tmp):
    arm = f"zphi-f{fanin}"
    arm_dir = OUT / arm
    arm_dir.mkdir(parents=True, exist_ok=True)
    wrapper_source = wrapper(fanin)
    wrapper_path = tmp / f"{arm}-top.v"
    wrapper_path.write_text(wrapper_source, encoding="ascii")
    netlist = tmp / f"{arm}.json"
    log = arm_dir / "yosys.log"
    options = "-family xc7 -top bench_top -flatten -nodsp"
    script = (
        f"read_verilog -sv rtl/zphi_dot_tree.v {wrapper_path}; "
        f"synth_xilinx {options} -run begin:coarse; "
        "techmap -map +/cmp2lut.v -map +/cmp2lcu.v -D LUT_WIDTH=6; "
        "alumacc; share -fast; opt; memory -nomap; opt_clean; "
        f"synth_xilinx {options} -run map_memory:check; "
        "select -clear; select bench_top; "
        f"write_json -selected {netlist}; stat"
    )
    print(f"synthesizing {arm}", flush=True)
    started = time.monotonic()
    subprocess.run(["yosys", "-ql", str(log), "-p", script],
                   cwd=ROOT, check=True)
    elapsed = time.monotonic() - started
    module = json.loads(netlist.read_text(encoding="utf-8"))["modules"]["bench_top"]
    cells = collections.Counter(cell["type"] for cell in module["cells"].values())
    latches = {name: count for name, count in cells.items() if name.startswith("LD")}
    if latches:
        raise SystemExit(f"{arm}: latch gate failed: {latches}")
    if cells["DSP48E1"]:
        raise SystemExit(f"{arm}: DSP gate failed: {cells['DSP48E1']}")
    input_bits = sum(len(port["bits"]) for port in module["ports"].values()
                     if port["direction"] == "input")
    expected_inputs = fanin * (2 * COORD_W + 2)
    if input_bits != expected_inputs or cells["IBUF"] != expected_inputs:
        raise SystemExit(f"{arm}: visibility failed: ports={input_bits}, "
                         f"IBUF={cells['IBUF']}, expected={expected_inputs}")
    compressed = log.with_suffix(".log.gz")
    compressed.write_bytes(gzip.compress(log.read_bytes(), compresslevel=9,
                                         mtime=0))
    log.unlink()
    return {
        "fanin": fanin,
        "coordinate_input_bits": COORD_W,
        "coordinate_output_bits": COORD_W + 1 + (fanin.bit_length() - 1),
        "input_port_bits": input_bits,
        "lut": sum(cells[f"LUT{i}"] for i in range(1, 7)),
        "carry4": cells["CARRY4"],
        "muxf7": cells["MUXF7"],
        "muxf8": cells["MUXF8"],
        "ff": sum(count for name, count in cells.items() if name.startswith("FD")),
        "dsp48e1": cells["DSP48E1"],
        "synthesis_wall_seconds": elapsed,
        "cells_by_type": dict(sorted(cells.items())),
        "wrapper_sha256": hashlib.sha256(wrapper_source.encode("ascii")).hexdigest(),
        "raw_log": str(compressed.relative_to(ROOT)),
        "raw_log_sha256": digest(compressed),
    }


def main():
    for tool in ("python3", "iverilog", "vvp", "yosys"):
        if shutil.which(tool) is None:
            raise SystemExit(f"missing required tool: {tool}")
    OUT.mkdir(parents=True, exist_ok=True)
    subprocess.run(["python3", "tests/test_zphi_fanin_artifact.py"],
                   cwd=ROOT, check=True)
    with tempfile.TemporaryDirectory(prefix="zphi-measure-") as name:
        arms = [synthesize(fanin, Path(name)) for fanin in FANINS]

    direct_data = json.loads(DIRECT.read_text(encoding="ascii"))
    deferred_data = json.loads(DEFERRED.read_text(encoding="ascii"))
    direct = {row["fanin"]: row for row in direct_data["arms"]
              if row["format"] == "tnf"}
    int4 = {row["fanin"]: row for row in direct_data["arms"]
            if row["format"] == "int4"}
    int8 = {row["fanin"]: row for row in direct_data["arms"]
            if row["format"] == "int8"}
    deferred = {row["fanin"]: row for row in deferred_data["arms"]}
    comparisons = []
    for row in arms:
        fanin = row["fanin"]
        comparisons.append({
            "fanin": fanin,
            "direct_packed_lut_over_zphi_lut": direct[fanin]["lut"] / row["lut"],
            "deferred_packed_lut_over_zphi_lut": deferred[fanin]["lut"] / row["lut"],
            "zphi_lut_over_int4_lut": row["lut"] / int4[fanin]["lut"],
            "zphi_lut_over_int8_lut": row["lut"] / int8[fanin]["lut"],
            "claim_boundary": "post-synthesis structural only; transport widths and numerical contracts are not matched",
        })
    result = {
        "schema": "exact-zphi-fanin-synthesis-v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "contract": "measurements/exact-zphi-fanin/BENCHMARK_CONTRACT.md",
        "source_sha256": {str(path.relative_to(ROOT)): digest(path) for path in SOURCES},
        "tools": {
            "yosys": subprocess.check_output(["yosys", "-V"], text=True).strip(),
            "iverilog": subprocess.check_output(["iverilog", "-V"], text=True,
                                                stderr=subprocess.STDOUT).splitlines()[0],
        },
        "simulation": {"arms": 4, "vectors_per_arm": 96, "errors": 0},
        "synthesis_policy": "xc7 -flatten -nodsp; documented coarse sequence with share -fast",
        "arms": arms,
        "comparisons": comparisons,
        "negative_results": [
            "No conversion to or from packed TNF is included.",
            "The pair representation uses 34 input bits per lane and is not storage-matched to packed TNF, int8, or int4.",
            "No P&R, timing, power, memory-traffic, nonlinear-activation, or workload claim is made.",
        ],
    }
    output = OUT / "result.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    for row in arms:
        comp = next(x for x in comparisons if x["fanin"] == row["fanin"])
        print(f"f{row['fanin']:<2} LUT={row['lut']:<6} CARRY4={row['carry4']:<4} "
              f"DSP={row['dsp48e1']} direct/zphi="
              f"{comp['direct_packed_lut_over_zphi_lut']:.3f}x")
    print(f"wrote {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
