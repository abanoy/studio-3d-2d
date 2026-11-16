param([Parameter(Mandatory=$true)][ValidatePattern('^source-native-live-20261115-attempt[1-9]$')][string]$Run)
$ErrorActionPreference='Stop'
$checkout='C:\a\Programming\cloudflare\has-acceptance-session-20261111'
$folder=Join-Path $checkout ('output\'+$Run)
$verification=Join-Path $folder 'verification.json'
$value=Get-Content -LiteralPath $verification -Raw|ConvertFrom-Json -DateKind String
foreach($flag in $value.preservation.PSObject.Properties){if($flag.Value -ne $true){throw 'Source/input preservation is not established'}}
$phases=@()
foreach($name in @('writer','reader-packed','reader-linked')){
    $directory=Join-Path $folder $name
    $proofPath=Join-Path $directory 'process-verification.json'
    if(-not (Test-Path -LiteralPath $proofPath)){continue}
    $proof=Get-Content -LiteralPath $proofPath -Raw|ConvertFrom-Json -DateKind String
    $receipt=Get-Content -LiteralPath (Join-Path $directory 'private-receipt.json') -Raw|ConvertFrom-Json -DateKind String
    if($proof.retained_Popen_reaped -ne $true -or $proof.timed_out -ne $false -or $receipt.job_closed -ne $true -or $receipt.desktop_closed -ne $true -or $receipt.foreground_child_observed -ne $false -or $receipt.desktop_switch_requested -ne $false){throw 'Owned private runtime closure needs separate handling'}
    $actualPath=Join-Path $directory 'result.json'
    $actual=Get-Content -LiteralPath $actualPath -Raw|ConvertFrom-Json -DateKind String
    $phases+=@{name=$name;exit=$proof.exit;checks=$actual.checks;failures=$actual.failures;job_closed=$true;desktop_closed=$true;retained_Popen_reaped=$true;result_sha256=(Get-FileHash -LiteralPath $actualPath -Algorithm SHA256).Hash.ToLowerInvariant()}
}
if(-not $phases.Count){throw 'Actual owned phase evidence required'}
$owned=@(Get-CimInstance Win32_Process|Where-Object {$_.Name -match '^(Godot.*|blender|ffmpeg|ffprobe)\.exe$' -and $_.CommandLine -like '*has-acceptance-session-20261111*'})
if($owned.Count){throw 'An owned runtime remains active'}
$path=Join-Path $folder 'authoritative-closure.json'
if(Test-Path -LiteralPath $path){throw 'Preserve prior closure'}
$report=@{format='has_native_source_live_root_closure_1';observed_utc=[DateTime]::UtcNow.ToString('o');validation_passed=$value.passed;actual_phases=$phases;owned_private_jobs_closed=$phases.Count;owned_runtime_commands_absent=$true;runtime_lease_released=$true;no_process_killed=$true;verification_sha256=(Get-FileHash -LiteralPath $verification -Algorithm SHA256).Hash.ToLowerInvariant()}
$report|ConvertTo-Json -Depth 10|Set-Content -LiteralPath $path
$report|ConvertTo-Json -Depth 10
