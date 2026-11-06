Complete Hybrid Animation Studio in /workspace/studio-3d-2d for the GitHub repository abanoy/studio-3d-2d.

Authoritative requirements
- Follow CODEX_CUSTOM_ANIMATION_STUDIO_SPEC.md and docs/design/HAS_2026-10-29_Voice_Design_Addendum_for_Codex.md.
- The addendum takes precedence wherever they conflict.
- Preserve distinctions between decided requirements, optional ideas, suggestions, preferences to test, and unresolved decisions.
- Read AGENTS.md, LLM.md, the progress memo, the existing requirements matrix, actual source code, and relevant tests before modifying a subsystem.
- Continue the existing application. Preserve working features, saved-project compatibility, source assets, and user changes.

Establish a finite completion checklist
1. Reconcile both documents into one checklist with stable requirement IDs and references to their source sections.
2. Separate required implementation, required verification, optional/deferred ideas, unresolved owner decisions, and tests requiring unavailable environments or assets.
3. Give each required item an explicit acceptance condition, current implementation status, verification status, and supporting evidence.
4. Distinguish verified behavior from code merely being present and from historical test reports.
5. Keep this checklist current. Derive any completion percentage from a documented scoring method; do not present an informal estimate as a measured result.

Implementation priorities
- Preserve the central workflow: external 3D environment → animated camera → independent editable 2D drawings → synchronized audio and preview → playable MP4.
- Prioritize missing required capabilities and significant reliability gaps over cosmetic work or repeated small refinements.
- Address larger remaining areas, including native importer fidelity, long/dense-project memory and loading, animation editing, required compositing tools, and tutorial coverage, according to the reconciled checklist.
- Do not repeatedly polish completed requirements while larger required items remain actionable.
- Do not expand optional or aspirational features into mandatory commitments.
- Ask only for decisions or information that cannot reasonably be inferred. Continue independent authorized work while awaiting answers.

Execution and verification
- Work autonomously in small, runnable increments.
- Reproduce defects where practical, implement the change, and run meaningful checks appropriate to it.
- Verify actual behavior, persistence, Undo/Redo, source preservation, and preview/export agreement where relevant.
- Keep passed, failed, skipped, unrun, and externally blocked checks distinct.
- Do not weaken assertions, fabricate fixtures or results, raise resource limits without justification, or claim procedural tests establish native-format fidelity.
- Keep graphical automation on an explicitly isolated test display or private desktop; never fall back to the owner's visible desktop.
- Preserve historical evidence and avoid committing incidental generated outputs.

Repository delivery
- Commit verified changes and push them to GitHub main without force-pushing.
- Preserve concurrent changes and resolve conflicts carefully.
- Do not modify the owner's Windows installation, the separate web/prototype application, deploy, publish releases, redistribute native assets, or message others without separate authorization.
- Maintain concise implementation documentation and accurate append-only development history.

Progress reporting and continuation
- Report only substantive implementation progress, verification findings, decisions needed, or specific blockers.
- After each increment, state what changed, how it was verified, the commit, and material remaining limitations.
- Send one result message per completed increment. Do not repeat summaries or issue empty status messages.
- An incremental commit does not complete the overall goal. Select the next actionable checklist item and continue.
- If automatic continuation repeats messages without doing work, stop that automation and explain the failure once. Distinguish an automation problem from a project blocker.

External blockers
- Identify exactly which requirements need Windows, physical hardware, owner-approved native fixtures, credentials, or an unresolved owner decision.
- State the specific missing prerequisite and the acceptance test it prevents.
- Complete useful independent implementation and verification before declaring the overall goal blocked.
- Do not invent missing assets, permissions, decisions, or acceptance results.

Finish condition
Finish when every required checklist item is either:
A. implemented and verified with evidence; or
B. explicitly blocked by a named external prerequisite or owner decision, with all independent work completed.

At that point, provide:
- the final checklist and evidence locations;
- the latest pushed commit and repository status;
- implemented features and verified workflows;
- remaining defects or limitations;
- the exact external tests, assets, hardware, or decisions still needed.

Claim full product completion only when all required acceptance conditions pass. Otherwise report that cloud-executable work is complete with explicitly listed external blockers.