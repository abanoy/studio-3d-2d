# Import Krita artwork

In desktop Studio, choose Draw → Import Krita artwork, then select a local `.kra`.
Review the source dimensions and layers, prepare a preview, scrub its local frame
control, and choose Add drawing layer. The checkerboard shows transparency.
The prepared clip starts at the scene frame selected when import began. Stills
have an explicit exposure length; animation uses the native inclusive playback
range, sampled at the movie's rate. Fitting preserves the whole source canvas.

Layer visibility starts exactly as saved in Krita. Choose source layers lets you
change individual UUID visibility choices for a scratch render. Nothing silently
removes a Background or guesses that it is a matte. Group visibility still applies
as it does in Krita; enabling a child does not automatically enable its parent.
The selected native layers render together into **one new drawing layer**.
Existing layers, camera keys, models and audio remain independent. Undo removes
the complete import; Redo restores the same editable drawing images.

A configured Krita renderer and installed FFmpeg are required; no runtime is bundled or installed.
Studio checks `HYBRID_KRITA`, a personally saved location, then the usual Program
Files locations. Locate Krita remembers `krita.exe` separately from project data.
The batch renderer runs on a private Windows desktop, with no visible fallback
or command sent to the owner's open Krita instance. Preparation is cancellable.

On Linux, an explicitly configured `HYBRID_KRITA_CONTAINER_IMAGE=sha256:…` may
select an existing local image containing Krita, Python3, Xvfb and xauth. The
renderer uses its own virtual display, offline network, read-only root and source
file, a bounded temporary filesystem, and only the owned output bind. It never
mounts the host display or document plugins. A trusted worker extension is written
only into its temporary private profile; it waits for each native document frame,
exports through Krita’s document API, and closes the document before normal quit.
KRA contents never provide executable startup code. Xvfb reports readiness through
its own display pipe before Krita starts. Image selection comes from the
application environment, never the artwork. Missing images fail without pulling
or opening a visible renderer. Cancellation removes only the labeled owned
container and reaps its launcher; the receipt records actual container isolation
separately from Windows desktop verification.

Changing the scene, frame, working mode or document revision invalidates pending
work. Cancel and New cannot adopt a late result. Adding artwork is deferred while
another file operation runs. The native source hash is checked again at adoption;
changed/missing sources refuse without adding a layer. That final bounded hash
check and packet validation are synchronous; very large inputs can briefly pause
the interface. Images decode one hold per editor frame.

The optional layer `origin` is descriptive ancestry: original filename/hash,
dimensions, source rate/range, explicit visibility choices, fit, import rate and
original placement. It contains no external source path and never automatically
opens a native file. Painting or retiming later does not rewrite that ancestry or
pretend the modified pixels still equal the native file. Packed and linked HAS
both retain the normalized drawing PNGs; the original KRA is not needed to reopen
the imported scene. Recovery uses the same metadata/pixels. Older readers can
display the ordinary cels but may drop optional ancestry on resave.

Current limits are four drawing layers,400 total held drawings across scenes,
1920×1080, and240 frames per native preparation. Registered raster owners have
separate320MiB admission; compressible inactive artwork can remain cold. Preparation also bounds native source size, pixels, layers,
render time, memory and output bytes; see [the worker contract](raster_clip_preparation.md).
Oversized or dense input refuses instead of truncating it. Native audio, editable
Krita layer structures/tiles, linked source refresh and ICC/HDR fidelity are
unsupported by this importer. Video/chroma and nested sequences have their own
workflows. Krita remains the native editor.

`python tests/verify_krita_import.py` exercises the installed native renderer and
actual hidden Studio flow with the owner's local Hecatia sample. Unit guards are
in `test_drawing_origin.py` and `drawing_origin_unit.gd`; see the dated progress
memo for exact accepted runs and retained failures, rather than treating this
procedure as a new full-application regression or physical-input certification.

The original native acceptance fixture is authored by real Krita through
`tests/author_krita_fixture.py --image sha256:… --output /absolute/fresh/folder`.
It creates forty unique transparent frames at24fps using only original rectangles
and this repository's trusted fixture plugin. It is not a synthetic KRA header or
an owner artwork copy. `tools/krita-runtime.Dockerfile` records the tested runtime
recipe; image packages can change at rebuild, so record the resulting image ID and
actual Krita version. The runtime must already exist locally before preparation.
`tests/krita_original_smoke.gd` accepts the fixture folder/source and exercises the
normal review, preview, editable import, persistence and movie flow; `--read`
reopens the saved scene, `--linked` selects its linked version and `--visibility`
checks an explicit native background override followed by Cancel. Use an explicitly
owned private display through `run.configure_private_display`; the older Windows
verifier remains specific to its historical local fixture.
