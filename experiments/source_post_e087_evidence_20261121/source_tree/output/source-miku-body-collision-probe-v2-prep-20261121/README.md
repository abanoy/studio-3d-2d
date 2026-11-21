# Private saved-Miku collision probe: explicit editing context

SOURCE ONLY, UNPARSED/UNRUN. This is a versioned successor to the frozen31-control probe. All six original files are preserved byte-exact under bases/. The old31 assertions remain unchanged; nine new controls exercise actual Model.sample draft/timeline behavior and reject non-boolean context values. Total authored controls:40. No current app, helper parser, model, project, native or GPU work was executed.

## Corrected creation and cleanup boundary

The saved Miku case has six visible draft pose channels that differ from its authored body base. The original probe hard-coded editing=false and could therefore test another pose. Root must now call await Probe.begin(actor, frame, private_request, owned_host, app.mode.selected==2). The fifth argument is mandatory and must be a boolean. A pure sample_initial helper shares that exact sampling boundary with the new actual-Model controls. Do not assume true means a draft exists: the actual Model samples the draft only at its own draft frame. Record the supplied context with the reproduction result; the summary reports initial_editing_context and keeps saved_draft_context_qualified false.

This successor also captures initial_world before applying the sampled pose, in the same order as SecondaryLive.create. Failure/disposal applies the same supplied editing context after removing temporary live state. The real SecondaryLive.advance calls and its smoothing/collision math are unchanged. During raw/visible FK inspection the same live-pose application boundary as SecondaryLive.advance is retained.

Copy the new secondary_collision_probe.gd and secondary_collision_probe_unit.gd into an owned snapshot at res://src/ and res://tests/ respectively. Use the exact dependency pins in bases/INPUTS.json. The nine added controls use the real existing Model with a draft at frame3 and distinct keyed motion; no native Miku geometry is used by these source controls. Root must parse/run the40 controls and then execute the actual saved-case probe on a private graphical desktop with a retained wall-clock watchdog. Initialization awaits process_frame and actual frame_post_draw; there is no visible fallback or headless contact claim.

## Existing qualification limits remain

Read bases/README.md for exact private request admission, sphere/capsule membership, independent per-tick solver/raw-FK/final-blend particle measurements, strict input preservation and original source controls. The old text describes31 controls and the old four-argument API; this successor is the authoritative fifth-argument correction. Segments, actual deformed skin, moving arms, actor inertia, sweeping and body-triangle collision are still not qualified. The separately prepared geometry helper can measure segment/skin crossings once Root independently binds its actual skinning frames. Private dimensions, source arrays, projects and assets must remain local.

The Junko screenshot case remains separate from this saved Miku scene; see bases/JUNKO_CASE.md. All original source and failure/unrun evidence is preserved. New generated collider persistence still needs an explicit supported capability/old-reader refusal. No application adoption.
