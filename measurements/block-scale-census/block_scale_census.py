#!/usr/bin/env python3
"""
Binade census of MX-style block scales over LLM weight tensors.

For every 2-D weight tensor, group elements along the contraction axis into
blocks of K and take the block's absmax. Two spans are reported, because the
distinction matters and the earlier record did not state which was meant:

  continuous span   log2(max_b absmax_b / min_b absmax_b)   -- pre-quantisation
  quantised span    max_b E_b - min_b E_b                   -- after the MX shared
                    exponent E_b = floor(log2(absmax_b)) - emax_elem

emax_elem = 2 for E2M1 (MXFP4), per OCP Microscaling Specification v1.0.

No torch import: safetensors is parsed directly, so the record is reproducible
with numpy alone.
"""
import json
import struct
import sys
import glob
import os
import numpy as np

K = 32
EMAX_ELEM = 2  # E2M1


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
            u = np.frombuffer(raw, dtype='<u2').astype(np.uint32) << 16
            arr = u.view(np.float32)
        elif dt == 'F16':
            arr = np.frombuffer(raw, dtype='<f2').astype(np.float32)
        elif dt == 'F32':
            arr = np.frombuffer(raw, dtype='<f4')
        else:
            continue
        yield name, arr.reshape(shape)


def census(repo_id, include_embeddings, local_glob):
    files = sorted(glob.glob(local_glob))
    if not files:
        raise SystemExit(f'no safetensors matching {local_glob}')
    all_absmax, per_tensor, blocks, params = [], {}, 0, 0
    for path in files:
        for name, w in read_safetensors(path):
            if w.ndim != 2:
                continue
            is_embed = ('embed' in name) or name.endswith('lm_head.weight')
            if is_embed and not include_embeddings:
                continue
            rows, cols = w.shape
            if cols % K:
                w = w[:, : cols - (cols % K)]
                cols = w.shape[1]
            if cols == 0:
                continue
            am = np.abs(w.reshape(rows, cols // K, K)).max(axis=2).ravel()
            am = am[am > 0]
            if am.size == 0:
                continue
            all_absmax.append(am.astype(np.float64))
            per_tensor[name] = float(np.log2(am.max() / am.min()))
            blocks += rows * (cols // K)
            params += rows * cols
    a = np.concatenate(all_absmax)
    E = np.floor(np.log2(a)).astype(np.int64) - EMAX_ELEM
    spans = sorted(per_tensor.values())
    return {
        'model': repo_id,
        'block_size': K,
        'emax_elem': EMAX_ELEM,
        'include_embeddings': include_embeddings,
        'blocks': int(blocks),
        'weights_covered': int(params),
        'nonzero_blocks': int(a.size),
        'continuous_span_binades': round(float(np.log2(a.max() / a.min())), 4),
        'quantised_span_binades': int(E.max() - E.min()),
        'shared_exp_min': int(E.min()),
        'shared_exp_max': int(E.max()),
        'distinct_shared_exponents': int(np.unique(E).size),
        'per_tensor_span_max_binades': round(max(spans), 4),
        'per_tensor_span_median_binades': round(float(np.median(spans)), 4),
        'per_tensor_span_p99_binades': round(float(np.percentile(spans, 99)), 4),
        'tensors': len(per_tensor),
    }


if __name__ == '__main__':
    out = []
    MODELS = [
        ('HuggingFaceTB/SmolLM2-135M', '/tmp/models/SmolLM2-135M.safetensors'),
        ('Qwen/Qwen2.5-0.5B', '/tmp/models/Qwen2.5-0.5B.safetensors'),
    ]
    for repo, path in MODELS:
        for inc in (False, True):
            r = census(repo, inc, path)
            out.append(r)
            print(json.dumps(r, indent=2), flush=True)
    with open('/Users/playra/dayo-crosscheck/block_scale_census.json', 'w') as f:
        json.dump(out, f, indent=2)
    print('written')
