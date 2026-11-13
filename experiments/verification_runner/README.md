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
