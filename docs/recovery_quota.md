# Shared recovery storage reservations

Before writing a checkpoint, each Studio process reserves space against the same
512MiB recovery root. A short OS file lock serializes reservation admission and
release. The lock inode remains in place; the OS releases it if the helper exits.
The reservation itself records the Studio PID and process incarnation, so it
survives helper exit and protects the complete background checkpoint operation.

Admission counts actual cache bytes plus every outstanding reservation. This
conservatively counts some in-progress bytes twice, favoring refusal over exceeding
the bound. Drawing estimates include PNG overhead; projects that exceed the cheap
raw estimate use the existing bounded, one-image-at-a-time encoded measurement.
The checkpoint still reserves6MiB for metadata/transient files. The helper also
allows for bounded registry publication. The512MiB limit is unchanged.

After success or a normal failure, the worker releases only its own reservation.
Later admissions reclaim a reservation only when a read-only process probe proves
the owner exited or its PID now belongs to another incarnation. Unknown owners
stay reserved. No recovery payload, source, other session or unknown cache file is
deleted by this protocol. Corrupt registries, unsafe links, unknown caller identity
and unavailable helpers refuse checkpoint writes with a message; ordinary manual
project saves remain available.

This closes the race between independent recovery budget checks. It does not
certify whole-process/GPU memory, full-disk or physical power-loss behavior, Windows
target execution, or removal of arbitrary orphaned caches. Retained valid states
can still consume the cache and require manual review.

The final private-display run passed180checks:8Python quota cases,37retention,
33journal and102background snapshot/writer/app/preview/scheduling checks. Another
70nested-reference/audio/real-crash/cold-startup/lesson/media checks passed on the
other private display, including exact preview inputs and48frame1080p24H264/AAC.
The Python cases include real simultaneous subprocess clients, a killed owner,
unknown ownership, corrupt metadata, sparse near-capacity occupancy and actual
symbolic links. The Godot worker verifies refusal while another reservation holds
the budget, unchanged previous metadata and release after success/failure.
See [the evidence receipt](benchmarks/recovery_quota_2026-11-07.json).
Run `python tests/verify_recovery_quota.py --output /absolute/new-case --isolated-display :109`.
