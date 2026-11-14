# Independent selected-MDL capture review

Result: no blocking issue found in the output-only helper for the stated capture/recheck contract. This is source review and authored CPU evidence only; production integration, SourceIO behavior, native models, app/runtime/graphics, metadata report fit, and owner acceptance were not exercised.

Reviewed module SHA-256: `ce5a7af22a25e461a079d9a45a22c24ca7f7795bd897b37400b8d244f21c42be`. Independently recorded source/test/review-test hashes are in `source-sha256.log`.

The helper preserves the supplied absolute path, reads into immutable bytes, independently hashes those bytes, and captures size, nanosecond mtime, device and inode. It checks initial path identity against opened-handle identity, repeats handle checks after the bounded read, and repeats path identity after reading. Oversize input is rejected before opening; NotInspected contains only a bounded reason, with no native hash.

Initial open denial can return NotInspected only after a second identical path stat. Disappearance, changed identity/mtime, or loss of stat permission following the first eligible observation becomes SourceIdentityError. A successful open establishes the strict path: short reads, read errors, uncheckable handle/path identity and close errors cannot become optional omission. The final recheck validates the capture hash, repeats the read/identity checks and compares both bytes and independently recomputed SHA.

The eighteen authored test methods were reviewed for mock fidelity. Replacement and restored-mtime byte-change tests use real authored files; short-read and I/O-error wrappers retain a real file handle; the post-read disappearance mock targets the actual second path-stat call. The additional independent matrix passed nine tests, with the exact output retained in `cpu-review.log`. Its cases cover initial stat permission failure, mandatory second path stat after open denial, later stat denial, real mtime change with open denial, refusal before reading on first handle mismatch, real mtime change after reading, close failure, bounded immutable capture, and recheck stat/read failures. The first-handle mismatch case intentionally controls the snapshot comparison; the authored same-byte replacement test separately exercises real file identity changes.

Caller requirements remain material: keep the original SourceIO path, retain the upstream original/container SHA guard, call final recheck immediately before optional metadata publication, and propagate this helper's local SourceIdentityError alongside the metadata adapter's identity error. These output-only functions do not implement that integration. Observed stat/byte consistency does not prove absence of transient adversarial mutation between observations, as the accompanying README states.

Review writes are confined to this review directory. No reviewed source, runtime, converter, native original, production file, or Git state was changed. The approved Python interpreter was invoked with `-B`; the independent tests used fresh authored temporary byte fixtures only.

## Evidence index

- `test_snapshot_review.py`: independent nine-test CPU matrix.
- `cpu-review.log`: nine passed, zero failed; process exit code zero.
- `source-sha256.log`: independently calculated reviewed-source and review-test hashes.
- `REVIEW.md`: this scope, findings and evidence index.
