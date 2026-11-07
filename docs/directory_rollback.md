# Directory backup payload validation

Before rotating `project.json` into `project.backup.json`, Storage now checks the
previous manifest's declared payloads. Structural metadata alone allowed a primary
with a missing GLB to replace a readable backup. A subsequent interrupted save
could then leave neither committed version readable.

The guard checks managed relative paths, file hashes and bounded image decoding,
including nested sequences. It reads asset hashes without loading geometry and
keeps only digest strings after each cel check. Current-save PNG verification is
reused; older image records without a pixel checksum retain their loader profile.
The operation's digest cache is discarded afterward. It does not retain an eager
project's decoded images or change the saved schema.

An invalid previous primary is not rotated over the backup. A valid replacement
can still repair the project. The existing manifest fingerprint and worker lock
continue to reject stale or competing promotions. This is scoped validation, not
protection against hostile concurrent mutation of immutable payloads.

The before/fixed fixture removes only an owned managed copy of a generated GLB;
original source bytes remain exact. The original code overwrote the valid backup
with the invalid primary. The fixed code preserves and loads the backup. Twenty-six
focused checks cover missing/changed assets, missing/corrupt/changed drawing pixels,
unsafe paths, legacy drawings, valid rotation, nested payloads and bounded digest
reuse. A real worker SIGKILL immediately before primary promotion leaves both
committed files unchanged, the good backup loadable by Godot and the candidate
available for inspection.

Run `python tests/verify_directory_rollback.py` after activating the cloud tools.
Evidence is recorded in `benchmarks/directory_rollback_2026-11-06.json`. Native
Windows, physical power loss and native-rig acceptance remain separate gates.
