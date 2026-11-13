# Independent read-only review of the static-choice draft

Reviewed the listed output-only source bytes. No further clear implementation blocker was found after the fixes below. This is a source review, not a Godot parse, UI, conversion, native appearance or graphics pass. No tests, model/archive reads, native tools, installed runtimes, main changes or Git operations were performed by this reviewer.

| File under overlay | SHA256 |
| --- | --- |
| tools/source_mdl_choices.py | a0f5e551ba9e2e38e3a92ca1d824a09311bf4ec4979a0d9947c128d15666e555 |
| tools/source_choice_io.py | 7d193d4e29389f27483ce3670ce240433af526bd8e186b6851a581fb22e70640 |
| tools/source_appearance.py | 97b54184b92b391feb55f91c9308a89821574dd16f1f292318c13ed07a521f7b |
| tools/prepare_source.py | 2d23571e8bbcfe8c5cbde98bce006282c991f7c2e08670215bc552dc69b3c23e |
| tools/blender_source_bridge.py | dfef09700405e96e289b92bc2b5e98d897f9fcdc86fce54be7f649a7b161372b |
| src/source_choice_dialog.gd | c77da213044d4850758b8a72521978d5ad4d3706366941f6b32e5fe1094948f5 |
| src/source_import.gd | 255a8721603ec49f43c1063a3b4f72248f87476b5cb3b605fbb31346ef10194d |

Two concrete findings were sent to the author and their corrections were reread:

1. `source_appearance.load()` had an initial size check followed by an unbounded read. It now reads at most `MAX_REQUEST + 1`, then refuses excess data. This closes the request-growth allocation gap while retaining the strict schema.
2. The chooser originally serialized `str(group.index)` after JSON parsing. Godot parses JSON numbers as floating point, and float Variant string conversion retains `.0`; the strict Python worker would therefore refuse keys such as `0.0`. The chooser now casts stored metadata/group IDs to integers and uses `str(int(group.index))`. Skin and choice values also remain explicit integer request values. This source issue was not covered by mocked Python transport tests.

The numeric behavior is established by primary Godot4.6 source: [JSON token parsing](https://raw.githubusercontent.com/godotengine/godot/4.6/core/io/json.cpp) at369-372, [Variant string conversion](https://raw.githubusercontent.com/godotengine/godot/4.6/core/variant/variant.cpp) at1553-1554, and [real-number formatting](https://raw.githubusercontent.com/godotengine/godot/4.6/core/string/ustring.cpp) at1490-1498. These pages were read as documentation; no downloaded runtime or tool was used.

The MDL reader's inspected prefix offsets,64-byte material records,16-byte bodyparts,148-byte models and vertex-count offset80 match the existing documented common-layout scope. Counts, ranges, skin material indices, table aliases and external name-pointer overlaps are bounded; tables are reserved before external names. Uninspected native structures remain explicitly outside this claim. The parser preserves numeric choice identities, raw-name hashes and true zero-vertex blanks separately from display text.

Metadata IO performs no extraction. The current input hash and loose-MDL read are capped, and the shared GMA index parser is constrained by an admitted4MiB window. GMA selected payload CRC and VPK selected payload CRC are checked. Original directory/segment stamps are compared after inspection, including failure paths. Existing metadata status files and originals are protected by exclusive creation, including the error handler. Other existing conversion status behavior remains unchanged.

Absent appearance requests preserve the old default actor/BSP-prop `load_model` branch and omit the new request field. Explicit MDL selections rebind original/native SHA and plan every converted choice before changing visibility. Explicit appearance on a BSP is refused. Converted/native group counts, blank ownership, duplicate groups and ambiguous skin-slot mappings remain worker-side refusal gates rather than guesses.

The chooser keeps default preparation available while metadata is pending or unavailable. Member changes and dialog teardown invalidate the inspection generation and kill only that metadata PID; each inspection uses a fresh result path, and a timeout ends the optional inspection. Choosing defaults omits the appearance request. An all-blank explicit choice disables preparation, and the worker independently refuses it. A failed selected conversion cannot silently fall back to a default import.

Before any main port, the remaining gates are real Godot parse and UI lifecycle/request serialization, then exact fresh-source native conversion and app adoption/persistence using the reviewed inputs. Skin shader pixels, broader native geometry/flex equivalence, model assembly and jiggle remain separate. The absence of further source findings does not certify those unrun gates.
