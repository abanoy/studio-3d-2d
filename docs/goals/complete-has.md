Finish Hybrid Animation Studio’s remaining required implementation and complete every acceptance check that can reasonably run in the cloud before preparing a local handoff.

Repository: abanoy/studio-3d-2d
Workspace: /workspace/studio-3d-2d
Current pushed baseline: c47c500

Follow CODEX_CUSTOM_ANIMATION_STUDIO_SPEC.md and docs/design/HAS_2026-10-29_Voice_Design_Addendum_for_Codex.md. The addendum overrides conflicts. Preserve required, optional, suggested and unresolved distinctions.

PRIMARY OBJECTIVE

Complete the application and its acceptance evidence. Do not substitute progress reporting, checklist maintenance or handoff preparation for implementation.

Preserve the essential workflow:
3D environment → animated camera → independent editable 2D drawings → synchronized preview/audio → portable .has → playable MP4.

ACCEPTANCE BEFORE HANDOFF

Review the actual acceptance steps, relevant code and evidence for each requirement. Separate:
- Software implementation defects.
- Missing or incomplete software tests.
- Missing native assets or dependencies.
- Tests requiring Windows.
- Observations requiring actual people or physical devices.

Finish software defects and missing cloud-testable cases here. A Windows-first product does not make every unfinished requirement local-only. Missing assets may be tested in the cloud once supplied.

Do not conclude that independent cloud work is exhausted merely because checklist entries are marked externally blocked.

CURRENT PRIORITIES

1. Investigate the two retained one-pixel VRM cold-reopen rendering differences. Establish the cause and whether they violate the governing acceptance contract. Preserve the original failed assertions and report any remaining limitation honestly.
2. Review the remaining native import/fidelity conditions against their exact required supported profiles. Implement actionable defects and verify unsupported-feature diagnostics.
3. Complete the combined Source BSP/VRM/PMX acceptance scenario when a complete approved map and dependencies are available. Do not require a game installation for self-contained supplied files.
4. Complete any other acceptance gaps found by this review.

Scenario A’s software route is already verified by 27 checks, with 20 placement regressions after fixing floating placement. Reuse that evidence; do not repeat unchanged passing work without a relevant reason.

EXECUTION AND EVIDENCE

Work autonomously in runnable increments. Verify persistence, Undo/Redo, original-source preservation and preview/export agreement where relevant.

Maintain stable requirement IDs and separate implementation from verification. Record passed, failed, skipped, unrun and blocked checks accurately. Do not weaken assertions simply to obtain passes or add optional features as mandatory completion gates.

Keep graphical automation isolated from the owner’s desktop. Keep private native assets outside Git.

Commit verified changes and push to main without force. Append accurate development history and preserve concurrent changes.

LOCAL HANDOFF

Prepare a local handoff only after independent cloud work is complete. Include:
- Latest pushed commit.
- Exact remaining acceptance steps and runnable commands.
- Expected results and required evidence.
- Specific Windows, asset, device or human prerequisites.
- Known unresolved defects and failed checks.

A local Codex worker can automate Windows checks, but cannot certify novice usability, artistic comfort, tablet latency or audible synchronization without actual observations.

FINISH CONDITION

Finish when every required condition either passes with evidence or has a demonstrated external prerequisite, with all independent work completed.

Do not claim full product completion while required acceptance remains unverified. Store this goal and its progress records in the cloud repository, independently of the owner’s PC.
