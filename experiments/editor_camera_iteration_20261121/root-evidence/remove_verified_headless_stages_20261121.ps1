$ErrorActionPreference = 'Stop'
$workspace = 'C:\a\Programming\cloudflare'
$outputRoot = 'C:\a\Programming\cloudflare\has-body-addition-20261120\output'
$literalTargets = @(
 'C:\a\Programming\cloudflare\has-headless-components-1795240469769670600',
 'C:\a\Programming\cloudflare\has-headless-components-1795240567956647400',
 'C:\a\Programming\cloudflare\has-headless-components-1795240843368455500',
 'C:\a\Programming\cloudflare\has-headless-components-1795241062433191300'
)
function Require($condition, [string]$message) { if (-not $condition) { throw $message } }
$plan = Get-Content -LiteralPath "$outputRoot\HEADLESS_CLEANUP_PLAN_V2_20261121.json" -Raw | ConvertFrom-Json
$audit = Get-Content -LiteralPath "$outputRoot\HEADLESS_CLEANUP_AUDIT_V3_20261121.json" -Raw | ConvertFrom-Json
Require ($plan.remote_commit -eq '59a112a08373f12dcf771c21734b35391b757d4e') 'Unexpected backed-up checkpoint'
Require ((Get-FileHash -LiteralPath "$outputRoot\post-e087-remote-verification-20261121.json" -Algorithm SHA256).Hash.ToLowerInvariant() -eq 'cc70a5f821ff7be8b58a0c324b3233d4a95736232b39fe164de8e09ae9b76804') 'Remote receipt differs'
Require ($plan.stages.Count -eq 4 -and $audit.stages.Count -eq 4) 'Unexpected stage count'
$inventory = @()
$summaries = @()
foreach ($target in $literalTargets) {
 $entry = @($plan.stages | Where-Object { $_.path -ceq $target })
 $proof = @($audit.stages | Where-Object { $_.path -ceq $target })
 Require ($entry.Count -eq 1 -and $proof.Count -eq 1) 'Target missing from reviewed plan/audit'
 Require ($entry[0].historical_closure_proven -and $entry[0].source_driver_recoverable -and $entry[0].archived_result_exact) 'Closure or backup proof missing'
 $rootItem = Get-Item -LiteralPath $target -Force
 Require ($rootItem.PSIsContainer -and $rootItem.FullName -ceq $target -and $rootItem.Parent.FullName -ceq $workspace) 'Exact workspace boundary failed'
 Require (($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'Root is a reparse point'
 $items = @(Get-ChildItem -LiteralPath $target -Recurse -Force)
 Require (@($items | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count -eq 0) 'Descendant reparse point'
 $files = @($items | Where-Object { -not $_.PSIsContainer })
 $dirs = @($items | Where-Object { $_.PSIsContainer })
 $logicalBytes = [long](($files | Measure-Object -Property Length -Sum).Sum)
 Require ($files.Count -eq $entry[0].files -and $dirs.Count -eq $entry[0].subdirectories -and $logicalBytes -eq $entry[0].logical_bytes) 'Inventory changed since reviewed audit'
 Require ((Get-FileHash -LiteralPath $proof[0].archive -Algorithm SHA256).Hash.ToLowerInvariant() -eq $proof[0].result_sha256) 'Archived result changed'
 Require ((Get-FileHash -LiteralPath $proof[0].source_driver -Algorithm SHA256).Hash.ToLowerInvariant() -eq $proof[0].source_driver_sha256) 'Archived driver changed'
 $inventory += [pscustomobject]@{ stage = $target; files = @($files | ForEach-Object { [pscustomobject]@{ relative = $_.FullName.Substring($target.Length + 1); bytes = $_.Length; last_write_utc_ticks = $_.LastWriteTimeUtc.Ticks } }) }
 $summaries += [pscustomobject]@{ stage = $target; files = $files.Count; subdirectories = $dirs.Count; logical_bytes = $logicalBytes; removed = $false }
}
$inventoryPath = "$outputRoot\HEADLESS_REMOVAL_PRE_INVENTORY_20261121.json"
$inventory | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $inventoryPath -Encoding utf8
$allProcesses = @(Get-CimInstance Win32_Process -ErrorAction Stop)
$matches = @()
$unreadable = @()
foreach ($proc in $allProcesses) {
 if ($proc.ProcessId -eq $PID) { continue }
 $line = [string]$proc.CommandLine
 if (-not $line -and $proc.Name -match '^(python|pythonw|Godot|blender|ffmpeg|ffprobe).*\.exe$') { $unreadable += [pscustomobject]@{ pid = $proc.ProcessId; name = $proc.Name } }
 foreach ($target in $literalTargets) {
  if ($line.Replace('/', '\').IndexOf($target, [StringComparison]::OrdinalIgnoreCase) -ge 0) { $matches += [pscustomobject]@{ pid = $proc.ProcessId; name = $proc.Name; stage = $target } }
 }
}
Require ($matches.Count -eq 0 -and $unreadable.Count -eq 0) 'Process ownership remains unresolved'
$result = [ordered]@{ format = 'has_exact_four_verified_headless_removal_1'; utc = [DateTime]::UtcNow.ToString('o'); remote_commit = $plan.remote_commit; remote_receipt_sha256 = $plan.remote_receipt_sha256; host_process_count = $allProcesses.Count; target_process_matches = $matches; unreadable_runtime_candidates = $unreadable; inventory_sha256 = (Get-FileHash -LiteralPath $inventoryPath -Algorithm SHA256).Hash.ToLowerInvariant(); stages = $summaries; status = 'REMOVAL_IN_PROGRESS'; actual_disk_allocation_reclaimed_measured = $false }
$resultPath = "$outputRoot\HEADLESS_VERIFIED_REMOVAL_20261121.json"
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resultPath -Encoding utf8
foreach ($summary in $summaries) {
 $target = $summary.stage
 Require ($literalTargets -ccontains $target) 'Nonliteral target refused'
 $resolved = Get-Item -LiteralPath $target -Force
 Require ($resolved.FullName -ceq $target -and $resolved.Parent.FullName -ceq $workspace -and ($resolved.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'Immediate boundary check failed'
 Remove-Item -LiteralPath $target -Recurse -Force
 Require (-not (Test-Path -LiteralPath $target)) 'Directory remains after removal'
 $summary.removed = $true
 $result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resultPath -Encoding utf8
}
$result.status = 'REMOVED_FOUR_REMOTE_VERIFIED_DISPOSABLE_STAGES'
$result.total_files = [long](($summaries | Measure-Object -Property files -Sum).Sum)
$result.total_logical_bytes = [long](($summaries | Measure-Object -Property logical_bytes -Sum).Sum)
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resultPath -Encoding utf8
$result | ConvertTo-Json -Depth 8
