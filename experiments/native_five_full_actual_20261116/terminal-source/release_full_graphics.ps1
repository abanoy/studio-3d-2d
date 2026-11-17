param(
    [Parameter(Mandatory=$true)][string]$ReceiptInventory,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$ReceiptInventorySha256,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$FullReportSha256
)
. (Join-Path $PSScriptRoot 'context.ps1')
$gate=Terminal-Source-Gate -RequirePass
$state=$gate.state
$hostPath=Join-Path $RunRoot 'authoritative-host-termination.json';$rawHostPath=Join-Path $RunRoot 'authoritative-host-terminal.json'
$hostProof=Read-Json $hostPath;$rawHost=Read-Json $rawHostPath
if($hostProof.raw_observation_sha256 -ne (File-Sha $rawHostPath) -or $hostProof.canonical_run -cne (Split-Path $RunRoot -Leaf) -or $hostProof.source_commit -ne $ExpectedCommit -or $rawHost.canonical_run -cne $RunRoot -or $rawHost.source_commit -ne $ExpectedCommit){throw 'Fresh host proof context differs'}
if($hostProof.coordinator_pid -ne $CoordinatorPid -or $hostProof.python_pid -ne $PythonPid -or $hostProof.expected_creation_utc -cne $CoordinatorBirth -or $hostProof.expected_python_creation_utc -cne $PythonBirth){throw 'Fresh host process identities differ'}
if($rawHost.coordinator.pid -ne $CoordinatorPid -or $rawHost.coordinator.expected_creation_utc -cne $CoordinatorBirth -or $rawHost.coordinator.original_absent -ne $true -or $rawHost.python.pid -ne $PythonPid -or $rawHost.python.expected_creation_utc -cne $PythonBirth -or $rawHost.python.original_absent -ne $true -or $rawHost.state_status -ne 'passed' -or $rawHost.suite_exit -ne 0 -or $rawHost.no_process_killed -ne $true -or $rawHost.owned_runtime_command_matches_absent -ne $true -or $rawHost.owned_runtime_matches.Count -ne 0 -or $rawHost.checked_utc -cne $hostProof.observed_utc){throw 'Measured raw host closure differs'}
foreach($key in @('coordinator_absent','python_absent','owned_runtime_command_matches_absent','no_process_killed','source_before_after_and_current_exact')){if($hostProof[$key] -ne $true){throw 'Actual host closure gate differs'}}
if($hostProof.coordinator_matches.Count -or $hostProof.owned_runtime_matches.Count -or $hostProof.functional_source_entries -ne 1019){throw 'Host closure scope differs'}
$inventoryPath=Owned-Output-File $ReceiptInventory
if((File-Sha $inventoryPath) -ne $ReceiptInventorySha256){throw 'Exact reviewed fresh receipt inventory required'}
$inventory=Read-Json $inventoryPath;$audit=$inventory.summary
$reportPath=Join-Path $Checkout 'output\verification.json'
if((File-Sha $reportPath) -ne $FullReportSha256){throw 'Exact fresh full report required'}
$start=[DateTimeOffset]::Parse($state.started_utc);$finish=[DateTimeOffset]::Parse($state.finished_utc)
$reportTime=(Get-Item -LiteralPath $reportPath).LastWriteTimeUtc.Ticks
if($reportTime -lt $start.UtcTicks -or $reportTime -gt $finish.UtcTicks){throw 'Full report is stale/outside this run'}
$report=Read-Json $reportPath
if($gate.source.source_sha256['tests/verify.py'] -ne '459b90eeeae9d5523654c07fcbb3de27dad0e889943f46947333e8eb5a65437a' -or $report.Count -ne 157){throw 'Unchanged full verifier/result-key registry differs'}
$normalized=[IO.File]::ReadAllText($reportPath).TrimStart([char]0xfeff).Replace("`r`n","`n").TrimEnd()
$log=[IO.File]::ReadAllText((Join-Path $RunRoot 'canonical.log')).TrimStart([char]0xfeff).Replace("`r`n","`n").TrimEnd()
if(-not $log.EndsWith($normalized,[StringComparison]::Ordinal)){throw 'Canonical log/fresh normalized full report suffix differs'}
$prefix=$log.Substring(0,$log.Length-$normalized.Length)
foreach($line in ($prefix -split "`n")){if($line.Trim().Length -and -not $line.StartsWith('PASS ',[StringComparison]::Ordinal)){throw 'Unexpected canonical log prefix'}}
if($audit.format -ne 'has_canonical_metadata_receipt_audit_1' -or $audit.passed -ne $true -or $audit.source_commit -ne $ExpectedCommit -or $audit.run_directory -cne $RunRoot -or $audit.functional_source_entries -ne 1019 -or $audit.full_result_top_level_entries -ne $report.Count){throw 'Receipt audit/source/normalized report binding differs'}
if($audit.coordinator_pid -ne $CoordinatorPid -or $audit.suite_python_pid -ne $PythonPid -or $audit.state.process_started -cne $CoordinatorBirth -or $audit.state.finished_utc -cne $state.finished_utc){throw 'Receipt audit actual state binding differs'}
foreach($key in @('all_receipts_private_closed','all_receipts_fresh_for_run','all_inline_exact_physical_matches','source_before_after_equal','authoritative_host_context_bound','fresh_root_all_exit_0','fresh_root_all_private_closed')){if($audit[$key] -ne $true){throw 'Fresh receipt gate failed'}}
if($audit.missing_referenced_receipts -ne 0 -or $audit.unexpected_failures.Count -ne 0){throw 'Fresh receipt failure/missing reference'}
$reportDocuments=@($inventory.report_documents|Where-Object {$_.file.path -ceq $reportPath -and $_.file.sha256 -eq $FullReportSha256})
if($reportDocuments.Count -ne 1){throw 'Receipt audit must bind the exact normalized full report bytes'}
foreach($document in $inventory.report_documents){
    $documentPath=Owned-Output-File $document.file.path
    if((File-Sha $documentPath) -ne $document.file.sha256){throw 'A report document changed after receipt reference audit'}
}
$rows=@($inventory.receipts)
if($rows.Count -le 0 -or $audit.unique_receipt_files -ne $rows.Count -or $audit.unique_desktops -ne $rows.Count){throw 'Observed receipt/desktop counts differ'}
$desktops=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
$physicalByDesktop=@{}
$success=0;$cancelled=0
if($report.krita_import.cancelled_receipt -isnot [string] -or [string]::IsNullOrWhiteSpace($report.krita_import.cancelled_receipt)){throw 'The source-registered cancellation receipt is missing'}
$expectedCancel=Owned-Output-File $report.krita_import.cancelled_receipt
$kritaPath=Join-Path $Checkout 'tests\verify_krita_import.py'
if((File-Sha $kritaPath) -ne $gate.source.source_sha256['tests/verify_krita_import.py'] -or -not [IO.File]::ReadAllText($kritaPath).Contains("assert r['exit']==2 and r['cancelled'] and r['child_desktop_confirmed']")){throw 'Registered cancellation source assertion differs'}
foreach($row in $rows){
    $receiptPath=Owned-Output-File $row.file.path
    if((File-Sha $receiptPath) -ne $row.file.sha256){throw 'Physical receipt changed after audit'}
    $receipt=Read-Json $receiptPath
    if(($receipt|ConvertTo-Json -Depth 20 -Compress) -cne ($row.receipt|ConvertTo-Json -Depth 20 -Compress)){throw 'Audited receipt does not equal physical receipt'}
    if($receipt.format -ne 'studio_private_desktop_1' -or -not $receipt.desktop -or -not $desktops.Add([string]$receipt.desktop)){throw 'Receipt identity/desktop duplicate'}
    $physicalByDesktop[$receipt.desktop]=$receipt
    foreach($key in @('private_window_seen','child_desktop_confirmed','job_closed','desktop_closed')){if($receipt[$key] -ne $true){throw 'Physical private job is not closed'}}
    foreach($key in @('desktop_switch_requested','foreground_child_observed')){if($receipt[$key] -ne $false){throw 'Physical job isolation differs'}}
    $when=(Get-Item -LiteralPath $receiptPath).LastWriteTimeUtc.Ticks
    if($when -lt $start.UtcTicks -or $when -gt $finish.UtcTicks -or $row.within_run_interval -ne $true -or $row.isolation_and_closure_passed -ne $true){throw 'Physical receipt is stale or unqualified'}
    if($row.fresh_root -eq $true -and $receipt.exit -ne 0){throw 'Fresh root receipt must exit zero'}
    if($receipt.exit -eq 0 -and -not $receipt.error -and -not $receipt.monitor_error){$success++}
    elseif($receipt.exit -eq 2 -and $receiptPath.Equals($expectedCancel,[StringComparison]::OrdinalIgnoreCase) -and $receipt.cancelled -eq $true -and $receipt.error -ceq 'Owned converter cancelled' -and -not $receipt.monitor_error){$cancelled++}
    else{throw 'Unexpected physical receipt exit/error'}
    if(-not $row.preserved_raw_copy){throw 'A retained raw receipt alias is missing'}
    $copy=Owned-Output-File $row.preserved_raw_copy.path
    if((File-Sha $copy) -ne $row.file.sha256){throw 'Retained receipt alias differs'}
}
if($cancelled -ne 1 -or $success+$cancelled -ne $rows.Count -or $audit.success_exit_0_files -ne $success -or $audit.expected_krita_cancel_exit_2_files -ne $cancelled){throw 'Actual receipt counts/registered cancellation differ'}
$inline=@($inventory.inline_receipts)
if($inline.Count -ne $audit.inline_occurrences){throw 'Actual inline receipt count differs'}
foreach($entry in $inline){
    $actual=$physicalByDesktop[$entry.receipt.desktop]
    if(-not $actual -or ($actual|ConvertTo-Json -Depth 20 -Compress) -cne ($entry.receipt|ConvertTo-Json -Depth 20 -Compress)){throw 'An inline full-report receipt has no exact physical match'}
}
# The count of one cancellation is source-registered by the pinned current
# Krita test; no historical private-job total is reused.
# A fresh second observation is mandatory after metadata/hash audit. No process
# termination is available; the interactive sibling owner review is preserved.
$null=Observe-Owned-Absence
$release=@{format='has_root_canonical_graphics_lease_release_1';released=$true;released_utc=[DateTime]::UtcNow.ToString('o');source_commit=$ExpectedCommit;canonical_run=(Split-Path $RunRoot -Leaf);coordinator_pid=$CoordinatorPid;python_pid=$PythonPid;all_private_jobs_closed=$true;no_process_killed=$true;root_observer_issued_no_termination=$true;termination_claim_scope='Root closure/release observer only; registered controlled cancellation remains separately counted.';owned_runtime_command_matches_absent=$true;private_jobs=$rows.Count;normal_exit_0=$success;expected_Krita_cancellation_exit_2=$cancelled;functional_source_entries=1019;canonical_state_sha256=(File-Sha (Join-Path $RunRoot 'state.json'));host_proof_sha256=(File-Sha $hostPath);receipt_inventory_sha256=$ReceiptInventorySha256;full_report_sha256=$FullReportSha256;normalized_log_report_suffix_equal=$true;owner_sibling_review_untouched=$true}
Write-Fresh-Json (Join-Path $RunRoot 'graphics-lease-released.json') $release
$release|ConvertTo-Json -Depth 12
