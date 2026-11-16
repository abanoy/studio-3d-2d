$ErrorActionPreference='Stop'
$checkout='C:\a\Programming\cloudflare\has-acceptance-session-20261111'
$review='C:\a\Programming\cloudflare\HAS-Review-20261115-SFM-Joints-f0dd57a'
$full=Join-Path $checkout 'output\windows-canonical-bone-binding-20261115T225514304'
Set-Location -LiteralPath $checkout
$built=Get-Content -LiteralPath (Join-Path $review 'BUILD-VERIFICATION.json') -Raw|ConvertFrom-Json -DateKind String
$released=Get-Content -LiteralPath (Join-Path $full 'graphics-lease-released.json') -Raw|ConvertFrom-Json -DateKind String
if($built.passed -ne $true -or $built.source_commit -ne 'f0dd57a2e568089d396fecba819ab987da658bf0' -or $released.released -ne $true){throw 'Passed build and closed full required'}
if((git rev-parse HEAD).Trim() -ne $built.source_commit){throw 'Source revision changed before replay'}
$commandPath=Join-Path $checkout 'experiments\resume_full_20261115\replay\command.json'
$spec=Get-Content -LiteralPath $commandPath -Raw|ConvertFrom-Json
$command=@($spec.command)
if($command[0] -ne 'C:\Program Files\Python313\python.exe' -or $command[1] -ne '-B' -or $command[2] -ne (Join-Path $checkout 'experiments\resume_full_20261115\replay\validate_after_full.py')){throw 'Unexpected reviewed command'}
if((Get-FileHash -LiteralPath $command[0] -Algorithm SHA256).Hash.ToLowerInvariant() -ne '03573716a7fcbd8b7fed8fe0163bbfbd3a852546920d6a666123f307c8dac7d9'){throw 'Approved Python changed'}
$result=Join-Path $checkout 'output\sfm-joints-final-validation-f0dd57a-20261115'
if(Test-Path -LiteralPath $result){throw 'Preserve previous replay/owner output'}
$workers=@(Get-CimInstance Win32_Process|Where-Object {
 (($_.Name -match '^(blender|Godot.*|ffmpeg|ffprobe)\.exe$') -and ($_.CommandLine -like '*has-acceptance-session-20261111*' -or $_.CommandLine -like '*HAS-Review-20261115-SFM-Joints-f0dd57a*')) -or
 (($_.Name -match '^pythonw?\.exe$') -and $_.CommandLine -like '*has-acceptance-session-20261111*' -and ($_.CommandLine -like '*validate_after_full.py*' -or $_.CommandLine -like '*tests/verify.py*' -or $_.CommandLine -like '*tests\verify.py*'))
})
if($workers.Count){throw 'An owned runtime/replay remains; no lease granted'}
$env:PYTHONDONTWRITEBYTECODE='1'
$launchRoot=Join-Path $checkout ('output\sfm-joints-final-replay-launch-'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfff'))
New-Item -ItemType Directory -Path $launchRoot -ErrorAction Stop|Out-Null
$arguments=@($command|Select-Object -Skip 1)
$argumentLine=($arguments|ForEach-Object {'"'+$_+'"'}) -join ' '
$process=Start-Process -FilePath $command[0] -ArgumentList $argumentLine -WorkingDirectory $checkout -WindowStyle Hidden -RedirectStandardOutput (Join-Path $launchRoot 'stdout.log') -RedirectStandardError (Join-Path $launchRoot 'stderr.log') -PassThru
$record=@{format='has_root_final_review_replay_launch_1';pid=$process.Id;creation_utc=$process.StartTime.ToUniversalTime().ToString('o');source_commit=$built.source_commit;review=$review;validation_output=$result;launch_folder=$launchRoot;command=$command;exclusive_private_graphics_lease=$true;actual_full_release_sha256=(Get-FileHash -LiteralPath (Join-Path $full 'graphics-lease-released.json') -Algorithm SHA256).Hash.ToLowerInvariant();command_file_sha256=(Get-FileHash -LiteralPath $commandPath -Algorithm SHA256).Hash.ToLowerInvariant();launcher_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant();owned_workers_absent_before_launch=$true}
$record|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $launchRoot 'launch.json')
$record|ConvertTo-Json -Depth 6
