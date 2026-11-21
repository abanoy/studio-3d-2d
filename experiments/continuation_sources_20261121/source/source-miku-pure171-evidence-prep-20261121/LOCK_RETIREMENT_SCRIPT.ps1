$ErrorActionPreference = 'Stop'
$control = 'C:\a\Programming\cloudflare\has-body-addition-20261120\output'
$stage = 'C:\a\Programming\cloudflare\has-miku-pure171-1795254278305351200'
$lane = "$control\source-miku-pure171.lock"
function Require($ok,[string]$message) { if (-not $ok) { throw $message } }
function Digest([string]$path) { (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }
Require ((Digest "$stage\PUBLIC_RESULT.json") -ceq '11949400cb062f0f4971431b9a998683189d30e40da0dd0bfa079196c660b02c') 'Failure result differs'
$receipt = "$stage\Studio\output\private-desktop\probe-unit.json"
Require ((Digest $receipt) -ceq '6b17bb20c7a1bfe834ce85dc9fb6f30496ae0ec7b712d9f5435aa13ea199a02c') 'Prelaunch refusal differs'
$r = Get-Content -LiteralPath $receipt -Raw | ConvertFrom-Json
Require ($r.exit -eq 2 -and $r.error -ceq '[Errno 5] Create private test desktop' -and -not $r.child_desktop_confirmed -and -not $r.private_window_seen -and $null -eq $r.child_pid) 'Refusal is not the exact prelaunch failure'
Require ((Digest $lane) -ceq '14df038cbaa2979881a833b6dec3b740d0ca07e0ce48eb388561f309bfccebd3') 'Lock token changed'
$item = Get-Item -LiteralPath $lane -Force
Require ($item.FullName -ceq $lane -and $item.Directory.FullName -ceq $control -and -not $item.PSIsContainer -and $item.Length -eq 32 -and ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'Lock boundary refused'
$processes = @(Get-CimInstance Win32_Process -ErrorAction Stop)
$matches = @();$unreadable = @()
foreach ($proc in $processes) {
 if ($proc.ProcessId -eq $PID) { continue }
 $line=[string]$proc.CommandLine
 if (-not $line -and $proc.Name -match '^(python|pythonw|Godot|blender|ffmpeg|ffprobe).*\.exe$') { $unreadable += $proc.ProcessId }
 if ($line.Replace('/', '\').IndexOf($stage,[StringComparison]::OrdinalIgnoreCase) -ge 0 -or $line.Replace('/', '\').IndexOf('source-miku-pure171-prep-20261121\run_headless171.py',[StringComparison]::OrdinalIgnoreCase) -ge 0) { $matches += $proc.ProcessId }
}
Require ($matches.Count -eq 0 -and $unreadable.Count -eq 0) 'An owner process remains unresolved'
$destination="$control\source-miku-pure171-prelaunch-refused-1795254278305351200.lock"
Require (-not (Test-Path -LiteralPath $destination)) 'Retained lock copy already exists'
Move-Item -LiteralPath $lane -Destination $destination
Require (-not (Test-Path -LiteralPath $lane) -and (Digest $destination) -ceq '14df038cbaa2979881a833b6dec3b740d0ca07e0ce48eb388561f309bfccebd3') 'Lock retirement failed'
$result=[ordered]@{ format='has_miku171_prelaunch_lock_retirement_1'; status='PRELAUNCH_REFUSAL_PROVEN_NO_ENGINE_OR_JOB_CREATED'; original_result_unchanged=((Digest "$stage\PUBLIC_RESULT.json") -ceq '11949400cb062f0f4971431b9a998683189d30e40da0dd0bfa079196c660b02c'); receipt_unchanged=((Digest $receipt) -ceq '6b17bb20c7a1bfe834ce85dc9fb6f30496ae0ec7b712d9f5435aa13ea199a02c'); historical_status_remains='FAIL'; assertions_executed=0; engine_launched=$false; pinned_launcher_CreateDesktop_precedes_CreateJobObject_and_CreateProcess=$true; host_process_count=$processes.Count; target_matches=$matches; unreadable_runtime_candidates=$unreadable; lock_preserved_at=$destination; lock_sha256=(Digest $destination); utc=[DateTime]::UtcNow.ToString('o') }
$result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$control\MIKU171_PRELAUNCH_LOCK_RETIRED_20261121.json" -Encoding utf8
$result | ConvertTo-Json -Depth 6
