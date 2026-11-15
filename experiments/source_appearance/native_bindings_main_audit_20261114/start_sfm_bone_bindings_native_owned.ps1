$ErrorActionPreference='Stop'
$checkout='C:\a\Programming\cloudflare\has-acceptance-session-20261111'
Set-Location -LiteralPath $checkout
$revision=(& git rev-parse HEAD).Trim()
if($revision -ne '7477ed32dc5c43324783f76736164553bb4a79c5'){throw 'Source checkpoint changed before native admission'}
$manifest=Join-Path $checkout 'output\sfm-bone-bindings-native-inputs-20261114.json'
if((Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'f41595de1db83c90aca99fea3c74661bfa97b2eefc6cddf2520155bc49fe9c3f'){throw 'Native manifest changed'}
$workers=@(Get-CimInstance Win32_Process | Where-Object {
    (($_.Name -match '^(blender|Godot.*|ffmpeg|ffprobe)\.exe$') -and $_.CommandLine -like '*has-acceptance-session-20261111*') -or
    (($_.Name -match '^pythonw?\.exe$') -and $_.CommandLine -like '*has-acceptance-session-20261111*' -and ($_.CommandLine -like '*verify_source_choices_native*' -or $_.CommandLine -like '*tests/verify.py*' -or $_.CommandLine -like '*tests\verify.py*')) -or
    (($_.Name -match '^(pwsh|powershell)\.exe$') -and $_.CommandLine -like '*has-acceptance-session-20261111*run_canonical_owned.ps1*')
})
if($workers.Count){throw 'An owned native or graphics coordinator remains'}
$env:HYBRID_GODOT='C:\a\tools\Godot\Godot_v4.6-stable_win64.exe'
$env:HYBRID_PYTHON='C:\Program Files\Python313\python.exe'
$env:HYBRID_SOURCEIO=Join-Path $checkout 'output\dependencies\sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647'
$env:HYBRID_SOURCE_BLENDER='C:\Program Files\Blender Foundation\Blender 5.1\blender.exe'
$env:HYBRID_FFMPEG='C:\Program Files\ffmpeg\bin\ffmpeg.exe'
$env:PYTHONDONTWRITEBYTECODE='1'
if((Get-FileHash -LiteralPath $env:HYBRID_GODOT -Algorithm SHA256).Hash.ToLowerInvariant() -ne '63913d01be2c2d1f929b4a626f5347117126b34e9c64cbf350ea9f35a9657ebf'){throw 'Pinned engine changed'}
if((Get-FileHash -LiteralPath $env:HYBRID_PYTHON -Algorithm SHA256).Hash.ToLowerInvariant() -ne '03573716a7fcbd8b7fed8fe0163bbfbd3a852546920d6a666123f307c8dac7d9'){throw 'Approved Python changed'}
$launchRoot=Join-Path $checkout ('output\sfm-bone-bindings-native-launch-'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfff'))
New-Item -ItemType Directory -Path $launchRoot -ErrorAction Stop|Out-Null
$driver=Join-Path $checkout 'tests\verify_source_choices_native.py'
$argsList=@('-u','-B',$driver,'--inputs-manifest',$manifest,'--output',(Join-Path $launchRoot 'run'),'--shape-ui','--lease-confirmed')
$argLine=($argsList|ForEach-Object {'"'+$_+'"'}) -join ' '
$proc=Start-Process -FilePath $env:HYBRID_PYTHON -ArgumentList $argLine -WorkingDirectory $checkout -WindowStyle Hidden -RedirectStandardOutput (Join-Path $launchRoot 'stdout.log') -RedirectStandardError (Join-Path $launchRoot 'stderr.log') -PassThru
$row=@{format='has_root_sfm_bone_bindings_native_launch_1';pid=$proc.Id;creation_utc=$proc.StartTime.ToUniversalTime().ToString('o');launch=$launchRoot;source_commit=$revision;source_context='main_working_source_snapshot';arguments=$argsList;exclusive_private_graphics_lease=$true;authoritative_owned_graphics_absent_before_launch=$true;manifest_sha256='f41595de1db83c90aca99fea3c74661bfa97b2eefc6cddf2520155bc49fe9c3f';driver_sha256=(Get-FileHash -LiteralPath $driver -Algorithm SHA256).Hash.ToLowerInvariant();launcher_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()}
$row|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $launchRoot 'launch.json')
$row|ConvertTo-Json -Depth 6
