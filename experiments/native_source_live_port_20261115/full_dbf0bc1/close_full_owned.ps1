. (Join-Path $PSScriptRoot 'context.ps1')
$gate=Terminal-Source-Gate
$observed=Observe-Owned-Absence
$checked=[DateTime]::UtcNow.ToString('o')
$rawPath=Join-Path $RunRoot 'authoritative-host-terminal.json'
$flatPath=Join-Path $RunRoot 'authoritative-host-termination.json'
if((Test-Path -LiteralPath $rawPath) -or (Test-Path -LiteralPath $flatPath)){throw 'Preserve prior host proof'}
$raw=@{format='has_canonical_bone_binding_authoritative_terminal_observation_1';canonical_run=$RunRoot;source_commit=$ExpectedCommit;checked_utc=$checked;state_status=$gate.state.status;suite_exit=$gate.state.suite_exit;coordinator=$observed[0];python=$observed[1];owned_runtime_command_matches_absent=$true;owned_runtime_matches=@();no_process_killed=$true;functional_source_entries=1014;source_before_after_and_current_exact=$true;owner_sibling_review_untouched=$true;root_birth_observation_sha256=$ExpectedBirthSha}
Write-Fresh-Json $rawPath $raw
$flat=@{format='has_canonical_authoritative_host_termination_1';canonical_run=(Split-Path $RunRoot -Leaf);source_commit=$ExpectedCommit;observed_utc=$checked;coordinator_pid=$CoordinatorPid;expected_creation_utc=$CoordinatorBirth;coordinator_absent=$true;python_pid=$PythonPid;expected_python_creation_utc=$PythonBirth;python_absent=$true;coordinator_matches=@();owned_runtime_command_matches_absent=$true;owned_runtime_matches=@();no_process_killed=$true;raw_observation_sha256=(File-Sha $rawPath);functional_source_entries=1014;source_before_after_and_current_exact=$true;owner_sibling_review_untouched=$true}
Write-Fresh-Json $flatPath $flat
$flat|ConvertTo-Json -Depth 12
