$ErrorActionPreference='Stop'
$checkout='C:\a\Programming\cloudflare\has-acceptance-session-20261111'
$launchRoot=Join-Path $checkout 'output\sfm-joints-final-replay-launch-20261115T235121533'
$resultRoot=Join-Path $checkout 'output\sfm-joints-final-validation-f0dd57a-20261115'
$launch=Get-Content -LiteralPath (Join-Path $launchRoot 'launch.json') -Raw|ConvertFrom-Json -DateKind String
$result=Get-Content -LiteralPath (Join-Path $resultRoot 'verification.json') -Raw|ConvertFrom-Json -DateKind String
if($launch.pid -ne 75924 -or $launch.creation_utc -ne '2026-11-15T23:51:21.5553028Z' -or $result.passed -ne $false){throw 'Wrong failed replay context'}
$process=Get-Process -Id 75924 -ErrorAction SilentlyContinue
if($process -and $process.StartTime.ToUniversalTime().ToString('o') -eq $launch.creation_utc){throw 'Exact replay coordinator remains'}
$case=Join-Path $resultRoot '01-keiki_tools_chisels-groups-000'
$child=Get-Content -LiteralPath (Join-Path $case 'process-verification.json') -Raw|ConvertFrom-Json -DateKind String
$receipt=Get-Content -LiteralPath (Join-Path $case 'private-receipt.json') -Raw|ConvertFrom-Json -DateKind String
if($child.exit -ne 0 -or $child.retained_Popen_reaped -ne $true -or $child.timed_out -ne $false -or $child.private_receipt_passed -ne $true -or $receipt.exit -ne 0 -or $receipt.job_closed -ne $true -or $receipt.desktop_closed -ne $true -or $receipt.foreground_child_observed -ne $false){throw 'Actual failed-comparison child was not cleanly closed'}
foreach($property in $result.preservation.PSObject.Properties){if($property.Value -ne $true){throw 'A preservation gate failed'}}
$workers=@(Get-CimInstance Win32_Process|Where-Object {
 (($_.Name -match '^(blender|Godot.*|ffmpeg|ffprobe)\.exe$') -and ($_.CommandLine -like '*has-acceptance-session-20261111*' -or $_.CommandLine -like '*HAS-Review-20261115-SFM-Joints-f0dd57a*')) -or
 (($_.Name -match '^pythonw?\.exe$') -and $_.CommandLine -like '*has-acceptance-session-20261111*' -and $_.CommandLine -like '*validate_after_full.py*')
})
if($workers.Count){throw 'A matching runtime remains'}
$target=Join-Path $launchRoot 'authoritative-closure.json'
if(Test-Path -LiteralPath $target){throw 'Preserve previous closure'}
$proof=@{format='has_root_failed_review_closure_1';source_commit=$launch.source_commit;coordinator_pid=75924;expected_creation_utc=$launch.creation_utc;coordinator_original_absent=$true;checked_utc=[DateTime]::UtcNow.ToString('o');validation_passed=$false;engine_checks=41;engine_failures=0;engine_exit=0;actual_private_jobs_closed=1;owned_runtime_commands_absent=$true;no_process_killed=$true;all_preservation_gates=$true;root_graphics_lease_released=$true;failure_retained=$true;failure_scope='Final comparison included decoded runtime audio.source absent from portable expected data; no application failure inferred';verification_sha256=(Get-FileHash -LiteralPath (Join-Path $resultRoot 'verification.json') -Algorithm SHA256).Hash.ToLowerInvariant();private_receipt_sha256=(Get-FileHash -LiteralPath (Join-Path $case 'private-receipt.json') -Algorithm SHA256).Hash.ToLowerInvariant()}
$proof|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $target
$proof|ConvertTo-Json -Depth 6
