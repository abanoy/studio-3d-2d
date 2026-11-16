. (Join-Path $PSScriptRoot '..\full_dbf0bc1\context.ps1')
$gate=Terminal-Source-Gate
if($gate.state.status -ne 'failed' -or $gate.state.suite_exit -ne 1 -or $gate.state.finished_utc -cne '2026-11-16T02:43:59.4000841Z'){throw 'This helper closes only the exact failed partial run'}
if((File-Sha (Join-Path $PSScriptRoot '..\full_dbf0bc1\context.ps1')) -ne 'cf0ce6feefdb6b482a0448452faffbada5284b271113fdc9b4abb2ac0a007891'){throw 'Reviewed neutral terminal context changed'}
$hostPath=Join-Path $RunRoot 'authoritative-host-termination.json'
$rawHostPath=Join-Path $RunRoot 'authoritative-host-terminal.json'
if((File-Sha $hostPath) -ne '4f007342d71ca0d2b21086c96635b05e98920f9fa30a3561cda2cc8d28d7dcaa' -or (File-Sha $rawHostPath) -ne 'ff12c0eeb37aa47eb6f031f41e2773cb3305aeb0b55cf2ffbb2d4783438abf61'){throw 'Actual failed-run host proof changed'}
$hostProof=Read-Json $hostPath
foreach($key in @('coordinator_absent','python_absent','owned_runtime_command_matches_absent','source_before_after_and_current_exact')){if($hostProof[$key] -ne $true){throw 'Actual owned host closure is incomplete'}}
$auditPath=Join-Path $PSScriptRoot 'PARTIAL_RECEIPT_AUDIT.json'
if((File-Sha $auditPath) -ne 'e06c6abfbb16ab4480cba2fc0b3e05b21b09ced1c55b1c4e04117661d3713f6d'){throw 'Reviewed failed-run receipt audit changed'}
$audit=Read-Json $auditPath
if($audit.passed_as_partial_receipt_audit -ne $true -or $audit.canonical_status -ne 'failed' -or $audit.canonical_suite_exit -ne 1 -or $audit.full_suite_passed -ne $false -or $audit.fresh_full157_report_used -ne $false -or $audit.source_commit -ne $ExpectedCommit -or $audit.run_directory -cne $RunRoot -or $audit.physical_receipts -ne 46 -or $audit.rows.Count -ne 46 -or $audit.unique_desktops -ne 46 -or $audit.exit_0 -ne 46 -or $audit.registered_cancel_exit_2 -ne 0){throw 'Exact failed partial evidence scope differs'}
foreach($context in $audit.source_metadata_context){if((File-Sha (Owned-Output-File $context.path)) -ne $context.sha256){throw 'Failed-run source metadata changed'}}
$start=[DateTimeOffset]::Parse($gate.state.started_utc)
$finish=[DateTimeOffset]::Parse($gate.state.finished_utc)
$observation=[DateTimeOffset]::Parse($hostProof.observed_utc)
if($audit.observation_window_end_utc -cne $hostProof.observed_utc -or $observation -le $finish){throw 'Late child observation window is not bound'}
$desktops=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
$late=0
foreach($row in $audit.rows){
    $path=Owned-Output-File $row.source_path
    if((File-Sha $path) -ne $row.source_sha256){throw 'Physical failed-run receipt changed'}
    $receipt=Read-Json $path
    if(($receipt|ConvertTo-Json -Depth 20 -Compress) -cne ($row.receipt|ConvertTo-Json -Depth 20 -Compress)){throw 'Receipt audit/physical fields differ'}
    if($receipt.exit -ne 0 -or $receipt.error -or $receipt.monitor_error -or $receipt.format -ne 'studio_private_desktop_1' -or -not $desktops.Add([string]$receipt.desktop)){throw 'Unexpected failed-run job exit/identity'}
    foreach($key in @('private_window_seen','child_desktop_confirmed','job_closed','desktop_closed')){if($receipt[$key] -ne $true){throw 'A private job or desktop remains unclosed'}}
    foreach($key in @('desktop_switch_requested','foreground_child_observed')){if($receipt[$key] -ne $false){throw 'A private job isolation flag differs'}}
    $stamp=(Get-Item -LiteralPath $path).LastWriteTimeUtc.Ticks
    if($stamp -lt $start.UtcTicks -or $stamp -gt $observation.UtcTicks){throw 'Receipt is outside the explicit failed/late-closure window'}
    if($stamp -gt $finish.UtcTicks){
        $late++
        if($receipt.child_pid -ne 71828 -or $row.after_failed_state_finish -ne $true){throw 'Unexpected late job requires separate root review'}
    }
    $copy=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot $row.stored))
    if(-not $copy.StartsWith(($PSScriptRoot+'\'),[StringComparison]::OrdinalIgnoreCase)){throw 'Retained receipt escaped this packet'}
    No-Reparse $copy
    if((File-Sha $copy) -ne $row.source_sha256){throw 'Retained failed-run receipt bytes differ'}
}
if($late -ne 1){throw 'Measured late teardown completion differs'}
$null=Observe-Owned-Absence
# Broader failure cleanup observation: include checkout-owned Python/private
# helpers and wrapper coordinators, not just the graphical engine command.
# Readable command scope is explicit; the owner's sibling review is untouched.
$helpers=@(Get-CimInstance Win32_Process|Where-Object {
    $_.ProcessId -ne $PID -and $_.CommandLine -and $_.CommandLine.IndexOf($Checkout,[StringComparison]::OrdinalIgnoreCase) -ge 0 -and (
        $_.Name -match '^pythonw?\.exe$' -or
        ($_.Name -match '^(pwsh|powershell)\.exe$' -and $_.CommandLine -match '(run_canonical_owned|start_canonical|private_desktop|run_chain_owned|run_state_owned|run_headless_preload|start_review_replay|run_review_builder)')
    )
})
if($helpers.Count){throw 'A checkout-owned private helper/wrapper command remains; no release'}
$record=@{format='has_root_canonical_failed_graphics_lease_release_1';released=$true;release_kind='closed_failed_partial_run';released_utc=[DateTime]::UtcNow.ToString('o');source_commit=$ExpectedCommit;canonical_run=(Split-Path $RunRoot -Leaf);canonical_status='failed';suite_exit=1;full_suite_passed=$false;completed_core_groups=36;full157_report_used=$false;coordinator_pid=$CoordinatorPid;python_pid=$PythonPid;functional_source_entries=1014;source_before_after_current_exact=$true;observed_partial_private_jobs=46;observed_partial_private_exit0=46;registered_Krita_cancel_exit2=0;late_closed_teardown_child_pid=71828;late_closed_receipt_after_failed_state_finish_seconds=7.8069579;all_collected_jobs_desktops_closed_private=$true;owned_runtime_commands_absent=$true;owned_private_helpers_wrappers_absent=$true;root_manual_or_process_sweep_termination_performed=$false;outer_timeout_wrapper_termination='Source/trace inference from Python subprocess.run; wrapper PID not captured. No global no-process-termination claim.';owner_sibling_review_untouched=$true;owner_manual_hair_selection='DEFERRED_NO_OBSERVED_RESULT';partial_receipt_audit_sha256=(File-Sha $auditPath);failed_state_sha256=(File-Sha (Join-Path $RunRoot 'state.json'));host_proof_sha256=(File-Sha $hostPath);limits='Failure lease closure only. The original full remains FAILED; no final report, remaining suite phases or complete default acceptance is inferred. Command observation is checkout-scoped, not universal global nonuse.'}
Write-Fresh-Json (Join-Path $RunRoot 'graphics-lease-closed-after-failure.json') $record
$record|ConvertTo-Json -Depth 12
