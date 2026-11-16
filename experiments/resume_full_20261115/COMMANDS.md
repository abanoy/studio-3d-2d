# Future commands — not executed by preparation

These are for the root worker after independently observed terminal PASS and
identity-bound process closure. A running/failed/interrupted run is ineligible.
Keep current HEAD at f0dd57a through the review build. Do not run any command
below merely because this document exists.

```powershell
$resumePython = 'C:\Program Files\Python313\python.exe'
$resumeSourceRecipe = 'C:\a\Programming\cloudflare\has-acceptance-session-20261111\experiments\resume_full_20261115\publication'
$resumeRecipe = 'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\resume-full-publication-f0dd57a-20261115'
$resumeRun = 'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\windows-canonical-bone-binding-20261115T225514304'
$resumeState = Get-Content -LiteralPath "$resumeRun\state.json" -Raw | ConvertFrom-Json
if ($resumeState.status -ne 'passed' -or $resumeState.suite_exit -ne 0 -or $resumeState.source_unchanged -ne $true) { throw 'Fresh full PASS required' }
# Execute only from a byte-verified fresh output copy: summary acquisition remains output-only.
if (Test-Path -LiteralPath $resumeRecipe) { throw 'Preserve existing execution folder' }
$resumeSourceIndexSha = (Get-FileHash -LiteralPath "$resumeSourceRecipe\INDEX.json" -Algorithm SHA256).Hash.ToLowerInvariant()
if ($resumeSourceIndexSha -ne 'f4965594eb313b0ac07ac9d49041cba8cc9f520c99b099115fd5666ae05da873') { throw 'Reviewed public recipe INDEX changed' }
$resumeSourceIndex = Get-Content -LiteralPath "$resumeSourceRecipe\INDEX.json" -Raw | ConvertFrom-Json
foreach ($resumeRow in $resumeSourceIndex.files) {
    if ($resumeRow.path -notmatch '^[A-Za-z0-9_.-]+$') { throw 'Recipe member path refused' }
    $resumeSourceFile = Join-Path $resumeSourceRecipe $resumeRow.path
    if ((Get-Item -LiteralPath $resumeSourceFile).Length -ne $resumeRow.bytes -or (Get-FileHash -LiteralPath $resumeSourceFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $resumeRow.sha256) { throw 'Source recipe bytes changed' }
}
New-Item -ItemType Directory -Path $resumeRecipe -ErrorAction Stop | Out-Null
$resumeCopyRows = foreach ($resumeRow in $resumeSourceIndex.files) {
    $resumeSourceFile = Join-Path $resumeSourceRecipe $resumeRow.path
    $resumeCopiedFile = Join-Path $resumeRecipe $resumeRow.path
    Copy-Item -LiteralPath $resumeSourceFile -Destination $resumeCopiedFile -ErrorAction Stop
    if ((Get-Item -LiteralPath $resumeCopiedFile).Length -ne $resumeRow.bytes -or (Get-FileHash -LiteralPath $resumeCopiedFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $resumeRow.sha256 -or (Get-FileHash -LiteralPath $resumeSourceFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $resumeRow.sha256) { throw 'Copied recipe or source changed' }
    [ordered]@{source=$resumeSourceFile;copied=$resumeCopiedFile;bytes=$resumeRow.bytes;sha256=$resumeRow.sha256;byte_identical=$true}
}
Copy-Item -LiteralPath "$resumeSourceRecipe\INDEX.json" -Destination "$resumeRecipe\SOURCE-RECIPE-INDEX.json" -ErrorAction Stop
if ((Get-FileHash -LiteralPath "$resumeRecipe\SOURCE-RECIPE-INDEX.json" -Algorithm SHA256).Hash.ToLowerInvariant() -ne $resumeSourceIndexSha -or (Get-FileHash -LiteralPath "$resumeSourceRecipe\INDEX.json" -Algorithm SHA256).Hash.ToLowerInvariant() -ne $resumeSourceIndexSha) { throw 'Recipe index changed during copy' }
$resumeCopyProof = [ordered]@{format='has_publication_recipe_execution_copy_1';source_commit=$resumeState.source_commit;canonical_run=$resumeRun;source_recipe=$resumeSourceRecipe;execution_recipe=$resumeRecipe;source_index_sha256=$resumeSourceIndexSha;copied_files=$resumeCopyRows;recipes_executed=$false}
[System.IO.File]::WriteAllText((Join-Path $resumeRecipe 'COPY-PROVENANCE.json'),($resumeCopyProof|ConvertTo-Json -Depth 8),[System.Text.UTF8Encoding]::new($false))
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
