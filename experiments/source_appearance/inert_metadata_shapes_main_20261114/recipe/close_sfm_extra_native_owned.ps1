param([Parameter(Mandatory=$true)][string]$LaunchRoot)
$ErrorActionPreference='Stop'
$checkout='C:\a\Programming\cloudflare\has-acceptance-session-20261111'
$base=[IO.Path]::GetFullPath((Join-Path $checkout 'output'))
$resolved=[IO.Path]::GetFullPath($LaunchRoot)
if(-not $resolved.StartsWith($base+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Closure folder outside session output'}
$launch=Get-Content -LiteralPath (Join-Path $resolved 'launch.json') -Raw|ConvertFrom-Json
if($launch.format -ne 'has_root_sfm_extra_native_launch_1' -or $launch.launch -ne $resolved){throw 'Launch binding mismatch'}
$p=Get-Process -Id $launch.pid -ErrorAction SilentlyContinue
$observed=$null
if($p){
 $observed=$p.StartTime.ToUniversalTime().ToString('o')
 if($observed -eq $launch.creation_utc){throw 'Exact owned coordinator is still running; no closure written'}
}
$workers=@(Get-CimInstance Win32_Process | Where-Object {
    (($_.Name -match '^(blender|Godot.*|ffmpeg|ffprobe)\.exe$') -and $_.CommandLine -like '*has-acceptance-session-20261111*') -or
    (($_.Name -match '^pythonw?\.exe$') -and $_.CommandLine -like '*has-acceptance-session-20261111*verify_source_choices_native*')
})
if($workers.Count){throw 'Owned runtime commands remain; no release written'}
$reportPath=Join-Path $resolved 'run\verification.json'
if(-not (Test-Path -LiteralPath $reportPath)){throw 'Terminal verification report missing'}
$report=Get-Content -LiteralPath $reportPath -Raw|ConvertFrom-Json
$row=@{format='has_root_sfm_extra_native_terminal_1';observed_utc=[DateTime]::UtcNow.ToString('o');pid=$launch.pid;creation_utc=$launch.creation_utc;exact_coordinator_identity_absent=$true;current_same_pid_creation_utc=$observed;matching_owned_runtime_commands=@();processes_killed=@();verification_sha256=(Get-FileHash -LiteralPath $reportPath -Algorithm SHA256).Hash.ToLowerInvariant();launch_sha256=(Get-FileHash -LiteralPath (Join-Path $resolved 'launch.json') -Algorithm SHA256).Hash.ToLowerInvariant();suite_passed=$report.passed;graphics_lease_released=$true}
$target=Join-Path $resolved 'authoritative-host-terminal.json'
if(Test-Path -LiteralPath $target){throw 'Preserve existing terminal proof'}
$row|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $target
$row|ConvertTo-Json -Depth 6
