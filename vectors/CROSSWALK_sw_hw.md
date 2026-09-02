# Cross-walk: 83 форматов x {SW-пак | decode-HW | compute-HW}

SSOT SW = `INDEX_all_formats.json`; HW = trinity-fpga #199 (снимок 02-03.07.2026, НЕ live).

> **Три независимые оси** (encoding != compute != FPGA). Формат может иметь SW-пак и одновременно быть HW-structural — это НЕ противоречие.

- SW: bitexact **69** / selfconsistent **6** / structural **8** = 83
- decode-HW Tier-E (в SSOT-83): **38**  |  compute-HW Tier-E (в SSOT-83): **10**
- HW-потолок AX7203 = **71/83** (decode 41 + compute 30); takum32/64 = routing-failure
- HW-ячейки ВНЕ SSOT-83 (FPGA element-id): bitnet, e8m0, mxint8

| Формат | SW-пак | n | decode-HW | compute-HW |
|---|---|---:|:---:|:---:|
| `afp` | bit-exact | 8 | - | - |
| `bcd` | bit-exact | 0 | Tier-E | - |
| `bfloat16` | bit-exact | 0 | Tier-E | - |
| `binary128` | bit-exact | 8 | Tier-E | - |
| `binary16` | bit-exact | 8 | Tier-E | - |
| `binary256` | bit-exact | 8 | - | - |
| `binary32` | bit-exact | 8 | Tier-E | - |
| `binary64` | bit-exact | 8 | Tier-E | - |
| `block_fp` | structural | 0 | - | - |
| `cray_float` | bit-exact | 8 | - | - |
| `decimal128` | bit-exact | 8 | Tier-E | - |
| `decimal32` | bit-exact | 7 | Tier-E | - |
| `decimal64` | bit-exact | 7 | Tier-E | - |
| `double_double` | bit-exact | 8 | Tier-E | - |
| `fp4_e2m1` | bit-exact | 16 | Tier-E | - |
| `fp6_e2m3` | bit-exact | 64 | Tier-E | - |
| `fp6_e3m2` | bit-exact | 64 | Tier-E | - |
| `fp8_e4m3` | bit-exact | 0 | - | - |
| `fp8_e5m2` | bit-exact | 0 | Tier-E | - |
| `gf10` | bit-exact | 8 | Tier-E | Tier-E |
| `gf1024` | self-consist. | 0 | - | - |
| `gf12` | bit-exact | 8 | - | Tier-E |
| `gf128` | self-consist. | 0 | - | - |
| `gf14` | bit-exact | 14 | Tier-E | Tier-E |
| `gf16` | bit-exact | 0 | - | Tier-E |
| `gf20` | bit-exact | 8 | - | Tier-E |
| `gf24` | bit-exact | 8 | - | Tier-E |
| `gf256` | self-consist. | 0 | - | - |
| `gf32` | bit-exact | 8 | - | Tier-E |
| `gf4` | bit-exact | 16 | - | Tier-E |
| `gf48` | self-consist. | 0 | - | - |
| `gf512` | self-consist. | 0 | - | - |
| `gf6` | bit-exact | 64 | - | Tier-E |
| `gf64` | bit-exact | 8 | - | - |
| `gf8` | bit-exact | 256 | - | Tier-E |
| `gf8_bfp` | bit-exact | 256 | - | - |
| `gf96` | self-consist. | 0 | - | - |
| `gf_lns_hybrid` | bit-exact | 8 | - | - |
| `gfternary` | bit-exact | 4 | - | - |
| `ibm_hfp128` | bit-exact | 8 | - | - |
| `ibm_hfp32` | bit-exact | 8 | Tier-E | - |
| `ibm_hfp64` | bit-exact | 8 | Tier-E | - |
| `int128` | bit-exact | 7 | - | - |
| `int16` | bit-exact | 7 | Tier-E | - |
| `int32` | bit-exact | 7 | Tier-E | - |
| `int4` | bit-exact | 16 | Tier-E | - |
| `int64` | bit-exact | 7 | - | - |
| `int8` | bit-exact | 256 | Tier-E | - |
| `lns16` | bit-exact | 5 | Tier-E | - |
| `lns32` | bit-exact | 5 | - | - |
| `lns64` | bit-exact | 5 | - | - |
| `lns8` | bit-exact | 256 | Tier-E | - |
| `minifloat` | structural | 0 | - | - |
| `ms_mbf32` | bit-exact | 8 | Tier-E | - |
| `ms_mbf64` | bit-exact | 8 | Tier-E | - |
| `mxfp4` | bit-exact | 0 | - | - |
| `mxfp6` | bit-exact | 64 | - | - |
| `mxfp8` | bit-exact | 256 | Tier-E | - |
| `mxgf4` | bit-exact | 16 | - | - |
| `mxgf6` | bit-exact | 64 | - | - |
| `nf4` | bit-exact | 16 | Tier-E | - |
| `per_channel_scale` | bit-exact | 256 | - | - |
| `posit16` | bit-exact | 8 | Tier-E | - |
| `posit32` | bit-exact | 8 | Tier-E | - |
| `posit64` | bit-exact | 8 | - | - |
| `posit8` | bit-exact | 256 | Tier-E | - |
| `q_format` | structural | 0 | - | - |
| `quad_double` | bit-exact | 8 | Tier-E | - |
| `shared_exp` | structural | 0 | - | - |
| `stochastic_rounding` | structural | 0 | - | - |
| `takum16` | bit-exact | 3 | Tier-E | - |
| `takum32` | bit-exact | 0 | - | - |
| `takum64` | bit-exact | 0 | - | - |
| `takum8` | bit-exact | 256 | Tier-E | - |
| `tapered_fp` | structural | 0 | - | - |
| `tf32` | bit-exact | 8 | Tier-E | - |
| `unum_i` | structural | 0 | - | - |
| `unum_ii` | structural | 0 | - | - |
| `vax_d` | bit-exact | 8 | Tier-E | - |
| `vax_f` | bit-exact | 8 | Tier-E | - |
| `vax_g` | bit-exact | 8 | Tier-E | - |
| `vax_h` | bit-exact | 8 | - | - |
| `x87_fp80` | bit-exact | 8 | - | - |
