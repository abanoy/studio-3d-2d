# Reviewed-plan SFM resource stager

This output-only source passed root review and the exact two-case extraction
subsequently ran successfully; see `../NATIVE-RESULTS.md` for its scoped result.
Default mode performs read-only archive indexing and preservation checks;
`--execute` is a distinct explicit mutation mode. Keep every run's evidence and
partial staging. There is no cleanup function.

The script binds the exact raw `../plan.json` bytes to SHA256
`4a747c6bc883af7e69ca448a0d7ac60f76f14b78550682647f683449cd1d2aaf`.
It accepts only the two named cases and the 296-resource / 181,460,484-byte
allowlist. It imports the existing `tools/source_archive.py` resource-path
guard, which in turn uses `asset_audit.py`; these files remain read-only.
Installed 7-Zip must match the previously approved SHA256
`e2ca3ec168ae9c0b4115cd4fe220145ea9b2dc4b6fc79d765e91f415b34d00de`.
No Blender, Godot, GPU, network, installed-content mounting or installations
occur. The 7-Zip subprocess has no shell and is hidden on Windows.

Preflight command, after root code review, from the checkout:

```powershell
& 'C:\Program Files\Python313\python.exe' -B -u 'output\sfm-next-cases-20261112\source\stage_resources.py'
```

Only after the reviewed code/preflight is authorized for execution, append
`--execute`. Both commands require `../stage` to be absent; another direct child
named `stage-<letters/digits/underscore>` can be supplied with `--stage-root` for
a fresh retry. Existing/failed staging refuses overwrite and remains retained.
The optional `--archive-root` reads the same two RAR filenames from an explicit
existing directory; exact recorded SHA/size/mtime must still match. It changes
no extraction allowlist or input identity contract.

All archive identities, indexes and selected member CRC/length checks complete
before the stage directory is created. Every index member is checked for unsafe
Windows names, traversal, aliasing, links/reparse metadata, streams, encryption,
split records and invalid fields. Only exact allowlisted model/material resource
types can be staged. Each member is streamed from `7z x -so -spd` into a fresh
exclusive file under its case/package layout, with an indexed byte cap, CRC and
SHA256. The selected MDL additionally requires its exact recorded SHA and IDST49
header/length. Both subprocess pipes are independently bounded and timed out;
stderr and partial payloads are retained if a failure occurs.

The final manifest requires the exact staged file set, total count/bytes,
individually unchanged staged hashes/stamps and unchanged original archives,
tool, frozen plan and source guards. No recursive filesystem mutation occurs.
Link checks run before paths are used and after staging. This is ordinary
single-owner staging, not a claim of resistance to a hostile concurrent process
replacing directory entries between filesystem operations.

`test_stage_resources.py` exercises meaningful CPU boundaries using synthetic
payloads/processes and the two retained real archive-index logs. It launches
only the existing Python with tiny stdout/stderr/timeout examples; it does not
invoke 7-Zip or extract real resources. Generated CPU artifacts remain under
`../cpu-tests-<nonce>`, including failures. Run with Python `-B`. Its pass is
resource-safety evidence, not native conversion/material/rig/render acceptance.

`vmt_closure.py` reads a hash-bound successful staging receipt and verifies every
staged input before and after its read-only VMT analysis. Its bounded tokenizer
handles quoted/unquoted keys, adjacent quotes, comments, nested blocks and
conditional annotations; include traversal stays within the verified owned
index. It reports a conservative union, unknown path-like values/blocks and
conditions explicitly, without executing shaders/proxies or evaluating patch
semantics. Twelve CPU parser/path/negative controls pass. The actual ten-VMT
closure result is in `../NATIVE-RESULTS.md`; Nitori's native bump resource is
missing, while its supported simple base-texture inputs resolve. No substitution
or external mount filled that gap. This parser does not decode VTFs or establish
material/render fidelity. The historical
`plan.json` future converter commands use the earlier proposed staging location;
regenerate their loose-MDL paths to the actual verified stage, preserving both
request hashes as the MDL checksum and the RAR checksum as upstream provenance.
