# Voxel integration evidence

This packet preserves the integration of worker commit96e5d50b into38b39ec7 and the subsequent reviewed failed-rebake correction. A native bake can return without replacing earlier data; the correction clears that data first and refuses export after a failed rebuild. A later real rebuild can recover. The seven current implementation/test sources are copied exactly; source_inventory.json pins their raw bytes. CPU verification source hashes match the five runtime source snapshots.

Primary integration CPU results are42 Voxel (34 writer +8 reader),45 SDFGI (37+8), and103 direct-lighting (87+16):190 checks, zero failures, no graphical execution or image measurements. The Voxel total includes eight new failed-rebuild/recovery controls. These CPU results do not establish rendered appearance.

The worker benchmark is separate historical evidence:60 Forward+ graphical checks on the worker branch96e, before the subsequent stale-data correction. Its small RGB/metric values are generated-fixture measurements. They are not new primary integration GPU qualification. Primary Voxel GPU execution remains pending in this record.

The38 pure port controls qualify the dependency refresh before the correction. The6 later pure controls qualify the corrected runtime pin, exact55/71 file bindings, and missing/drift rejection. Neither proof claims graphical execution. Reproduction scripts are retained as provenance; their original owned-output and checkout assumptions still apply.

The published5d receipt and raw hash inventory independently verify retrieval of main5d37647c. Publication is separate from test completion. At Root's request, that checkout's Full run was LIVE under session76914; this packet supplies no Full PASS claim and copies no live job aggregate. Prior failed Full runs retain their prior status.

Only UTF-8 text source, hashes, compact reports and code are included. No HAS/GLB, model artwork, images, video, binaries, private pose/skin/collider/calibration arrays, SDK trees or native-rich aggregate are copied. Nothing is deleted and no engine runs are performed by this collector.

Known limitation reported by Root after these CPU checks: moving the room bounds outside all static environment contributors after a successful bake can retain the prior probe data; a subsequent sync can re-show stale indirect light despite an export error. The current42 checks and a99f2812 runtime fix cover native early-return failure, not this separate empty-contributor path. The worker follow-up remains separate and pending; no claim that all failed-rebuild paths are fixed is made.
