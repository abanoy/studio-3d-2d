$ErrorActionPreference='Stop'
$checkout='C:\a\Programming\cloudflare\has-acceptance-session-20261111'
Set-Location -LiteralPath $checkout
$revision=(& git rev-parse HEAD).Trim()
if($revision -ne 'ee81e8648c0b038279da1e01de878e0fc3c79590'){throw 'Reviewed source checkpoint changed'}
$runner=Join-Path $checkout 'experiments\verification_runner\run_canonical_owned.ps1'
if((Get-FileHash -LiteralPath $runner -Algorithm SHA256).Hash.ToLowerInvariant() -ne '6856faad316cc7188abb46a558aea3e0c08e2d409fedf173bf3b55a9a89c6bfa'){throw 'Canonical runner changed'}
$dirty=@(& git diff --name-only -- src tests tools data examples project.godot main.tscn run.py launch.pyw | Where-Object {$_ -notmatch '(^|/)__pycache__/|\.pyc$'})
$new=@(& git ls-files --others --exclude-standard -- src tests tools data examples | Where-Object {$_ -notmatch '(^|/)__pycache__/|\.pyc$'})
if($dirty.Count -or $new.Count){throw 'Uncommitted functional source remains'}
$workers=@(Get-CimInstance Win32_Process | Where-Object {
    (($_.Name -match '^(blender|Godot.*|ffmpeg|ffprobe)\.exe$') -and $_.CommandLine -like '*has-acceptance-session-20261111*') -or
    (($_.Name -match '^pythonw?\.exe$') -and $_.CommandLine -like '*has-acceptance-session-20261111*' -and ($_.CommandLine -like '*verify_source_choices_native*' -or $_.CommandLine -like '*tests/verify.py*' -or $_.CommandLine -like '*tests\verify.py*')) -or
    (($_.Name -match '^(pwsh|powershell)\.exe$') -and $_.CommandLine -like '*has-acceptance-session-20261111*run_canonical_owned.ps1*')
})
if($workers.Count){throw 'An owned graphics/verification coordinator remains'}
$env:HYBRID_GODOT='C:\a\tools\Godot\Godot_v4.6-stable_win64.exe'
$env:HYBRID_PYTHON='C:\Program Files\Python313\python.exe'
$env:HYBRID_SOURCEIO=Join-Path $checkout 'output\dependencies\sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647'
$env:HYBRID_SOURCE_BLENDER='C:\Program Files\Blender Foundation\Blender 5.1\blender.exe'
$env:HYBRID_FFMPEG='C:\Program Files\ffmpeg\bin\ffmpeg.exe'
$env:PYTHONDONTWRITEBYTECODE='1'
$runRoot=Join-Path $checkout ('output\windows-canonical-inert-'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfff'))
New-Item -ItemType Directory -Path $runRoot -ErrorAction Stop|Out-Null
$psExe='C:\Users\noble\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
$argsList=@('-NoLogo','-NoProfile','-ExecutionPolicy','Bypass','-File',$runner,'-RunFolder',$runRoot)
$argLine=($argsList|ForEach-Object {'"'+$_+'"'}) -join ' '
$proc=Start-Process -FilePath $psExe -ArgumentList $argLine -WorkingDirectory $checkout -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runRoot 'coordinator.stdout.log') -RedirectStandardError (Join-Path $runRoot 'coordinator.stderr.log') -PassThru
$row=@{format='has_root_canonical_inert_launch_1';pid=$proc.Id;creation_utc=$proc.StartTime.ToUniversalTime().ToString('o');source_commit=$revision;run_folder=$runRoot;arguments=$argsList;runner_sha256='6856faad316cc7188abb46a558aea3e0c08e2d409fedf173bf3b55a9a89c6bfa';exclusive_private_graphics_lease=$true;authoritative_owned_workers_absent_before_launch=$true;scoped_native_run='output/sfm-extra-native-launch-20261114T013526736';launcher_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()}
$row|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $runRoot 'launch.json')
$row|ConvertTo-Json -Depth 6
