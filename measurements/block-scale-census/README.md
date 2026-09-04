# Binade census of MX-style block scales

How much of an MX shared-scale field do LLM weight tensors actually occupy?

```bash
python3 block_scale_census.py     # numpy only; no torch, no safetensors package
```

`result.json` is the record. Every number in it is recomputed by the script from
the model files named in its own provenance block; nothing is quoted.

## What is measured

For every 2-D weight tensor, elements are grouped along the contraction axis
into blocks of K=32 and the block's absmax is taken. Two spans are reported,
because they are different quantities and an earlier record of this measurement
did not state which was meant:

| quantity | definition |
|---|---|
| continuous span | `log2(max_b absmax_b / min_b absmax_b)` over all blocks |
| quantised span | `max_b E_b - min_b E_b`, with `E_b = floor(log2(absmax_b)) - emax_elem` |

`emax_elem = 2` for E2M1, the MXFP4 element. The quantised form is the one an
encoder actually stores; the continuous form is the range before the scale is
rounded to a power of two.

Both are reported with and without embedding tensors, because the tensor
selection changes the block count and any comparison against another census
has to match on it.

## Result

| model | blocks | continuous | quantised | distinct E | max per-tensor span |
|---|---:|---:|---:|---:|---:|
| SmolLM2-135M | 3,317,760 | 8.3183 | 9 | 10 | 6.2536 |
| Qwen2.5-0.5B | 11,182,080 | 9.12 | 9 | 10 | 7.335 |

Embeddings excluded in both rows; the with-embeddings rows are in `result.json`
and move the block count, not the span.

E8M0 is eight bits with one code reserved for NaN. Ten distinct shared exponents
are occupied on both models, against 255 usable codes. The occupied window moves
between models — SmolLM2-135M runs E in [-8, +1], Qwen2.5-0.5B in [-11, -2] —
while its width does not.

## The decisive check, and the controls

Perplexity agreeing to four decimals between an E8M0 field and a 4-bit one is
a checksum on the encoder, not evidence that the two assign the same scale.
`scale_code_diff.py` diffs the two scale-code arrays directly and counts the
blocks where they differ. `scale_code_diff.json` is the record.

A 4-bit field places its bias at each tensor's minimum and has fifteen usable
codes, one reserved for NaN, because E2M1 elements carry no NaN encoding of
their own. A block differs when its code falls outside that window.

**Zero blocks differ, in all eighteen configurations** -- both models, block
sizes 16, 32 and 64, and all three rounding rules for the shared exponent
(floor, which the specification recommends, plus ceil and round-to-nearest-even).

| model | K=16 | K=32 | K=64 |
|---|---:|---:|---:|
| SmolLM2-135M | 0 / 6,635,520 | 0 / 3,317,760 | 0 / 1,658,880 |
| Qwen2.5-0.5B | 0 / 22,364,160 | 0 / 11,182,080 | 0 / 5,591,040 |

The distinct-exponent count stays between nine and eleven across every one of
those configurations. The rounding rule moves it by at most one.

## What this does not show

Weights only. Activations and gradients share the same scale encoding across
MXFP8/6/4 and MXINT8, they are wider, and nothing here measures them; if the
eight bits are earning their place, that is where to look. Two models, both
under 1B, below the scale at which weight outliers have been reported. The
continuous span grew 0.80 binades for 3.37x the blocks while the quantised span
and the distinct-exponent count did not move at all, so the two metrics
disagree about whether there is a trend, and two points cannot settle it.

A narrower field also forfeits the stated design property of E8M0 — "the
representable exponents of these formats is a superset of the representable
exponents of FP32" — and needs a per-tensor or per-model bias to place its
window, which is a second scale level and costs context-free block decode.
The maximum per-tensor span is 6.25 and 7.34 binades, so a per-tensor bias
binds tighter than the model-wide union does.

This is a measurement of what the field holds, not a proposal to change it.

## Reproducing

The script takes local `.safetensors` paths. Fetch them from the revisions
pinned in `result.json`:

```bash
curl -L -o SmolLM2-135M.safetensors \
  https://huggingface.co/HuggingFaceTB/SmolLM2-135M/resolve/93efa2f097d58c2a74874c7e644dbc9b0cee75a2/model.safetensors
curl -L -o Qwen2.5-0.5B.safetensors \
  https://huggingface.co/Qwen/Qwen2.5-0.5B/resolve/060db6499f32faf8b98477b0a26969ef7d8b9987/model.safetensors
```

`result.json` carries the SHA-256 of each file as measured.
