# Resource gate v2: owned non-ID RNA identity

**AUTHORED, UNRUN.** No tests, Blender, exporter, material GUI, assets, engines,
CIM/Git or native operation was executed by the author. Only this new folder was
written. This is a source proposal, not B-resource/export/fidelity qualification.

## Exact preserved sources

`predecessors/base` contains the unchanged sources indexed by `BASES.json`:

| Source | Bytes | SHA256 |
| --- | ---: | --- |
| export_hook_proposal.py | 33179 | 1b6e6b5fa4acb1e3bea1d37fd433f42c1294ed70a24047c4ea0e4c60b18afbae |
| resource_gate_proposal.py | 25032 | 336119221fc6c96d78b69cf301e2d89b0130c48febaedb81fc1c0b0134211e14 |
| test_export_hook_proposal.py | 28206 | c9fd2dcb8411dbe827fee8583134cbedc065c71aba86070ce53fa9bd84aba328 |

The active export_hook_proposal.py is still byte-exact1b6e. Its17exporter source
pins, class/function/globals/closure checks, callback inventory, failure latch,
exact patch restoration, creator/NumPy/cache/argument-container identities and
glTF Python object/descriptor identities were not changed.

## Changed domain only

Blender may return fresh Python wrappers for the same non-ID RNA struct. The
resource gate therefore distinguishes those from cached ID and plain Python
identities. Only Node, Socket, Link, ImagePackedFile and PackedFile comparisons
use this private canonical key:

`(actual original local owner ID, exact admitted concrete RNA class, C pointer)`

Owner ID is compared with `is`; class is compared with `is`; pointer must be an
exact Python int, not bool, with0<value<2**64. Each struct must be an instance of
the genuine admitted API base and its concrete class name must resolve directly
in the supplied genuine bpy.types registry to that same class. No guessed
finite NodeSocket subclass whitelist or name-based identity fallback is used.

One original wrapper and its owner are retained for each admitted key; repeated
fresh wrappers can match that key. Same-owner/pointer type drift, invalid pointer
or changed owner refuses. A bounded private retention table never enters public
reports. Owner/material/Image/NodeTree ID refs remain strict `is`; they are not
replaced by C pointer equality. Pointers are not source/native geometry labels.

| Site | New check, preserving old policy |
| --- | --- |
| Node/link collections | Typed ordered C keys, unique membership in the admitted NodeTree |
| Sockets | Same NodeTree owner, admitted node key, input/output direction, unique collection membership, ordinal, bounded identifier and unchanged default metadata |
| Complete graph | Same allowed nodes/active output/configuration and complete directed endpoint keys; no ORM/group/extra path admitted |
| Packed aliases | Single ImagePackedFile and PackedFile keys owned by the same actual Image; alias size and bytes agree; existing pin/hash/PNG/CRC checks retained |
| Image snapshot | Image ID stays `is`; packed part/file C keys and filepath/view/tile/size/hash remain exact |
| Exporter socket wrapper | Exact Python search.NodeSocket class, exact list group_path and NodeTree ID remain; only underlying RNA socket is joined by its owned key |
| glTF/descriptor/cache | Strict Python and ID `is` rules remain unchanged |

No pointer generation counter exists. This policy assumes the existing frozen,
read-only graph lifecycle with no mutation/rebuild/handlers; it does not prove
historical identity across deletion/reallocation. Changed membership, endpoints,
metadata, bytes or other unexpected invalidation refuses, not repairs by names.

## Ordering and resource gates retained

All original graph admission occurs before ordinary ORM/gather/image acquisition.
Every bounded encoded PNG header/CRC and prospective decoded budget is checked
before any image.size/channels getter: per-image64MiB and total128MiB encoded and
prospective decoded limits remain. Alias encoded-byte reads stay inside the same
admitted packed-size cap. All-image-path PNG/AUTO MIME restrictions, alpha-only
refusal, UDIM/unused/shared image restrictions and complete channel mappings
remain. No image pixel, geometry, material setter or shader simplification is
added. No normal or non-NORMAL semantic gate is relaxed.

Final resource report is versioned
`has_narrow_actual_resource_reference_observation_2`. Its existing shader/global
reachability/semantic limitations remain false. The API constructor and hook
entry points are unchanged; the caller supplies the full genuine bpy.types
namespace, which exposes ID/NodeTree/Image/NodeSocket/NodeLink/PackedFile/
ImagePackedFile and the actual registered concrete classes.

## Source-only checks and next qualification

`SOURCE_DIFF.json` contains exact base/new hashes and unified diffs. Static AST
review confirms all30old test methods and every old assertion AST are unchanged.
Fixtures gained only API-like owner/pointer/type-registry support. Eight new
tests exercise fresh wrappers, wrong owner/type/pointer, bool/invalid pointers,
foreign socket/duplicate membership, packed alias payload drift, endpoint/
identifier/direction/default drift and still-strict ID/descriptor lookalikes.
All38methods are authored and **unrun by the author**.

```powershell
$resourceRNA = 'C:\a\Programming\cloudflare\has-body-addition-20261120\output\source-resource-rna-successor-prep-20261120'
& 'C:\Program Files\Python313\python.exe' -B -X utf8 -m unittest discover -s $resourceRNA -p test_export_hook_proposal.py -v
```

Root must review the exact frozen source and run those synthetic checks. Later
actual API/export qualification requires already-qualified B resources and fresh
native IDs in its own private owned job. Source/CPU approval cannot certify real
wrapper behavior or authorize an export. Historical B point identity, renderer
equivalence, resource/export binding, full non-NORMAL semantic equivalence,
original2e-5normal fidelity and HAS adoption remain unqualified here.
