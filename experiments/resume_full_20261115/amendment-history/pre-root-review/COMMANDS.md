# Future commands — not executed by preparation

These are for the root worker after independently observed terminal PASS and
identity-bound process closure. A running/failed/interrupted run is ineligible.
Keep current HEAD at f0dd57a through the review build. Do not run any command
below merely because this document exists.

```powershell
$resumePython = 'C:\Program Files\Python313\python.exe'
$resumeRecipe = 'C:\a\Programming\cloudflare\has-acceptance-session-20261111\experiments\resume_full_20261115\publication'
$resumeRun = 'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\windows-canonical-bone-binding-20261115T225514304'
$resumeState = Get-Content -LiteralPath "$resumeRun\state.json" -Raw | ConvertFrom-Json
if ($resumeState.status -ne 'passed' -or $resumeState.suite_exit -ne 0 -or $resumeState.source_unchanged -ne $true) { throw 'Fresh full PASS required' }
$resumeHostSha = (Get-FileHash -LiteralPath "$resumeRun\authoritative-host-termination.json" -Algorithm SHA256).Hash.ToLowerInvariant()
$resumeHostRawSha = (Get-FileHash -LiteralPath "$resumeRun\authoritative-host-terminal.json" -Algorithm SHA256).Hash.ToLowerInvariant()
& $resumePython -B "$resumeRecipe\preflight_terminal.py" --terminal-permission --host-proof-sha256 $resumeHostSha --host-raw-sha256 $resumeHostRawSha
if ($LASTEXITCODE -ne 0) { throw 'Preflight failed; stop' }
& $resumePython -B "$resumeRecipe\audit_receipts.py" --terminal-permission --host-proof-sha256 $resumeHostSha --host-raw-sha256 $resumeHostRawSha
if ($LASTEXITCODE -ne 0) { throw 'Receipt audit failed; stop' }
$resumeInventorySha = (Get-FileHash -LiteralPath "$resumeRecipe\receipt-audit\receipt-inventory.json" -Algorithm SHA256).Hash.ToLowerInvariant()
& $resumePython -B "$resumeRecipe\summarize_canonical.py" --terminal-permission --host-proof "$resumeRun\authoritative-host-termination.json" --host-sha256 $resumeHostSha --receipt-inventory "$resumeRecipe\receipt-audit\receipt-inventory.json" --receipt-sha256 $resumeInventorySha --destination "$resumeRecipe\actual-summary"
if ($LASTEXITCODE -ne 0) { throw 'Summary failed; stop' }
```

Root must inspect the actual receipt audit and authoritatively closed identities,
then independently create the genuine `graphics-lease-released.json` binding
the actual state, host proof and receipt inventory. No recipe creates it.
Continue only after that action and independent review:

```powershell
$resumeReleaseSha = (Get-FileHash -LiteralPath "$resumeRun\graphics-lease-released.json" -Algorithm SHA256).Hash.ToLowerInvariant()
& $resumePython -B "$resumeRecipe\finalize_receipt_index.py" --terminal-permission --inventory-sha256 $resumeInventorySha --release-sha256 $resumeReleaseSha
if ($LASTEXITCODE -ne 0) { throw 'Receipt index failed; stop' }
$resumeSummaryIndexSha = (Get-FileHash -LiteralPath "$resumeRecipe\actual-summary\INDEX.json" -Algorithm SHA256).Hash.ToLowerInvariant()
$resumeAuditIndexSha = (Get-FileHash -LiteralPath "$resumeRecipe\receipt-audit\INDEX.json" -Algorithm SHA256).Hash.ToLowerInvariant()
& $resumePython -B "$resumeRecipe\build_consolidated_packet.py" --terminal-permission --summary-index-sha256 $resumeSummaryIndexSha --audit-index-sha256 $resumeAuditIndexSha
if ($LASTEXITCODE -ne 0) { throw 'Consolidation failed; stop' }
```

After root reviews the resulting packet and build preparation, execute the exact
argument array in `builder/command.json`. This is filesystem preparation only,
with no graphics. It refuses stale source, old full context and an existing
target. Do not advance HEAD before building the pinned f0dd57a snapshot.

After the new build passes, root must grant a separate private graphics lease
before using `replay/command.json`. The GDScript is still unparsed/unrun and the
168 checks are proposed counts. Keep generated review output/.godot and failures;
this preparation grants no cleanup, source-edit or installed-app replacement.
