# Krita reference findings — 2026-10-29

Read-only inspection of the owner's nine supplied KRA references in the separate
artist-animation-assistant samples directory. Originals were not edited. Inspected
ZIP directories, bounded document/keyframe XML, and representative saved composite
previews. Native raster tiles, complete animated playback and effects rendering
were not decoded. This is reference research, not a KRA importer or fidelity test.

## Animation references

All six are 2560×1440, 24 fps, RGBA with sRGB-elle-V2-srgbtrc.icc. Ranges below are
inclusive; counts include hidden layers. Key entries are per-layer entries rather
than unique global frames or proof of distinct image contents.

| File | Range | Frames | Paint layers | Key entries | Layer style nodes |
| --- | --- | ---: | ---: | ---: | ---: |
| part1.kra | 0–174 | 175 | 16 | 412 | 7 |
| part2.kra | 0–261 | 262 | 9 | 448 | 4 |
| part3.kra | 0–231 | 232 | 15 | 606 | 9 |
| part4.kra | 0–233 | 234 | 11 | 912 | 7 |
| part5.kra | 0–318 | 319 | 10 | 543 | 6 |
| part6.kra | 0–114 | 115 | 10 | 157 | 0 |

The references mix dense background tracks with independently timed drawing/layout
tracks. Key spacings include ones, twos, threes, sixes and long holds. All inspected
animation layer composite operations are normal, but separate styles and layer
opacity still affect appearance. Generic duplicated layer names must not become
identifiers. Hidden layers and existing key timing must survive eventual import.

## Still references

| File | Dimensions | Layer nodes | Structure / composite operations |
| --- | --- | ---: | --- |
| alice.kra | 2880×1800 | 100 | 16 groups, 84 paint; normal, luminize, overlay, darken, multiply |
| hecatia.kra | 2160×3840 | 19 | Paint layers; normal |
| hecatia_redo.kra | 1800×2880 | 82 | 6 groups, 76 paint; normal, overlay, multiply |

Layer styles are present in the first and third stills. These are structural
references for preserving the owner's workflow, not material to restyle or replace.
Private previews are excluded from the source snapshot and permanent delivery.

## Consequences for the studio

- Keep independent layer exposures and hold semantics alongside camera/pose tracks.
- Future resolution/duration controls must support the actual 1440p/319-frame work.
  Current 1080p, 240-frame and 32-cel bounds cannot open these projects.
- Preserve groups, opacity, profiles, styles, source IDs and unsupported metadata.
  Any flattened fallback needs an explicit loss report and the native original.
- Avoid eagerly allocating full canvases for every key: one 1440p RGBA8 canvas is
  about 14.06 MiB and these six documents contain 3,078 key entries. Lazy/tiled
  storage and memory measurements are necessary before native animation import.
- A KRA merged PNG represents the saved composite; it does not establish native
  layer recovery, effects equivalence or full animation playback.

The current app still accepts embedded GLB and PCM16 WAV, with its own editable
PNG cels. No native KRA picker, importer, tile decoder or Krita automation was added.
Next drawing priorities remain owner feedback and recovery; native import is a
separate bounded milestone after preserving the current working loop.

Primary format/workflow references: [Krita KRA format](https://docs.krita.org/en/general_concepts/file_formats/file_kra.html)
and [Krita animation timeline](https://docs.krita.org/en/reference_manual/dockers/animation_timeline.html).
