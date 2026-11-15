# Independent native base geometry: frozen bounded result

This stdlib-only reader compared six existing native MDL49/VVD4/DX90VTX files
with the twelve accepted Nitori/Keiki GLBs. It imports no converter, SourceIO,
NumPy, Blender or engine module. No model runtime, GPU, extraction, download,
installation, main-source or Git write occurred. Actual decoded vertex/index
arrays stayed in memory; only source and metadata were saved.

The final run is `comparisons/1794553295277979700/comparison.json`, with **30/30
synthetic CPU controls first**, unchanged source/HEAD and all 296 staged-resource,
two original-archive and twelve bundle/report/verification identities preserved.
`RESULTS.json` is the compact outcome; `archive-candidate/` contains byte-identical
frozen source, fixture identities, compact results and replay documentation.

## Twelve actual statuses

| Bundle | Base position/UV/named VVD-weight map | Native attributed triangles |
| --- | --- | --- |
| Nitori ordinary baseline | Match | Unrun: unsupported legacy VTX layout |
| Keiki ordinary baseline | Unresolved: two Tools correspondences | Tools unresolved; box/flame match |
| Nitori explicit skin 0 | Match | Unrun: unsupported legacy VTX layout |
| Keiki explicit 000 | Unresolved: two Tools correspondences | Tools unresolved; box/flame match |
| Nitori skin 1 | Match | Unrun: unsupported legacy VTX layout |
| Nitori skin 2 | Match | Unrun: unsupported legacy VTX layout |
| Keiki 001 | Unresolved: two Tools correspondences | Tools unresolved; box matches |
| Keiki 010 | Unresolved: two Tools correspondences | Tools unresolved; flame matches |
| Keiki 011 | Unresolved: two Tools correspondences | Tools unresolved |
| Keiki 100 | Match | Match |
| Keiki 101 | Match | Match |
| Keiki 110 | Match | Match |

Across 28 mesh comparisons, 23 have an unambiguous base attribute map and 15
have matching oriented triangle-corner multiplicities. Every derived vertex has
at least one native candidate. The five Tools cases are not certified by merely
finding candidates; two distinct near-native classes remain unassigned.

The fixed tolerances are 0.000002 metres for positions, 0.000002 UV and 0.000002
named bone weight. Maximum errors among accepted correspondences are about
0.0000005214 metres, zero UV and 0.0000001193 weight. These are explicitly
bounded numerical comparisons, not bit-exact export or native renderer proof.

## Format, transform and identity contract

The native reader is original stdlib `struct` code. Official Valve format
headers and the pinned reader were consulted as documentation, never imported.
`review/FORMAT-BOUNDS.md` records source links, byte sizes and limits. It reads
MDL49 common prefixes, VVD4 48-byte vertices and ordered LOD0 fixups, and only
the documented packed legacy VTX7 TRI_LIST layout (stripgroup 25 / strip 27).
Checks bind versions, three file checksums, byte offsets/counts, model/mesh
origins, native bones, fixup coverage, strip/index ranges, winding and weights.
Strip vertex offsets are not added to stripgroup index values. VVD global bone
IDs are authoritative here; hardware-palette renderer equivalence is untested.

No transform was fitted to the GLB. The existing adapter declares Source Z-up
to glTF Y-up at scale 0.01905, giving `(x,z,-y)*0.01905`. Its pinned importer
creates Blender vertices at Source coordinates times scale and reverses each
triangle winding through `np.flip(indices)`. The glTF Y-up export is a proper
axis rotation, not another winding fit. The importer flips UV V once; the
installed glTF export code flips it again, yielding the original Source UV.
Those source lines were read as documentation; no Blender module was executed.

Native bone index, exact original name/hash and parent are joined to the actual
GLB palette/source node separately. Palette order is not assumed to equal MDL
table order. UV/weight seams and coincident-triangle multiplicities are retained.
Exact-equal native attribute rows remain explicit candidate sets; no unique
native-ID identity is claimed for indistinguishable rows. Expanded vertex
counts and raw normal/seam limitations are reported, not silently collapsed.

## Exact unresolved observations

- **Nitori topology:** the legacy reader reaches mesh 0 stripgroup 1 at byte 127
  and reads invalid layout fields. The pinned importer has an optional extra
  eight-byte layout, but this oracle does not guess that variant or its meaning
  to force agreement. MDL/VVD base attributes are independently available;
  native triangle correspondence remains unrun.
- **Tools correspondences:** GLB vertices 953 and 1063 each match native LOD0
  rows 1116 and 1148 within the fixed position bound. Those native positions are
  only 0.0000002378 metres apart and their UV/weights are identical. Their raw
  normals differ by about 1.022; the observed derived-normal errors distinguish
  them strongly, but no new normal-precision rule was invented to select IDs.
  A separately documented normal/seam or topology correspondence is the next
  bounded step. Scalar diagnostics are retained without geometry payloads.
- **Normals:** Keiki Tools contains 15 raw zero normal vectors. The initial
  unit-normal assumption was therefore removed as an invalid format assertion;
  finite raw values are preserved and reported. Normal fidelity, normal-seam
  identity and renderer repairs are not certified. Nitori's observed normal
  differences also remain separate from its position/UV/weight result.

The initial strict refusals, earlier comparisons, ambiguity diagnostics and
source hashes remain. Independent review found a preservation exit-status gap;
it was corrected, negatively tested and re-reviewed before the final run.
Failed preservation now retains a marked receipt and returns nonzero, without
retry. The final actual preservation/source/HEAD checks all passed.

## Replay and broader work

Keep these source files in the owned
`<checkout>/output/source-native-geometry-oracle-20261113/source/` layout.
Do not run a future archived experiment copy directly: its task-root inference
is deliberately tied to this owned output layout. With the exact private
resources and existing approved Python available, `compare_cases.py` performs
the CPU gate before native reads, preserves all identities, creates a fresh
result folder and never calls a converter or renderer. Missing/different
fixtures must be reviewed and rebound explicitly, not replaced silently.

Native flex-delta/controller evaluation, native shader pixels, runtime jiggle,
hardware palette state, native bone posing, GPU/app adoption and movies remain
separate. These two models do not cover the supplied 82-MDL corpus. The short
`NEXT-REPRESENTATIVES.md` matrix retains Junko, Mima and a distinct accessory case
without starting any new conversion or extraction.
