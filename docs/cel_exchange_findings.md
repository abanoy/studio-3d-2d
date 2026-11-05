# Read-only companion cel exchange probe

The sibling “Start artist assistant stage” supplied an independently authored packet
under its canonical `experiments/EXP-0059-local-cel-exchange-fixture/fixture/` and
`docs/interop/CEL_EXCHANGE_PROPOSAL.md`. Studio read those files without modifying
the sibling app, installing an importer, or copying its assets into source Git.

`tests/cel_exchange_probe.gd` is an optional detached headless test. Its38checks pass
against the current private fixture: one1920x1080RGBA8 layer, three distinct PNGs,
12frames at24/1, explicit A[0,3), blank[3,5), B[5,9), A[9,12). Every source PNG byte
hash/length and decoded RGBA hash agrees with the producer. Alpha values0/96/255
survive decoding. Every frame assignment matches Drawing.cel_at; frames-1/12 are
absent. Filenames supply no timing. Source hashes remain unchanged afterward.

There is an important distinction between source bytes and a composited image.
Studio currently initializes transparent canvases with `Color.TRANSPARENT`, which
is white RGB with zero alpha in pinned Godot4.6. The fixture uses zero RGB under
zero alpha. Initial complete composite hashes therefore differed. Diagnostics show
**zero alpha differences and zero RGB differences at nonzero alpha**; the partial
sample[35,140,220,96] is exact. Compositing original versus Studio result over both
opaque black and white gives identical bytes. No drawing-engine change was needed.
Raw source/decoded hashes remain exact and separately recorded; composite visual
equivalence does not assert matching invisible RGB or change the originals.
Primary API: [Godot4.6 Color constants](https://docs.godotengine.org/en/4.6/classes/class_color.html#class-color-constant-transparent).

The declared sRGB interpretation fits current behavior; this is not ICC conversion,
monitor calibration, arbitrary-profile or multilayer fidelity evidence. Current
receiver bounds are1080p,4layers,32cels,240frames, FPS numerator<=120/denominator<=1001.
The fixture fits;24000/1001 does not fit the current numerator bound and must not be
silently approximated. The optional probe is not a hardened generic packet parser.

The two apps retain independently editable `.aaa` and `.has` documents. A future
adapter still needs explicit user installation/preview controls, bounds/path checks,
layer/cel identity/copy-on-edit rules and provenance persistence. Studio's current
storage writer filters layer/cel fields, so unknown exchange metadata is not yet a
provenance-preserving save contract. Source/correction/approval declarations stay
inert and do not authorize replacement, training, upload or distribution.

No HAS roundtrip or user-facing exchange import is claimed. The read-only receiver
result is in ignored `output/cel-exchange-probe.json`/`.log`; canonical evidence paths
are sent to the sibling after the verified Studio checkpoint. Existing native model,
camera, drawing and timeline work continues independently of that adapter decision.
