# Session-owned verification runner

This preserves the exact hidden-run coordinator used for the November12 attempt.
It is not part of the application. The recorded attempt failed at the old live
appearance oracle; its source hashes stayed unchanged. It is not a full pass.

Review its machine-specific checkout/runtime/input variables before reuse in a
new owned checkout. Reserve a fresh output directory, then launch PowerShell
with `Start-Process -WindowStyle Hidden`, passing the runner and `-RunFolder`.
Only the ordinary tests run graphics, through `run.command` private desktops.
Observe the saved PID together with process creation time; a state file alone
is not proof that a process remains live. Inspect final state and actual logs.
Never overlap graphical test runs or use a visible fallback.

`contact_hair_off_diagnostic_20261112.py` is the historical diagnostic generator.
Run only in an owned checkout of4fee0a9, with the documented native fixtures.
It expects that exact old test assertion, deliberately preserves its failure,
records pose/history comparisons and stops before later recording/movie tests.
Its child exit1 is expected diagnostic evidence, not a passed case. The current
corrected test will intentionally fail its old-source replacement guard. Normal
app and default test execution never load this reference.
