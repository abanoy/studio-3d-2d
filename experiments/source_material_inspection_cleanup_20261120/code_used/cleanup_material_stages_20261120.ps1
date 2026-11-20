param([switch]$Execute)
$ErrorActionPreference = 'Stop'
$cleanupRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$cleanupOutput = [IO.Path]::GetFullPath((Join-Path $cleanupRoot 'output'))
$receiptPath = Join-Path $cleanupOutput 'material-inspection-checkpoint-remote-receipt.json'
$planPath = Join-Path $cleanupOutput 'material-stages-cleanup-plan.json'
$resultPath = Join-Path $cleanupOutput 'material-stages-cleanup-result.json'
$targets = @(
    @('source-material-library-stage-20261120', 'HEADER.json', 'source_material_library_20261120/evidence/header/HEADER.json'),
    @('source-material-binding-run-1795211952067898200', 'PUBLIC_MATERIAL_BINDING_ROOT_RESULT.json', 'source_material_binding_20261120/evidence/actual/PUBLIC_MATERIAL_BINDING_ROOT_RESULT.json'),
    @('source-library-enumeration-run-1795212892760261100', 'PUBLIC_FAILED_RUN.json', 'source_material_library_20261120/evidence/actual-failed-01/PUBLIC_FAILED_RUN.json'),
    @('source-library-enumeration2-run-1795213937191361100', 'PUBLIC_LIBRARY_CENSUS2_ROOT_RESULT.json', 'source_material_library_census2_20261120/evidence/actual/PUBLIC_LIBRARY_CENSUS2_ROOT_RESULT.json'),
    @('source-material-inspection-run-1795214325882521800', 'PUBLIC_MATERIAL_INSPECTION_FAILED_RUN.json', 'source_material_inspection_20261120/evidence/actual-failed/PUBLIC_MATERIAL_INSPECTION_FAILED_RUN.json'),
    @('source-material-inspection2-run-1795215149366755200', 'PUBLIC_MATERIAL_INSPECTION2_ROOT_RESULT.json', 'source_material_inspection2_20261120/evidence/actual/PUBLIC_MATERIAL_INSPECTION2_ROOT_RESULT.json')
)
function Inventory([string]$path) {
    $baseItem = Get-Item -LiteralPath $path -Force
    if (-not $baseItem.PSIsContainer -or ($baseItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Unsafe cleanup root' }
    $entries = @(Get-ChildItem -LiteralPath $path -Recurse -Force)
    if (@($entries | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count) { throw 'Reparse entry refused' }
    $rows = @($entries | Where-Object { -not $_.PSIsContainer } | Sort-Object FullName | ForEach-Object {
        if (-not $_.FullName.StartsWith($path + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Entry escaped cleanup root' }
        [ordered]@{ relative = $_.FullName.Substring($path.Length + 1); bytes = $_.Length; mtime_ticks = $_.LastWriteTimeUtc.Ticks; sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant() }
    })
    $encoded = [Text.Encoding]::UTF8.GetBytes((ConvertTo-Json -InputObject $rows -Depth 6 -Compress))
    [ordered]@{ files = $rows.Count; bytes = [long](($rows | Measure-Object -Property bytes -Sum).Sum); inventory_sha256 = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($encoded)).ToLowerInvariant() }
}
$records = @()
foreach ($target in $targets) {
    $resolved = (Resolve-Path -LiteralPath (Join-Path $cleanupOutput $target[0])).Path
    $expected = [IO.Path]::GetFullPath((Join-Path $cleanupOutput $target[0]))
    if ($resolved -cne $expected -or -not $resolved.StartsWith($cleanupOutput + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Resolved target escaped owned output' }
    $originalProof = Join-Path $resolved $target[1]
    $savedProof = Join-Path (Join-Path $cleanupRoot 'experiments') $target[2]
    $originalHash = (Get-FileHash -LiteralPath $originalProof -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($originalHash -cne (Get-FileHash -LiteralPath $savedProof -Algorithm SHA256).Hash.ToLowerInvariant()) { throw 'Saved compact proof differs' }
    $records += [ordered]@{ name = $target[0]; resolved = $resolved; compact_proof = $target[2]; compact_proof_sha256 = $originalHash; inventory = (Inventory $resolved) }
}
$plan = [ordered]@{ format = 'has_verified_owned_material_stages_cleanup_plan_1'; roots_checked_before_any_removal = $true; target_count = $records.Count; targets = $records; disposable_copies_only = $true; pending_source_preparations_and_full_proofs_retained = $true }
if (-not $Execute) {
    if (Test-Path -LiteralPath $planPath) { throw 'Plan already exists' }
    [IO.File]::WriteAllText($planPath, (ConvertTo-Json -InputObject $plan -Depth 10) + "`n", [Text.UTF8Encoding]::new($false))
    Write-Output (ConvertTo-Json -InputObject @{ status = 'PLAN_ONLY_NO_REMOVAL'; targets = $records.Count; files = ($records.inventory.files | Measure-Object -Sum).Sum; logical_bytes = ($records.inventory.bytes | Measure-Object -Sum).Sum } -Compress)
    exit 0
}
$oldPlan = Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
if (($oldPlan.targets | ConvertTo-Json -Depth 10 -Compress) -cne ($records | ConvertTo-Json -Depth 10 -Compress)) { throw 'Targets changed since plan' }
$backupProof = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
if ($backupProof.format -cne 'has_material_inspection_remote_exact_bytes_1' -or $backupProof.all_changed_files_verified -ne $true -or $backupProof.commit -notmatch '^[0-9a-f]{40}$') { throw 'Remote backup proof missing' }
$head = (& git -C $cleanupRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $head -cne $backupProof.commit) { throw 'Backup proof is not current HEAD' }
if (Test-Path -LiteralPath $resultPath) { throw 'Cleanup result already exists' }
$journal = [ordered]@{ format = 'has_verified_owned_material_stages_cleanup_result_1'; commit = $head; remote_proof_sha256 = (Get-FileHash -LiteralPath $receiptPath -Algorithm SHA256).Hash.ToLowerInvariant(); verified_roots = $records.Count; removed = @(); status = 'IN_PROGRESS'; free_space_gain_measured = $false }
foreach ($record in $records) {
    if ((Inventory $record.resolved | ConvertTo-Json -Compress) -cne ($record.inventory | ConvertTo-Json -Compress)) { throw 'Target changed immediately before removal' }
    Remove-Item -LiteralPath $record.resolved -Recurse -Force
    if (Test-Path -LiteralPath $record.resolved) { throw 'Removed target still exists' }
    $journal.removed += [ordered]@{ name = $record.name; files = $record.inventory.files; logical_bytes = $record.inventory.bytes; absence_confirmed = $true }
    [IO.File]::WriteAllText($resultPath, (ConvertTo-Json -InputObject $journal -Depth 10) + "`n", [Text.UTF8Encoding]::new($false))
}
$journal.status = 'REMOVED_EXACT_VERIFIED_OWNED_STAGES'
[IO.File]::WriteAllText($resultPath, (ConvertTo-Json -InputObject $journal -Depth 10) + "`n", [Text.UTF8Encoding]::new($false))
Write-Output (ConvertTo-Json -InputObject @{ status = $journal.status; targets = $journal.removed.Count; files = ($journal.removed.files | Measure-Object -Sum).Sum; logical_bytes = ($journal.removed.logical_bytes | Measure-Object -Sum).Sum } -Compress)
