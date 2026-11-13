# Read-only supplemental native process audit; never invokes the cleanup script body.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'execute-sfm-v2-cleanup.ps1') -LibraryOnly
$sfReceipt=@{process_audit_count=0; process_checks=[Collections.Generic.List[object]]::new(); last_process_check=$null}
$result=Get-SfmProcessUsage
$result.executor_sha256=Get-SfmSha (Join-Path $PSScriptRoot 'execute-sfm-v2-cleanup.ps1')
$result.audit_source_sha256=Get-SfmSha $PSCommandPath
$path=Join-Path $PSScriptRoot ('nonuse-host-'+[Guid]::NewGuid().ToString('N')+'.json')
$stream=[IO.FileStream]::new($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
$writer=[IO.StreamWriter]::new($stream,[Text.UTF8Encoding]::new($false))
try { $writer.Write(($result|ConvertTo-Json -Depth 15)); $writer.WriteLine() } finally { $writer.Dispose() }
@{report=$path; processes=$result.processes_in_snapshot; matches=@($result.matching_processes).Count; unknown=@($result.unknown_live_owned_or_runtime_processes).Count; inaccessible=@($result.inaccessible_processes).Count; deletes_moves_kills_or_git_mutation=$false}|ConvertTo-Json
Assert-SfmNonuseResult $result
