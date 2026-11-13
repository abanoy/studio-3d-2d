param([Parameter(Mandatory=$true)][string]$RunFolder)
$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
$checkout='C:\a\Programming\cloudflare\has-acceptance-session-20261111'
$pythonPath='C:\Program Files\Python313\python.exe'
$resolvedRun=[System.IO.Path]::GetFullPath($RunFolder)
$outputBoundary=[System.IO.Path]::GetFullPath((Join-Path $checkout 'output'))+[System.IO.Path]::DirectorySeparatorChar
if (-not $resolvedRun.StartsWith($outputBoundary,[System.StringComparison]::OrdinalIgnoreCase)) { throw 'Run folder escaped owned output' }
if (-not (Test-Path -LiteralPath $resolvedRun -PathType Container)) { throw 'Run folder must be reserved first' }
Set-Location -LiteralPath $checkout
$env:HYBRID_HECATIA_KRA=(Resolve-Path -LiteralPath 'output/owner-fixtures/hecatia.kra').Path
$env:HYBRID_NATIVE_INPUTS='C:\a\dump'
$env:HYBRID_FFMPEG='C:\Program Files\ffmpeg\bin\ffmpeg.exe'
$env:PYTHONDONTWRITEBYTECODE='1'
Remove-Item Env:HYBRID_FAN_PROJECT -ErrorAction SilentlyContinue
$sourceProbe=@'
import hashlib,json,pathlib,subprocess,sys
r=pathlib.Path.cwd()
files=[p for d in ['src','tests','tools','data','examples'] for p in (r/d).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts]
files += [r/n for n in ['project.godot','main.tscn','run.py','launch.pyw']]
state={p.relative_to(r).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
pathlib.Path(sys.argv[1]).write_text(json.dumps({'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'source_sha256':state},indent=2)+'\n',encoding='utf-8')
'@
$state=[ordered]@{format='has_owned_canonical_run_1';pid=$PID;process_started=(Get-Process -Id $PID).StartTime.ToUniversalTime().ToString('o');started_utc=[DateTime]::UtcNow.ToString('o');status='running';checkout=$checkout;run_folder=$resolvedRun;source_commit=(& git rev-parse HEAD).Trim();python=$pythonPath;command=@($pythonPath,'-u','tests/verify.py');script_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()}
$statePath=Join-Path $resolvedRun 'state.json'
function Save-State { [System.IO.File]::WriteAllText($statePath,($state | ConvertTo-Json -Depth 8),[System.Text.UTF8Encoding]::new($false)) }
Save-State
$suiteExit=-1
try {
    & $pythonPath -c $sourceProbe (Join-Path $resolvedRun 'source-before.json')
    if ($LASTEXITCODE -ne 0) { throw 'Cannot capture initial source hashes' }
    & $pythonPath -u tests/verify.py *> (Join-Path $resolvedRun 'canonical.log')
    $suiteExit=$LASTEXITCODE
    & $pythonPath -c $sourceProbe (Join-Path $resolvedRun 'source-after.json')
    if ($LASTEXITCODE -ne 0) { throw 'Cannot capture final source hashes' }
    $state['suite_exit']=$suiteExit
    $comparison=@'
import json,pathlib,sys
folder=pathlib.Path(sys.argv[1]);before=json.loads((folder/'source-before.json').read_bytes());after=json.loads((folder/'source-after.json').read_bytes())
assert before==after,'Functional source or revision changed during canonical verification'
'@
    & $pythonPath -c $comparison $resolvedRun
    $state['source_unchanged']=($LASTEXITCODE -eq 0)
    if (-not $state['source_unchanged']) { throw 'Source identity changed during the run' }
    $state['status']=if ($suiteExit -eq 0) {'passed'} else {'failed'}
} catch {
    $state['status']='runner_error'
    $state['runner_error']=$_.ToString()
    $state['suite_exit']=$suiteExit
    [System.IO.File]::WriteAllText((Join-Path $resolvedRun 'runner-error.txt'),($_ | Out-String))
} finally {
    $state['finished_utc']=[DateTime]::UtcNow.ToString('o')
    Save-State
}
exit $(if ($state.status -eq 'passed') {0} elseif ($suiteExit -gt 0) {$suiteExit} else {1})
