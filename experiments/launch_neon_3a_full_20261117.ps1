$ErrorActionPreference='Stop'
$hasRoot='C:\a\Programming\cloudflare\has-acceptance-session-20261111'
$hasReview='C:\a\Programming\cloudflare\has-neon-review-20261116-c2d52ff'
$hasPrepared=Get-Content -LiteralPath (Join-Path $hasRoot 'experiments\neon_windows_3a3701a_20261117\PREPARATION.json') -Raw | ConvertFrom-Json
$hasRun=[System.IO.Path]::GetFullPath($hasPrepared.run_folder)
$hasRunner=$hasPrepared.runner
$hasPwsh=$hasPrepared.powershell
if ($hasPrepared.revision -ne '3a3701ab6edfa81dc883759403c170b8555aab07' -or $hasPrepared.result -ne 'UNRUN') {throw 'Exact unrun preparation required'}
if ($hasRun -ne 'C:\a\Programming\cloudflare\has-neon-review-20261116-c2d52ff\output\windows-neon-3a3701a-20261117T185401541257') {throw 'Reserved run differs'}
if ((Get-FileHash -LiteralPath $hasRunner -Algorithm SHA256).Hash.ToLowerInvariant() -ne '8a1c2195db1c06cf91910778a48182c825a4ad0ad3a7b3acde9f940ca68e3dc4') {throw 'Runner changed'}
if ((Get-FileHash -LiteralPath $hasPwsh -Algorithm SHA256).Hash.ToLowerInvariant() -ne '2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233') {throw 'PowerShell changed'}
if ((& git -C $hasReview rev-parse HEAD).Trim() -ne $hasPrepared.revision) {throw 'Candidate changed'}
if (Test-Path -LiteralPath (Join-Path $hasRun 'state.json')) {throw 'Fresh unstarted run required'}
$hasNativePattern='^(Godot.*|blender|ffmpeg|ffprobe)\.exe$'
foreach($hasName in @('Godot_v4.6-stable_win64.exe','blender.exe','ffmpeg.exe','ffprobe.exe')) {if($hasName -notmatch $hasNativePattern){throw 'Native matcher positive case failed'}}
foreach($hasName in @('notblender.exe','blenderXexe','ffmpeg.exe.bak')) {if($hasName -match $hasNativePattern){throw 'Native matcher negative case failed'}}
$hasOwned=@(Get-CimInstance Win32_Process | Where-Object {
 $_.ProcessId -ne $PID -and
 ($_.CommandLine -like '*has-neon-review-20261116-c2d52ff*' -or $_.CommandLine -like '*has-acceptance-session-20261111*') -and
 ($_.Name -match $hasNativePattern -or
  ($_.Name -match '^pythonw?\.exe$' -and $_.CommandLine -match 'tests[\\/]verify|windows_private_desktop|run_canonical_owned|run_owned\.py|run_observation\.py|root_runner\.py|run_neon_late_stage|run_neon_color') -or
  ($_.Name -match '^(pwsh|powershell)\.exe$' -and $_.CommandLine -match 'run_canonical_owned|private_desktop'))
})
$hasScope=@{format='has_root_neon_launch_scope_observation_1';observed_utc=[DateTime]::UtcNow.ToString('o');owned_count=$hasOwned.Count;owned_matches=@($hasOwned|Select-Object ProcessId,Name,CreationDate,CommandLine);termination_issued=$false}
[System.IO.File]::WriteAllText((Join-Path $hasRun 'prelaunch-owned-scope.json'),($hasScope|ConvertTo-Json -Depth 8),[System.Text.UTF8Encoding]::new($false))
if ($hasOwned.Count -ne 0) {throw 'An owned runtime is still active; no full launch'}
$hasArguments=@('-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$hasRunner,'-RunFolder',$hasRun)
$hasCoordinator=Start-Process -FilePath $hasPwsh -ArgumentList $hasArguments -WorkingDirectory $hasReview -WindowStyle Hidden -RedirectStandardOutput (Join-Path $hasRun 'coordinator.stdout.log') -RedirectStandardError (Join-Path $hasRun 'coordinator.stderr.log') -PassThru
$hasBirth=(Get-Process -Id $hasCoordinator.Id).StartTime.ToUniversalTime().ToString('o')
$hasLaunch=[ordered]@{format='has_root_neon_full_launch_1';observed_utc=[DateTime]::UtcNow.ToString('o');coordinator_pid=$hasCoordinator.Id;coordinator_creation_utc=$hasBirth;run_folder=$hasRun;source_commit=$hasPrepared.revision;functional_source_files=1029;runner=$hasRunner;runner_sha256=$hasPrepared.runner_sha256;arguments=$hasArguments;graphics_lease='root-exclusive';main_merged=$false;prior_root_scopes_empty=$true}
[System.IO.File]::WriteAllText((Join-Path $hasRun 'launch.json'),($hasLaunch|ConvertTo-Json -Depth 8),[System.Text.UTF8Encoding]::new($false))
$hasChild=$null
$hasDeadline=[DateTime]::UtcNow.AddSeconds(20)
do {
 $hasMatches=@(Get-CimInstance Win32_Process | Where-Object {$_.ParentProcessId -eq $hasCoordinator.Id -and $_.Name -eq 'python.exe' -and $_.CommandLine -match '-u tests[\\/]verify\.py$'})
 if ($hasMatches.Count -gt 1) {throw 'Multiple canonical children; retain coordinator for Root inspection'}
 if ($hasMatches.Count -eq 1) {$hasChild=$hasMatches[0];break}
 Start-Sleep -Milliseconds 100
} while ([DateTime]::UtcNow -lt $hasDeadline)
if ($null -eq $hasChild) {throw 'Canonical child not yet observed; retain coordinator and inspect, never launch a duplicate'}
$hasPythonBirth=(Get-Process -Id $hasChild.ProcessId).StartTime.ToUniversalTime().ToString('o')
$hasObservation=[ordered]@{format='has_root_neon_corrected_birth_observation_1';coordinator=@{pid=$hasCoordinator.Id;creation_utc=$hasBirth};python=@{pid=[int]$hasChild.ProcessId;parent_pid=$hasCoordinator.Id;creation_utc=$hasPythonBirth;command_line=$hasChild.CommandLine}}
$hasApi=[ordered]@{format='has_root_birth_api_detail_1';identity_api='Get-Process.StartTime';precision='100ns';python_pid=[int]$hasChild.ProcessId;python_get_process_birth=$hasPythonBirth;python_CIM_birth=$hasChild.CreationDate.ToUniversalTime().ToString('o');CIM_birth_not_used_for_identity=$true}
[System.IO.File]::WriteAllText((Join-Path $hasRun 'root-birth-observation.json'),($hasObservation|ConvertTo-Json -Depth 8),[System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText((Join-Path $hasRun 'root-birth-api-detail.json'),($hasApi|ConvertTo-Json -Depth 8),[System.Text.UTF8Encoding]::new($false))
$hasObservation|ConvertTo-Json -Depth 8 -Compress
