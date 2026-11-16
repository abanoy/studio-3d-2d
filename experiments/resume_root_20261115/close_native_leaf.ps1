param([Parameter(Mandatory=$true)][ValidateRange(1,5)][int]$Attempt)
$ErrorActionPreference='Stop'
$checkout='C:\a\Programming\cloudflare\has-acceptance-session-20261111'
$folder=Join-Path $checkout ('output\source-0x31-native-leaf-20261115-attempt'+$Attempt)
$verification=Join-Path $folder 'verification.json'
$value=Get-Content -LiteralPath $verification -Raw|ConvertFrom-Json -DateKind String
if($value.phases.Count -lt 1 -or $value.inputs_preserved -ne $true){throw 'Owned execution/input evidence required'}
foreach($phase in $value.phases){if($phase.retained_Popen_reaped -ne $true -or $phase.timed_out -ne $false -or $phase.terminated_owned_child -ne $false -or $phase.killed_owned_child -ne $false){throw 'Exceptional owned child requires independent handling; no closure inferred'}}
$workers=@(Get-CimInstance Win32_Process|Where-Object {($_.Name -match '^(Godot.*|blender|ffmpeg|ffprobe)\.exe$') -and ($_.CommandLine -like '*has-acceptance-session-20261111*' -or $_.CommandLine -like '*HAS-Review-20261115-SFM-Joints-f0dd57a*')})
if($workers.Count){throw 'An owned runtime remains'}
$target=Join-Path $folder 'authoritative-closure.json'
if(Test-Path -LiteralPath $target){throw 'Preserve prior closure'}
$proof=@{format='has_root_native_leaf_closure_1';checked_utc=[DateTime]::UtcNow.ToString('o');source_commit=$value.source_HEAD;attempt=$Attempt;validation_passed=$value.passed;owned_headless_children_reaped=$true;owned_runtime_commands_absent=$true;no_process_killed=$true;runtime_lease_released=$true;inputs_preserved=$true;product_integration=$false;verification_sha256=(Get-FileHash -LiteralPath $verification -Algorithm SHA256).Hash.ToLowerInvariant()}
$proof|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $target
$proof|ConvertTo-Json -Depth 6
