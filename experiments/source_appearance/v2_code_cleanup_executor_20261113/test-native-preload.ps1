[CmdletBinding()]
param([ValidateSet('Forged','LegitimateReuse')][string]$Case='Forged')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$executor=Join-Path $PSScriptRoot 'execute-sfm-v2-cleanup.ps1'
if ($Case -ceq 'Forged') {
    # Deliberately untrusted resident type. The executor must refuse before it
    # could use this implementation, including in read-only LibraryOnly mode.
    Add-Type -TypeDefinition 'public static class SfmCleanupNativeV2 { public static string CurrentDirectory(int pid,long ticks) { throw new System.Exception("FORGED_IMPLEMENTATION_USED"); } }'
} else {
    . $executor -LibraryOnly
}
$refused=$false; $reason=$null
try { . $executor -LibraryOnly } catch { $reason=$_.Exception.Message; $refused=$reason -like 'Preloaded SfmCleanupNativeV2 is refused.*' }
if (-not $refused) { throw ('Preloaded native implementation was not refused: '+$reason) }
$current=[Diagnostics.Process]::GetCurrentProcess()
@{format='has_sfm_v2_preloaded_native_negative_2';case=$Case;passed=$true;expected_refusal=$true;reason=$reason;process_id=$PID;process_created_utc=$current.StartTime.ToUniversalTime().ToString('o');process_creation_ticks=$current.StartTime.ToUniversalTime().Ticks;command_line=[Environment]::CommandLine;executor_sha256=(Get-FileHash -LiteralPath $executor -Algorithm SHA256).Hash.ToLowerInvariant();test_source_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant();execute_invoked=$false;deletes_moves_kills_or_git_mutation=$false}|ConvertTo-Json
