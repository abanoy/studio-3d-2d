$ErrorActionPreference='Stop'
$checkout='C:\a\Programming\cloudflare\has-acceptance-session-20261111'
$runRoot=Join-Path $checkout 'output\native-jiggle-headless-transport-prep-20261115\runtime-post-full-f0dd57a'
$path=Join-Path $runRoot 'verification.json'
$value=Get-Content -LiteralPath $path -Raw|ConvertFrom-Json -DateKind String
if($value.passed -ne $true -or $value.result.checks -ne 41588 -or $value.result.failures -ne 0 -or $value.result.configurations -ne 220 -or $value.source_runtime_inputs_preserved -ne $true -or $value.phases.Count -ne 2){throw 'Actual native transport PASS required'}
foreach($phase in $value.phases){if($phase.passed -ne $true -or $phase.exit -ne 0 -or $phase.retained_Popen_reaped -ne $true -or $phase.timed_out -ne $false -or $phase.terminated_owned_child -ne $false -or $phase.killed_owned_child -ne $false -or $phase.error_markers.Count -ne 0){throw 'Retained headless child did not close cleanly'}}
$workers=@(Get-CimInstance Win32_Process|Where-Object {($_.Name -match '^(Godot.*|blender|ffmpeg|ffprobe)\.exe$') -and ($_.CommandLine -like '*has-acceptance-session-20261111*' -or $_.CommandLine -like '*HAS-Review-20261115-SFM-Joints-f0dd57a*')})
if($workers.Count){throw 'A matching runtime remains'}
$target=Join-Path $runRoot 'authoritative-closure.json'
if(Test-Path -LiteralPath $target){throw 'Preserve prior closure'}
$proof=@{format='has_root_native_transport_closure_1';checked_utc=[DateTime]::UtcNow.ToString('o');source_commit=$value.HEAD;qualified_full_revision=$value.qualified_full_revision;passed=$true;actual_checks=41588;actual_configurations=220;both_retained_Popen_children_reaped=$true;owned_runtime_commands_absent=$true;no_process_killed=$true;runtime_lease_released=$true;private_oracle_not_published=$true;verification_sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant();full_root_closure='output/windows-canonical-bone-binding-20261115T225514304/authoritative-host-termination.json'}
$proof|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $target
$proof|ConvertTo-Json -Depth 6
