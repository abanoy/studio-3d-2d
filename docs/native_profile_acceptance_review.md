# Native profile acceptance review — 2026-11-09

This review follows addendum 3.4/3.5 and the actual IMPORT-02/03 and scenario B
conditions. Format coverage is a roadmap. Practical supported behavior and
truthful loss reports are required; perfect reproduction of every native shader,
constraint, simulator, or speculative format is not an extra acceptance gate.

| Profile | Supported behavior and evidence | Limits and remaining required evidence |
| --- | --- | --- |
| Source MDL/SFM/GMA models | All 82 supplied MDLs have conversion/normal-ingress/render evidence. Nine complete characters have separate pose/contact/cold checks. Current GMA native-worker regression passes alongside MMD/PMX. Source sidecars/dependency diagnostics and original hashes are retained. | Source `.phy` is fingerprinted and explicitly reported as omitted; HAS generated physics is separately tested. Approximate native materials and missing dependencies are diagnosed. Installed-content browsing needs an installation only when browsing its content or resolving dependencies there. Standalone files do not require SFM/GMod installed. |
| Source BSP environments | Bounded static entity lights and original style-0 LDR brush-lightmap cases exercise supported code and retain unsupported-lighting diagnostics. | No complete approved native BSP with its materials/props/lightmaps is available here. Procedural brush tests do not establish native map fidelity or complete scenario B. |
| MMD PMD/PMX and VPD/VMD | Thirteen renderable native model/environment conversions and 93 app checks cover shared model ingress, review/apply, pose/motion, Undo/Redo, portable replay and movies. Current PMD/PMX worker regression passes. Bone-only PMD refuses clearly. | Toon/sphere/edge shading and native physics/constraint limitations are explicitly reported. Street PMX lacks five named atlas files; material-color fallback is tested, complete street material fidelity is not. |
| VRM0/1 | Four supplied files have source/BIN preservation, actual worker ingress, humanoid/bone bindings, manual pose and expressions, supported spring startup/steps, generated HAS physics, portable replay and movie evidence. Sakuya terminal helpers are handled without inventing bones. Current fixed-version cold pixels are exact on all four. | MToon/outline approximation, gaze/first-person data-only behavior and unsupported procedural/material expression effects remain declared. These are scoped compatibility limits, not claims of full native reproduction. Historical arbitrary depth-tie image references remain preserved. |
| Canonical GLB and registered glTF extensions | Embedded resources and source identity are retained. The loader rejects external resources; it now checks required features against the pinned engine's actual registered extension catalogue and names unsupported features. Optional metadata stays optional. | Native unsupported required features refuse instead of being stripped. Other exchange/native source formats remain covered only by their separately documented adapter profiles, not inferred from GLB or extension counts. |
| Native HAS model/map/project packages | The existing `.has` ZIP/manifest contract supports independent asset kinds and projects, embedded dependencies and provenance. | The owner already chose reuse of `.has`. No new extension or speculative hex-header format is required. |

The review found two independent cloud fixes, both completed:

1. Cutout depth ties were allocation-dependent because only fully opaque materials
   received stable source order. Controlled legacy/copy/order probes identify the
   cause, including bit-exact camera/root/bone state. Current exact assertions pass
   after extending the policy to alpha-scissor materials. Explicit priorities,
   multipass, transparency and material-count bounds retain their contracts.
2. Unsupported required glTF features produced a generic app parse error despite
   precise engine logs. Preflight now names the feature and compatible-export
   action. Actual native refusal preserves world, camera, drawings, Undo and input
   bytes; supported Source/MMD/VRM imports still pass.

The current exact scenario A wrapper also passes, including fresh-process replay,
conversion/input-copy/writer-cache isolation, original SHA/mtime preservation and
an actual 1080p/24 H.264 movie. This does not supply novice or Windows observations.

The remaining native prerequisite is concrete input data: a complete BSP with
available dependencies and the five street atlas PNG files listed in the
[handoff](local_acceptance_handoff.md). The uploaded attachment inventory contains
none of those named files and no `.bsp`. `temp.gma` exceeded the transfer tool's
32 MiB limit and was not inspected; its contents cannot be assumed. These assets
can be tested in the cloud if supplied. No blanket local-only importer gate exists.

Evidence, each with its own executed scope:

- [Source corpus](benchmarks/supplied_source_corpus_2026-11-08.json), [MMD/GMA](benchmarks/native_mmd_gma_2026-11-08.json), [native VRM](benchmarks/native_vrm_2026-11-09.json).
- [Cutout causality and exact current replay](benchmarks/vrm_cutout_order_2026-11-09.json).
- [Required-feature refusal, supported native workers and scenario A wrapper](benchmarks/required_feature_diagnostics_2026-11-09.json).
- [Remaining prerequisites](cloud_remaining_prerequisites.md), [A–F review](acceptance_handoff_review.md), and [completion ledger](completion_checklist.json).
