Continue Hybrid Animation Studio in /workspace/studio-3d-2d for the GitHub repository abanoy/studio-3d-2d.

AUTHORITATIVE REQUIREMENTS

Follow:
- CODEX_CUSTOM_ANIMATION_STUDIO_SPEC.md
- docs/design/HAS_2026-10-29_Voice_Design_Addendum_for_Codex.md

The addendum overrides conflicts. Preserve distinctions between required, optional, suggested, and unresolved features.

Read AGENTS.md and relevant source, tests, development history, and completion records before changing a subsystem. Continue the existing application while preserving working features, project compatibility, original assets, and concurrent user changes.

GOAL AND PROGRESS RECORDS

Keep this goal in docs/goals/complete-has.md in the cloud repository, independent of my PC.

Maintain docs/completion_checklist.json and its generated Markdown report. Each required item must have:
- A stable requirement ID and source references.
- An explicit acceptance condition.
- Separate implementation and verification statuses.
- Evidence and specific remaining work or external prerequisites.

Do not treat code presence or historical reports as current verification. Publish completion percentages only when derived from an audited, documented scoring method.

IMPLEMENTATION

Preserve the central workflow:
external 3D environment → animated camera → independent editable 2D drawings → synchronized audio and preview → playable MP4.

Prioritize missing required capabilities and significant reliability gaps. Do not repeatedly refine completed features while larger required items remain actionable.

Resume from the actual repository state. Commit b0acd76 added bounded delivery sizes; editable canvases remain 1080p. The next priority is MEM-02: integrity-checked cold/lazy raster storage and measured unique-art loading behavior before increasing resource limits. Reassess priorities when evidence warrants it.

Work autonomously in small, runnable increments. Make reasonable implementation decisions without repeatedly requesting confirmation. Ask only when a missing decision or prerequisite prevents useful progress, and continue independent work where possible.

VERIFICATION AND DELIVERY

For each change:
1. Reproduce the relevant problem where practical.
2. Implement a concrete improvement.
3. Run meaningful checks appropriate to its scope.
4. Verify persistence, Undo/Redo, source preservation, and preview/export agreement where relevant.
5. Update the checklist and append accurate development history.
6. Commit verified changes and push to GitHub main without force-pushing.

Keep passed, failed, skipped, unrun, and externally blocked checks distinct. Do not weaken assertions, invent results, or claim procedural fixtures establish native-format fidelity.

Keep graphical automation on an explicitly isolated display or private desktop. Never fall back to my visible desktop.

Preserve historical evidence and exclude incidental generated outputs from commits.

Do not modify my Windows installation, the separate web/prototype application, deploy, publish releases, redistribute native assets, or message others without separate authorization.

COMMUNICATION AND CONTINUATION

Continue through actionable required work; an incremental commit does not complete the overall goal.

Use commentary for substantive progress during active work. After a completed increment, provide one concise result update stating:
- What changed.
- What was verified.
- The commit and push status.
- Material limitations and the next task.

Do not send repeated summaries, empty replies, or multiple final answers for the same result. Do not use a final answer as a heartbeat or as a mechanism for triggering continuation.

Before repeating any action or message, check the previous result. Retry a failed operation only when there is a new diagnosis or meaningful state change.

If automatic continuation produces another turn without new instructions:
- Inspect the saved progress and actual repository state.
- Perform the next concrete action before reporting progress.
- Do not repeat the previous final answer.

If an automation fault causes repeated replies without work:
- Stop the faulty automatic continuation if that control is available.
- Explain the failure once.
- Preserve the goal, checklist, code, and next actionable task.
- Clearly distinguish the automation fault from a project blocker.
- Do not claim the platform fault is fixed without evidence.
- Resume concrete work when I explicitly instruct you to continue.

ENVIRONMENT RECOVERY

When the cloud environment restarts, wait for readiness, inspect the preserved worktree, and resume unfinished work. Do not restart the project or repeat completed implementation merely because the environment restarted.

EXTERNAL PREREQUISITES

Identify exactly which requirements need Windows, physical hardware, approved native fixtures, credentials, or an unresolved owner decision. State the missing prerequisite and the acceptance test it prevents.

Complete independent work before declaring the overall goal blocked. Do not invent missing permissions, assets, decisions, or acceptance results.

FINISH CONDITION

Finish when every required checklist item is either:
A. Implemented and verified with evidence; or
B. Blocked by a specifically named external prerequisite or owner decision, with all independent work completed.

At that point, provide:
- The final checklist and evidence locations.
- The latest pushed commit and repository status.
- Implemented and verified workflows.
- Remaining defects and limitations.
- Exact external tests, assets, hardware, or decisions still required.

Claim full product completion only when all required acceptance conditions pass. Otherwise, accurately describe the completed cloud work and remaining external blockers.