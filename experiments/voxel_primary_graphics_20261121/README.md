# Primary bounded-room VoxelGI graphics — 2026-11-21

The primary integration run at revision 28db0902825721626b17b218aa2a4554ab6da552
passed 68 focused checks: writer 56 and fresh-process reader 12, with Neon and
Classic fixtures. This is distinct from the earlier worker GPU 60 and independent
Full 183 runs; it is not a complete-suite or native-fidelity result.

A red wall supplies indirect light to a floor receiver while a skinned black
blocker moves into the bounce path and away. Its receiver red-channel readings
were 22.38282776 → 18.86719322 → 22.38282776. Scene setup independently changed
22.75003242 →19.08987045 → 22.75003242 in Neon and
22.69925499 →19.05080795 → 22.69925499 in Classic. These are generated-fixture
measurements, not physical lighting or arbitrary-model guarantees.

All measured full-image and receiver-patch preview/capture, movie-source and
cold-reopen differences at frames 0, 1 and 3 were0. The retained ffprobe projection
reports H.264,1920×1080,24fps,four decoded frames. The two private desktop
receipts confirm successful exits,closed Jobs/desktops,no foreground child and
no desktop switch. No engine or graphics job was started while preparing this
evidence.

Read-only visual review of the actual Scene setup frames 0/1 captures showed a
very dark room,stable red wall hotspot,and black blocker moving into the central
bounce path. The floor difference is subtle at full-frame scale and quantified
by the receiver patch. The images are not copied,and no owner appearance
acceptance or photorealism is asserted.

source_hashes.json retains the 227 entries actually present in the completed
wrapper result; all were read back unchanged. It does not invent a 238-entry
source claim. code_used/ holds exact copies of the focused runtime,test,inherited
fixture and verifier; code_pins.json binds them. ORIGINS.json pins the local result
and metadata inputs. input_metadata.json contains only sizes/hashes for generated
fixtures and packed/expected recipes. Baked data is regenerated on reopen.

summary.json removes movie paths and model transform strings. The packet has no
PNG,GLB,HAS,movie,native parameter/pose arrays or calibration matrices. Small RGB
triples and public generated-fixture source code are retained. The source and
results stay local or in their repository; this packet is compact evidence,not
a standalone executable/artwork distribution.

Moving-scene movie export and source-PNG comparisons were Neon only: one
four-frame MP4, compared at frames 0, 1 and 3. Classic has moving preview/capture
and fresh-process cold comparisons, but no moving-video export measurement in
this 68-check fixture. Missing Classic export fields do not mean zero error.
The separate worker empty-room recovery movies are not included in this scope.
