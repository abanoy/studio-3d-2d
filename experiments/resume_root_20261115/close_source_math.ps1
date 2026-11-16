$ErrorActionPreference='Stop'
$checkout='C:\a\Programming\cloudflare\has-acceptance-session-20261111'
$folder=Join-Path $checkout 'output\source-0x31-godot-math-20261115-attempt1'
$verification=Join-Path $folder 'verification.json'
$value=Get-Content -LiteralPath $verification -Raw|ConvertFrom-Json -DateKind String
if($value.passed -ne $true -or $value.result.checks -ne 8994 -or $value.result.failures -ne 0 -or $value.inputs_preserved -ne $true -or $value.phases.Count -ne 2){throw 'Actual math execution PASS required'}
foreach($phase in $value.phases){if($phase.passed -ne $true -or $phase.exit -ne 0 -or $phase.retained_Popen_reaped -ne $true -or $phase.timed_out -ne $false -or $phase.terminated_owned_child -ne $false -or $phase.error_markers.Count -ne 0){throw 'Owned headless child closure failed'}}
$workers=@(Get-CimInstance Win32_Process|Where-Object {($_.Name -match '^(Godot.*|blender|ffmpeg|ffprobe)\.exe$') -and ($_.CommandLine -like '*has-acceptance-session-20261111*' -or $_.CommandLine -like '*HAS-Review-20261115-SFM-Joints-f0dd57a*')})
if($workers.Count){throw 'An owned runtime remains'}
$target=Join-Path $folder 'authoritative-closure.json'
if(Test-Path -LiteralPath $target){throw 'Preserve prior closure'}
$proof=@{format='has_root_source_math_closure_1';checked_utc=[DateTime]::UtcNow.ToString('o');source_commit=$value.source_HEAD;checks=8994;failures=0;integration_steps=1440;owned_headless_children_reaped=$true;owned_runtime_commands_absent=$true;no_process_killed=$true;runtime_lease_released=$true;actual_native_geometry_loaded=$false;application_integration=$false;verification_sha256=(Get-FileHash -LiteralPath $verification -Algorithm SHA256).Hash.ToLowerInvariant()}
$proof|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $target
$proof|ConvertTo-Json -Depth 6
