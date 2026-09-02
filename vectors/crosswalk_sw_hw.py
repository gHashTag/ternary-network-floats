#!/usr/bin/env python3
"""Cross-walk: [format x {SW-pack tier | decode-HW Tier-E | compute-HW Tier-E}].

Links the t27 SW conformance packs (INDEX_all_formats.json, this repo) to the
trinity-fpga HW Tier-E state (issue #199). THREE INDEPENDENT AXES -- a format may
be SW-packable yet HW-structural (encoding != compute != FPGA):

  * SW-pack tier   -> from INDEX_all_formats.json (bitexact / selfconsistent / structural)
  * decode-HW      -> Tier-E 4/4 on AX7203 (CI GREEN + SHA256 + UART fails=0 + IDCODE)
  * compute-HW     -> Tier-E 4/4 GF-arithmetic (ADD/MUL) on AX7203

HW state is a POINT-IN-TIME snapshot copied from #199 (2026-07-02..03). Not live.
Terminal HW ceiling on XC7A200T = 71/83 (decode-HW 41 + compute-HW 30);
takum32/64 = routing-failure (unroutable on this part).
"""
import json, os, sys

OUT = os.path.dirname(os.path.abspath(__file__))
IDX = json.load(open(os.path.join(OUT, "INDEX_all_formats.json")))

# --- decode-HW Tier-E cells (41), verbatim from #199 comment scan 2026-07-02..03.
# NOTE: some #199 ids differ from t27 SSOT ids (bf16<->bfloat16, fp8_e4m3<->fp8_e4m3fn,
# mxfp8_e4m3<->mxfp8, mxint8/bitnet/e8m0 are FPGA-side element ids). Mapped below.
DECODE_HW_199 = {
    "bcd","bf16","binary128","binary16","binary32","binary64","bitnet",
    "decimal128","decimal32","decimal64","double_double","e8m0","fp4_e2m1",
    "fp6_e2m3","fp6_e3m2","fp8_e5m2","gf10","gf14","ibm_hfp32","ibm_hfp64",
    "int16","int32","int4","int8","lns16","lns8","ms_mbf32","ms_mbf64",
    "mxfp8_e4m3","mxint8","nf4","posit16","posit32","posit8","quad_double",
    "takum16","takum8","tf32","vax_d","vax_f","vax_g",
}
# id remap #199 -> t27 SSOT id
REMAP = {"bf16":"bfloat16","mxfp8_e4m3":"mxfp8"}
DECODE_HW = {REMAP.get(x, x) for x in DECODE_HW_199}

# --- compute-HW Tier-E cells (GF ADD/MUL), from #199. Counted per (format x op);
# here we mark the FORMAT as compute-HW-proven if any GF-arith op passed on HW.
COMPUTE_HW = {"gf4","gf6","gf8","gf10","gf12","gf14","gf16","gf20","gf24","gf32"}

rows = []
for p in IDX["packs"]:
    fid = p["id"]
    sw = p["kind"]  # bitexact / bitexact_selfconsistent / structural
    dhw = "Tier-E" if fid in DECODE_HW else "-"
    chw = "Tier-E" if fid in COMPUTE_HW else "-"
    rows.append((fid, sw, p.get("n_vectors", 0), dhw, chw))

rows.sort()
sw_be = sum(1 for r in rows if r[1] == "bitexact")
sw_sc = sum(1 for r in rows if r[1] == "bitexact_selfconsistent")
sw_st = sum(1 for r in rows if r[1] == "structural")
dhw_n = sum(1 for r in rows if r[3] == "Tier-E")
chw_n = sum(1 for r in rows if r[4] == "Tier-E")
tier_e_union = sum(1 for r in rows if r[3] == "Tier-E" or r[4] == "Tier-E")

# formats HW-proven but NOT in the t27 SSOT 83 (FPGA-side element ids)
extra_hw = sorted({REMAP.get(x, x) for x in DECODE_HW_199} - {r[0] for r in rows})

out = {
    "schema": "t27-conformance-crosswalk/v0.1",
    "generated_from": "INDEX_all_formats.json (SW) x trinity-fpga #199 (HW, 2026-07-02..03 snapshot)",
    "axes_note": "encoding != compute != FPGA. SW-pack, decode-HW, compute-HW are "
                 "INDEPENDENT. A format may be SW-packable yet HW-structural.",
    "hw_ceiling": "71/83 on XC7A200T (decode-HW 41 + compute-HW 30); takum32/64 unroutable",
    "totals": {
        "sw_bitexact": sw_be, "sw_selfconsistent": sw_sc, "sw_structural": sw_st,
        "decode_hw_tier_e_in_ssot": dhw_n, "compute_hw_tier_e_in_ssot": chw_n,
        "tier_e_union_in_ssot": tier_e_union,
        "hw_ids_outside_ssot83": extra_hw,
    },
    "rows": [
        {"format": r[0], "sw_pack": r[1], "n_vectors": r[2],
         "decode_hw": r[3], "compute_hw": r[4]} for r in rows
    ],
}
with open(os.path.join(OUT, "CROSSWALK_sw_hw.json"), "w") as f:
    json.dump(out, f, indent=2)

# markdown table
lines = ["# Cross-walk: 83 форматов x {SW-пак | decode-HW | compute-HW}", "",
         f"SSOT SW = `INDEX_all_formats.json`; HW = trinity-fpga #199 (снимок 02-03.07.2026, НЕ live).",
         "",
         "> **Три независимые оси** (encoding != compute != FPGA). Формат может иметь "
         "SW-пак и одновременно быть HW-structural — это НЕ противоречие.",
         "",
         f"- SW: bitexact **{sw_be}** / selfconsistent **{sw_sc}** / structural **{sw_st}** = 83",
         f"- decode-HW Tier-E (в SSOT-83): **{dhw_n}**  |  compute-HW Tier-E (в SSOT-83): **{chw_n}**",
         f"- HW-потолок AX7203 = **71/83** (decode 41 + compute 30); takum32/64 = routing-failure",
         f"- HW-ячейки ВНЕ SSOT-83 (FPGA element-id): {', '.join(extra_hw) or '—'}",
         "",
         "| Формат | SW-пак | n | decode-HW | compute-HW |",
         "|---|---|---:|:---:|:---:|"]
for r in rows:
    sw_lbl = {"bitexact":"bit-exact","bitexact_selfconsistent":"self-consist.","structural":"structural"}[r[1]]
    lines.append(f"| `{r[0]}` | {sw_lbl} | {r[2]} | {r[3]} | {r[4]} |")
with open(os.path.join(OUT, "CROSSWALK_sw_hw.md"), "w") as f:
    f.write("\n".join(lines) + "\n")

print(f"SW: bitexact={sw_be} selfconsistent={sw_sc} structural={sw_st} (=83)")
print(f"decode-HW in SSOT={dhw_n}  compute-HW in SSOT={chw_n}  Tier-E union in SSOT={tier_e_union}")
print(f"HW ids outside SSOT-83: {extra_hw}")
print("wrote CROSSWALK_sw_hw.json + CROSSWALK_sw_hw.md")
