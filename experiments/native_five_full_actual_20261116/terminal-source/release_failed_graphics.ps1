param(
    [Parameter(Mandatory=$true)][string]$PartialReceiptInventory,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$PartialReceiptInventorySha256
)
. (Join-Path $PSScriptRoot 'context.ps1')
$gate=Terminal-Source-Gate
$state=$gate.state
if($state.status -notin @('failed','runner_error') -or ($state.suite_exit -isnot [long] -and $state.suite_exit -isnot [int]) -or $state.suite_exit -eq 0){throw 'Actual nonzero failed terminal state required; never use this as a PASS release'}
$hostPath=Join-Path $RunRoot 'authoritative-host-termination.json'
$rawHostPath=Join-Path $RunRoot 'authoritative-host-terminal.json'
$hostProof=Read-Json $hostPath;$rawHost=Read-Json $rawHostPath
if($hostProof.raw_observation_sha256 -ne (File-Sha $rawHostPath) -or $hostProof.canonical_run -cne (Split-Path $RunRoot -Leaf) -or $hostProof.source_commit -ne $ExpectedCommit -or $rawHost.canonical_run -cne $RunRoot -or $rawHost.source_commit -ne $ExpectedCommit){throw 'Actual failed host proof context differs'}
if($hostProof.coordinator_pid -ne $CoordinatorPid -or $hostProof.python_pid -ne $PythonPid -or $hostProof.expected_creation_utc -cne $CoordinatorBirth -or $hostProof.expected_python_creation_utc -cne $PythonBirth){throw 'Actual failed host identities differ'}
if($rawHost.coordinator.pid -ne $CoordinatorPid -or $rawHost.coordinator.expected_creation_utc -cne $CoordinatorBirth -or $rawHost.coordinator.original_absent -ne $true -or $rawHost.python.pid -ne $PythonPid -or $rawHost.python.expected_creation_utc -cne $PythonBirth -or $rawHost.python.original_absent -ne $true -or $rawHost.state_status -cne $state.status -or $rawHost.suite_exit -ne $state.suite_exit -or $rawHost.checked_utc -cne $hostProof.observed_utc -or $rawHost.root_observer_issued_no_termination -ne $true -or $rawHost.owned_runtime_command_matches_absent -ne $true -or $rawHost.owned_runtime_matches.Count -ne 0 -or $rawHost.functional_source_entries -ne 1019 -or $rawHost.source_before_after_and_current_exact -ne $true -or $rawHost.root_birth_observation_sha256 -ne $ExpectedBirthSha){throw 'Actual raw failed closure differs'}
foreach($key in @('coordinator_absent','python_absent','owned_runtime_command_matches_absent','source_before_after_and_current_exact','root_observer_issued_no_termination')){if($hostProof[$key] -isnot [bool] -or $hostProof[$key] -ne $true){throw 'Actual failed host closure is incomplete'}}
if($hostProof.coordinator_matches.Count -or $hostProof.owned_runtime_matches.Count -or $hostProof.functional_source_entries -ne 1019){throw 'Actual failed host scope differs'}
$inventoryPath=Owned-Output-File $PartialReceiptInventory
if((File-Sha $inventoryPath) -ne $PartialReceiptInventorySha256){throw 'Exact separately reviewed current partial receipt inventory required'}
$audit=Read-Json $inventoryPath
if($audit.format -ne 'has_current_failed_full_private_receipt_audit_1' -or $audit.root_reviewed_current_run -ne $true -or $audit.full_suite_passed -ne $false -or $audit.final_full_report_used -ne $false -or $audit.source_commit -ne $ExpectedCommit -or $audit.run_directory -cne $RunRoot){throw 'This is not a reviewed current failed-run inventory'}
if($audit.state_sha256 -ne (File-Sha (Join-Path $RunRoot 'state.json')) -or $audit.host_proof_sha256 -ne (File-Sha $hostPath) -or $audit.source_before_sha256 -ne $ExpectedSourceSha -or $audit.source_after_sha256 -ne $ExpectedSourceSha){throw 'Partial receipt audit state/source/host bindings differ'}
if($audit.observation_window_end_utc -cne $hostProof.observed_utc){throw 'Partial receipt observation window differs'}
$start=[DateTimeOffset]::Parse($state.started_utc);$finish=[DateTimeOffset]::Parse($state.finished_utc);$window=[DateTimeOffset]::Parse($hostProof.observed_utc)
if($window -lt $finish){throw 'Failed observation precedes actual terminal time'}
$rows=@($audit.rows);$latePins=@($audit.late_receipts)
if($audit.physical_receipts -ne $rows.Count -or $audit.unique_desktops -ne $rows.Count){throw 'Partial receipt/desktop counts differ'}
$lateByPath=@{}
foreach($pin in $latePins){
    $path=Owned-Output-File $pin.path
    if($lateByPath.ContainsKey($path) -or (File-Sha $path) -ne $pin.sha256 -or ($pin.child_pid -isnot [long] -and $pin.child_pid -isnot [int])){throw 'Late receipt needs unique exact separately reviewed path/hash/child identity'}
    $lateByPath[$path]=$pin
}
$cancelByPath=@{}
foreach($pin in @($audit.registered_cancellations)){
    $path=Owned-Output-File $pin.path
    if($cancelByPath.ContainsKey($path) -or (File-Sha $path) -ne $pin.sha256 -or $pin.registration -cne 'krita_import_cancel'){throw 'Unknown or duplicate controlled cancellation'}
    # Only the current pinned source's deliberate Krita cancellation is registered.
    $sourcePath=Join-Path $Checkout 'tests\verify_krita_import.py'
    if((File-Sha $sourcePath) -ne $gate.source.source_sha256['tests/verify_krita_import.py'] -or -not [IO.File]::ReadAllText($sourcePath).Contains("assert r['exit']==2 and r['cancelled'] and r['child_desktop_confirmed']")){throw 'Current cancellation source assertion differs'}
    $phasePath=Owned-Output-File (Join-Path $Checkout 'output\krita-import-verification.json')
    if($pin.phase_report_sha256 -ne (File-Sha $phasePath)){throw 'Controlled cancellation must bind the fresh actual Krita phase report'}
    $phase=Read-Json $phasePath;$stamp=(Get-Item -LiteralPath $phasePath).LastWriteTimeUtc.Ticks
    if($stamp -lt $start.UtcTicks -or $stamp -gt $window.UtcTicks -or (Owned-Output-File $phase.cancelled_receipt) -cne $path){throw 'Controlled cancellation registration is stale or refers to another job'}
    $cancelByPath[$path]=$pin
}
$desktops=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
$paths=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$normal=0;$cancelled=0;$late=0
foreach($row in $rows){
    $path=Owned-Output-File $row.source_path
    if(-not $paths.Add($path) -or (File-Sha $path) -ne $row.source_sha256){throw 'Duplicate or changed physical partial receipt'}
    $receipt=Read-Json $path
    if(($receipt|ConvertTo-Json -Depth 20 -Compress) -cne ($row.receipt|ConvertTo-Json -Depth 20 -Compress)){throw 'Partial audit/physical receipt fields differ'}
    if($receipt.format -ne 'studio_private_desktop_1' -or -not $receipt.desktop -or -not $desktops.Add([string]$receipt.desktop)){throw 'Partial receipt identity/desktop differs'}
    foreach($key in @('private_window_seen','child_desktop_confirmed','job_closed','desktop_closed')){if($receipt[$key] -isnot [bool] -or $receipt[$key] -ne $true){throw 'A collected private job/desktop remains unclosed'}}
    foreach($key in @('desktop_switch_requested','foreground_child_observed')){if($receipt[$key] -isnot [bool] -or $receipt[$key] -ne $false){throw 'Collected private isolation differs'}}
    if($receipt.monitor_error){throw 'Private monitor error is not a controlled cancellation'}
    if($receipt.exit -eq 0 -and -not $receipt.error){$normal++}
    elseif($receipt.exit -eq 2 -and $cancelByPath.ContainsKey($path) -and $receipt.cancelled -eq $true -and $receipt.error -ceq 'Owned converter cancelled'){$cancelled++}
    else{throw 'Unexpected partial job exit/error requires a separate reviewed successor'}
    $stamp=(Get-Item -LiteralPath $path).LastWriteTimeUtc.Ticks
    if($stamp -lt $start.UtcTicks -or $stamp -gt $window.UtcTicks){throw 'Partial receipt is outside the actual current run/closure window'}
    if($stamp -gt $finish.UtcTicks){
        $late++
        if(-not $lateByPath.ContainsKey($path) -or $lateByPath[$path].child_pid -ne $receipt.child_pid -or $row.after_failed_state_finish -ne $true){throw 'Every late child needs exact separately reviewed identity'}
    }elseif($lateByPath.ContainsKey($path) -or $row.after_failed_state_finish -ne $false){throw 'A declared late receipt is not actually late'}
    $copy=Owned-Output-File $row.preserved_raw_copy
    if((File-Sha $copy) -ne $row.source_sha256){throw 'Retained partial receipt copy differs'}
}
if($normal -ne $audit.normal_exit0 -or $cancelled -ne $audit.registered_cancel_exit2 -or $cancelled -ne $cancelByPath.Count -or $late -ne $lateByPath.Count -or $normal+$cancelled -ne $rows.Count){throw 'Actual partial normal/cancel/late counts differ'}
$null=Observe-Owned-Absence
$helpers=@(Get-CimInstance Win32_Process|Where-Object {
    $_.ProcessId -ne $PID -and $_.CommandLine -and $_.CommandLine.IndexOf($Checkout,[StringComparison]::OrdinalIgnoreCase) -ge 0 -and (
        $_.Name -match '^pythonw?\.exe$' -or
        ($_.Name -match '^(pwsh|powershell)\.exe$' -and $_.CommandLine -match '(run_canonical_owned|start_canonical|private_desktop|run_chain_owned|run_state_owned|run_headless_preload|start_review_replay|run_review_builder)')
    )
})
if($helpers.Count){throw 'A checkout-owned private helper/wrapper remains; retain lease'}
$release=@{format='has_root_current_failed_graphics_lease_release_1';released=$true;release_kind='closed_failed_partial_run';released_utc=[DateTime]::UtcNow.ToString('o');source_commit=$ExpectedCommit;canonical_run=(Split-Path $RunRoot -Leaf);canonical_status=$state.status;suite_exit=$state.suite_exit;full_suite_passed=$false;final_full_report_used=$false;coordinator_pid=$CoordinatorPid;python_pid=$PythonPid;functional_source_entries=1019;source_before_after_current_exact=$true;observed_partial_private_jobs=$rows.Count;normal_exit0=$normal;registered_Krita_cancel_exit2=$cancelled;explicit_late_receipts=$late;all_collected_jobs_desktops_closed_private=$true;owned_runtime_commands_absent=$true;owned_private_helpers_wrappers_absent=$true;root_observer_issued_no_termination=$true;termination_claim_scope='This root observer never terminates processes; test-child cancellation/timeout actions are separately scoped, not globally excluded.';owner_sibling_review_untouched=$true;partial_receipt_audit_sha256=$PartialReceiptInventorySha256;failed_state_sha256=(File-Sha (Join-Path $RunRoot 'state.json'));host_proof_sha256=(File-Sha $hostPath);limits='Only the explicitly reviewed current failed partial run is closed. No full PASS or unobserved phases are inferred; command absence is checkout-scoped.'}
Write-Fresh-Json (Join-Path $RunRoot 'graphics-lease-closed-after-failure.json') $release
$release|ConvertTo-Json -Depth 12
