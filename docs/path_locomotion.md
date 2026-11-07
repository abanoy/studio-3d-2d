# Optional walking along a movement path

In Pose, open **Movement path…** on a supported character with a flat
route. Turn on **Suggest walking on this path**, choose a frame and press
**Preview this frame**. Preview changes only the visible pose and playhead;
final captures still use the saved scene. Cancel restores the previous playhead,
view and pose. **Apply path** saves the route and walking choice as one Undo.
Turning the suggestion off restores authored motion; Undo restores the choice.

Advanced exposes step length, foot lift, body lowering and walking amount. Length,
lift and lowering are percentages of measured leg length. The regular Motion
feeling master switch and amount also control walking; per-part anticipation
controls remain separate. Existing helper settings and upper-body motion survive.
The window keeps Apply and Cancel visible while its content scrolls.

The saved intent uses `studio_path_walking_1` inside strict
`studio_motion_assist_4` settings on the existing Model9 component document.
Generated steps never replace authored keys or alter original model bytes.
Recovery, ordinary directory/HAS save, packed cold Open, preview and export use
this same intent. Route presets exchange position keys only: after loading one,
review or enable walking separately. They do not carry these walking settings.

`src/path_locomotion.gd` samples the authored path. Alternating feet retain fixed
stance targets and use eased swing travel/lift, resolved by the existing two-leg
IK solver. Root lowering and leg poses are derived. The suggestion eases in over
0.15 seconds (bounded by half the remaining duration), preserving the exact
starting pose. Neutral leg/hip keys at introduction are supported; later or
nonneutral lower-body keys are refused. An upper-arm draft remains editable while
walking continues. Direct lower-body/root drafts suspend walking at that editing
frame, so manual posing remains exact; final rendering ignores transient drafts.

The current bound is 240 project frames and 64 strides. Build checks every
half-frame before publishing a usable plan. It supports straight routes and forward-progressing flat bends while keeping
authored facing unchanged, including smooth upright yaw keys. Arc length controls
step timing; stance position and orientation stay fixed
in world space and swing targets follow the authored route. It refuses competing
planted-foot ranges, ambiguous/missing legs, grouped characters, nonuniform
parents, changing scale or root tilt, slopes, reversals, Hold jumps and excessive
stride/speed. Some wider bends need shorter steps or more body lowering; plans
that miss the existing 0.2 mm foot-contact bound refuse atomically.
Unsupported saved walking refuses before replacing the installed world or camera.
This does not certify terrain adaptation, automatic turning, general native rigs,
physical input comfort or artist acceptance. MOTION-03 remains partial/open.

Sampling snapshots and restores live root and every bone field around temporary
IK. Plans retain weak actor/bone bindings and one detached cached result. Changed
source, parent or bindings refuse before use; transient editing fields have
separate draft handling. Zero amount and disabled walking return authored motion.
Detached project candidates preflight in their own non-rendering 3D viewport,
leaving the installed camera and world untouched.

```sh
python tests/verify_walking_path.py --isolated-display :107 --output /absolute/new/result
```

On Linux, supply an already provisioned private display. Windows uses the existing
private desktop launcher. The historical straight-only cloud run passes 29 evaluator, 26 canonical
settings, 22 actual app and 4 fresh-process reader checks. Its original included
17-bone figure reaches targets within 0.2 mm over 97 half-frame samples. The reader
uses a new packed asset cache with the owned original source and writer cache
unavailable; drawing pixels and the saved project bytes remain exact. The actual
48-frame 1080p/24 H.264 export has the same input image as final walking preview at
the tested frame. No native fixture or hardware GPU acceptance is claimed.

The original prototype receipt remains historical evidence. Current integration
and regression evidence is in [walking integration](benchmarks/walking_path_2026-11-06.json).

The flat-bend extension and straight-route regression are recorded in
[the November 7 receipt](benchmarks/bending_walk_2026-11-07.json). Use `--bend`
with the command above to exercise a two-segment bend. No facing keys are inferred
or overwritten. Generated walking remains optional saved intent using the existing
schema; older builds can refuse the newly supported route at preflight. General
turning beyond these bounds, terrain, grouped rigs and native/artist acceptance remain open.

Smooth authored yaw now passes the same app/cold-reader/export workflow; use
`--bend --turn` for this case. During a swing the foot turns toward its next
landing orientation. The planted foot keeps its world orientation. This does not
steer the character automatically. Root tilt, stepped turns, turns above 5 degrees
per half-frame and sustained pivots without travel refuse. A component-clip dwell
of up to one frame keeps the existing stance while authored facing continues.
The [authored-turn receipt](benchmarks/authored_turn_walking_2026-11-07.json)
records 43 evaluator, 26 settings, 23 app and 6 cold-reader checks for both a turning
bend and the straight-route regression. All 193 quarter-frame turning samples meet
the existing contact bounds; full-precision five-frame pose replay and two rendered
frames agree exactly across save/Open/export. MOTION-03 remains partial/open.
