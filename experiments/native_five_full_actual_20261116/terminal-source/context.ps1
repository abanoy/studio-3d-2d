$ErrorActionPreference='Stop'
$Checkout='C:\a\Programming\cloudflare\has-acceptance-session-20261111'
$RunRoot=Join-Path $Checkout 'output\windows-canonical-bone-binding-20261116T041518335'
$ExpectedCommit='52f63c944ded7a651da871524d23a345b606424d'
$CoordinatorPid=79488
$CoordinatorBirth='2026-11-16T04:15:18.3655401Z'
$PythonPid=91024
$PythonBirth='2026-11-16T04:15:18.9615298Z'
$ExpectedLaunchSha='7623acd4cd9d4e7a2623412437363e3da4acb1c121ad87e71fff87e887de93dd'
$ExpectedSourceSha='4b1eb25e1da8e510106fe3dd01c4b5014c7cc719133f18e1bbccd386ec9deae7'
$ExpectedBirthSha='ce9b8c1197b02b3d575083635419b7309160ea70ab08896d819f5d112c2da6df'
$ExpectedRunnerSha='6856faad316cc7188abb46a558aea3e0c08e2d409fedf173bf3b55a9a89c6bfa'

function Read-Json([string]$Path){
    # Exact measured seven-digit UTC strings must not auto-convert to DateTime.
    return Get-Content -LiteralPath $Path -Raw|ConvertFrom-Json -AsHashtable -DateKind String
}
function File-Sha([string]$Path){return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
function No-Reparse([string]$Path){
    $item=Get-Item -LiteralPath $Path -Force
    while($null -ne $item){
        if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Reparse path refused'}
        $item=if($item -is [IO.FileInfo]){$item.Directory}else{$item.Parent}
    }
}
function Owned-Output-File([string]$Path){
    $resolved=(Resolve-Path -LiteralPath $Path).Path
    $boundary=$Checkout+'\output\'
    if(-not $resolved.StartsWith($boundary,[StringComparison]::OrdinalIgnoreCase)){throw 'Evidence must be under owned output'}
    No-Reparse $resolved
    return $resolved
}
function Terminal-Source-Gate([switch]$RequirePass){
    $state=Read-Json (Join-Path $RunRoot 'state.json')
    # Gate before any process query, final report read, or output write.
    if($state.status -notin @('passed','failed','runner_error') -or -not $state.finished_utc){throw 'Actual terminal state required; retain active lease'}
    if($state.format -ne 'has_owned_canonical_run_1' -or $state.source_commit -ne $ExpectedCommit -or $state.pid -ne $CoordinatorPid -or $state.process_started -cne $CoordinatorBirth -or $state.run_folder -cne $RunRoot -or $state.checkout -cne $Checkout -or $state.script_sha256 -ne $ExpectedRunnerSha){throw 'Terminal source/coordinator context differs'}
    if($RequirePass -and ($state.status -ne 'passed' -or $state.suite_exit -ne 0 -or $state.source_unchanged -ne $true)){throw 'Actual coherent full PASS required for release'}
    if((File-Sha (Join-Path $RunRoot 'launch.json')) -ne $ExpectedLaunchSha -or (File-Sha (Join-Path $RunRoot 'root-birth-observation.json')) -ne $ExpectedBirthSha){throw 'Actual launch/birth bytes differ'}
    $launch=Read-Json (Join-Path $RunRoot 'launch.json')
    $birth=Read-Json (Join-Path $RunRoot 'root-birth-observation.json')
    if($launch.source_commit -ne $ExpectedCommit -or $launch.pid -ne $CoordinatorPid -or $launch.creation_utc -cne $CoordinatorBirth -or $launch.run_folder -cne $RunRoot -or $launch.runner_sha256 -ne $ExpectedRunnerSha){throw 'Actual launch fields differ'}
    if($birth.format -ne 'has_root_full_child_birth_observation_1' -or $birth.source_commit -ne $ExpectedCommit -or $birth.coordinator_pid -ne $CoordinatorPid -or $birth.coordinator_birth -cne $CoordinatorBirth -or $birth.python_pid -ne $PythonPid -or $birth.python_birth -cne $PythonBirth -or $birth.python_parent -ne $CoordinatorPid -or $birth.python_command -cne '"C:\Program Files\Python313\python.exe" -u tests/verify.py' -or $birth.run_folder -cne $RunRoot){throw 'Actual child birth proof differs'}
    $beforePath=Join-Path $RunRoot 'source-before.json';$afterPath=Join-Path $RunRoot 'source-after.json'
    if((File-Sha $beforePath) -ne $ExpectedSourceSha -or (File-Sha $afterPath) -ne $ExpectedSourceSha){throw 'Exact before/after source bytes differ'}
    $before=Read-Json $beforePath;$after=Read-Json $afterPath
    if($before.commit -ne $ExpectedCommit -or $after.commit -ne $ExpectedCommit -or $before.source_sha256.Count -ne 1019 -or $after.source_sha256.Count -ne 1019 -or $state.source_unchanged -ne $true){throw 'Exact current1019 source gate differs'}
    $paths=@()
    foreach($part in @('src','tests','tools','data','examples')){
        $paths+=@(Get-ChildItem -LiteralPath (Join-Path $Checkout $part) -Recurse -File -Force|Where-Object {$_.Extension -cne '.pyc' -and $_.FullName -cnotmatch '\\__pycache__\\'})
    }
    foreach($name in @('project.godot','main.tscn','run.py','launch.pyw')){$paths+=Get-Item -LiteralPath (Join-Path $Checkout $name)}
    if($paths.Count -ne 1019){throw 'Current functional membership count differs'}
    foreach($file in $paths){
        No-Reparse $file.FullName
        $name=$file.FullName.Substring($Checkout.Length+1).Replace('\','/')
        if(-not $before.source_sha256.Contains($name) -or (File-Sha $file.FullName) -ne $before.source_sha256[$name]){throw 'Current functional source member/hash differs'}
    }
    $head=(& git -C $Checkout rev-parse HEAD).Trim()
    if($LASTEXITCODE -ne 0 -or $head -ne $ExpectedCommit){throw 'Actual HEAD changed before terminal admission'}
    return @{state=$state;source=$before}
}
# Observation only: neither helper calls Stop-Process, taskkill or a kill API.
function Observe-Owned-Absence{
    $identities=@()
    foreach($pin in @(@{pid=$CoordinatorPid;birth=$CoordinatorBirth},@{pid=$PythonPid;birth=$PythonBirth})){
        $process=Get-Process -Id $pin.pid -ErrorAction SilentlyContinue
        $now=$null
        if($process){$now=$process.StartTime.ToUniversalTime().ToString('o')}
        $absent=($null -eq $process -or [DateTimeOffset]::Parse($now) -ne [DateTimeOffset]::Parse($pin.birth))
        if(-not $absent){throw 'Exact owned process remains; no closure/release'}
        $identities+=@{pid=$pin.pid;expected_creation_utc=$pin.birth;pid_present=($null -ne $process);current_creation_utc=$now;original_absent=$absent}
    }
    # The owner has an interactive sibling review. Observe checkout-owned
    # commands only; never kill, switch, or require global engine absence.
    $workers=@(Get-CimInstance Win32_Process|Where-Object {
        (($_.Name -match '^(blender|Godot.*|ffmpeg|ffprobe)\.exe$') -and $_.CommandLine -like '*has-acceptance-session-20261111*') -or
        (($_.Name -match '^pythonw?\.exe$') -and $_.CommandLine -like '*has-acceptance-session-20261111*' -and ($_.CommandLine -like '*verify_source_choices_native*' -or $_.CommandLine -like '*tests/verify.py*' -or $_.CommandLine -like '*tests\verify.py*'))
    })
    if($workers.Count){throw 'A checkout-owned runtime command remains; no closure/release'}
    return $identities
}
function Write-Fresh-Json([string]$Path,$Value){
    if(Test-Path -LiteralPath $Path){throw 'Preserve existing proof'}
    [IO.File]::WriteAllText($Path,($Value|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))
}
