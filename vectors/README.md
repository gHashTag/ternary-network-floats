# t27 numeric-format conformance vector packs (v0)

Bit-precise (and, where bit-precision is undefined, structural) conformance
vectors for the **complete t27 numeric-format catalog**, in a single shared row
schema so one differ runs across all packs.

- SSOT: https://github.com/gHashTag/t27/blob/master/specs/numeric/formats_catalog.t27
- Format spec: https://github.com/gHashTag/t27/blob/master/conformance/FORMAT-SPEC-001.json
- Cross-walk (SW pack vs decode-HW vs compute-HW): `CROSSWALK_sw_hw.md`
- Anchor identity (ASCII): `phi^2 + 1/phi^2 = 3`
- Context preprint: https://arxiv.org/abs/2606.05017
- Schema tag: `t27-conformance/v0.1`

## Coverage at a glance

The catalog defines **83 numeric formats** across 13 families. This directory
ships **83 conformance packs — one per format**, with no gaps:

| Class | Packs | Meaning |
|---|---|---|
| **Bit-precise** | **69** | Native bits decode to f64 with an independent reference codec (a second witness distinct from the encoder that produced the vectors); `abs_error = 0` by construction for every representable value. Values not exactly representable in a format report a nonzero `abs_error` **honestly** (e.g. 0.1 in bf16) — nothing is hidden. |
| **Self-consistent** | **6** | Wide GoldenFloat rungs (`gf48/96/128/512/1024`) plus the open-bias `gf256` that re-derive under a single dyadic-exact decode law but have **no independent second witness**, so they are deliberately **not** promoted to the stronger bit-precise label (honesty rule #10). |
| **Structural** | **8** | The format has no single fixed radix-2 S:E:M round-trip (parametric / technique / variable-width). These packs carry full catalog metadata plus an explicit `structural_reason` and are marked `bitexact: false`. They are honest placeholders, **not** bit-exact claims. |
| **Total** | **83** | One pack per catalog format. |

> **encoding != compute != FPGA.** This bit-precise label is a **software**
> round-trip claim (decode/encode). A "second witness" here means an independent
> software re-derivation (e.g. the iverilog RTL-simulation decode recorded for
> `gf14`), NOT an on-silicon HW-conformance tier (Tier-E on trinity-fpga #199).
> A format can be SW bit-precise and HW-structural, or vice-versa — see
> `CROSSWALK_sw_hw.md` for all three axes.

Coverage policy (deterministic, reproducible):

- formats <= 8 bits -> **exhaustive** enumeration of every code;
- formats > 8 bits -> a **curated** named vector set (zero, one, two, three,
  half, four, neg_one, neg_three, plus format specials) via explicit encoders —
  no brute force, no multi-megabyte files;
- non-S:E:M formats -> **structural** pack with a documented reason.

## Index — bit-precise packs (69)

| Pack | Format | Vectors | Round-trip |
|---|---|---|---|
| `afp_conformance_v0.json` | AFP | 8 | ✔ (S1E8M7 (bf16-payload) explicit codec; anchor 3.0 exact at 0x4040; abs_error=0) |
| `bcd_conformance_v0.json` | BCD | 100 | ✔ (packed BCD, 100 curated decimal values) |
| `bf16_golden_conformance_v0.json` | BFLOAT16 | 8 | ✔ (pre-existing curated (+golden accumulation)) |
| `binary128_conformance_v0.json` | BINARY128 | 8 | ✔ |
| `binary16_conformance_v0.json` | BINARY16 | 8 | ✔ |
| `binary256_conformance_v0.json` | BINARY256 | 8 | ✔ |
| `binary32_conformance_v0.json` | BINARY32 | 8 | ✔ |
| `binary64_conformance_v0.json` | BINARY64 | 8 | ✔ |
| `cray_float_conformance_v0.json` | CRAY_FLOAT | 8 | ✔ |
| `decimal128_conformance_v0.json` | DECIMAL128 | 8 | ✔ (IEEE 754-2008 BID decode (coeff*10^exp); 3.0 exact) |
| `decimal32_conformance_v0.json` | DECIMAL32 | 7 | ✔ (IEEE 754-2008 BID decode (coeff*10^exp); 3.0 exact) |
| `decimal64_conformance_v0.json` | DECIMAL64 | 7 | ✔ (IEEE 754-2008 BID decode (coeff*10^exp); 3.0 exact) |
| `double_double_conformance_v0.json` | DOUBLE_DOUBLE | 8 | ✔ (Bailey/Hida limb-sum decode (2x binary64); 3.0 exact) |
| `fp4_e2m1_conformance_v0.json` | FP4_E2M1 | 16 | ✔ |
| `fp6_e2m3_conformance_v0.json` | FP6_E2M3 | 64 | ✔ |
| `fp6_e3m2_conformance_v0.json` | FP6_E3M2 | 64 | ✔ |
| `fp8_e4m3fn_conformance_v0.json` | FP8_E4M3 | 14 | ✔ (pre-existing curated) |
| `fp8_e5m2_conformance_v0.json` | FP8_E5M2 | 16 | ✔ (pre-existing curated) |
| `gf10_conformance_v0.json` | GF10 | 8 | ✔ (GoldenFloat phi-aligned S1E3M6, bias 3 (rule e=round(9/phi^2)=3)) |
| `gf12_conformance_v0.json` | GF12 | 8 | ✔ |
| `gf14_conformance_v0.json` | GF14 | 14 | ✔ (GoldenFloat wide rung S1E5M8, bias 15; independent 2nd witness = iverilog exhaustive 16384/16384 (trinity-fpga #239)) |
| `gf16_conformance_v0.json` | GF16 | 21 | ✔ (pre-existing silicon-oracle anchor) |
| `gf20_conformance_v0.json` | GF20 | 8 | ✔ |
| `gf24_conformance_v0.json` | GF24 | 8 | ✔ |
| `gf32_conformance_v0.json` | GF32 | 8 | ✔ |
| `gf4_conformance_v0.json` | GF4 | 16 | ✔ |
| `gf6_conformance_v0.json` | GF6 | 64 | ✔ |
| `gf64_conformance_v0.json` | GF64 | 8 | ✔ |
| `gf8_conformance_v0.json` | GF8 | 256 | ✔ |
| `gf8_bfp_conformance_v0.json` | GF8_BFP | 256 | ✔ |
| `gf_lns_hybrid_conformance_v0.json` | GF_LNS_HYBRID | 8 | ✔ |
| `gfternary_conformance_v0.json` | GFTERNARY | 4 | ✔ (2-bit {-phi,0,+phi}, exhaustive) |
| `ibm_hfp128_conformance_v0.json` | IBM_HFP128 | 8 | ✔ (base-16, named small values) |
| `ibm_hfp32_conformance_v0.json` | IBM_HFP32 | 8 | ✔ (base-16 exponent) |
| `ibm_hfp64_conformance_v0.json` | IBM_HFP64 | 8 | ✔ (base-16 exponent) |
| `int128_conformance_v0.json` | INT128 | 7 | ✔ |
| `int16_conformance_v0.json` | INT16 | 7 | ✔ |
| `int32_conformance_v0.json` | INT32 | 7 | ✔ |
| `int4_conformance_v0.json` | INT4 | 16 | ✔ |
| `int64_conformance_v0.json` | INT64 | 7 | ✔ |
| `int8_conformance_v0.json` | INT8 | 256 | ✔ |
| `lns16_conformance_v0.json` | LNS16 | 5 | ✔ |
| `lns32_conformance_v0.json` | LNS32 | 5 | ✔ |
| `lns64_conformance_v0.json` | LNS64 | 5 | ✔ |
| `lns8_conformance_v0.json` | LNS8 | 256 | ✔ |
| `ms_mbf32_conformance_v0.json` | MS_MBF32 | 8 | ✔ |
| `ms_mbf64_conformance_v0.json` | MS_MBF64 | 8 | ✔ |
| `mxfp4_e2m1_conformance_v0.json` | MXFP4 | 16 | ✔ (pre-existing curated) |
| `mxfp6_conformance_v0.json` | MXFP6 | 64 | ✔ |
| `mxfp8_conformance_v0.json` | MXFP8 | 256 | ✔ |
| `mxgf4_conformance_v0.json` | MXGF4 | 16 | ✔ |
| `mxgf6_conformance_v0.json` | MXGF6 | 64 | ✔ |
| `nf4_conformance_v0.json` | NF4 | 16 | ✔ (16-entry quantile table) |
| `per_channel_scale_conformance_v0.json` | PER_CHANNEL_SCALE | 256 | ✔ (INT8 payload, exhaustive 256 codes, unit scale=1.0; anchor 3.0 at code 0x03) |
| `posit16_conformance_v0.json` | POSIT16 | 8 | ✔ |
| `posit32_conformance_v0.json` | POSIT32 | 8 | ✔ |
| `posit64_conformance_v0.json` | POSIT64 | 8 | ✔ |
| `posit8_conformance_v0.json` | POSIT8 | 256 | ✔ |
| `quad_double_conformance_v0.json` | QUAD_DOUBLE | 8 | ✔ (Bailey/Hida limb-sum decode (4x binary64); 3.0 exact) |
| `takum16_conformance_v0.json` | TAKUM16 | 3 | ✔ (Takum tapered-log, exhaustive 65536 (400-bit witness)) |
| `takum32_conformance_v0.json` | TAKUM32 | 15 | ✔ (Takum tapered-log, curated 15 vec) |
| `takum64_conformance_v0.json` | TAKUM64 | 15 | ✔ (Takum tapered-log, curated 15 vec) |
| `takum8_conformance_v0.json` | TAKUM8 | 256 | ✔ (Takum (Hunhold 2024) tapered-log, exhaustive 8-bit) |
| `tf32_conformance_v0.json` | TF32 | 8 | ✔ |
| `vax_d_conformance_v0.json` | VAX_D | 8 | ✔ |
| `vax_f_conformance_v0.json` | VAX_F | 8 | ✔ |
| `vax_g_conformance_v0.json` | VAX_G | 8 | ✔ |
| `vax_h_conformance_v0.json` | VAX_H | 8 | ✔ |
| `x87_fp80_conformance_v0.json` | X87_FP80 | 8 | ✔ (explicit integer bit) |

`bfloat16` carries an attached `golden_accumulation` section (bf16 reduction
reference for tt-mlir #6252). `gf14` carries an explicit `witnesses[]` array
recording its independent second witness (trinity-fpga #239).

## Index — self-consistent packs (6)

Single dyadic-exact decode law, no independent second witness
(kind=`bitexact_selfconsistent` in the index). Five are wide GoldenFloat rungs;
`gf256` is a wide rung whose bias is an open R&D parameter, so it is recorded
self-consistently rather than promoted. (`gf14`, the sixth Phase-A rung, WAS
promoted to bit-precise once its exhaustive iverilog witness landed — see the
changelog.)

| Pack | Format | n_vec | Note |
|---|---|---|---|
| `gf1024_conformance_v0.json` | GF1024 | 15 | wide-rung GoldenFloat oracle (dyadic-exact, single decode law) |
| `gf128_conformance_v0.json` | GF128 | 15 | wide-rung GoldenFloat oracle (dyadic-exact, single decode law) |
| `gf256_conformance_v0.json` | GF256 | 8 | wide GoldenFloat rung, bias = open R&D parameter (dyadic-exact, single decode law) |
| `gf48_conformance_v0.json` | GF48 | 15 | wide-rung GoldenFloat oracle (dyadic-exact, single decode law) |
| `gf512_conformance_v0.json` | GF512 | 15 | wide-rung GoldenFloat oracle (dyadic-exact, single decode law) |
| `gf96_conformance_v0.json` | GF96 | 15 | wide-rung GoldenFloat oracle (dyadic-exact, single decode law) |

## Index — structural packs (8)

| Pack | Format | Why structural (not bit-exact) |
|---|---|---|
| `block_fp_conformance_v0.json` | BLOCK_FP | This format has no single fixed bit layout (parametric / technique / variable-width). A bit-precise round-trip vector table is not well-defined; the catalog metadata and anchor note are recorded instead. |
| `minifloat_conformance_v0.json` | MINIFLOAT | This format has no single fixed bit layout (parametric / technique / variable-width). A bit-precise round-trip vector table is not well-defined; the catalog metadata and anchor note are recorded instead. |
| `q_format_conformance_v0.json` | Q_FORMAT | This format has no single fixed bit layout (parametric / technique / variable-width). A bit-precise round-trip vector table is not well-defined; the catalog metadata and anchor note are recorded instead. |
| `shared_exp_conformance_v0.json` | SHARED_EXP | This format has no single fixed bit layout (parametric / technique / variable-width). A bit-precise round-trip vector table is not well-defined; the catalog metadata and anchor note are recorded instead. |
| `stochastic_rounding_conformance_v0.json` | STOCHASTIC_ROUNDING | This format has no single fixed bit layout (parametric / technique / variable-width). A bit-precise round-trip vector table is not well-defined; the catalog metadata and anchor note are recorded instead. |
| `tapered_fp_conformance_v0.json` | TAPERED_FP | This format has no single fixed bit layout (parametric / technique / variable-width). A bit-precise round-trip vector table is not well-defined; the catalog metadata and anchor note are recorded instead. |
| `unum_i_conformance_v0.json` | UNUM_I | This format has no single fixed bit layout (parametric / technique / variable-width). A bit-precise round-trip vector table is not well-defined; the catalog metadata and anchor note are recorded instead. |
| `unum_ii_conformance_v0.json` | UNUM_II | This format has no single fixed bit layout (parametric / technique / variable-width). A bit-precise round-trip vector table is not well-defined; the catalog metadata and anchor note are recorded instead. |

These eight entries are genuinely parametric / technique-level (no single fixed
bit layout), so they cannot be promoted without pinning free parameters. They
are recorded structurally rather than forced into a round-trip they do not
satisfy.

## Shared row schema

Each bit-precise vector row carries:

```
name              short label
input_f64         the f64 value (or "NaN" / "Inf" / "-Inf" for specials)
input_f64_hex     big-endian IEEE-754 double hex of input
<fmt>_bits_hex    the native format bit pattern, hex
<fmt>_bits_int    the native format bit pattern, integer
decoded_f64       value after decode back to f64
decoded_f64_hex   big-endian double hex of decoded
abs_error         |input_f64 - decoded_f64| (0 for representable values)
category          one of: zero, subnormal, normal, inf, nan, phi_anchor
```

The bits field is named per format (`gf16_bits_*`, `fp8_bits_*`, …). All other
keys are identical across packs, so one differ tool runs across the whole set.
(A few externally-generated wide-rung packs — e.g. `gf14` — use the compact
WP-29/30 `label/bits/hex/value` row layout; their values were cross-checked
against a plain IEEE decode.)

Structural packs share the top-level metadata block (`schema`, `format`,
`format_name`, `catalog`, `ssot`, `preprint`, `anchor_identity`) but carry
`bitexact: false` and a `structural_reason` instead of a `vectors` array of
round-trips.

## Machine-readable index

`INDEX_all_formats.json` lists all 83 packs with totals
(`total_formats: 83`, `total_packs: 83`, `bitexact_packs: 69`,
`selfconsistent_packs: 6`, `structural_packs: 8`), the anchor identity, the SSOT path, and the preprint.

## SHA-256

```
384a16af29fe5305d07a2eb07f9056cf0b6fe0d97b83eb3f04fcba90f2397f32  afp_conformance_v0.json
637912a0b8d1a4a1e5a50ddafa2c6dbc8e44c7e96218fb8c70763bc69de505cb  bcd_conformance_v0.json
98bbddcbb8a520dc45a6dfed7209c50a0acc0fabc4d3b430359969467eee4e13  bf16_golden_conformance_v0.json
9d08a8a6a10f94e875f73e5f44643f088435a570bfafaef9991464d5377b26e0  binary128_conformance_v0.json
84fd7629430b06d761ac3b92fc85208c472a4582040b1ac2001cc87a6612f7b4  binary16_conformance_v0.json
43d39ae4c4808276ba1ed5b2d8c221c17983a53570da2fc161996b0f7ea3aee3  binary256_conformance_v0.json
9dc16a1c3b65b7f7a5d59c546886ed12e99fb37cbfc9f3d5d45813921e6a70ff  binary32_conformance_v0.json
1d3e3d6daee576ae3b2b4dca6f26560390535fb7441a54b389f98a4238e58bec  binary64_conformance_v0.json
3129fa92145096e55527c2fc22d9e6bed23db1a6d88148e8b711a3b6641a43c1  block_fp_conformance_v0.json
b1a8f6652112be3f49949bafe9f6cd7f46f0271e8f4e19cadb55c2a0e972f503  cray_float_conformance_v0.json
84dbc594340717415385b3bd86eb20432f5430aba047557579f2e2a96de0dc2d  decimal128_conformance_v0.json
e13bc9cd6bc33545ab55f575e23d2343418ded5eddf1395b61f31321dc7d272e  decimal32_conformance_v0.json
fedef68cfe1b910e737574bbe331dc19fbe1724edbd35ec8beac89b1595bea0d  decimal64_conformance_v0.json
f8dc9608093afada65df94852a9b78c3a4a5466415389c5ec359afd19d3b208c  double_double_conformance_v0.json
8ded6625c4644139320dd89b2b7815d6ba27177c35b7d645b2d93b8cfdc63fd9  fp4_e2m1_conformance_v0.json
de70d6aacf0ac2d47decae0866d14f126058176428315d4c767e460c0a9ae5e5  fp6_e2m3_conformance_v0.json
17a80f0a3b5b2495dbcd6de6062d8c1f8ce19b9746d1e370e6d16897ef5f9c02  fp6_e3m2_conformance_v0.json
7193ccd0d330d3e05154432abcec5da4a4c170e11004d4ffa44ff5cbbff9cba9  fp8_e4m3fn_conformance_v0.json
9c31fbd03923bd6555304848a092504dfbc02f72d2be82d2b80f49243e925a18  fp8_e5m2_conformance_v0.json
bb70cbc510d9ac07cb4228e918592734b8b7f658015c80537c8ab597c84d3e72  gf1024_conformance_v0.json
af62499491faf340d7940b0b10ab0208745e57faa97bbe19588fe1d879db485b  gf10_conformance_v0.json
1ff5d68adba8634f644ad49ddecb97f587dd2ed6fc39997118f1e2cc390f6b27  gf128_conformance_v0.json
ea00efde4825931a421ec9feb5910f3ad9ab7ab5d38a77d2c364ea9fa49a7f96  gf12_conformance_v0.json
e2364f36a4cb5812b81d2f8f4253688b4d269201463c8481e18568438114a718  gf14_conformance_v0.json
d1c0eb5bd66247b3c5db9a00a95e29cf4359653aec56f2f9e6827f96898d1509  gf16_conformance_v0.json
76c7814558901d5633cb16ffead7468583de5577c4ccf0378c296c73ae08acc5  gf20_conformance_v0.json
983642c7aea54b7e6c5b6e41edcf20828bfc3a1f2707307eaa713ca5a45e612c  gf24_conformance_v0.json
ff57cf6a48ec3fe1e0bc64ebed758c9af2fb0767286844088d3a61fd6f4dee7d  gf256_conformance_v0.json
f7222e2442f2c106e7f3590e5dbe8ed177603fc2324560987af138ae9abeceb4  gf32_conformance_v0.json
313dcab7d4eb5728895b5a0cd224b6368cbe39dde5583db76a5138f608928550  gf48_conformance_v0.json
25471b7a0e3dc3633118191e722ced2f450a3ed8a6228ad2492f92084f556f96  gf4_conformance_v0.json
7a9be0ebca1e129fbefeb23a5a9bc900beb8215eb856f70c1cc46717ba0189f2  gf512_conformance_v0.json
887223d0bc8b00d76b70238ddbc8933e3a773ed6a9fbc10264d9fdbebca76cd3  gf64_conformance_v0.json
9c9fc955db5f6c9b185bdd5d88bd92f3f21a71ad4d784b944330d5cba85fb724  gf6_conformance_v0.json
fe600234cab0e589b69d84e673d74729cff153f9e4e63e871e285fa82ad2cc70  gf8_bfp_conformance_v0.json
6dccbc6628cbc051e06a006a0731499970c1d99e65fc0d42d9007d8f0ed1402d  gf8_conformance_v0.json
5b2ddc76f1c7a8c0ce50b1e4a8bf8bfcc7d3419916fa3b36780fdd5da02eb0bf  gf96_conformance_v0.json
eb7c946281fb6ed6fadd9c63c7e7fa186412480910c9fedcb25fbc056c1bd34a  gf_lns_hybrid_conformance_v0.json
9f246d24511fbff6fb9e83e60e1bedfce401052537f7c8929fe205d0f6e57b81  gfternary_conformance_v0.json
2f02899d621a8a7aebfdf2a69a2484d7616c61ac7cebdc483f643e8109c4e31f  ibm_hfp128_conformance_v0.json
8e35040e30d3a0091ecca5fdb08d1dd1ce98031e5d655239c7196bc667fc3876  ibm_hfp32_conformance_v0.json
fbe42a167c13f226fe8eaf876c9e17109fb32dbddd76d3a677cc0b9aef2626a1  ibm_hfp64_conformance_v0.json
df77519366e4c59888dcfafa66c20db4389e162f7dae96767684f46d8427d9fc  int128_conformance_v0.json
a14f51cd6b29bef2215573bc7f1d299559d5d34af36fd0ffceb513f0659765b9  int16_conformance_v0.json
e7f8ddbc4f8606a83febb5c8836f38a143c28f650d73330af5650ea698d91570  int32_conformance_v0.json
ec35d81224f9635c21b53165e123d1b6b0ed13ad3c1d7ec830e018df22c46ad1  int4_conformance_v0.json
15e7ae6bd373de5b4f755c71877d6bb662c241526f3a5f4ead22307764f754f5  int64_conformance_v0.json
3e7358f28f5d242e24a46fcf0359e24e21bb4f54834e88b38235fc6332e86978  int8_conformance_v0.json
0b4b9d4ce2162e079239aa05e742c7f699453b96f6a8abd90c17bca95d88eff6  lns16_conformance_v0.json
7877795b137b599bafb64e8c4b114e128a2ef5af433db222b2875e0df6919872  lns32_conformance_v0.json
9969a97f62be45bc120cc2310b5be5c0e6c83d3151a51d6fbb5173db54581ec0  lns64_conformance_v0.json
1cb3ca966b7564b15d6b64b37efb4548fa4b6ff26686576cf5da9ac7657379b8  lns8_conformance_v0.json
d42d1d167c5aa9f504de5ca9ebc04cbd863ff5ebb300fbcb09306413d7b334c3  minifloat_conformance_v0.json
260382da8c40576d046d6d044753522e1c3730e55a4712f21e91b21ad918c365  ms_mbf32_conformance_v0.json
8d750f03d47a4113548a5e57be2201d4b7f5689143b3605a9a51a60b49988ec9  ms_mbf64_conformance_v0.json
b5795fed0c0f2b580174b443d2c54519c4953916525237bb7ea7d6831f14fde7  mxfp4_e2m1_conformance_v0.json
3db420779597b673a691d409b1fc11aee8168549c55be1c8ebfb70dc8330e0c7  mxfp6_conformance_v0.json
16eedca7e82c4e6753f8248dce0000ba9a50ba09bab9be747b0dcac3efc21b6b  mxfp8_conformance_v0.json
5e8d03fe80c59b458dc4bbd3fba3213dbc00626d8bc73b2cfcc09836539e89fb  mxgf4_conformance_v0.json
9d77d8be5522942e9276b723915b3223123b7741a076a1bfd819cc73ab29f1ec  mxgf6_conformance_v0.json
723ddd4237153c7c0cc6a9c3436ba071f8affcef8ad0c384070a3e1a3bf13f45  nf4_conformance_v0.json
d60b7dacff5f609455f5f0da2011ac6ab6f276097d6a21f477d21be82c8457e5  per_channel_scale_conformance_v0.json
7cc2edfeb0f52769b1a536dcbe04945a301cdcc3799a23267380b0c4fb0b82d5  posit16_conformance_v0.json
aee6cc72691a0ae211e39bf6315ac68a5fe74e87190e0c27088871c6ccc87f52  posit32_conformance_v0.json
66b14056938549c1aaa522097ee8744246581cf6d3bb6002cef3b2f3f6ea0ff6  posit64_conformance_v0.json
0c638ef95b6537e4dc0e256dc1ca2d9363152b3d5a800501472230ce98a84b76  posit8_conformance_v0.json
2bc0c114aecd1d0dbfa7925efe298cea80efd510022ee0734cf9450af8027b63  q_format_conformance_v0.json
62ef8067fd1d70ef0abac77d4b0252a3686b9cd698ee4806e0bc1e01bcfe7cfa  quad_double_conformance_v0.json
ca139ebd7bc5c139357c533bb0a6509e4edd05044d7869fcea57cf34d052c3c7  shared_exp_conformance_v0.json
fc2a0a6dcce7bbb0eccc1e23ebdacb9abbd81cd54111796be6dc7e6a87a2071a  stochastic_rounding_conformance_v0.json
924a2e5626df001d2780f542f5aff0c0152a8c819f35866dce2e2152409c1a11  takum16_conformance_v0.json
c5b034ff12169e921ce3a9411a0317ccd85003dde6c71c8461ced3fd73b3c80f  takum32_conformance_v0.json
1c4fc6d0579626ed364e9044aa455df4f1a1984b8b14cd370004498d86f73a0c  takum64_conformance_v0.json
e81b280fbd1a30381c169760b24b5686db82eff8debcc5412cb43d1a0be9a05f  takum8_conformance_v0.json
e20d828fda7d3d6b86d047b390fae2964622b83fb8200220f5a4283bc5ae2b4b  tapered_fp_conformance_v0.json
b35c334092b49dad9a944d37a91697f08f442b633142e81c69296c12bac0055d  tf32_conformance_v0.json
2b28ce1eca1f39623122fbdd853945d05c73adc47e132c250e6ccb56217d689b  unum_i_conformance_v0.json
a79c4cdca84fc702a4ce25fd36040912f841dc9d75f35476e78dbbdfc6fb12f8  unum_ii_conformance_v0.json
b87494ddee38fe68f77dd8082e8a9811530cc346526b80e59c81b17665677792  vax_d_conformance_v0.json
a7f45aec8da42931da5ad9f24c3ee369419ec58a783abe657a275210ae9b1e4d  vax_f_conformance_v0.json
9a6372bbf85a50457e0b66db8849845333582e3fef28934047963e89dd95e65a  vax_g_conformance_v0.json
eaaa44e4ce2e5454da2cc83571bf3261a84a1b6fabb0dc8064c04cd71fa581f0  vax_h_conformance_v0.json
e9be37c939c7108081bd2190e949f4d01be7ad12511d82bb8849f337c94e7e0c  x87_fp80_conformance_v0.json
```

## Provenance

The hand-curated reference packs (byte-stable) come from dedicated generators
(`gen_fp8_e4m3.py`, `gen_fp8_e5m2.py`, `gen_mxfp4_e2m1.py`, `gen_bf16_golden.py`);
`gf16_conformance_v0.json` is the original SSOT silicon-oracle anchor pack; and
`takum8/16/32/64`, `bcd`, `gf14` ship curated / externally-generated vector
sets. The remaining packs (and `INDEX_all_formats.json`) are produced by the
catalog-wide master generator:

```
gen_all_formats.py   # reads the live SSOT, emits one pack per catalog format
```

The generator preserves the pre-existing curated packs verbatim (they are held
in an EXISTING/SELFCONSISTENT registry inside the script), injects the recorded
independent witness into `gf14` (from a WITNESSES registry), and is safe to
re-run:

```
python3 gen_all_formats.py
```

All packs are ASCII-only. Apache-2.0, consistent with the t27 repository.

## Changelog

- **2026-07-04b** — corrected `gf14` from self-consistent back to **bit-precise**.
  gf14 (Phase-A FP32-width GoldenFloat rung, S1E5M8 bias 15) HAS an independent
  second witness: an exhaustive iverilog RTL decode over all 16384 codes via the
  parametric `gf_decode_param #(14,5,8,15)` generator merged in trinity-fpga
  PR #239 (merge `cb845f75f`), abs_error=0 for every code (also confirmed by a
  plain IEEE re-decode). The witness is now recorded in the pack `witnesses[]`
  array. The five wider Phase-B rungs (`gf48/96/128/512/1024`) are NOT covered by
  #239 (FP32-only) and stay self-consistent; `gf256` (open bias) stays
  self-consistent. Net vs the prior draft: bit-precise 68 -> 69,
  self-consistent 7 -> 6, structural 8 (unchanged).

- **2026-07-04** — promoted `afp` and `per_channel_scale` from structural to
  **bit-precise** (explicit reference codecs); added `gf256` as a self-consistent
  wide rung; relabelled `gf48/96/128/512/1024` bit-precise -> self-consistent
  (honesty rule #10). Added `CROSSWALK_sw_hw.md/.json` mapping every format across
  the three independent axes (SW pack | decode-HW Tier-E | compute-HW Tier-E,
  HW snapshot from trinity-fpga #199). The `takum8/16/32/64` and `bcd` curated
  packs were already bit-precise and are unchanged.

- **2026-06-28** — promoted 6 packs from structural to **bit-precise**
  (`gf10`, `decimal32/64/128`, `double_double`, `quad_double`).

- **2026-06-14** — promoted 6 packs from structural to **bit-precise**
  (`ibm_hfp32/64/128`, `x87_fp80`, `nf4`, `gfternary`).

