$ErrorActionPreference = 'Stop'
$workspaceBoundary = 'C:\a\Programming\cloudflare'
$recordRoot = 'C:\a\Programming\cloudflare\has-body-addition-20261120\output'
$expectedNames = @(
 'has-easing-headless-1795254145851799500',
 'has-easing435-app-cpu-1795254384845561100',
 'has-easing435-app-cpu-1795254695259497400',
 'has-easing435-app-cpu-1795254761995523000',
 'has-easing-headless-1795254831934151300',
 'has-easing435-graphics-parse-1795258322734840400',
 'has-easing-c315-graphics-parse-1795260866931895900'
)
$preflightPath = Join-Path $recordRoot 'EASING_CLEANUP_EXACT_PREFLIGHT_20261121.json'
$preflight = Get-Content -LiteralPath $preflightPath -Raw | ConvertFrom-Json
if ($preflight.status -ne 'PASS' -or -not $preflight.all_source_evidence_recovery_bytes_verified -or -not $preflight.exact_native64_identities_and_membership_preserved -or $preflight.targets.Count -ne 7 -or $preflight.files -ne 5640 -or $preflight.logical_bytes -ne 47366153) { throw 'Exact backed-up preflight required' }
foreach ($target in $preflight.targets) {
 if ($target.name -notin $expectedNames) { throw 'Unnamed target refused' }
 $literalTarget = Join-Path $workspaceBoundary $target.name
 $resolvedTarget = (Resolve-Path -LiteralPath $literalTarget).ProviderPath
 if ($resolvedTarget -cne $literalTarget -or $target.path -cne $literalTarget -or ([System.IO.Path]::GetDirectoryName($resolvedTarget)) -cne $workspaceBoundary) { throw 'Resolved absolute target boundary mismatch' }
 $directory = Get-Item -LiteralPath $resolvedTarget -Force
 if (-not $directory.PSIsContainer -or ($directory.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) { throw 'Ordinary directory required' }
}
& 'C:/Program Files/Python313/python.exe' -I -S -B 'C:/a/Programming/cloudflare/has-body-addition-20261120/output/check_easing_cleanup_ready_20261121.py' --verify-only
if ($LASTEXITCODE -ne 0) { throw 'Fresh exact native/hash/recovery verification failed' }
$processes = @(Get-CimInstance -ClassName Win32_Process -ErrorAction Stop)
$unreadable = @($processes | Where-Object { $_.Name -match '(?i)python|blender|godot' -and [string]::IsNullOrWhiteSpace($_.CommandLine) })
$usingTargets = @($processes | Where-Object {
 $commandText = [string]$_.CommandLine
 $found = $false
 foreach ($targetName in $expectedNames) { if ($commandText.IndexOf($targetName, [StringComparison]::OrdinalIgnoreCase) -ge 0) { $found = $true } }
 $found
})
$processAudit = [ordered]@{ format='has_easing_cleanup_process_check_1'; process_count=$processes.Count; unreadable_relevant_processes=@($unreadable | Select-Object ProcessId,Name); target_users=@($usingTargets | Select-Object ProcessId,Name); scan_utc=[DateTime]::UtcNow.ToString('o'); processes_terminated=0 }
$processAudit | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $recordRoot 'EASING_CLEANUP_PROCESS_CHECK_20261121.json') -Encoding utf8
if ($unreadable.Count -ne 0 -or $usingTargets.Count -ne 0) { throw 'Active or unreadable relevant process; retain targets' }
$removed = @()
foreach ($target in $preflight.targets) {
 $literalTarget = Join-Path $workspaceBoundary $target.name
 if ((Resolve-Path -LiteralPath $literalTarget).ProviderPath -cne $literalTarget) { throw 'Target changed before removal' }
 $currentFiles = @(Get-ChildItem -LiteralPath $literalTarget -Recurse -Force -File -ErrorAction Stop)
 $entries = @(Get-ChildItem -LiteralPath $literalTarget -Recurse -Force -ErrorAction Stop)
 if ($currentFiles.Count -ne $target.files -or @($entries | Where-Object { $_.Attributes -band [System.IO.FileAttributes]::ReparsePoint }).Count -ne 0) { throw 'Final ordinary membership check failed' }
 Remove-Item -LiteralPath $literalTarget -Recurse -Force -ErrorAction Stop
 if (Test-Path -LiteralPath $literalTarget) { throw 'Owned target still exists' }
 $removed += [ordered]@{ path=$literalTarget; files=$target.files; logical_bytes=$target.logical_bytes }
}
$result = [ordered]@{ format='has_easing_verified_cpu_cleanup_1'; status='PASS'; remote_revision=$preflight.remote_revision; exact_named_roots=7; files=5640; logical_bytes=47366153; allocated_bytes_freed_claimed=$false; fresh_process_scan_clear=$true; original_assets_or_installed_tools_modified=$false; current_Full_checkout_modified=$false; removed=$removed; utc=[DateTime]::UtcNow.ToString('o') }
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $recordRoot 'EASING_CLEANUP_REMOVED_20261121.json') -Encoding utf8
[PSCustomObject]@{Status='PASS';Directories=7;Files=5640;LogicalBytes=47366153} | ConvertTo-Json -Compress
