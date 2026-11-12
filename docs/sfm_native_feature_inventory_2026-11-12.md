# Actual supplied SFM metadata — November 12, 2026

The approved metadata-only follow-up parsed all **82 actual MDL49 definitions**
from the 22 supplied archives, with **zero final errors or version refusals**.
They represent **71 distinct MDL hashes**, all matching the historical conversion
corpus. Only 62,843,920 bytes of MDL definitions were staged into an owned output
folder. No VVD/VTX, textures, model scripts or other archive payloads were staged.
Every original archive's SHA-256, size and modification stamp remain unchanged
from the earlier review. Native readers ran under the existing Blender-bundled
Python executable with no Blender app, scene import, GPU, network or installation.

| Native records | All 82 files | 71 distinct definitions |
| --- | ---: | ---: |
| Bodygroups | 288 | 243 |
| Bodygroup choices | 489 | 412 |
| Zero-vertex blank choices | 188 | 157 |
| Controllers / rules | 3,203 / 3,203 | 2,991 / 2,991 |
| Flex descriptors | 3,902 | 3,690 |
| Models with differing skin families | 28 | 27 |
| Models declaring procedural bones | 55 | 46 |
| Declared procedural bones, all JIGGLE | 2,655 | 1,905 |

All inspected controllers declare 0..1; every rule is one FETCH1 operation.
There are no stereo UI records. This broadens model coverage, but compound,
signed and stereo rule cases still need Scout or another selected source.

Each file contains one local sequence and one **one-frame** animation header;
there are no recorded sequence events, include-model references, attachments,
native IK chains or pose parameters in this corpus. These zero counts are native
metadata observations, not a claim that Source features generally do not exist.
No animation frames were decoded. This corpus supplies no positive moving native
sequence example for playback tests.

Concrete next cases:

- **Nitori tanktop glove:** three distinct skin material remaps, changing the
  Gloves/Glovesg/Glovesw families, plus a glove bodygroup with a genuine blank
  choice. A small positive candidate for skin/bodygroup switching, persistence,
  Undo and preview/export tests; no switching was implemented or exercised here.
- **Keiki main and chisels:** `Tools`, range 0..1. Main uses controller/descriptor 121
  and FETCH1(121); chisels uses controller/descriptor 0 and FETCH1(0). Chisels has
  tools/box/flame bodygroups, each with a zero-vertex blank choice. This is a
  nonfacial flex case, beyond a catalogue of expressions.
- **Junko v25 main + hair:** main has 145 bones / 16 distinct skins; hair has 69 bones,
  49 JIGGLE declarations and a Hat bodygroup with a blank choice. Their six common
  bone names have matching parent names. Rest transforms, inverse binds, skin
  alignment, assembly and native jiggle behavior remain untested. A bone-name
  match is evidence for a reviewed binding candidate, not automatic bone merge.
- **Mima head:** current native metadata confirms the earlier 82 controllers,
  156 descriptors and hair/hat blank alternatives. Its existing prepared 143 targets
  remain a separate count. It has one skin family; Mima **body** has four.

Two useful interpretation guards: a Keiki bodygroup choice named `blank` actually
has 14,521 vertices, so use native zero-geometry evidence rather than the label.
The two Bunny outfit-props definitions have 11 skin rows but only 10 distinct index
remaps; retain both counts instead of treating every row as a distinct appearance.

The first staging attempt mistakenly rejected 7-Zip's empty symbolic/hard-link
fields; the corrected guard rejects nonempty link targets, streams, encryption
and unsafe/duplicate paths. The first serializer completed 27 files and failed 55
because the pinned reader's type-labelled bone attribute contains a JiggleRule
object. The final research probe reads the actual MDL49 uint32 type field using
the same layout as that reader, leaving the runtime and all models unchanged.
Both initial observations, logs and partial outputs remain retained.

[The compact native inventory](benchmarks/sfm_native_feature_inventory_2026-11-12.json)
is the repository metadata record. It contains per-model counts/identities, selected native control/rule/
skin/bodygroup records and preservation details, with no art, raw vertex/delta
arrays or credentials. Detailed 4.18 MB metadata, full bone/rule lists and failed
logs remain private under `output/sfm-extra-native-inventory/1794519206301446900`.
After remote verification, its duplicate `stage` was removed: 82 MDLs / 62,843,920
bytes. Every file was checked against the identical private copy retained in
`output/sfm-extra-native-inventory/portable-root-639301165838922272/stage` for
ongoing feature cases. Original archives remain protected. See the
[cleanup receipt](benchmarks/sfm_native_definition_cleanup_2026-11-12.json).

This inventory proves the features are present. It does not prove HAS skin
switching, native shaders, jiggle constraints/solver fidelity, assembly, arbitrary
native controller semantics, artist usability or rendered equivalence.

The earlier [feature review](sfm_extra_features_2026-11-12.md) and
[identity audit](benchmarks/sfm_extra_feature_inventory_2026-11-12.json) remain
separately scoped. The actual model versions were read before parsing; this pass
refuses unsupported versions rather than coercing them to MDL49. Archive staging
used the installed 7-Zip CLI and existing Source resource-path guards, bounded to
16 MiB per definition / 128 MiB total, with indexed size/CRC/header/SHA checks.

## Reproduce the native metadata inventory

The committed [MDL-only audit](../tools/audit_sfm_native_metadata.py) and
[pinned-structure probe](../tools/sfm_native_metadata_probe.py) preserve the
extraction/parser logic used for this research. Supply explicit paths to existing
approved tools and the original archive directory. The audit verifies all 22
archive identities and the full 82-definition hash multiset against committed
receipts. The probe checks the recorded reader-layout hashes, reads actual MDL
versions and refuses unsupported versions. It does not change the native runtime.

```powershell
python tools/audit_sfm_native_metadata.py --archive-root "C:/path/to/supplied-archives" --seven-zip "C:/path/to/7z.exe" --python "C:/path/to/approved-python.exe" --sourceio output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647 --output output/sfm-extra-native-inventory/new-run
```

The selected Python needs the dependencies already present in the approved
Blender-bundled Python used here. No installation occurs. Choose a new output
folder for each run. Complete MDL copies and detailed metadata stay under the
ignored output folder; review and promote compact metadata separately.

The research run completed 82/82 using the retained experiment scripts. Root then
verified the portable probe against the retained definitions and ran the complete
portable archive-staging/parser CLI. Both parse 82/82 with zero errors/refusals;
every model record exactly matches the final research `metadata-v2.json`, with
all original archive identities unchanged. The earlier `metadata.json` retains
the 27-success/55-error serializer trial. The compact receipt records exact tool,
runtime and result hashes. Blender's bundled Python was used only as an existing
metadata interpreter; this does not establish Blender 5.1 scene-import support.
