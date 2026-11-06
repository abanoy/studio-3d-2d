# Copy, cut and paste drawings on the timeline

Right-click a drawing block to **Copy drawing** or **Cut drawing**. Right-click
a free range on the same drawing layer and choose **Paste drawing here**.
The entire copied exposure keeps its length, even when you copied from its middle.
Each paste creates a fresh cel with independent editable pixels. Painting the
source or another paste does not change the clipboard's captured drawing.

Copy does not edit the project or add Undo history. Cut and Paste each create
one ordinary drawing history command. Undo/Redo restores their cel ranges and
pixels. Cut leaves an empty range; Paste does not overwrite, shorten or extend
another cel. An overlap, scene-end overflow or the existing global32cel limit
refuses the operation with a message. Layer visibility and opacity still apply.

The clipboard holds at most one full-HD RGBA8 image (8,294,400 bytes), plus its
exposure length and scene/layer address. It clears when its document, sequence
owner or source layer disappears. Copies cannot cross layers, documents or
sequence owners. This preserves the addendum's unresolved cross-track behavior.
The operating system clipboard and existing 3D motion-piece actions are separate.

Menus capture scene revision, video settings and cel identities/ranges/image
revisions. A changed document invalidates the open menu. Painting, navigation,
active timeline gestures, pose drags, export and physics recording block clip
editing. Pending drawing selection/fill/color previews are cancelled when a valid
menu opens. Clipboard data is transient; only the resulting normal cels enter
HAS, recovery and rendering. No project format or cel budget changes.

History retains the existing conservative full-cel accounting and64MiB policy.
This increment does not improve dense-project memory, add ripple/stretch, or
resolve cross-track clip ownership. Physical Windows input and artist acceptance
remain separate gates.

Reproduce with the pinned Godot/FFmpeg activated:

```sh
python tests/verify_cel_clipboard.py --isolated-display :104 --output /absolute/new/audit-folder
```

Linux requires an explicitly provisioned private display. Windows uses the
existing private desktop launcher and validates its receipts; Windows was not
run for this increment.

Fresh Linux software checks:27domain,29Studio and4cold-reader checks pass.
They include actual timeline right-click menu routing, frozen Copy pixels,
independent repeated pastes, Cut/Paste Undo/Redo, exact exposures, overlap/end
refusal, stale-menu/export/recording/budget guards, nested-owner isolation, New
cleanup, normal packed Save and source-cache-unavailable fresh-process Open.
Real H2641080p24 MP4 has48frames/two seconds, with exact frame16 preview/export
input agreement. The saved HAS stays byte-identical during cold readback.

Proof: `/workspace/has-handoff-audit/cel-clipboard-guards/verification.json`.
The first graphical attempt refused safely because the prior private display
was gone. A new owned dummy104display was started; no shared-display fallback.

Existing regressions also pass:161drawing-timing checks including full60second
H264/AAC movie, packed/linked cold readers and actual SIGKILL normal startup;
36live-physics drawing-history checks plus3cold reader;37ordinary3D animation
clip-menu checks with exact split/reopen/recovery pictures. Three optional native
clip fixtures skip because they are unavailable. Python discovery312run/311pass/
1existing optional independent MMD-reader skip. These are scoped software checks,
not Windows/device/native-asset or full-product acceptance.
