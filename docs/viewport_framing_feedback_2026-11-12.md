# Scene view, camera framing and resolution — deferred feedback

Recorded November 12, 2026 while work remains paused. This adds the owner's
screenshot observations and requests to the pickup notes. No implementation,
app launch, reproduction tests or acceptance changes were performed.

## Scene setup and optional camera focus

The white rectangular frame is useful for composing a specific camera shot,
camera positions, presets or output formats. While simply arranging the scene,
the owner wants to use the whole available view to see and edit the scene,
with the framed/focused camera panel available as an option. Do not force scene
setup into the smaller output-shaped panel or treat its surrounding space as
unusable. Keep the distinction between the working scene view and what the
chosen camera will render clear.

An optional **3 by 3 composition grid** (nine cells / rule of thirds) is also
suggested for shot framing. Record it as an optional guide, not a compulsory
overlay. Framing guides should help compose the shot without becoming output
artwork.

## Bug: rotation controls escape the focused panel

In the supplied screenshot, a white camera frame surrounds the scene in the
center/right; the RGB rotation rings appear well outside it in the gray area
to the left. The owner identifies this as a focus-panel bug. On resume,
reproduce the drawing/positioning and interaction behavior before diagnosing
the cause. In focused mode, gizmos and their hit targets must respect the
intended panel boundaries and agree with the displayed 3D view. Check panel
resizing and aspect changes as well. This is related to, but separate from,
the ring-direction and camera-facing-ring requests in
[rotation_gizmo_feedback_2026-11-12.md](rotation_gizmo_feedback_2026-11-12.md).

## Output resolution and an exploratory timeline idea

- Keep **1920 by 1080 as the default output**, but provide a way to choose a
  specific resolution, including presets such as **4K** and custom dimensions.
  Camera framing/aspect should make the chosen output clear.
- The owner also floated **changing resolution dynamically in the timeline**,
  describing it as a potentially Advanced feature and a "wild thing." Preserve
  this as an exploratory idea, not an agreed implementation design or a new
  mandatory acceptance gate. On resume, distinguish actual output-dimension
  changes from animated framing/cropping or per-shot settings and determine
  the intended timeline/export behavior before implementing this idea.

## Screenshot evidence and continuation

The supplied image was viewed in the conversation and copied byte-for-byte to
private owned staging so its temporary clipboard location is not the only copy:

`C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\owner-feedback-20261112\viewport-camera-frame.png`

SHA256: `255c5b3fc02ef2765e8fab5ffd32c68498b3ccf3ed778ee21c2814995c38434d`.
Size: 60,256 bytes. The screenshot contains private native artwork and is **not
uploaded to Git**. Preserve this unbacked private evidence with the pending
reviews. Original clipboard image is unchanged.

After an explicit resume, reproduce the focus/gizmo bug, refine full-area scene
setup versus optional shot framing, and review the grid/resolution requests.
Verify preview/export agreement, preserved camera keys and independent drawing
layers, saved settings/projects and gizmo interaction as relevant. Do not resume
work or ask for owner participation merely because this note exists. Existing
unfinished aggregate and ledger counts remain unchanged.
