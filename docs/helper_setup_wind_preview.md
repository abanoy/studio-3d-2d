# Try a loose-part setup before Apply

The Windows loose-parts editor can now try proposed joints before adding them
to the scene. The try-out uses a temporary derived model and its own solver;
it does not create an authored asset or edit the original model.

1. Select a model, pause that model's Physics and Hair & clothes, then open
   **Set up loose parts**. Review the orange area, attachment and proposed joints.
2. Refine one part, or check several parts with **Include in setup**.
3. Turn on **Try a local blow**. Preparation checks the real imported bindings,
   paused pose and expression before displaying the temporary result.
4. Click a motion-group row to focus it. **Try wind on this group** changes its
   temporary wind check. Several groups can be checked. Strength and direction
   controls appear when the prepared groups are available.
5. Turn the try-out off or press Escape, including while the review window has
   keyboard focus. The original meshes, pose, refinement overlays and controls
   return. **Apply** remains a separate action and requires all live motion to be
   paused before installing the setup as one Undo edit.

Focusing a row, checking temporary wind and including a part in Apply are
separate operations. A linked group may contain several surfaces sharing joints
or weights; the editor explains that scope. These temporary checks do not create
permanent Hair & clothes exclusions or independent weights for linked surfaces.

Independent moving objects can continue during review and the wind try-out.
Save, seeking, playback, recording, final capture, scene replacement, changed
review data and closing invalidate the temporary result. A late worker or import
cannot put it back after cancellation. Unsupported embedded scene effects and
inconsistent bindings are refused before display.

The window uses a viewport-bounded 680-pixel default. Extra wind controls stay
hidden before preparation so ordinary part and joint refinement has more room.
The first focused motion group is actually checked. The worker uses the checked
profile work folder as its current directory; absolute per-job paths and the
owned Windows Job/start gate remain unchanged, including for deep job paths.

## Recorded Windows verification

The current main working-source snapshot passes 208 CPU checks (11 transport,
128 synthetic imported-binding, 69 actual editor/hosting) and 305 private graphics
checks (221 focused/lifecycle, 45 independent peer/owned child, 39 retained native
Back hair). The focused case retains all 199 earlier predicates and adds four UI,
17 popup-Escape endpoint and one real long-job launch check. The ordinary
native-free graphical default is 221+45; the native case is explicit.

The separate driver-domain controls pass 120 checks without a subprocess.
Every accepted run preserves current main/snapshot sources, executable hashes,
HEAD, fixtures, requests and any original/staged native inputs. All three accepted
graphical jobs exit zero and close their private desktop and process Job without
foreground placement. These are software checks, not artist, physical keyboard,
natural-hair, native Source-jiggle or clean-install approval.

Two failed attempts remain recorded: the original deep job current-directory
launch error (207 checks, one failure and 11 skipped endpoint predicates), then
a test's literal mixed-slash comparison (219 checks, one failure). Neither is
relabelled as a pass. The final retry preserves the original motion/restoration
checks and adds the explicit long-job guard.

Use the approved Windows Python with:

```powershell
python -B tests/verify_helper_preview.py --mode prepare --allow-checkout-eol
python -B tests/verify_helper_preview.py --mode cpu --allow-checkout-eol
python -B tests/verify_helper_preview.py --mode graphical --lease-confirmed --allow-checkout-eol
```

The coordinator must exclusively own graphical testing; every graphical command
uses the copied main `run.command()` and its private Windows desktop. The verifier
copies exact current main source into a fresh profile without prototype overlays,
and labels uncommitted source only with explicit `--allow-working-source`.
`--native --inputs-manifest output/wind-review-inputs.json` adds the strict retained
Back hair case. A new checkout must rebuild its private input pair rather than
consume a cached prototype candidate. See the main fixture resolver and
[native input rebuilding](../experiments/local_wind_review/main_driver_proposal_20261113/REBUILD_INPUTS.md).

The earlier full default pass at `9897f86` predates this port. A fresh full default
from the committed integration remains required; scoped checks are not a new
aggregate pass. Evidence: [main integration](benchmarks/helper_pending_preview_main_2026-11-13.json).
