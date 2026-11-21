# Physics on imported ragdolls

Normal Add model, viewport drop, timeline import and Installed-library imports
start new models with Physics off. Hair & clothes also stays off until chosen.
Importing preserves the authored pose and retained native setup; it does not start
motion or add animation keys. Use Physics explicitly when ready. The same standard
model-rig adapter remains available for MMD, GMod, SFM, VRM and compatible common
format skeletons. Unknown chains, invalid scales and oversized rigs remain
poseable with an explanation rather than being forced into invalid ragdolls.
Unrigged props keep their explicit Physics toggle; maps/groups remain static
collision geometry.

The import must be visible at the current frame, with no import/warning dialog,
conversion, playback, export, drawing or manipulation in progress. Native conversion
retains the off intent across its asynchronous preparation. An explicit later
Physics On still uses the existing activation path; an explicit Off cancels a
queued start. Activation is transient,
not a saved key or model field. The Simple toggle stops the body immediately and
freezes its current pose; only explicit Record creates simulation animation.
An empty-world grid still supplies no physical floor.

Adding an asset rebuilds the existing world. Previously live bodies, solid props
and secondary-only/combined body-hair modes resume at their frozen poses after
that rebuild, with velocities reset. They do not steal selection or move the
camera. This is a deliberate restart, not uninterrupted momentum through a
structural edit. Importing while recording first finishes the existing take under
the normal lifecycle rule, then resumes live unrecorded motion.

Queued starts wait for modal dialogs but are cancelled by explicit Physics off,
Save, seeking/playback, export, New/Open, Undo/world replacement or changed actor
data. An asynchronous import that finishes at a frame where its object is absent
stays static; show it and use Physics when ready. Ordinary HAS Open restores
authored poses/recorded takes without launching fresh simulation. Low-level asset
setup with no interactive request also stays passive, for deterministic authoring
and reusable fixtures. There is no special test-environment switch in the product.

`ImportActions.placement()` defaults `physics_on_import` to false and carries that
explicit intent alongside
the already captured view. It is not serialized into model metadata. Append
captures existing live modes before freezing/rebuilding; PhysicsEditor queues
requests bound to exact root identity, data and frame. This prevents stale deferred
activation on a replacement document. Body/hair startup uses the existing shared
solvers, validated native bone IDs, Local/World Record and HAS/MP4 evaluation.
No model/world/container version or source format exporter is added.

`python tests/verify_import_physics.py` runs hidden Windows GPU checks for real
picker/import Off defaults followed by explicit activation, aerial gravity, no
unrequested keys, immediate freeze,
two ragdolls, map collision rebuild, unsupported rigs, unrigged props, modal delay,
cancellation, retained peer intent (separate from the new model default),
secondary-only and native combined mode restoration, explicit Local
Record, authored HAS reopen/independent drawing/MP4, timeline presence and source
hashes. Current measured results and saved-copy status belong in progress_memo.md.
This does not certify all native physics, arbitrary costumes/contact, physical
mouse feel or universal frame rates.
