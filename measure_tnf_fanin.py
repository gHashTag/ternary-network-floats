#!/usr/bin/env python3
"""Measure direct TNF and native int4/int8 fully unrolled dot trees."""

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
OUT = ROOT / "measurements" / "direct-tnf-fanin"
FANINS = (8, 16, 32, 64)
SOURCES = [
    ROOT / "rtl" / "tnf_weight_apply.v",
    ROOT / "rtl" / "tnf_add_full.v",
    ROOT / "rtl" / "tnf_dot_tree.v",
    ROOT / "rtl" / "signed_int_dot.v",
    ROOT / "tests" / "tnf_fanin_tb.v",
    ROOT / "tests" / "int_fanin_tb.v",
    ROOT / "tests" / "test_tnf_fanin_artifact.py",
    ROOT / "oracle" / "tnf_ref.py",
    ROOT / "measure_tnf_fanin.py",
    OUT / "BENCHMARK_CONTRACT.md",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tool_output(command):
    return subprocess.check_output(
        command, cwd=ROOT, text=True, stderr=subprocess.STDOUT
    ).strip()


def wrapper(kind, fanin):
    if kind == "tnf":
        sample_bits = fanin * 16
        weight_bits = fanin * 2
        body = f"tnf_dot_tree #(.FANIN({fanin})) u (.*);"
        result_bits = 16
    else:
        width = int(kind[3:])
        sample_bits = fanin * width
        weight_bits = sample_bits
        body = (
            f"signed_int_dot #(.FANIN({fanin}), .WIDTH({width}), "
            ".ACC_W(32)) u (.*);"
        )
        result_bits = 32
    return (
        "module bench_top (\n"
        f"  input wire [{sample_bits - 1}:0] samples,\n"
        f"  input wire [{weight_bits - 1}:0] weights,\n"
        f"  output wire [{result_bits - 1}:0] result\n"
        ");\n"
        f"  {body}\n"
        "endmodule\n"
    )


def design_sources(kind):
    if kind == "tnf":
        return [
            ROOT / "rtl" / "tnf_weight_apply.v",
            ROOT / "rtl" / "tnf_add_full.v",
            ROOT / "rtl" / "tnf_dot_tree.v",
        ]
    return [ROOT / "rtl" / "signed_int_dot.v"]


def synthesize(kind, fanin, tmp):
    arm = f"{kind}-f{fanin}"
    arm_dir = OUT / arm
    arm_dir.mkdir(parents=True, exist_ok=True)
    wrapper_path = tmp / f"{arm}-top.v"
    netlist = tmp / f"{arm}.json"
    wrapper_source = wrapper(kind, fanin)
    wrapper_path.write_text(wrapper_source, encoding="ascii")
    log = arm_dir / "yosys.log"
    sources = design_sources(kind)
    synth_options = "-family xc7 -top bench_top -flatten -nodsp"
    # The stock coarse stage calls the exhaustive SAT-based `share` pass. Its
    # pairwise search did not complete TNF fan-in 64 after 35 minutes. Run the
    # documented coarse sequence explicitly with `share -fast`, then resume the
    # standard synth_xilinx script. The same policy is applied to every arm.
    script = (
        "read_verilog -sv "
        + " ".join(str(p.relative_to(ROOT)) for p in sources)
        + f" {wrapper_path}; synth_xilinx {synth_options} -run begin:coarse; "
        + "techmap -map +/cmp2lut.v -map +/cmp2lcu.v -D LUT_WIDTH=6; "
        + "alumacc; share -fast; opt; memory -nomap; opt_clean; "
        + f"synth_xilinx {synth_options} -run map_memory:check; "
        + "select -clear; select bench_top; "
        + f"write_json -selected {netlist}; stat"
    )
    print(f"synthesizing {arm}", flush=True)
    started = time.monotonic()
    subprocess.run(["yosys", "-ql", str(log), "-p", script],
                   cwd=ROOT, check=True)
    elapsed_seconds = time.monotonic() - started
    module = json.loads(netlist.read_text(encoding="utf-8"))["modules"]["bench_top"]
    cells = collections.Counter(cell["type"] for cell in module["cells"].values())
    latches = {name: count for name, count in cells.items() if name.startswith("LD")}
    if latches:
        raise SystemExit(f"{arm}: latch gate failed: {latches}")
    if cells["DSP48E1"]:
        raise SystemExit(f"{arm}: DSP gate failed: {cells['DSP48E1']}")
    input_bits = sum(len(port["bits"]) for port in module["ports"].values()
                     if port["direction"] == "input")
    expected_inputs = fanin * (18 if kind == "tnf" else 2 * int(kind[3:]))
    if input_bits != expected_inputs or cells["IBUF"] != expected_inputs:
        raise SystemExit(
            f"{arm}: operand visibility gate failed: ports={input_bits}, "
            f"IBUF={cells['IBUF']}, expected={expected_inputs}"
        )
    compressed_log = log.with_suffix(log.suffix + ".gz")
    compressed_log.write_bytes(gzip.compress(log.read_bytes(), compresslevel=9,
                                              mtime=0))
    log.unlink()
    return {
        "format": kind,
        "fanin": fanin,
        "topology": "fully-unrolled-balanced-tree",
        "sample_bits_each": 16 if kind == "tnf" else int(kind[3:]),
        "weight_bits_each": 2 if kind == "tnf" else int(kind[3:]),
        "accumulator_bits": 16 if kind == "tnf" else 32,
        "input_port_bits": input_bits,
        "lut": sum(cells[f"LUT{i}"] for i in range(1, 7)),
        "carry4": cells["CARRY4"],
        "muxf7": cells["MUXF7"],
        "muxf8": cells["MUXF8"],
        "ff": sum(count for name, count in cells.items() if name.startswith("FD")),
        "dsp48e1": cells["DSP48E1"],
        "synthesis_wall_seconds": elapsed_seconds,
        "cells_by_type": dict(sorted(cells.items())),
        "wrapper_sha256": hashlib.sha256(wrapper_source.encode("ascii")).hexdigest(),
        "raw_log": str(compressed_log.relative_to(ROOT)),
        "raw_log_sha256": digest(compressed_log),
    }


def main():
    for tool in ("python3", "iverilog", "vvp", "yosys"):
        if shutil.which(tool) is None:
            raise SystemExit(f"missing required tool: {tool}")
    OUT.mkdir(parents=True, exist_ok=True)
    subprocess.run(["python3", "tests/test_tnf_fanin_artifact.py"],
                   cwd=ROOT, check=True)
    with tempfile.TemporaryDirectory(prefix="tnf-fanin-measure-") as name:
        tmp = Path(name)
        arms = [synthesize(kind, fanin, tmp)
                for fanin in FANINS for kind in ("tnf", "int4", "int8")]

    by_key = {(row["format"], row["fanin"]): row for row in arms}
    comparisons = []
    for fanin in FANINS:
        tnf_lut = by_key[("tnf", fanin)]["lut"]
        comparisons.append({
            "fanin": fanin,
            "tnf_lut_over_int4_lut": tnf_lut / by_key[("int4", fanin)]["lut"],
            "tnf_lut_over_int8_lut": tnf_lut / by_key[("int8", fanin)]["lut"],
            "int4_lut_over_tnf_lut": by_key[("int4", fanin)]["lut"] / tnf_lut,
            "int8_lut_over_tnf_lut": by_key[("int8", fanin)]["lut"] / tnf_lut,
            "claim_boundary": (
                "native-format post-synthesis structural ratio; not matched "
                "accuracy, storage width, timing, power, or model quality"
            ),
        })
    result = {
        "schema": "tnf-direct-fanin-synthesis-v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "contract": "measurements/direct-tnf-fanin/BENCHMARK_CONTRACT.md",
        "source_sha256": {
            str(path.relative_to(ROOT)): digest(path) for path in SOURCES
        },
        "tools": {
            "yosys": tool_output(["yosys", "-V"]),
            "iverilog": tool_output(["iverilog", "-V"]).splitlines()[0],
        },
        "simulation": {"arms": 12, "vectors_per_arm": 96, "errors": 0},
        "synthesis_command": (
            "yosys -p 'read_verilog -sv <arm sources> <generated wrapper>; "
            "synth_xilinx -family xc7 -top bench_top -flatten -nodsp "
            "-run begin:coarse; techmap -map +/cmp2lut.v -map "
            "+/cmp2lcu.v -D LUT_WIDTH=6; alumacc; share -fast; opt; "
            "memory -nomap; opt_clean; synth_xilinx -family xc7 -top "
            "bench_top -flatten -nodsp -run map_memory:check; select -clear; "
            "select bench_top; write_json -selected "
            "<tmp>/<arm>.json; stat'"
        ),
        "arms": arms,
        "comparisons": comparisons,
        "negative_results": [
            "No P&R: the fully unrolled fan-in-64 interfaces exceed the package I/O budget.",
            "The native TNF, int4, and int8 representations do not have matched accuracy or range.",
            "Direct packed-TNF RNE trees use more LUTs than both native integer baselines at every measured fan-in.",
            "No universal superiority claim follows from these structural synthesis ratios.",
        ],
    }
    output = OUT / "result.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    for row in arms:
        print(f"{row['format']:>4} f{row['fanin']:<2} "
              f"LUT={row['lut']:<6} CARRY4={row['carry4']:<5} "
              f"DSP={row['dsp48e1']}")
    print(f"wrote {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
