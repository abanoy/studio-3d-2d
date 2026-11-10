# Start the local Windows Codex worker

Repository: https://github.com/abanoy/studio-3d-2d

Give this folder to the local Windows Codex worker and say:

> Read WINDOWS_CODEX_GOAL.md and SESSION_STATE.json, retrieve the latest repository
> state, and finish the remaining Windows/native acceptance work. Follow the
> push, verify, then clean-up instructions. Save all new progress in the repository.

This small packet contains instructions and state, not the application or models.
The application, tests, requirements and full evidence are in the repo. The
verified cloud handoff baseline is `3f7a09cdccd7bde9b0d41ac817fb3079fb34a078`.
Latest main also contains this packet and the owner's repository/cleanup rule.
Retrieve latest main and preserve newer work rather than resetting to the baseline.

Use a session-created isolated checkout/worktree. Preserve an existing dirty
checkout and the owner's installed Studio. Reuse approved existing runtimes;
tool installation or installed-app replacement needs separate authorization.

After retrieving the repo, read `AGENTS.md`, both complete governing documents,
`docs/local_acceptance_handoff.md`, the current completion ledger and history.
The handoff contains the runnable Windows commands and exact A–F/device/install
cases. `docs/native_profile_acceptance_review.md` explains the supported profiles.

Every completed increment's source, tests, findings and compact progress/evidence
must be committed and pushed to the repo. Verify the remote copy before removing
finished tasks' disposable local files. Future work must clone/fetch/download that
saved state from the repo rather than relying on this computer's caches.

At assignment end, remove its verified session-owned checkout when no pending
work or unbacked-up deliverable remains. Original owner models/projects and
installed tools are protected; private artwork is not to be pushed.

`MANIFEST.json` gives packet-file SHA256 values. The latest committed repository
state remains authoritative over these pickup snapshots.
