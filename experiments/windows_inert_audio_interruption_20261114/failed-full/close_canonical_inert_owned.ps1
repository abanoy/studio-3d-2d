$ErrorActionPreference='Stop'
$runRoot='C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\windows-canonical-inert-20261114T014831592'
$launch=Get-Content -LiteralPath (Join-Path $runRoot 'launch.json') -Raw|ConvertFrom-Json -DateKind String
$state=Get-Content -LiteralPath (Join-Path $runRoot 'state.json') -Raw|ConvertFrom-Json -DateKind String
$observed=Get-Content -LiteralPath (Join-Path $runRoot 'coordinator-children-observed.json') -Raw|ConvertFrom-Json -DateKind String
if($launch.source_commit -ne 'ee81e8648c0b038279da1e01de878e0fc3c79590' -or $state.source_commit -ne $launch.source_commit -or $state.pid -ne 2124 -or $state.process_started -ne '2026-11-14T01:48:31.6093080Z'){throw 'Canonical source/identity binding mismatch'}
if($state.status -eq 'running'){throw 'Full suite is not terminal; no observation written'}
function Observe-Identity([int]$OwnedPid,[string]$Creation){
 $p=Get-Process -Id $OwnedPid -ErrorAction SilentlyContinue
 $creationNow=$null
 if($p){$creationNow=$p.StartTime.ToUniversalTime().ToString('o')}
 $originalAbsent=($null -eq $p -or $creationNow -ne $Creation)
 if(-not $originalAbsent){throw 'Exact owned process is still present'}
 return @{pid=$OwnedPid;expected_creation_utc=$Creation;pid_present=($null -ne $p);current_creation_utc=$creationNow;original_absent=$originalAbsent}
}
if($observed.python.pid -ne 19828 -or $observed.python.creation_utc -ne '2026-11-14T01:48:32.1931020Z' -or $observed.python.parent_pid -ne 2124){throw 'Actual verification child binding mismatch'}
$coordinator=Observe-Identity 2124 '2026-11-14T01:48:31.6093080Z'
$python=Observe-Identity 19828 '2026-11-14T01:48:32.1931020Z'
$workers=@(Get-CimInstance Win32_Process | Where-Object {
    (($_.Name -match '^(blender|Godot.*|ffmpeg|ffprobe)\.exe$') -and $_.CommandLine -like '*has-acceptance-session-20261111*') -or
    (($_.Name -match '^pythonw?\.exe$') -and $_.CommandLine -like '*has-acceptance-session-20261111*' -and ($_.CommandLine -like '*verify_source_choices_native*' -or $_.CommandLine -like '*tests/verify.py*' -or $_.CommandLine -like '*tests\verify.py*'))
})
if($workers.Count){throw 'Matching owned runtime commands remain; no proof written'}
$checked=[DateTime]::UtcNow.ToString('o')
$raw=@{format='has_canonical_inert_authoritative_terminal_observation_1';canonical_run=$runRoot;source_commit=$launch.source_commit;checked_utc=$checked;state_status=$state.status;suite_exit=$state.suite_exit;coordinator=$coordinator;python=$python;owned_runtime_command_matches_absent=$true;owned_runtime_matches=@();no_process_killed=$true}
$rawPath=Join-Path $runRoot 'authoritative-host-terminal.json'
$flatPath=Join-Path $runRoot 'authoritative-host-termination.json'
if((Test-Path -LiteralPath $rawPath) -or (Test-Path -LiteralPath $flatPath)){throw 'Preserve previous host proof'}
$raw|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $rawPath
$flat=@{format='has_canonical_authoritative_host_termination_1';canonical_run=(Split-Path $runRoot -Leaf);source_commit=$launch.source_commit;observed_utc=$checked;coordinator_pid=2124;expected_creation_utc='2026-11-14T01:48:31.6093080Z';coordinator_absent=$true;python_pid=19828;expected_python_creation_utc='2026-11-14T01:48:32.1931020Z';python_absent=$true;coordinator_matches=@();owned_runtime_command_matches_absent=$true;owned_runtime_matches=@();no_process_killed=$true;raw_observation_sha256=(Get-FileHash -LiteralPath $rawPath -Algorithm SHA256).Hash.ToLowerInvariant()}
$flat|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $flatPath
$flat|ConvertTo-Json -Depth 6
