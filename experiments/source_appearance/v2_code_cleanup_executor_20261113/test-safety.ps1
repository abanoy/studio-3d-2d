[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$testHome=Join-Path $PSScriptRoot ('synthetic-'+[Guid]::NewGuid().ToString('N'))
. (Join-Path $PSScriptRoot 'execute-sfm-v2-cleanup.ps1') -LibraryOnly
[void](New-Item -ItemType Directory -Path $testHome -ErrorAction Stop)
# Isolated authored data only. Production constants remain unchanged on disk.
$sfScope=$testHome
$sfRoots=@($testHome)
$results=[Collections.Generic.List[object]]::new()
function Expect-Refusal([string]$Name,[scriptblock]$Action) {
    $refused=$false; $reason=$null
    try { & $Action } catch { $refused=$true; $reason=$_.Exception.Message }
    Assert-Sfm $refused ('Synthetic negative control unexpectedly passed: '+$Name)
    $results.Add(@{name=$Name; passed=$true; expected_refusal=$true; reason=$reason})
}
function Expect-Pass([string]$Name,[scriptblock]$Action) {
    & $Action
    $results.Add(@{name=$Name; passed=$true; expected_refusal=$false})
}
$fixture=Join-Path $testHome 'authored.txt'
[IO.File]::WriteAllBytes($fixture,[Text.Encoding]::UTF8.GetBytes('authored fixture'))
$item=Get-Item -LiteralPath $fixture
$entry=@{path=$fixture; project=$testHome; relative_path='authored.txt'; bytes=$item.Length; mtime_ns=[long](($item.LastWriteTimeUtc.Ticks-621355968000000000L)*100L); sha256=Get-SfmSha $fixture}
Expect-Pass 'safe-relative' { Assert-SfmRelative 'src/example.gd' }
Expect-Pass 'synthetic-valid-file-identity' { Assert-SfmFile $entry -Source }
$longDirectory=Join-Path (Join-Path (Join-Path $testHome ('a'*80)) ('b'*80)) ('c'*80)
[void](New-Item -ItemType Directory -Path $longDirectory -Force -ErrorAction Stop)
$longFile=Join-Path $longDirectory 'authored.txt'
[IO.File]::WriteAllBytes($longFile,[Text.Encoding]::UTF8.GetBytes('long authored fixture'))
$longItem=Get-Item -LiteralPath $longFile
$longEntry=@{path=$longFile; project=$testHome; relative_path=[IO.Path]::GetRelativePath($testHome,$longFile).Replace('\','/'); bytes=$longItem.Length; mtime_ns=[long](($longItem.LastWriteTimeUtc.Ticks-621355968000000000L)*100L); sha256=Get-SfmSha $longFile}
Expect-Pass 'long-literal-file-native-identity' { Assert-Sfm ($longFile.Length -gt 260) 'Long-path control is too short.'; Assert-SfmFile $longEntry -Source }
foreach ($relative in @('../escape.py','src/../escape.py','/absolute.py','C:/absolute.py','src\escape.py','src/alias.','src/alias ','src/NUL.py','src/file.py:stream','src/*.py')) {
    Expect-Refusal ('unsafe-relative-'+$relative) { Assert-SfmRelative $relative }
}
$bad=$entry.Clone(); $bad.path=Join-Path ([IO.Path]::GetDirectoryName($testHome)) 'outside.txt'
Expect-Refusal 'absolute-relative-membership-escape' { Assert-SfmFile $bad -Source }
$bad=$entry.Clone(); $bad.relative_path='output/example.gd'; $bad.path=Join-Path $testHome 'output\example.gd'
Expect-Refusal 'retained-output-never-candidate' { Assert-SfmFile $bad -Source -Candidate }
$bad=$entry.Clone(); $bad.bytes++
Expect-Refusal 'changed-size' { Assert-SfmFile $bad -Source }
$bad=$entry.Clone(); $bad.mtime_ns+=100L
Expect-Refusal 'changed-nanosecond-stamp' { Assert-SfmFile $bad -Source }
[IO.File]::WriteAllBytes($fixture,[Text.Encoding]::UTF8.GetBytes('mutated! fixture'))
$bad=$entry.Clone(); $new=Get-Item -LiteralPath $fixture
$bad.bytes=$new.Length; $bad.mtime_ns=[long](($new.LastWriteTimeUtc.Ticks-621355968000000000L)*100L)
Expect-Refusal 'actual-mutated-file-sha' { Assert-SfmFile $bad -Source }
$setA=New-SfmPathSet @($fixture)
$setB=New-SfmPathSet @($fixture,(Join-Path $testHome 'unlisted.txt'))
Expect-Pass 'equal-membership' { Assert-SfmMembership $setA $setA 'synthetic equal' }
Expect-Refusal 'unlisted-file-membership' { Assert-SfmMembership $setB $setA 'synthetic extra' }
Expect-Refusal 'missing-file-membership' { Assert-SfmMembership $setA $setB 'synthetic missing' }
Expect-Refusal 'case-alias-membership' { New-SfmPathSet @($fixture,$fixture.ToUpperInvariant()) }
Expect-Pass 'clear-nonuse-result' { Assert-SfmNonuseResult @{matching_processes=@();unknown_live_owned_or_runtime_processes=@()} }
Expect-Refusal 'observed-process-use' { Assert-SfmNonuseResult @{matching_processes=@(@{process_id=123;created_utc='synthetic'});unknown_live_owned_or_runtime_processes=@()} }
Expect-Refusal 'inaccessible-owned-runtime' { Assert-SfmNonuseResult @{matching_processes=@();unknown_live_owned_or_runtime_processes=@(@{process_id=123;created_utc='synthetic'})} }
Expect-Refusal 'wrong-published-executor-sha' { Assert-SfmDigest ('1'*64) ('2'*64) }
$nativeTicks=[Diagnostics.Process]::GetCurrentProcess().StartTime.ToUniversalTime().Ticks
Expect-Pass 'exact-native-owner-and-full-creation' {
    $owner=[SfmCleanupNativeV2]::OwnerIdentity($PID,$nativeTicks-($nativeTicks % 10L))
    Assert-Sfm ($owner.CreationTicks -eq $nativeTicks -and $owner.Sid -ceq [Security.Principal.WindowsIdentity]::GetCurrent().User.Value) 'Retained native owner/creation differs.'
}
Expect-Refusal 'native-owner-snapshot-creation-mismatch' { [SfmCleanupNativeV2]::OwnerIdentity($PID,($nativeTicks-($nativeTicks % 10L))-10L) }
Expect-Pass 'exact-own-process-native-cwd' { Assert-Sfm (Test-SfmSamePath ([SfmCleanupNativeV2]::CurrentDirectory($PID,$nativeTicks)) ([Environment]::CurrentDirectory)) 'Own-process CWD differs.' }
Expect-Refusal 'native-pid-creation-mismatch' { [SfmCleanupNativeV2]::CurrentDirectory($PID,$nativeTicks-1L) }
Expect-Pass 'different-session-unresolved-owner-classified-unknown' {
    $script:syntheticProcessRow=[pscustomobject]@{
        ProcessId=$PID; Name='synthetic-non-runtime.exe';
        CreationDate=[DateTime]::new(($nativeTicks-($nativeTicks % 10L))-10L,[DateTimeKind]::Utc);
        SessionId=([Diagnostics.Process]::GetCurrentProcess().SessionId+100);
        CommandLine=$null; ExecutablePath=$null
    }
    function Get-CimInstance { param([string]$ClassName) return $script:syntheticProcessRow }
    $sfReceipt=@{process_audit_count=0; process_checks=[Collections.Generic.List[object]]::new(); last_process_check=$null}
    $actual=Get-SfmProcessUsage
    Assert-Sfm (@($actual.unknown_live_owned_or_runtime_processes).Count -eq 1) 'Different-session unresolved owner escaped unknown coverage.'
    Expect-Refusal 'different-session-unresolved-owner-is-blocker' { Assert-SfmNonuseResult $actual }
}
foreach ($preloadCase in @('Forged','LegitimateReuse')) {
    Expect-Pass ('preloaded-native-refused-'+$preloadCase) {
        $childOutput=& 'C:\Users\noble\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe' -NoProfile -NonInteractive -File (Join-Path $PSScriptRoot 'test-native-preload.ps1') -Case $preloadCase
        Assert-Sfm ($LASTEXITCODE -eq 0) 'Fresh-process native guard control failed.'
        $child=($childOutput -join "`n")|ConvertFrom-Json -AsHashtable
        Assert-Sfm ($child.passed -eq $true -and $child.expected_refusal -eq $true -and $child.execute_invoked -eq $false) 'Native guard control did not attest expected refusal.'
    }
}
$scriptText=[IO.File]::ReadAllText((Join-Path $PSScriptRoot 'execute-sfm-v2-cleanup.ps1'))
Expect-Pass 'single-literal-remove-operation-static' {
    Assert-Sfm ([regex]::Matches($scriptText,'(?m)^\s*Remove-Item -LiteralPath ').Count -eq 1) 'Expected exactly one removal operation.'
    Assert-Sfm ($scriptText -notmatch '(?im)^\s*(Move-Item|Stop-Process|Remove-Item .*-(Recurse|Force|Path)\b)') 'Unbounded mutation command found.'
}
$report=@{format='has_sfm_v2_cleanup_synthetic_controls_1'; passed=$true; tests=$results.Count; results=$results.ToArray(); fixture_root=$testHome; executor_sha256=Get-SfmSha (Join-Path $PSScriptRoot 'execute-sfm-v2-cleanup.ps1'); test_source_sha256=Get-SfmSha $PSCommandPath; deletes_moves_kills_or_git_mutation=$false; fixture_retained=$true; production_execute_invoked=$false; exact_production_nonuse_and_remote_publication='UNRUN_BY_SYNTHETIC_TESTS'}
$reportPath=Join-Path $testHome 'TESTS.json'
$report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $reportPath -Encoding utf8NoBOM
$report | ConvertTo-Json -Depth 10
