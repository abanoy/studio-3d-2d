# Checkout EOL admission addendum

Narrow read-only review found no clear blocker in the explicit `--allow-checkout-eol` change. Without the flag, a raw mismatch still refuses. With it, only CRLF byte pairs are reduced to LF for comparison; other edits are not ignored. The fixed five core source files are textual, and evidence retains both raw hashes and the admission label.

The flag does not rewrite working files or normalize copied Studio source. The builder still freezes the exact requested Git blobs; those blobs remain the final-copy checksum source. PLAN.md explicitly includes the flag and retains the original strict-raw preflight failure. The earlier audit remains unchanged.

No CLI/default/execute mode, build, copy, Godot, product or GPU operation was run. This addendum is static review, not runtime validation.
