# Neutral Source eyes — development

New EyeRefract preparations can now retain a usable neutral iris in the same
ordinary GLB/PBR model as the rest of the character. The earlier generic material
path looked only for a base texture; Scout's native material instead supplies
`$iris`, so its eyes previously remained blank. Existing projects are unchanged.

The bridge uses the native eye helper's rest frame, reciprocal iris scale as a
radius, and offset to stage a neutral UV projection. It applies only the matching
eye material's loops, then uses the resolved native iris texture with clamped
edges. Iris alpha is cornea/noise data, not eyeball visibility, so it is not linked
to opacity. Source UVs on the body, mesh positions, bones and deforms stay intact.
The result needs no Source shader or Source-specific runtime posing mode in HAS.

This is an explicit approximation. It does not reproduce refraction, cornea,
lighting/ambient occlusion, dilation, animated gaze or all native shader controls.
Import reports and existing import warnings say so. Missing/ambiguous helpers,
invalid parameters or a missing iris refuse the eye conversion and retain the
existing gray fallback with a reason. A material shared across several mesh
owners currently refuses rather than borrowing the wrong eye's frame.

The native eye data fields are documented in Valve's
[SDK studio header](https://raw.githubusercontent.com/ValveSoftware/source-sdk-2013/master/src/public/studio.h).
The installed SourceIO helper exposes their transform/scale/offset. The neutral
projection is original HAS approximation code; the header does not establish
that this reproduces Source's rendering equation. No vendor shader/code/assets
were copied into the app; only the owner's installed texture is prepared locally.

## Evidence

Two isolated candidates preceded production edits. The first treated helper
radius as diameter and produced visibly small irises; its images remain in
`output/source-eyes-candidate/1793677962816626300`. After inspecting the native
helper's sphere radius convention, the corrected candidate at
`output/source-eyes-candidate/1793678118305846600` produces larger neutral irises.
Both full-body/face comparisons were privately rendered and visually inspected.
These are compatibility improvements, not artist-approved native fidelity.

Six projection tests cover frame center/radius, offset, invalid parameters/
coordinates, unclamped UVs and input preservation. Five actual Blender controls
exercise a rotated/scaled/translated eye helper and mesh, staged edits before
mutation, unchanged body UVs, shared-binding refusal and missing parameters.

The actual SFM-only wrapper passes17 app checks, retaining83 bones, six resolved
textures including the native iris, both native eye records and explicit warnings,
pose/Undo, camera/independent ink, managed and packed HAS reopen, map append and
H2641080p24/48-frame export. Exact GLB comparison against the saved prior texture
fix proves only two eye UV surfaces change; eye vertex positions and11 other
surfaces' positions/UVs remain exact. Exported eyes are opaque and use clamped
texture samplers. Evidence: `output/source-eyes/1793678337943190400` and
`output/source-eyes-verification.json`.

The eleven remaining affected regression groups completed0 on the same frozen
functional source as the focused eye wrapper: native GMod32, host/path/browser
cases, particle data/UI29+5, native CSS/cross-addon browser, workspace/world/HAS/
fill. Eight additional private graphical receipts are confirmed/closed with no
foreground child observed. Evidence: `C:\Users\noble\.codex\worktrees\ec34\cloudflare\hybrid-animation-studio\output\source-eyes-review\1793678426956154600` and
`output/source-eyes-review.json`. Together with focused native and three isolated
comparison receipts,12 accepted private graphical receipts are retained. This is
not a new full verifier result or clean-machine/physical-input/artist acceptance. The normal
installed Studio and frozen web preview remain unchanged. Reimport a Source asset
into a separate scene to compare new preparation; saved embedded assets are never
silently replaced. An editable common gaze/eye-control contract, older Eyes shader
compositing, broad native asset coverage and richer material fidelity remain open.
