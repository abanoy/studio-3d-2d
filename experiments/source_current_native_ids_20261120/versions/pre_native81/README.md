# Fresh SourceIO current-ID preparation — current driver v3

**Current CPU profile81 passed; actual SourceIO/Blender outcome PENDING.**

The current root source pair is driver f9bc228e / tests3ae6d497, with common
worker b9ad1631, ledger ab2d0d30 and their unchanged test sources. Root actually
ran58 coordinator CPU methods in1.039s. Reusing the exact unchanged19 ledger and
4 worker-bootstrap results yields the current81-method profile. These are CPU
code/admission tests, not native import performance or actual SDK/API evidence.

| Source version | Driver/tests | Coordinator CPU | Current-profile total | Scope |
| --- | --- | ---: | ---: | --- |
| Original v1 | f33f979a / da1b656d | 51 in0.944s | 74 | Historical; exact original24-file packet in versions/v1 |
| Intermediate v2 | b0495e8e / 640d12dc | 53 in1.137s | 76 | Historical; source and result/logs in versions/v2 |
| Current v3 | f9bc228e / 3ae6d497 | 58 in1.039s | **81** | Current root source and cpu/driver58 |

The common19 methods took0.004s and the4 bootstrap methods0.029s; the current
unittest sum is1.072s. Do not add totals across versions:19/4 are shared unchanged
results, and51/53/58 test changing coordinator versions. Every actual result JSON
and copied log remains byte-exact. No old result was relabelled or replaced.

## Preserved version history

versions/v1 is the complete original24-file/193,366-byte packet, including its
original CONTENTS.json SHA256
a1b065cf2250679648647943001a77eb2446a5df6d938183ee598f3800787ab1.
All original payload/source/report bytes are preserved. Its74/51 CPU summary,
README, source pair and restricted synthetic-hardlink failure remain historical.
The old root cpu/driver51 and code_used runner are retained historical mirrors.

The19-test result snapshots worker4f578d and the recipe as contemporaneous
UNEXECUTED context. That run executed only ledger ab2d0d and tests cec5e3.
It does not qualify b9ad16. The separate4 bootstrap tests exercised b9ad16 with
fake objects and the pinned pure AST instrumentation; actual worker main,
Blender/SourceIO and native inputs were not executed by those tests. The pure
helper remains available in the repository at
experiments/normal_setter_boundary_sentinel_20261117/instrumentation.py:
3,306 bytes / SHA256
361fcad3dbff79bfd5367cd71ac5a769fc8155d6f38a1b061d5ce6e631f5a895.

The original restricted51-method attempt failed because Windows denied creating
its synthetic temporary hardlink (WinError5), before that refusal guard was
exercised. The unchanged f33/da host-context repeat passed all51 with no waived
assertion. Its compact failure result/reason and original stderr hash remain.

## Two actual preflight refusals

preflight/v1-HARDLINK_PATH.json is Root's exact f33 preflight refusal. The
selected System32 PowerShell is a legitimate two-link NTFS file; the unchanged
single-link guard refused it before CIM, native launch or input copies. A
reviewed v2 uses the approved single-link Codex PowerShell. No guard was relaxed
to admit the System32 hardlink.

preflight/v2-FILE_CHANGED_BEFORE_READ.json is Root's exact b049 refusal at
stage1795201036841498500. Only its CIM-before observation occurred; native/
Blender jobs and native input copies were zero, and B was not opened. The
corresponding exact runtime-stamp-diagnostic.json records a directory attribute
transition262176 to32 (only0x40000) on otherwise identical runtime files.
Device/inode/size/nanosecond-time/link counts and literal file bytes stayed exact.

The reviewed v3 policy normalizes only the directory-enumeration recall-on-open
hint0x40000 for the relevant stamp comparison and retains raw attributes.
It does not qualify internal EA state. Reparse0x400, all other attributes,
device/inode/size/nsmtime/link counts, literal hashes and all other safety gates
remain strict. See preflight/STAMP_POLICY.md and the primary Microsoft reference
recorded in the refusal. The58 CPU result binds this successor to f9bc/3ae;
the53 result qualifies only b049/640, and51 only f33/da.

## Actual native work remains separate

Root's current f9bc/b9ad/ab2d private retry outcome is PENDING. This packet makes
no assertion about its currently running process state and contains no terminal
Blender/SourceIO or current-model result. Root must append the actual outcome and
its exact source/input/placement/owned-process-closure receipts separately.

The first actual scope is only the new Object/Mesh/native-ID creation chain and
current ordered RNA weights on three staged literal-pinned native inputs. Old B,
historical GLB and parameters remain Root hash-only provenance, not child-opened
inputs or point-label sources. Full9e1061-source/closed-job admission, immutable
runtime lock, private placement, retained handle/wait/reap and preservation
remain required. Source review and CPU results cannot supply those observations.

runtime/readonly-preflight.json separately records Root's exact immutable-lock
metadata match: six executables, all574 SDK files and120 exporter noncache files.
It launched no native process and opened no native inputs/captures. The raw
stamp diagnostic is filesystem metadata, not geometry/normal/weight data.

All current actual SDK/API, native-ID/RNA, old-B causality, generic storage,
normal, carrier/export, semantic-equivalence and adoption qualifications remain
false. The original failed normal gate stays unchanged at2e-5. The copied
ROOT_RECIPE.md is a byte-exact historical authoring recipe; CPU_SUMMARY.json and
the current exact source/Root results bind later versions.

No model, blend, GLB, native binary, private capture or native vector/normal/
weight/UV/source-ID array is in this packet. CONTENTS.json hashes every payload
except itself, including exact archived manifests. Only publication staging was
changed; no docs/app/helper files, tests, engines, process queries, Git operations
or deletions were performed by the staging author.
