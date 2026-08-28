# Conformance vector manifest

SHA-256 over every vector file in this directory, so a transcript claiming
conformance can name the exact bytes it was checked against.

Regenerate and verify:

```bash
python3 conformance/make_vector_manifest.py --check
```

Exit status is 0 when every file matches, non-zero on the first mismatch, a
missing file, or a file present in the directory and absent from the manifest.

## What version these are

The files are the `v0` set. This paper's text once described a `tnf-vectors-2`
and a repaired `tnf-vectors-3` carrying their own manifests; neither tag, nor a
manifest, nor a second set of files was ever committed here, and the lineage
cannot be reconstructed from what is in the tree. Rather than mint tags that
imply a history the repository does not hold, this manifest names the one set
that exists, at the commit that contains it.

A reader checking a digest should therefore quote the commit, not a version
name.

See `SHA256SUMS` in this directory for the digests.
