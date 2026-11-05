# Shot visibility distances and temporary editor views

Camera keys now retain the nearest and farthest visible distances as well as
position, rotation and FOV. Frame model/selected/scene can adjust the editor view
without cutting distant geometry out of the saved shot or movie. Export restores
the complete temporary view, including both distances; selection, structural
world updates, clip editing and project-setting Undo use the same view snapshot.

Simple mode retains the existing workflow: frame/navigate, then explicitly save a
camera key. Advanced adds Nearest visible distance and Farthest visible distance
in Scene/camera mode. Changing them only changes the temporary view; it creates
no key, history entry or dirty state. Save camera key stores the actual camera
values. Returning to Draw samples the shot instead. Invalid combinations refuse
with an explanation and leave the previous view intact.

Interactive model imports capture the same near/far range with their view request.
Placement keeps the complete model bounds inside that interval without moving the
camera or changing shot keys. An impossible fit refuses before changing the world
and explains how to widen the view distance. Existing requests without range
fields keep their earlier placement behavior. This is initial placement, not a
new physics floor or automatic model scaling.

## Format and compatibility

Optional numeric `near` and `far` fields live on the existing camera keys. They use
the key's existing hold/linear/ease timing. Absent fields mean0.05 and2000 scene
units, matching an older project's cold-start defaults. Old keys are not rewritten
on Open. Mixed old/new keys use those explicit defaults at missing endpoints.
Both values must be finite, near must be at least0.001, and far must be greater
than near and no more than1e12. The engine exposes float camera properties; keys
store the actual values read from them using the existing full-precision writer.

Model/world/HAS versions and original assets are unchanged. Older Studio builds
may ignore these optional fields, so use the updated build for shots with custom
visibility distances. This is perspective camera support; independent clipping
curves, orthographic authoring, depth of field and physical-camera controls remain
unfinished. Extreme near/far ratios still have the renderer's depth-precision
limitations; the numeric cap is not a guarantee of useful precision at that range.

Storage validates ranges before writing asset/cel copies or replacing a good save,
and on Open before replacing the live world. The managed source/path addresses of
packed models may change as usual; their hashes, native IDs and authored metadata
remain independent of the camera data.

## Evidence and checks

The retained original probe at `output/camera-clip-probe` demonstrated the bug:
framing a nearby box changed far12000 to2000, leaving the camera keys unchanged
while139876green pixels from a wall5000units away disappeared. The fix tests the
same actual distant geometry through explicit camera keys and the normal app.

Run `python -u tests/verify_camera_range.py` using the approved Windows execution
context. The focused suite covers Simple/Advanced controls, explicit keying/Undo,
interpolation, old/partial keys, real near clipping versus independent cyan paint,
same-shot pixel equality after reference framing, successful/cancelled MP4 view
restoration, selection/settings isolation, packed/linked HAS, real recovery,
legacy cold-open output, invalid save/Open preservation and original asset hashes.
It also checks real visible imported pixels beyond a custom near plane, a short
far-plane fit and an impossible-range refusal without world/view changes.
Available prepared MMD/GMod/SFM/VRM0/1 references are framed in the same large scene
and reopened together in packed HAS with exact authored fields/bone IDs and binary
hashes. Native sample availability and actual counts are in the report. All GPU
tests use the private Windows desktop, never a visible fallback.

See the current progress memo for completed runs and canonical-save status. The
full verifier includes this suite. This does not certify subjective camera feel,
all native assets, tablet hardware, arbitrary GPUs or a clean Windows installation.

Primary reference: [Godot4.6 Camera3D](https://docs.godotengine.org/en/4.6/classes/class_camera3d.html)
documents the camera's near/far culling boundaries and aspect/FOV relationship.
HAS's legacy far2000 is its own renderer default, distinct from Godot's default.
