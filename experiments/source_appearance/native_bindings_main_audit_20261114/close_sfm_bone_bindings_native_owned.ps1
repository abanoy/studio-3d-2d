param([Parameter(Mandatory=$true)][string]$LaunchRoot)
$ErrorActionPreference='Stop'
$checkout='C:\a\Programming\cloudflare\has-acceptance-session-20261111'
$resolved=[System.IO.Path]::GetFullPath($LaunchRoot)
$boundary=[System.IO.Path]::GetFullPath((Join-Path $checkout 'output'))+[System.IO.Path]::DirectorySeparatorChar
if(-not $resolved.StartsWith($boundary,[System.StringComparison]::OrdinalIgnoreCase) -or (Split-Path $resolved -Leaf) -notlike 'sfm-bone-bindings-native-launch-*'){throw 'Native terminal observation escaped its owned run'}
$launchPath=Join-Path $resolved 'launch.json'
$verificationPath=Join-Path $resolved 'run\verification.json'
$launch=Get-Content -LiteralPath $launchPath -Raw|ConvertFrom-Json -DateKind String
$verification=Get-Content -LiteralPath $verificationPath -Raw|ConvertFrom-Json -DateKind String
if($launch.format -ne 'has_root_sfm_bone_bindings_native_launch_1' -or $launch.launch -ne $resolved -or $verification.source_before.revision -ne $launch.source_commit){throw 'Native source/launch identity differs'}
$process=Get-Process -Id $launch.pid -ErrorAction SilentlyContinue
$currentCreation=$null
if($process){$currentCreation=$process.StartTime.ToUniversalTime().ToString('o')}
if($process -and $currentCreation -eq $launch.creation_utc){throw 'Exact owned coordinator is still running'}
$workers=@(Get-CimInstance Win32_Process | Where-Object {
 (($_.Name -match '^(blender|Godot.*|ffmpeg|ffprobe)\.exe$') -and $_.CommandLine -like '*has-acceptance-session-20261111*') -or
 (($_.Name -match '^pythonw?\.exe$') -and $_.CommandLine -like '*has-acceptance-session-20261111*' -and ($_.CommandLine -like '*verify_source_choices_native*' -or $_.CommandLine -like '*tests/verify.py*' -or $_.CommandLine -like '*tests\verify.py*'))
})
if($workers.Count){throw 'Matching owned runtime commands remain; no terminal proof written'}
$path=Join-Path $resolved 'authoritative-host-terminal.json'
if(Test-Path -LiteralPath $path){throw 'Preserve the previous host observation'}
$row=@{format='has_root_sfm_bone_bindings_native_terminal_1';pid=$launch.pid;creation_utc=$launch.creation_utc;current_same_pid_creation_utc=$currentCreation;observed_utc=[DateTime]::UtcNow.ToString('o');exact_coordinator_identity_absent=$true;matching_owned_runtime_commands=@();processes_killed=@();graphics_lease_released=$true;suite_passed=$verification.passed;launch_sha256=(Get-FileHash -LiteralPath $launchPath -Algorithm SHA256).Hash.ToLowerInvariant();verification_sha256=(Get-FileHash -LiteralPath $verificationPath -Algorithm SHA256).Hash.ToLowerInvariant()}
$row|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $path
$row|ConvertTo-Json -Depth 6
