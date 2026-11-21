# Physics scenario D: integrated software verification

All six mechanical addendum§17D steps pass with the original included17bone
humanoid, original practice room and three generated solid props. The actual
application imports compatible physics ON, grabs/moves/releases the humanoid,
freezes its fallen pose and opens its real Reset-pose context action. Unrecorded
manipulation creates no authored motion or Undo commands.

Local and World use the connected visible recording controls. Local records49
humanoid samples after10actual prop contacts while leaving unselected prop
authoring unchanged. World records the humanoid and all three props after five
contacts, with measured horizontal displacement above1.5metres in this run.
Both takes reach the exact48-frame end as one Undo command and stop simulation.
Arbitrary seeks replay saved motion. The recorder estimates238,963bytes; actual packed project metadata is230,715bytes,
below the
existing1MiBmetadata limit, while45application frames continue during recording.
Its largest observed sample operation is2.287ms and main-frame gap47.359ms on
this cloud executor; these are observations, not universal latency guarantees.

Twenty-eight writer checks and four fresh-reader checks pass. Originals and the
writer cache are unavailable to the cold reader; included repository originals
are hash-checked and never renamed. All49root/bone states across four model IDs
compare byte for byte using sorted full-precision sample strings. Exact final GPU
pixels, editable paint and PCM remain intact. The48-frame1080p24H264/AAC movie
uses the same frame24 input and decoded audio onset at sample48,001. Manual HAS
and original sources remain unchanged.

A first test retained an actor reference across a world rebuild; stable-ID lookup
corrects it. Another oracle parsed already-normalized JSON floats an extra time,
shifting one near-zero component by1.3e-23. A separate diagnostic proved identical
sample values with equal parse counts. Exact text oracles avoid that extra parse;
no numeric or pixel tolerance was increased. No application behavior was changed.

Run `python tests/verify_scenario_d.py --isolated-display :109 --output
/absolute/new/result` on a private owned display. Windows uses the private-desktop
launcher. Final Windows/physical input acceptance and native Source/MMD/VRM joint/
cloth fidelity remain separate. This two-second case does not establish long/dense
capture performance. See [recorded evidence](benchmarks/scenario_d_2026-11-07.json).
