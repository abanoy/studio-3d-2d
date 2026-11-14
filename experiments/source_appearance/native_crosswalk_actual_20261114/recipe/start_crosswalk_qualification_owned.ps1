$ErrorActionPreference='Stop'
$checkout='C:\a\Programming\cloudflare\has-acceptance-session-20261111'
$task='C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\crosswalk-qualification-20261114T0240'
Set-Location -LiteralPath $checkout
$revision=(& git rev-parse HEAD).Trim()
if($revision -ne '80a1e557512902b29b5fb95b3152bb4284fdf55e'){throw 'Reviewed diagnostic checkpoint changed'}
$lock=Join-Path $task 'fresh-input-lock.json'
$lockSha='afbd05bf636d3eb58df13e815547f2dbfef5c51ec4d74993c05f8082bcbb40d1'
if((Get-FileHash -LiteralPath $lock -Algorithm SHA256).Hash.ToLowerInvariant() -ne $lockSha){throw 'Reviewed diagnostic lock changed'}
$workers=@(Get-CimInstance Win32_Process | Where-Object {
    (($_.Name -match '^(blender|Godot.*|ffmpeg|ffprobe)\.exe$') -and $_.CommandLine -like '*has-acceptance-session-20261111*') -or
    (($_.Name -match '^pythonw?\.exe$') -and $_.CommandLine -like '*has-acceptance-session-20261111*' -and ($_.CommandLine -like '*tests/verify.py*' -or $_.CommandLine -like '*verify_source_choices_native*' -or $_.CommandLine -like '*run_prepared.py*'))
})
if($workers.Count){throw 'Owned verification/conversion process remains; no launch'}
$python='C:\Program Files\Python313\python.exe'
if((Get-FileHash -LiteralPath $python -Algorithm SHA256).Hash.ToLowerInvariant() -ne '03573716a7fcbd8b7fed8fe0163bbfbd3a852546920d6a666123f307c8dac7d9'){throw 'Approved Python changed'}
$argsList=@('-B','-u',(Join-Path $task 'driver\run_prepared.py'),'--lock',$lock,'--lock-sha256',$lockSha,'--run-conversion','--lease-confirmed')
$argLine=($argsList|ForEach-Object {'"'+$_+'"'}) -join ' '
$stdout=Join-Path $task 'coordinator.stdout.log'
$stderr=Join-Path $task 'coordinator.stderr.log'
$launchPath=Join-Path $task 'coordinator-launch.json'
if((Test-Path -LiteralPath $stdout) -or (Test-Path -LiteralPath $stderr) -or (Test-Path -LiteralPath $launchPath) -or (Test-Path -LiteralPath (Join-Path $task 'case-junko-default'))){throw 'Never reuse an attempted diagnostic task'}
$env:PYTHONDONTWRITEBYTECODE='1'
$proc=Start-Process -FilePath $python -ArgumentList $argLine -WorkingDirectory $checkout -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
$row=@{format='has_root_crosswalk_qualification_launch_1';pid=$proc.Id;creation_utc=$proc.StartTime.ToUniversalTime().ToString('o');source_commit=$revision;task=$task;input_lock_sha256=$lockSha;arguments=$argsList;scope='Exactly one Junko diagnostic overlay; no main/app/solver port';exclusive_native_lease=$true;authoritative_owned_runtime_commands_absent_before_launch=$true;launcher_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()}
$row|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $launchPath
$row|ConvertTo-Json -Depth 6
