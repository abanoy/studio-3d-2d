$ErrorActionPreference='Stop'
$checkout='C:\a\Programming\cloudflare\has-acceptance-session-20261111'
$runRoot=Join-Path $checkout 'output\windows-canonical-bone-binding-20261115T225514304'
$recipe=Join-Path $checkout 'output\resume-full-publication-f0dd57a-20261115'
$statePath=Join-Path $runRoot 'state.json'
$hostPath=Join-Path $runRoot 'authoritative-host-termination.json'
$inventoryPath=Join-Path $recipe 'receipt-audit\receipt-inventory.json'
$state=Get-Content -LiteralPath $statePath -Raw|ConvertFrom-Json -DateKind String
$hostProof=Get-Content -LiteralPath $hostPath -Raw|ConvertFrom-Json -DateKind String
$audit=(Get-Content -LiteralPath $inventoryPath -Raw|ConvertFrom-Json -DateKind String).summary
if($state.status -ne 'passed' -or $state.suite_exit -ne 0 -or $state.source_unchanged -ne $true -or $state.source_commit -ne 'f0dd57a2e568089d396fecba819ab987da658bf0'){throw 'Actual coherent full PASS required'}
if($audit.passed -ne $true -or $audit.unique_receipt_files -ne 192 -or $audit.unique_desktops -ne 192 -or $audit.success_exit_0_files -ne 191 -or $audit.expected_krita_cancel_exit_2_files -ne 1 -or $audit.missing_referenced_receipts -ne 0 -or $audit.unexpected_failures.Count -ne 0){throw 'Observed192-job audit differs'}
foreach($key in @('all_receipts_private_closed','all_receipts_fresh_for_run','all_inline_exact_physical_matches','source_before_after_equal','authoritative_host_context_bound')){if($audit.$key -ne $true){throw 'Receipt/closure gate failed'}}
foreach($key in @('coordinator_absent','python_absent','owned_runtime_command_matches_absent','no_process_killed')){if($hostProof.$key -ne $true){throw 'Actual root closure gate failed'}}
foreach($identity in @(@{id=15824;birth='2026-11-15T22:55:14.3418333Z'},@{id=16040;birth='2026-11-15T22:55:28.0068371Z'})){
 $process=Get-Process -Id $identity.id -ErrorAction SilentlyContinue
 if($process -and $process.StartTime.ToUniversalTime().ToString('o') -eq $identity.birth){throw 'Original owned process remains'}
}
$workers=@(Get-CimInstance Win32_Process|Where-Object {
 (($_.Name -match '^(blender|Godot.*|ffmpeg|ffprobe)\.exe$') -and $_.CommandLine -like '*has-acceptance-session-20261111*') -or
 (($_.Name -match '^pythonw?\.exe$') -and $_.CommandLine -like '*has-acceptance-session-20261111*' -and ($_.CommandLine -like '*verify_source_choices_native*' -or $_.CommandLine -like '*tests/verify.py*' -or $_.CommandLine -like '*tests\verify.py*'))
})
if($workers.Count){throw 'An owned runtime remains; no release'}
if((git -C $checkout rev-parse HEAD).Trim() -ne $state.source_commit){throw 'HEAD changed before review build'}
$target=Join-Path $runRoot 'graphics-lease-released.json'
if(Test-Path -LiteralPath $target){throw 'Preserve previous release'}
$release=@{format='has_root_canonical_graphics_lease_release_1';released=$true;released_utc=[DateTime]::UtcNow.ToString('o');source_commit=$state.source_commit;canonical_run=(Split-Path $runRoot -Leaf);coordinator_pid=15824;python_pid=16040;all_private_jobs_closed=$true;no_process_killed=$true;owned_runtime_command_matches_absent=$true;private_jobs=192;normal_exit_0=191;expected_Krita_cancellation_exit_2=1;canonical_state_sha256=(Get-FileHash -LiteralPath $statePath -Algorithm SHA256).Hash.ToLowerInvariant();host_proof_sha256=(Get-FileHash -LiteralPath $hostPath -Algorithm SHA256).Hash.ToLowerInvariant();receipt_inventory_sha256=(Get-FileHash -LiteralPath $inventoryPath -Algorithm SHA256).Hash.ToLowerInvariant()}
$release|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $target
$release|ConvertTo-Json -Depth 6
