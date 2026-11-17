#requires -Version 7.0
<# Root-only read-only probe. Does not invoke or dot-source the cleanup entry.
   Loads only four named helper definitions; no removal/file-write helper exists
   in the probe's extracted scope. Root captures its JSON output separately.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$candidate = Join-Path $PSScriptRoot 'execute_public_cache_cleanup.ps1'
$expectedSource = 'd5d827d020eeb785c3495204dd5d9f863a6984e8a16c7b0a4c0e2182bd3f3db3'
if ((Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash.ToLowerInvariant() -cne $expectedSource) { throw 'Pinned V2 source differs.' }
$tokens = $null; $errors = $null
$tree = [Management.Automation.Language.Parser]::ParseFile($candidate, [ref]$tokens, [ref]$errors)
if (@($errors).Count -ne 0) { throw 'Pinned V2 source does not parse.' }
$names = @('Require', 'Hash-Bytes', 'Git-ObjectId', 'Get-GitRaw')
$functions = @($tree.FindAll({ param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -in $names }, $true))
if ($functions.Count -ne 4) { throw 'Exact probe helper set differs.' }
$source = ($functions | ForEach-Object { $_.Extent.Text }) -join "`n"
if ($source -match 'Remove-Item|Write-NewJson|Read-Exact|Directory\]::Create') { throw 'A cleanup operation entered the read-only probe.' }
. ([scriptblock]::Create($source))
$script:StrictUtf8 = [Text.UTF8Encoding]::new($false, $true)
$script:WorkspaceRoot = 'C:\a\Programming\cloudflare\has-acceptance-session-20261111'
$script:GitExecutable = (Get-Command git -CommandType Application | Select-Object -First 1).Source
$script:GitTimeouts = [Collections.Generic.List[object]]::new()
$planPath = Join-Path $script:WorkspaceRoot 'experiments/remote_download_cache_cleanup_preparation_20261117/PLAN.json'
[byte[]]$planBytes = [IO.File]::ReadAllBytes($planPath)
Require ((Hash-Bytes $planBytes) -ceq '4e07e5a6b939af7bfc7c5ac0f42a3adc5f3f883800711f35d6e55be57e59c35f') 'Old frozen plan differs.'
$plan = ConvertFrom-Json -AsHashtable -Depth 100 -InputObject ($script:StrictUtf8.GetString($planBytes))
$checks = [Collections.Generic.List[object]]::new()
$head = Get-GitRaw @('rev-parse', '--verify', 'HEAD')
Require ($head -is [byte[]]) 'Git HEAD reader emitted an extra pipeline object instead of one byte array.'
Require ($script:StrictUtf8.GetString($head).Trim() -ceq 'e8cf93ce25811cbc967b1024a6d2c87ffd9cfb9a') 'Published main HEAD changed.'
$checks.Add(@{ case = 'HEAD'; actual_type = $head.GetType().FullName; bytes = $head.Length; sha256 = (Hash-Bytes $head) })
$blob = Get-GitRaw @('cat-file', 'blob', 'e8cf93ce25811cbc967b1024a6d2c87ffd9cfb9a:experiments/neon_followup_checkpoint_remote_20261117/COMPLETE_READBACK.json')
Require ($blob -is [byte[]]) 'Git blob reader emitted an extra pipeline object instead of one byte array.'
Require ($blob.Length -eq 781680 -and (Hash-Bytes $blob) -ceq '5a46fd420b208954375a217ec93f40fa2e0ac3b11a3dc3ffdbff210c92478dda'
         -and (Git-ObjectId 'blob' $blob) -ceq '7ff708daa2b2f5e23c92f40b4ec3652ac0641877') 'Exact committed proof blob bytes differ.'
$checks.Add(@{ case = 'published_proof_blob'; actual_type = $blob.GetType().FullName; bytes = $blob.Length; sha256 = (Hash-Bytes $blob) })
$paths = @($plan.targets | ForEach-Object { $_.path })
Require ($paths.Count -eq 71) 'Exact target count differs.'
$empty = Get-GitRaw (@('--literal-pathspecs', 'ls-files', '-z', '--') + $paths)
Require ($empty -is [byte[]] -and $empty.Length -eq 0) 'Untracked check must return one empty byte array; a cache is tracked or output is contaminated.'
$checks.Add(@{ case = 'empty_untracked71'; actual_type = $empty.GetType().FullName; bytes = 0; sha256 = (Hash-Bytes $empty) })
Require ($script:GitTimeouts.Count -eq 0) 'Read-only Git probe timed out.'
@{ format = 'has_root_readonly_git_byte_return_probe_1'; passed = $true; observed_utc = [DateTime]::UtcNow.ToString('o');
    candidate_source_sha256 = $expectedSource; PLAN_sha256 = '4e07e5a6b939af7bfc7c5ac0f42a3adc5f3f883800711f35d6e55be57e59c35f';
    checks = $checks.ToArray(); cleanup_entry_invoked = $false; deletion_invoked = $false;
    native_or_CIM_or_Git_mutation_or_active_full_reads = $false; cache_file_contents_read = $false } | ConvertTo-Json -Depth 12
