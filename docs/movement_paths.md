# Editable movement paths: first increment

In Simple mode, select a model in Pose and open **Movement pathâ€¦** in the
Properties panel. Add a point at a frame, then drag its black dot. Top adjusts
X/Z, Front X/Y and Side Z/Y; each preserves the hidden coordinate. Fit path
frames the controls. Apply saves ordinary root keys as one Undo action. Cancel
discards the staged changes. The blue line samples the existing motion system;
it respects explicit hold jumps and includes enabled motion assistance.

This implements the first manual waypoint step toward addendum Â§5.5. Automatic
walking, foot adaptation, freehand viewport path drawing, depth inference and
reusable path clips remain unfinished. The panel uses coordinates relative to
the model's group; it does not project a moving parent's world-space path.

Path edits now use independent position, rotation and scale timing. On the first
path edit, an older model is upgraded to Model9 without changing its existing
turn or scale curves. Undo restores the original model and version. Opening or
cancelling the panel does not upgrade anything. Adding and deleting points also
refreshes the displayed draft at that frame. There is a 256-point limit. Physics and Hair & clothes must be off during editing. A changed
scene, selection, video settings or playback invalidates staged Apply. Contact
bindings and full-range foot reach are validated before committing.

Verification uses headless mathematical checks and routed engine mouse events
on a private Windows desktop. It is not physical mouse or artist acceptance.
The source fixture is an original procedural skinned limb. Existing native motion
regression covers MMD, GMod, SFM and VRM0/1; this does not prove path editing on
every imported rig. See `output/movement-path-verification.json` and the dated
progress memo for exact results. Normal installed Studio remains at its previously
approved source until a later reviewed update.

The focused upgrade checks cover an older model and an already-upgraded model,
with animated turns and size, frame-zero drag/deletion, exact Undo/Redo, ordinary
packed Save/New/Open and a 48-frame MP4. The separate curve regression covers
372 checks. These are development-copy results; native-rig path acceptance and
broader ordinary Model9 editing still need review before normal installation.

Native contact acceptance (2026-11-03): the new private workflow tests five
prepared MMD/GMod/SFM/VRM rigs, a new frame-six position key, reachable/unreachable
Apply, exact Undo/Redo,97 half-frame peer samples, displayed planted feet and
ordinary packed save/reopen. Four images repeat exactly. Miku retains a one-pixel
reopen difference despite identical sampled poses, displayed bone transforms and
camera transform; this gate is still failing, not waived by a larger tolerance.
New capture-time knee hints now keep the five crouch fixtures uncrossed;
numerically pinned feet alone still do not establish natural posing. Source assets stay
unchanged. A canonical shot transform fixes the earlier VRM0 image mismatch;
the existing camera-range regression passes58 checks with all five native models.
See output/native-path-components-verification.json for the latest negative result.

Ordinary timeline integration (2026-11-03): component-contact clipboard30 and
original-model clipboard27 checks pass on private Windows desktops. The normal
timeline context path copies independent position/rotation/scale source times,
pastes to a transformed-parent instance and retains97 sampled root values.
Split/cut/paste, source-time gaps, movement,89 shifted samples after whole-object
retiming, Undo/Redo, persistent visibility, refusal guards, packed HAS and actual
MP4 pass. This uses the original procedural rig; five-native adapter experiments
are separate evidence. The component variant is now included in verify.py;
the full verifier completed successfully on 2026-11-03 with unchanged functional
source. Focused channel-click and live recording checks also passed. The separate
Miku rendering discrepancy remains unresolved; that native-path test is not part
of the full verifier.


## Rendering correction (2026-11-03)

The earlier Miku one-pixel failure is resolved in the current development source.
Repeated captures isolated a stable post-reopen difference;295 geometry/skin/bone/
camera fields matched exactly. Copying materials alone still failed, while explicit
ordering passed. The GLB loader now gives default-priority opaque materials a stable
source-material order. Transparent materials are untouched; any explicit priority
or next pass preserves the entire supplied set, as does more than256 distinct
opaque materials. No clamping or source-file rewrite occurs. Those skipped sets
retain their earlier tie behavior. Exact equality is not guaranteed for all assets.

The ordinary native path wrapper now passes121/121 with all five native rigs and
no diagnostic override. Six order-contract checks and the affected lighting,
live appearance and camera-range wrappers pass. Full regression was completed
before this fix; it is not claimed as fresh post-fix evidence. Normal installed
Studio is unchanged. User-facing few-pose acting quality remains a separate task.
