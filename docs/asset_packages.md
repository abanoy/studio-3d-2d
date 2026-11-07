# Independent model and map packages

Select an independent model or map in the World tree and choose **Save asset .has...**.
The package uses the existing portable `.has` container, as chosen by the owner.
It includes the selected canonical HAS object, its embedded GLB dependencies,
authored controls/animation and source provenance. No third-party format exporter
or new extension is involved. Grouped assets must first be made independent.

Use **Add 3D model** for model packages and **Add scene** for map packages; their
file pickers accept `.has`. Import adds a new object with an independent identity
and one Undo step. It preserves the current scene's camera, cels, audio, settings
and file identity. The original import provenance remains in package metadata.
Ordinary scene HAS files are refused by these asset import actions; use Open project.

Animated packages require frame0, matching frame rate and enough scene duration.
The app reports these requirements before appending the object. Static packages
can start at the current valid frame. Export preserves dirty state and recovery
identity and refuses the filename of the currently open scene. Like ordinary HAS
saves, it uses the validated background snapshot/atomic archive pipeline.

The Linux private-display verification passed74checks:4package contract tests,
28HAS tests,16save-fault tests,22actual-app writer checks and4fresh-reader checks.
Tests use original skinned model/map fixtures, actual save/Add model dialogs,
source/cache-offline imports, exact authored controls/provenance, Undo/Redo,
negative role/timing/ordinary-scene cases, current-file protection and a real
48frame1080p24H264 render. Full ecosystem native fidelity and Windows target
acceptance remain separate; these fixtures do not certify Source/MMD/VRM fidelity.
See [the evidence receipt](benchmarks/asset_packages_2026-11-07.json).
