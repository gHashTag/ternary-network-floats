#!/usr/bin/env python3
"""Reproduce simulation, synthesis, and optional post-route TNF MAC evidence."""

import argparse
import collections
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent
RTL = [
    ROOT / "rtl" / "tnf_weight_apply.v",
    ROOT / "rtl" / "tnf_add_full.v",
    ROOT / "rtl" / "tnf_mac.v",
    ROOT / "rtl" / "tnf_mac_e4m8_top.v",
    ROOT / "rtl" / "tnf_mac_e4m8_pnr_top.v",
]
TOP = "tnf_mac_e4m8_pnr_top"
XDC = ROOT / "constraints" / "tnf_mac_e4m8.xdc"
VERIFICATION = [
    ROOT / "tests" / "tnf_mac_e4m8_tb.v",
    ROOT / "tests" / "test_direct_tnf_artifact.py",
    ROOT / "oracle" / "tnf_ref.py",
    ROOT / "measure_tnf_rtl.py",
]


def run(command, *, cwd=ROOT, stdout=None, stderr=None):
    subprocess.run(command, cwd=cwd, check=True, stdout=stdout, stderr=stderr)


def output(command):
    return subprocess.check_output(command, cwd=ROOT, text=True,
                                   stderr=subprocess.STDOUT).strip()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact_path(path):
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def extract_last(pattern, text, cast=int):
    found = re.findall(pattern, text, re.MULTILINE)
    if not found:
        raise RuntimeError(f"pattern not found: {pattern}")
    return cast(found[-1])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir", type=Path,
        default=ROOT / "measurements" / "direct-tnf-mac-e4m8",
    )
    parser.add_argument("--chipdb", type=Path)
    parser.add_argument("--seeds", type=int, default=5)
    args = parser.parse_args()

    for tool in ("python3", "iverilog", "vvp", "yosys"):
        if shutil.which(tool) is None:
            raise SystemExit(f"missing required tool: {tool}")
    if args.chipdb and shutil.which("nextpnr-xilinx") is None:
        raise SystemExit("--chipdb requires nextpnr-xilinx")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    run(["python3", "tests/test_direct_tnf_artifact.py"])

    source_hashes = {
        str(path.relative_to(ROOT)): digest(path)
        for path in RTL + VERIFICATION
    }
    source_hashes[str(XDC.relative_to(ROOT))] = digest(XDC)

    with tempfile.TemporaryDirectory(prefix="tnf-measure-") as tmp_name:
        tmp = Path(tmp_name)
        netlist = tmp / "tnf_mac.json"
        yosys_log = args.output_dir / "yosys.log"
        yosys_script = (
            "read_verilog -sv "
            + " ".join(str(path.relative_to(ROOT)) for path in RTL)
            + f"; synth_xilinx -family xc7 -top {TOP} -flatten -nodsp"
            + f"; write_json {netlist}; stat"
        )
        run(["yosys", "-ql", str(yosys_log), "-p", yosys_script])

        design = json.loads(netlist.read_text(encoding="utf-8"))
        cells = design["modules"][TOP]["cells"]
        cell_types = collections.Counter(cell["type"] for cell in cells.values())
        lut_count = sum(cell_types[f"LUT{i}"] for i in range(1, 7))
        synth = {
            "lut": lut_count,
            "carry4": cell_types["CARRY4"],
            "ff": sum(value for name, value in cell_types.items()
                      if name.startswith("FD")),
            "dsp48e1": cell_types["DSP48E1"],
            "cells_by_type": dict(sorted(cell_types.items())),
            "raw_log": artifact_path(yosys_log),
            "raw_log_sha256": digest(yosys_log),
        }
        if synth["dsp48e1"] != 0:
            raise SystemExit(f"DSP gate failed: {synth['dsp48e1']}")
        latch_cells = {
            name: value for name, value in cell_types.items()
            if name.startswith("LD")
        }
        if latch_cells:
            raise SystemExit(f"latch gate failed: {latch_cells}")

        routed = []
        if args.chipdb:
            if not args.chipdb.is_file():
                raise SystemExit(f"chipdb not found: {args.chipdb}")
            for seed in range(1, args.seeds + 1):
                pnr_log = args.output_dir / f"nextpnr-seed{seed}.log"
                fasm = tmp / f"seed{seed}.fasm"
                command = [
                    "nextpnr-xilinx",
                    "--chipdb", str(args.chipdb),
                    "--json", str(netlist),
                    "--xdc", str(XDC),
                    "--fasm", str(fasm),
                    "--freq", "50",
                    "--placer", "heap",
                    "--router", "router2",
                    "--seed", str(seed),
                ]
                with pnr_log.open("w", encoding="utf-8") as handle:
                    run(command, stdout=handle, stderr=subprocess.STDOUT)
                text = pnr_log.read_text(encoding="utf-8")
                if "No clocks found in design" in text:
                    raise SystemExit(f"clock gate failed at seed {seed}: no clock")
                if "failed to find a route using dedicated resources" in text:
                    raise SystemExit(
                        f"clock gate failed at seed {seed}: non-dedicated route"
                    )
                row = {
                    "seed": seed,
                    "lut": extract_last(r"^Info:\s+SLICE_LUTX:\s+(\d+)/", text),
                    "ff": extract_last(r"^Info:\s+SLICE_FFX:\s+(\d+)/", text),
                    "carry4": extract_last(r"^Info:\s+CARRY4:\s+(\d+)/", text),
                    "dsp48e1": extract_last(r"^Info:\s+DSP48E1:\s+(\d+)/", text),
                    "fmax_mhz": extract_last(
                        r"Max frequency for clock .*?:\s+([0-9.]+)\s+MHz",
                        text, float,
                    ),
                    "target_mhz": 50.0,
                    "raw_log": artifact_path(pnr_log),
                    "raw_log_sha256": digest(pnr_log),
                }
                if row["dsp48e1"] != 0:
                    raise SystemExit(f"DSP gate failed at seed {seed}")
                row["target_met"] = row["fmax_mhz"] >= row["target_mhz"]
                routed.append(row)

    result = {
        "schema": "tnf-direct-rtl-measurement-v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "design": {
            "top": TOP,
            "format": "TNF(E_t=4,M=8)",
            "stored_width_bits": 16,
            "operation": "one ternary weight application plus one TNF RNE add",
            "boundary": (
                "Register-to-register top including both register banks and "
                "package I/O; this is a fresh direct-TNF measurement, not the "
                "historical paper neuron harness."
            ),
            "source_sha256": source_hashes,
        },
        "tools": {
            "yosys": output(["yosys", "-V"]),
            "iverilog": output(["iverilog", "-V"]).splitlines()[0],
            "nextpnr_xilinx": (
                output(["nextpnr-xilinx", "--version"]).splitlines()[0]
                if routed else None
            ),
            "chipdb": str(args.chipdb.resolve()) if args.chipdb else None,
            "part": args.chipdb.stem if args.chipdb else None,
            "chipdb_sha256": digest(args.chipdb) if args.chipdb else None,
        },
        "commands": {
            "simulation": "python3 tests/test_direct_tnf_artifact.py",
            "synthesis": (
                "yosys -p 'read_verilog -sv "
                + " ".join(str(path.relative_to(ROOT)) for path in RTL)
                + f"; synth_xilinx -family xc7 -top {TOP} -flatten -nodsp"
                + "; write_json <tmp>/tnf_mac.json; stat'"
            ),
            "place_and_route": (
                "nextpnr-xilinx --placer heap --router router2 --freq 50 "
                "--seed <1..N> --chipdb <path> --json <netlist> "
                "--xdc constraints/tnf_mac_e4m8.xdc --fasm <output>"
                if routed else None
            ),
        },
        "simulation": {"vectors": 5000, "errors": 0},
        "synthesis": synth,
        "place_and_route": {
            "seeds": routed,
            "fmax_median_mhz": statistics.median(
                row["fmax_mhz"] for row in routed
            ) if routed else None,
            "fmax_min_mhz": min(
                (row["fmax_mhz"] for row in routed), default=None
            ),
            "fmax_max_mhz": max(
                (row["fmax_mhz"] for row in routed), default=None
            ),
        },
    }
    result_path = args.output_dir / "result.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(json.dumps(result, indent=2))
    print(f"wrote {artifact_path(result_path)}")


if __name__ == "__main__":
    main()
