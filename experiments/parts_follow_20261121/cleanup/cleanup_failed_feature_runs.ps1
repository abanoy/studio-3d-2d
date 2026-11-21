param([switch]$RemoveVerified)
$ErrorActionPreference = 'Stop'
$sessionRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).ProviderPath
$outputRoot = (Resolve-Path -LiteralPath (Join-Path $sessionRoot 'output')).ProviderPath
$proofPath = Join-Path $outputRoot 'ARCHIVE_FOLLOWUP_REMOTE_VERIFIED_20261121.json'
$proof = Get-Content -LiteralPath $proofPath -Raw | ConvertFrom-Json
if ($proof.status -ne 'PASS' -or $proof.revision -ne 'c0618407539ac51a66cb7cb8c5fe44d5acee5e0d' -or -not $proof.all_remote_raw_bytes_equal) { throw 'Remote proof missing' }
$planPath = Join-Path $sessionRoot 'experiments\feature_publication_20261121\CLEANUP_PLAN.json'
$plan = Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
if ($plan.targets.Count -ne 6) { throw 'Unexpected cleanup scope' }
$logCopies = @(
 @('parts\writer-engine.log','failed_parts_input_and_runtime.log','failed_parts_input_closure.json'),
 @('parts\writer-engine.log','failed_parts_embedded_input_fix.log','failed_parts_fixture_closure.json'),
 @('parts\writer-engine.log','failed_parts_vertex_fixture.log','failed_parts_vertex_fixture_closure.json'),
 @('parts\reader-engine.log','failed_parts_json_scale_expectation.log','failed_parts_scale_expectation_closure.json'),
 @('ui-engine.log','failed_regression_missing_audio.log','failed_regression_prerequisite_closure.json'),
 @('engine.log','failed_face_output_folder.log','failed_face_folder_closure.json')
)
# Use the exact committed archive spelling for the embedded-input failure.
$logCopies[1][1] = 'failed_parts_embedded_input_fix.log'
$targets = @()
for ($i=0; $i -lt $plan.targets.Count; $i++) {
 $candidate = Join-Path $sessionRoot $plan.targets[$i]
 $resolved = (Resolve-Path -LiteralPath $candidate).ProviderPath
 if (-not $resolved.StartsWith($outputRoot + '\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Target outside owned output' }
 $item = Get-Item -LiteralPath $resolved -Force
 if (-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Target alias or non-directory' }
 $all = @(Get-ChildItem -LiteralPath $resolved -Recurse -Force)
 foreach ($child in $all) {
  if (-not $child.FullName.StartsWith($resolved + '\',[StringComparison]::OrdinalIgnoreCase) -or ($child.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Child alias or boundary violation' }
 }
 $files = @($all | Where-Object { -not $_.PSIsContainer })
 if ($files.Count -gt 200 -or @($files | Where-Object Length -gt 4194304).Count) { throw 'Unexpected generated-run size' }
 $actualLog = Join-Path $resolved $logCopies[$i][0]
 $savedLog = Join-Path $sessionRoot ('experiments\feature_pass_20261121\' + $logCopies[$i][1])
 if ((Get-FileHash -LiteralPath $actualLog -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $savedLog -Algorithm SHA256).Hash) { throw 'Failed log backup mismatch' }
 $closureName = if ($i -eq 5) { 'launch-result.json' } else { 'verification.json' }
 $savedClosure = Join-Path $sessionRoot ('experiments\feature_publication_20261121\' + $logCopies[$i][2])
 if ((Get-FileHash -LiteralPath (Join-Path $resolved $closureName) -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $savedClosure -Algorithm SHA256).Hash) { throw 'Terminal closure backup mismatch' }
 $targets += [pscustomobject]@{ path=$resolved; files=$files.Count; logical_bytes=($files | Measure-Object Length -Sum).Sum }
}
$processes = @(Get-CimInstance Win32_Process)
$blockers = @()
foreach ($process in $processes) {
 if ($process.Name -notmatch '^(pythonw?|Godot.*|blender)\.exe$') { continue }
 if ([string]::IsNullOrEmpty($process.CommandLine)) { throw ('Cannot inspect relevant process ' + $process.ProcessId) }
 foreach ($target in $targets) {
  if ($process.CommandLine.IndexOf($target.path,[StringComparison]::OrdinalIgnoreCase) -ge 0) { $blockers += $process.ProcessId }
 }
}
if ($blockers.Count) { throw ('Target users remain: ' + ($blockers -join ',')) }
$record = [ordered]@{ format='has_failed_feature_cleanup_1'; status='PREFLIGHT_ONLY'; verified_revision=$proof.revision; targets=$targets; directories=$targets.Count; files=($targets|Measure-Object files -Sum).Sum; logical_bytes=($targets|Measure-Object logical_bytes -Sum).Sum; fresh_processes_inspected=$processes.Count; target_users=0; originals_or_installed_tools_targeted=$false; native_review_or_active_full_targeted=$false; allocated_space_gain_measured=$false }
$record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $outputRoot 'FAILED_FEATURE_CLEANUP_PREFLIGHT_20261121.json') -Encoding utf8
if ($RemoveVerified) {
 foreach ($target in $targets) { Remove-Item -LiteralPath $target.path -Recurse -Force }
 foreach ($target in $targets) { if (Test-Path -LiteralPath $target.path) { throw 'Target remains after removal' } }
 $record.status='REMOVED'
 $record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $outputRoot 'FAILED_FEATURE_CLEANUP_REMOVED_20261121.json') -Encoding utf8
}
$record | ConvertTo-Json -Depth 8
