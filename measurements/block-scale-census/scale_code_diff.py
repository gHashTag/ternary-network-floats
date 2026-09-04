#!/usr/bin/env python3
"""
The decisive check for the bit-identity claim, plus the block-size and
rounding-rule controls promised on the OCP list.

Claim under test: on these weights a 4-bit power-of-two scale field with a
per-tensor bias assigns the same scale to every block as E8M0 does.

Perplexity agreeing to four decimals is a checksum, not evidence. This diffs
the two scale-code arrays directly and counts the blocks where they differ.

Also swept, because both were named as unrun controls:
  block size K in {16, 32, 64}
  scale rounding in {floor, ceil, rtne}   (floor is the OCP-recommended default)

numpy only; no torch, no safetensors package.
"""
import glob
import json
import struct
import numpy as np

EMAX_ELEM = 2          # E2M1
E8M0_CODES = 255       # 256 minus one reserved for NaN
FIELD4_CODES = 15      # 16 minus the same reserve


def read_safetensors(path):
    with open(path, 'rb') as f:
        n = struct.unpack('<Q', f.read(8))[0]
        header = json.loads(f.read(n))
        blob = f.read()
    for name, meta in header.items():
        if name == '__metadata__':
            continue
        dt, shape = meta['dtype'], meta['shape']
        a, b = meta['data_offsets']
        raw = blob[a:b]
        if dt == 'BF16':
            arr = (np.frombuffer(raw, dtype='<u2').astype(np.uint32) << 16).view(np.float32)
        elif dt == 'F16':
            arr = np.frombuffer(raw, dtype='<f2').astype(np.float32)
        elif dt == 'F32':
            arr = np.frombuffer(raw, dtype='<f4')
        else:
            continue
        yield name, arr.reshape(shape)


def shared_exp(absmax, rule):
    """MX shared exponent for a block, under three rounding rules."""
    l = np.log2(absmax.astype(np.float64))
    if rule == 'floor':
        e = np.floor(l)
    elif rule == 'ceil':
        e = np.ceil(l)
    elif rule == 'rtne':
        e = np.rint(l)          # ties to even, which is what rint does
    else:
        raise ValueError(rule)
    return e.astype(np.int64) - EMAX_ELEM


def run(model, path, K, rule):
    per_tensor_E, blocks, differing, clamped_tensors = [], 0, 0, 0
    for name, w in read_safetensors(path):
        if w.ndim != 2 or 'embed' in name or name.endswith('lm_head.weight'):
            continue
        rows, cols = w.shape
        cols -= cols % K
        if cols == 0:
            continue
        am = np.abs(w[:, :cols].reshape(rows, cols // K, K)).max(axis=2).ravel()
        am = am[am > 0]
        if am.size == 0:
            continue
        E = shared_exp(am, rule)
        blocks += E.size
        # 4-bit field with a per-tensor bias placed at the tensor's minimum
        code = E - E.min()
        out = int((code > FIELD4_CODES - 1).sum())
        differing += out
        if out:
            clamped_tensors += 1
        per_tensor_E.append(E)
    allE = np.concatenate(per_tensor_E)
    return {
        'model': model, 'block_size': K, 'rounding': rule,
        'blocks': int(blocks),
        'blocks_differing_under_4bit_per_tensor_bias': int(differing),
        'tensors_needing_clamp': int(clamped_tensors),
        'distinct_shared_exponents': int(np.unique(allE).size),
        'shared_exp_min': int(allE.min()), 'shared_exp_max': int(allE.max()),
        'quantised_span_binades': int(allE.max() - allE.min()),
        'e8m0_codes_available': E8M0_CODES,
        'field4_codes_available': FIELD4_CODES,
    }


if __name__ == '__main__':
    MODELS = [
        ('HuggingFaceTB/SmolLM2-135M', '/tmp/models/SmolLM2-135M.safetensors'),
        ('Qwen/Qwen2.5-0.5B', '/tmp/models/Qwen2.5-0.5B.safetensors'),
    ]
    out = []
    for model, path in MODELS:
        for K in (16, 32, 64):
            for rule in ('floor', 'ceil', 'rtne'):
                r = run(model, path, K, rule)
                out.append(r)
                print(json.dumps(r), flush=True)
    with open('/Users/playra/dayo-crosscheck/scale_code_diff.json', 'w') as f:
        json.dump(out, f, indent=2)
    print('written')
