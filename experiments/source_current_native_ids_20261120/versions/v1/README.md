# Fresh SourceIO current-ID preparation

**CPU preparation tested; native import/API qualification UNRUN.**

This staging packet preserves seven frozen source/recipe/test files byte for byte
from `output/source-current-id-prep-20261120`. It contains Root's actual CPU
evidence, a retained failed predecessor, a read-only runtime metadata preflight
and a source review summary. It is not an executed SourceIO/Blender probe and
does not qualify a current model, original B, normals, export or HAS adoption.

Root alone ran the CPU checks on application source
`9e3b039039833adce4723bbb70681595cd4eef16`:

| Check | Methods | unittest time | Retained result |
| --- | ---: | ---: | --- |
| Pure creation/weight ledger | 19 | 0.004 s | `cpu/ledger19/result.json` |
| Worker bootstrap with synthetic objects | 4 | 0.029 s | `cpu/worker4/result.json` |
| Root coordinator with fake readers/launches | 51 | 0.944 s | `cpu/driver51/result.json` |
| Total passing methods | **74** | **0.977 s** | `CPU_SUMMARY.json` |

The associated passing stderr/stdout files are exact copies, and each result
records the executed source version and unchanged hash/size/nanosecond times.
These are CPU test times, not native import performance. No SourceIO/Blender/
engine process or native input/capture was used by these tests.

The 19-test ledger result also snapshots worker `4f578d...` and the recipe as
contemporaneous **UNEXECUTED context**. Only ledger `ab2d0d...` and ledger tests
`cec5e3...` were executed by that run. It does not qualify worker `b9ad16...`.
That successor worker was exercised separately by the four bootstrap tests,
which imported only stdlib worker code and the pinned pure AST helper. The actual
worker `main`, Blender package, SourceIO SDK and native models remained unrun.

The first 51-test coordinator attempt returned exit1 because Windows denied
creation of a synthetic temporary hard link (`WinError5`). The hardlink refusal
guard had not been exercised. Its compact original result and bounded reason are
retained under `cpu/driver51-restricted-predecessor`; the original 9,056-byte
stderr is identified by SHA256 rather than copied. Root repeated the exact same
`f33f97...` driver / `da1b65...` tests in the approved host context: all51 passed,
with no source change or waived assertion. `code_used/CPUhardlinkrunner.py` is the
byte-exact Root CPU repeat runner. It is an archival source reference; its
original path-relative output layout is not an instruction to rerun the archive.

`runtime/readonly-preflight.json` records the actual Root read-only match to the
immutable `3bb7c2...` lock: six executables, all574 SourceIO files and120 exporter
noncache files matched their hash/size/nanosecond timestamps. This preflight
launched no native process and opened no native inputs/captures. It is a runtime
metadata check, not an SDK/API, current-ID or fidelity result.

The intended first actual probe is narrowly limited to a fresh SourceIO import's
new Object/Mesh/native-ID creation chain and current ordered RNA weights. It
will use three separately staged literal-pinned native files. Original B,
historical GLB and parameters remain Root hash-only provenance; the child opens
none of them. The four creation stages and returned container must retain the
same actual references and exact independently derived position/loop/source-ID/
raw-ID/weight words. No proximity, saved-B labels, sorted groups, normalization,
proxy or output-derived IDs may repair a mismatch.

The immutable source pins, request schema and private-launch recipe remain in
the copied `ROOT_RECIPE.md` and Python source. The recipe's authored-unrun wording
is preserved verbatim; the later Root CPU results above are the current evidence.
Root must first finish and physically close the exact full9e Windows suite with
1,061 functional/driver sources, then independently admit and launch one retained
private job, verify its real hidden placement, wait/reap and close the exact
owned process tree/desktop, and recheck source/runtime/input preservation.

All native/API, current-model, historical-B, generic weight-policy, normal,
carrier/export, semantic-equivalence and adoption qualifications remain false.
The original failed source normal gate remains unchanged at **2e-5**. A later
actual result must be appended as a separate hash-bound observation by Root; it
must not rewrite these CPU results or turn source review into execution evidence.

No original model, blend, GLB, native binary, private capture, native vector,
normal, source-ID, weight or UV array was copied into this packet. Only source,
CPU logs/results and bounded scalar metadata are staged. The pure AST helper
executed by the four bootstrap tests is already available in the repository at
`experiments/normal_setter_boundary_sentinel_20261117/instrumentation.py`,
3,306 bytes / SHA256
`361fcad3dbff79bfd5367cd71ac5a769fc8155d6f38a1b061d5ce6e631f5a895`.

`CONTENTS.json` hashes every staged payload file except itself. This folder is
publication staging only; no committed `experiments/` file was changed and no
Git operation, test, native computation or app launch was performed by the
staging author.
