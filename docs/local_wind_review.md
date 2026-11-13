# Local wind preview

The main application now has **Review local wind…** for a selected model with
declared hair/clothing joint chains. This includes compatible imported VRM
chains and parts already configured through the loose-parts setup.

Click a list row to focus it, then use **Try wind on this group** to include or
exclude it. Several checks can coexist. **Try a local blow** starts the preview;
strength and direction can be adjusted. Direction is chosen relative to the
camera when the preview starts. Camera navigation remains available.

The preview uses one temporary model and its own solver. It preserves the
original model, animation, scene settings and running body physics. Linked
weights/joints remain disclosed as a shared group. Stopping or closing restores
the original meshes. Save, Record, playback, seeking, asset replacement and final
output stop the preview; its temporary motion stays out of saved projects and
rendered output. Wind checks are temporary and do not author permanent group
exclusions in Hair & clothes.

This first phase requires already configured chains. Trying a proposed single
or batch helper setup **before Apply**, and making exclusions permanent, remain
unfinished. Generated helper names are still generic. Native Source jiggle,
runtime wardrobe switching and the wider supplied SFM feature set are separate.

## Verified software scope

The actual main project passes **94 unit checks and 845 private graphics checks**:
procedural62, VRM0 47, VRM1 47, derived Back hair49, lifecycle549 and primary91.
The original830 prototype predicates remain; twelve main-root/startup guards and
three canvas-first cleanup checks were added. All948 checked functional files
and prepared native inputs remain unchanged during the run. Six private desktop
receipts have clean exits, confirmed placement, no foreground child and closed
jobs/desktops. Two48-frame1080p PNG exports exclude the temporary candidate.
This is not a new wind-movie or persisted recovery-worker claim.

The first842-check main matrix passed, but the existing SceneView regression
found a cleanup error after explicitly freeing the canvas. Wind cleanup now
checks canvas lifetime before redrawing pose controls. The same focused five
checks produce an engine error with the preserved old Wind controller and a
clean result with the correction. The old failure remains recorded.

After that correction, eight existing wrapper runs pass: native readback,
selection teardown, original secondary helpers, part picking, batch setup,
SceneView, ordinary contact physics and component contact physics. Source and
HEAD stay fixed. The full default suite still needs a fresh stable-source run;
artist/device/native-fidelity and clean-install gates remain open.

Run `python tests/verify_wind_review.py --mode graphical --lease-confirmed
--allow-checkout-eol` serially under the graphics coordinator. The normal
`tests/verify.py` invokes that complete mode; headless/parse modes cannot replace
the six graphics cases. Native inputs use an explicit checksum-bound
`wind-review-inputs.json` under the normal prepared-fixture root. Exact rebuilding
instructions and the reviewed ribbon request are saved in
`experiments/local_wind_review/main_driver_proposal_20261113/REBUILD_INPUTS.md`.
Keep private model payloads out of Git and do not substitute unrelated bundles.

See [actual main evidence](benchmarks/local_wind_main_2026-11-13.json).
