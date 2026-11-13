# Prepared serial static-appearance conversion driver

`source/conversion_driver.py` is output-only preparation for root review. It has
not run Blender, created a private desktop or converted a native model. The
normal application, frozen appearance-worker copy and existing command arrays
are unchanged. Current corrected code has **21 passing CPU controls**. The earlier
18-control version also passed a real metadata/hash preflight; that exact source,
schema1 lock and result are retained as historical evidence. The corrected
schema2 driver still needs a fresh lock/preflight at root's next stable checkpoint.
None of these are a fourteen-conversion pass or native/render acceptance.

The exact schedule is two ordinary no-request baselines (Nitori, then Keiki),
their two explicit defaults, Nitori skins 1/2, Keiki's six other visible
combinations, and the two all-blank refusals. Unexpected failure stops the series.
The original fourteen arrays and older proof files remain intact. Each future
execution writes newly corrected candidate commands into a fresh direct
`conversion-run-<nonce>` folder, then keeps commands, environment, process log,
exit/private-desktop receipts, the worker's parameters/dependencies and bounded
GLB structure reports for each case. Failed/partial outputs are never deleted.

An immutable input lock binds the four reviewed appearance-worker files, all
functional files in that prototype and root checkout, the whole existing pinned
SourceIO file tree, the approved existing Python/Pythonw/Blender executables,
private launcher, original archives, all 296 staged files, request JSONs, VMT
closure/staging receipts and old command array. It checks SHA256, size and
modification stamps before each case and at completion, including current root
Git revision and exact functional/runtime file membership. Bytecode and output
are excluded from functional trees. Exact staged file membership is also frozen:
an added unlisted file refuses. Every consumed dependency must be a recorded
staged resource or one of the five verified model copies. A changed
source/runtime/input refuses.

The historical schema1 lock is `conversion-inputs-prepared1.json`, SHA256
`619264e06dbfefb2dea6a8e895cca6d866b7bc23c279032d3163fa02f2e6484e`,
bound to root `4fee0a9f25dca5c265966c7433e21a7ccd0c3bf9`. Default preflight at
`conversion-run-1794543782467396200/verification.json` passed, with every protected
input/source/runtime stamp unchanged and `all_fourteen_passed: false`.
Its matching old driver is retained byte-exact in
`conversion-driver-before-reviewfix/conversion_driver.py` (SHA256
`2fcfd053a184ef3a755cf576213e9794c639e715208b471e82d957b40b135490`).
The independent review found omitted bind/rest/default-weight data and unlisted
stage membership; those gaps are now corrected and covered by negative controls.
Root is correcting a separate canonical test contract, so no replacement lock was
created during that edit. Prepare and review a fresh schema2 lock/preflight for
the new stable checkpoint; this old lock deliberately refuses the corrected code.

After root source review and a stable checkpoint, prepare a fresh lock from the
checkout (the output filename must be new):

```powershell
$taskRevision = git rev-parse HEAD
& 'C:\Program Files\Python313\python.exe' -B -u 'output\sfm-next-cases-20261112\source\conversion_driver.py' --prepare-inputs 'output\sfm-next-cases-20261112\conversion-inputs-reviewed2.json' --expected-root-revision $taskRevision
```

The preparation prints the new lock's actual SHA256. Run normal preflight with
`--input-lock <that fresh path> --lock-sha256 <that printed hash>`. Only after that
preflight, source review and root's conversion lease, append both
`--run-conversions --lease-confirmed`. No real execution occurred in this
preparation task. `--prepare-inputs` / `--freeze-lock` is a separate preparation-only mode, requiring
a fresh direct `conversion-inputs-<name>.json` and the exact current forty-character
`--expected-root-revision`; it cannot be combined with execution flags.

The future outer child uses `CREATE_NO_WINDOW`; the approved private-desktop
launcher creates the Python worker suspended with `CREATE_NO_WINDOW`, assigns
its kill-on-close job and resumes it on a private desktop. That job owns the
Python-to-Blender tree, including timeout/cancellation. Each case requires a
closed job/desktop and no foreground activation; there is no visible fallback.
Blender remains the unchanged worker's factory/offline/background process. Owned
temporary/user directories and a sanitized child environment keep generated
files in the case. Output/log budgets and timeouts stop an unexpected process.

The worker receives an empty explicit mount plan and nonexistent owned GMod and
Workshop paths. Its actual conversion request must use exactly the copied model
sidecar folder and that candidate's owned package root. Optional Windows Steam
discovery can still read installation metadata; its providers cannot become
conversion mounts. Every resolved dependency provider and copied dependency
must match an owned source/checksum. There are no installations, network calls,
Steam writes or guessed resource replacements.

Future successful outputs must preserve the exact native skin table, bodygroup
catalogue/blank correspondence, selected named/numeric indices and request,
native bone name/parent list, flex descriptor names and controller ranges.
The ordinary default route must retain its ordinary report shape. GLB checks
require embedded resources, only selected mesh nodes, original joint names and
parent hierarchy, bounded valid triangle/skin/morph accessors and normalized
weights. Decoded geometry/skin/morph fingerprints for retained meshes must match
the no-request baseline, independently of intended material changes. They include
each used skin's joint ordering/names, decoded inverse binds, joint/mesh rest
chains and effective default morph weights; an unused skin cannot supply a
missing native binding. Sparse
float VEC3 morphs are decoded using the existing bounded helper reader.

Actual material/dependency reports distinguish active PBR inputs, inactive
material warnings, optional/unclassified lookup misses and the native preflight
gaps. Active fallback gray or missing base inputs fail. Nitori's three native
references to absent `materials/hairbump.vtf` remain explicit even if its simple
bridge never requests that unsupported bump map. Full shader/Phong/environment/
warp/glow equivalence is not claimed. An all-blank pass requires exit 1, the
exact geometry-refusal reason in worker and parent logs, clean private receipt,
and no successful GLB/parameters output; an arbitrary failed process does not pass.

The CPU controls use the two existing immutable command sets/request metadata,
synthetic GLB buffers and synthetic dependency files. They prove schedule and
argument rejection, exact source/stage membership preservation, catalogue/selection guards,
embedded GLB/skin/morph decoding, unsafe/external resource refusal, private receipt
requirements and exact refusal classification. Counterfactuals alter inverse
binds, rest transforms, joint order/default morph weights, move a required bone
into an unused skin, add an unlisted stage file and remove dependency approval.
They launch no native process. A second independent read-only review found no
remaining concrete blocker in those corrections.

Even a future fourteen-conversion pass would prove this worker's static bundle
route and the explicitly checked metadata/structure only. Native material-slot
mapping and independent native vertex/weight/morph deformation equivalence,
actual rendered differences, GPU review, app choice/adoption, Undo/Redo,
linked/packed/fresh-offline HAS, movies, runtime/animated variants, procedural
jiggle, component assembly and owner acceptance remain separate unfinished work.
Do not build or claim the full GPU/app harness before the first real converter
metadata and embedded GLB results have been reviewed.
