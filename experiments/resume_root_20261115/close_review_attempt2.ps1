$ErrorActionPreference='Stop'
$checkout='C:\a\Programming\cloudflare\has-acceptance-session-20261111'
$launchRoot=Join-Path $checkout 'output\sfm-joints-final-replay-launch2-20261116T001109854'
$resultRoot=Join-Path $checkout 'output\sfm-joints-final-validation-f0dd57a-replay2-20261115'
$launch=Get-Content -LiteralPath (Join-Path $launchRoot 'launch.json') -Raw|ConvertFrom-Json -DateKind String
$result=Get-Content -LiteralPath (Join-Path $resultRoot 'verification.json') -Raw|ConvertFrom-Json -DateKind String
if($launch.pid -ne 80412 -or $launch.creation_utc -ne '2026-11-16T00:11:09.8789596Z' -or $result.passed -ne $true -or $result.results.Count -ne 4){throw 'Wrong successful replay context'}
$process=Get-Process -Id 80412 -ErrorAction SilentlyContinue
if($process -and $process.StartTime.ToUniversalTime().ToString('o') -eq $launch.creation_utc){throw 'Exact replay coordinator remains'}
$total=0
foreach($child in $result.results){
 if($child.passed -ne $true -or $child.exit -ne 0 -or $child.retained_Popen_reaped -ne $true -or $child.timed_out -ne $false -or $child.private_receipt_passed -ne $true -or $child.observed_checks -ne $child.expected_checks){throw 'An actual replay child failed or remains'}
 $total+=$child.observed_checks
 $receipt=Get-Content -LiteralPath $child.private_receipt -Raw|ConvertFrom-Json -DateKind String
 foreach($key in @('private_window_seen','child_desktop_confirmed','job_closed','desktop_closed')){if($receipt.$key -ne $true){throw 'Private placement/closure failed'}}
 if($receipt.exit -ne 0 -or $receipt.foreground_child_observed -ne $false -or $receipt.desktop_switch_requested -ne $false){throw 'Private isolation failed'}
}
if($total -ne 180){throw 'Actual180-check scope differs'}
foreach($property in $result.preservation.PSObject.Properties){if($property.Value -ne $true){throw 'A preservation gate failed'}}
$workers=@(Get-CimInstance Win32_Process|Where-Object {
 (($_.Name -match '^(blender|Godot.*|ffmpeg|ffprobe)\.exe$') -and ($_.CommandLine -like '*has-acceptance-session-20261111*' -or $_.CommandLine -like '*HAS-Review-20261115-SFM-Joints-f0dd57a*')) -or
 (($_.Name -match '^pythonw?\.exe$') -and $_.CommandLine -like '*has-acceptance-session-20261111*' -and $_.CommandLine -like '*validate_after_full.py*')
})
if($workers.Count){throw 'An owned runtime/replay remains'}
$target=Join-Path $launchRoot 'authoritative-closure.json'
if(Test-Path -LiteralPath $target){throw 'Preserve previous closure'}
$proof=@{format='has_root_final_review_replay_closure_1';source_commit=$launch.source_commit;coordinator_pid=80412;expected_creation_utc=$launch.creation_utc;coordinator_original_absent=$true;checked_utc=[DateTime]::UtcNow.ToString('o');validation_passed=$true;engine_checks=180;engine_failures=0;actual_private_jobs_closed=4;owned_runtime_commands_absent=$true;no_process_killed=$true;all_nine_preservation_gates=$true;root_graphics_lease_released=$true;prior_failed_replay_retained=$true;verification_sha256=(Get-FileHash -LiteralPath (Join-Path $resultRoot 'verification.json') -Algorithm SHA256).Hash.ToLowerInvariant()}
$proof|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $target
$proof|ConvertTo-Json -Depth 6
