# Full-run preparation

`preflight_full.py` is a fresh successor of the prior preflight. It requires the exact full checkpoint SHA and reviewed functional-file count on the command line; it does not embed the old dbf0bc1/1014 context. Current reviewed count is1019.

It preserves the exact approved lock SHA3bb7c2… and checks all identity fields for six runtimes,574 SourceIO files and120 exporter sources. It reads the current commit before/after, hashes the five functional trees plus four entrypoints, checks the catalogue/count, and writes one exclusively created JSON receipt under this checkout/output. It runs no engine, version probe, process inventory, Git mutation or cleanup. Its UTC receipt timestamp is read only when root actually executes it.

```
python -B experiments/native_five_full_preflight_20261116/preflight_full.py --expected-commit FULL40DIGITSHA --expected-functional-count 1019 --output C:/a/Programming/cloudflare/has-acceptance-session-20261111/output/NEW-PREFLIGHT.json
```

The helper was only parsed with Python AST by this agent. Root owns checkpoint publication, execution and any full-suite lease.

`PROMOTION_READ_AUDIT.json` independently verifies the sealed0450… review packet and all10 exact promoted files. `FULL_COMPLETION_TEMPLATE.json` is a nonexecuting template with deliberately null launch/PID/birth/hash fields. Root must fill those from actual new-run records after launch; prior run identities and timestamps cannot be reused. It does not claim a run, closure or PASS and does not replace the authoritative host/receipt audit.
