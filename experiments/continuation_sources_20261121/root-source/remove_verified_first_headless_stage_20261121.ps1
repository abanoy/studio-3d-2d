$ErrorActionPreference = 'Stop'
$workspace = 'C:\a\Programming\cloudflare'
$target = 'C:\a\Programming\cloudflare\has-headless-components-1795240469769670600'
$control = 'C:\a\Programming\cloudflare\has-body-addition-20261120\output'
$remote = 'C:\a\Programming\cloudflare\has-ui-camera-full-20261121-435dc02'
function Require($condition, [string]$message) { if (-not $condition) { throw $message } }
function Digest([string]$path) { (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }
$proofPath = "$control\UI_CAMERA_REMOTE_VERIFIED_20261121.json"
$proof = Get-Content -LiteralPath $proofPath -Raw | ConvertFrom-Json
Require ($proof.status -ceq 'PASS' -and $proof.revision -ceq '435dc02426a7cdd313e43fe674c9008520845428' -and $proof.selected_paths -eq 1094) 'Remote backup not verified'
$archive = "$remote\experiments\editor_camera_iteration_20261121\source-initial-prelaunch-evidence-prep-20261121"
$pins = @(
 @{ local = "$target\PUBLIC_COMPONENT_RESULT.json"; saved = "$archive\PUBLIC_COMPONENT_RESULT.json"; hash = '6cf3c55964f6eea9eebda2cac1de8ec3ab5986de08476b18fd3271264d3bfac7' },
 @{ local = "$target\default_off\import-private.json"; saved = "$archive\import-private.json"; hash = '8295a6ee35c6bae8187b2f94f73f38cf79734f280f1af47d6301a726705aa2ad' }
)
foreach ($pin in $pins) { Require ((Digest $pin.local) -ceq $pin.hash -and (Digest $pin.saved) -ceq $pin.hash) 'Initial raw failure backup differs' }
Require ((Digest "$archive\component_initial_prelaunch_closed.json") -ceq 'c7f8f2dcecb134c45eb26976dec5715a77ff44cf9cc3294d3334b92eaf64d7b9') 'Closure backup differs'
$closure = Get-Content -LiteralPath "$archive\component_initial_prelaunch_closed.json" -Raw | ConvertFrom-Json
$driver = "$remote\experiments\source_additions_preparation_20261121\source_tree\output\source-headless-component-coordinator-prep-20261121\run_components.py"
Require ((Digest $driver) -ceq 'bd1e7cdc632ab52cbd8e5eb6946f3ee5e03abbe4e160f592462c9896615efd05') 'Published source driver differs'
$rootItem = Get-Item -LiteralPath $target -Force
Require ($rootItem.PSIsContainer -and $rootItem.FullName -ceq $target -and $rootItem.Parent.FullName -ceq $workspace -and ($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'Exact boundary refused'
$items = @(Get-ChildItem -LiteralPath $target -Recurse -Force)
Require (@($items | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count -eq 0) 'Reparse point refused'
$files = @($items | Where-Object { -not $_.PSIsContainer })
$dirs = @($items | Where-Object PSIsContainer)
$bytes = [long](($files | Measure-Object -Property Length -Sum).Sum)
Require ($files.Count -eq 1095 -and $dirs.Count -eq 20 -and $bytes -eq 9020814) 'Stage inventory changed'
$inventoryPath = "$control\HEADLESS_FIRST_REMOVAL_PRE_INVENTORY_20261121.json"
@($files | ForEach-Object { [pscustomobject]@{ relative = $_.FullName.Substring($target.Length + 1); bytes = $_.Length; last_write_utc_ticks = $_.LastWriteTimeUtc.Ticks } }) | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $inventoryPath -Encoding utf8
$processes = @(Get-CimInstance Win32_Process -ErrorAction Stop)
$matches = @(); $unreadable = @()
foreach ($proc in $processes) {
 if ($proc.ProcessId -eq $PID) { continue }
 $line = [string]$proc.CommandLine
 if (-not $line -and $proc.Name -match '^(python|pythonw|Godot|blender|ffmpeg|ffprobe).*\.exe$') { $unreadable += $proc.ProcessId }
 if ($line.Replace('/', '\').IndexOf($target, [StringComparison]::OrdinalIgnoreCase) -ge 0) { $matches += $proc.ProcessId }
}
Require ($matches.Count -eq 0 -and $unreadable.Count -eq 0) 'Process ownership unresolved'
$result = [ordered]@{ format = 'has_first_headless_verified_removal_1'; utc = [DateTime]::UtcNow.ToString('o'); remote_commit = $proof.revision; remote_receipt_sha256 = (Digest $proofPath); stage = $target; files = $files.Count; subdirectories = $dirs.Count; logical_bytes = $bytes; physical_allocation_reclaimed_measured = $false; host_process_count = $processes.Count; target_process_matches = $matches; unreadable_runtime_candidates = $unreadable; inventory_sha256 = (Digest $inventoryPath); status = 'REMOVAL_IN_PROGRESS'; removed = $false }
$resultPath = "$control\HEADLESS_FIRST_VERIFIED_REMOVAL_20261121.json"
$result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $resultPath -Encoding utf8
$immediate = Get-Item -LiteralPath $target -Force
Require ($immediate.FullName -ceq $target -and $immediate.Parent.FullName -ceq $workspace -and ($immediate.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'Immediate exact boundary refused'
Remove-Item -LiteralPath $target -Recurse -Force
Require (-not (Test-Path -LiteralPath $target)) 'Stage remains'
$result.status = 'REMOVED_REMOTE_VERIFIED_DISPOSABLE_STAGE'; $result.removed = $true
$result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $resultPath -Encoding utf8
$result | ConvertTo-Json -Depth 6
