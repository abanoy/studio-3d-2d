# This never invokes or dot-sources the cleanup entry script. Only six pure,
# explicitly named function definitions are extracted from its parsed AST.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$sourcePath = Join-Path $PSScriptRoot 'execute_public_cache_cleanup.ps1'
$parseTokens = $null; $parseErrors = $null
$tree = [Management.Automation.Language.Parser]::ParseFile($sourcePath, [ref]$parseTokens, [ref]$parseErrors)
if (@($parseErrors).Count -ne 0) { throw 'Cleanup source does not parse.' }
$pureNames = @('Require', 'Hash-Bytes', 'Git-ObjectId', 'Is-Integer', 'Same-Text', 'Decode-Response')
$definitions = @($tree.FindAll({ param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -in $pureNames }, $true))
if ($definitions.Count -ne 6) { throw 'Exact pure helper set differs.' }
$pureSource = ($definitions | ForEach-Object { $_.Extent.Text }) -join "`n"
if ($pureSource -match 'Remove-Item|Get-GitRaw|Read-Exact|Write-NewJson|File\]::|Process\]::') { throw 'An impure capability entered the helper test.' }
. ([scriptblock]::Create($pureSource))
$script:StrictUtf8 = [Text.UTF8Encoding]::new($false, $true)
$checks = [Collections.Generic.List[string]]::new()
function Pass([bool]$Condition, [string]$Name) { if (-not $Condition) { throw ('Synthetic check failed: ' + $Name) }; $checks.Add($Name) }
function Refuses([scriptblock]$Body, [string]$Name) {
    $caught = $false; try { $null = & $Body } catch { $caught = $true }
    Pass $caught $Name
}
function Base-Row {
    return @{ path = 'synthetic.txt'; response = @{ encoding = 'base64'; content = 'aGVsbG8K'; sha = 'ce013625030ba8dba906f756967f9e9ca394464a' } }
}
function Base-Proof {
    return @{ path = 'synthetic.txt'; bytes = 6; sha256 = '5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03'; git_blob = 'ce013625030ba8dba906f756967f9e9ca394464a'; independent_remote_bytes_exact = $true; remote_method = 'contents_base64' }
}
$decoded = Decode-Response (Base-Row) (Base-Proof) @{}
Pass ($decoded.bytes -eq 6 -and $decoded.sha256 -ceq '5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03') 'Independent Python-pinned base64/SHA256/Git blob positive'
$row = Base-Row; $row.path = 'wrong.txt'
Refuses { Decode-Response $row (Base-Proof) @{} } 'Wrong ordered path refused'
$row = Base-Row; $row.response.content = '!notbase64!'
Refuses { Decode-Response $row (Base-Proof) @{} } 'Malformed base64 refused'
$row = Base-Row; $row.response.sha = '0' * 40
Refuses { Decode-Response $row (Base-Proof) @{} } 'Changed cached Git blob refused'
$proof = Base-Proof; $proof.sha256 = '0' * 64
Refuses { Decode-Response (Base-Row) $proof @{} } 'Changed published SHA256 refused'
$proof = Base-Proof; $proof.bytes = $true
Refuses { Decode-Response (Base-Row) $proof @{} } 'Boolean byte count refused'
$proof = Base-Proof; $proof.independent_remote_bytes_exact = 1
Refuses { Decode-Response (Base-Row) $proof @{} } 'Numeric remote-exact flag refused'
$proof = Base-Proof; $proof.remote_method = 'unknown'
Refuses { Decode-Response (Base-Row) $proof @{} } 'Unproven remote method refused'
$row = Base-Row; $row.response.content = ''; $row.response.sha = '5a86d673ff6049551850dbd95af133d5fff20649'; $row.fallback_utf8 = "モデル`n"
$proof = @{ path = 'synthetic.txt'; bytes = 10; sha256 = '9e42777589e4f5943b2bbbd313a03ce47294bc5c7622cda7d09c122d00d4bfd1'; git_blob = $row.response.sha; independent_remote_bytes_exact = $true; remote_method = 'blob_sha_utf8_contents_api_oversize_fallback' }
$decoded = Decode-Response $row $proof @{}
Pass ($decoded.bytes -eq 10 -and $decoded.sha256 -ceq $proof.sha256) 'Non-English inline UTF8 fallback exact bytes'
$row = @{ path = 'empty.log'; response = @{ encoding = 'base64'; content = ''; sha = 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391' }; fallback_utf8 = '' }
$proof = @{ path = 'empty.log'; bytes = 0; sha256 = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'; git_blob = $row.response.sha; independent_remote_bytes_exact = $true; remote_method = 'blob_sha_utf8_contents_api_oversize_fallback' }
$decoded = Decode-Response $row $proof @{}
Pass ($decoded.bytes -eq 0 -and $decoded.remote_method -ceq $proof.remote_method) 'Empty inline fallback retains published fallback method'
$row = @{ path = 'docs/progress_memo.md'; response = @{ encoding = 'base64'; content = ''; sha = '6c47beb6077bb92709d01c7aecc76cf36a401dd5' } }
$proof = @{ path = $row.path; bytes = 18; sha256 = 'a88ef2be15e0c4ff82d2319ee54d6914e09fcd0540f864d2d11a1022b0489487'; git_blob = $row.response.sha; independent_remote_bytes_exact = $true; remote_method = 'blob_sha_utf8_contents_api_oversize_fallback' }
$auxiliary = @{ path = $row.path; encoding = 'utf-8'; blob_sha = $row.response.sha; content = "retained fallback`n" }
$decoded = Decode-Response $row $proof $auxiliary
Pass ($decoded.sha256 -ceq $proof.sha256) 'External1ce UTF8 fallback exact bytes'
$auxiliary.blob_sha = '0' * 40
Refuses { Decode-Response $row $proof $auxiliary } 'Wrong auxiliary Git blob refused'
$source = [IO.File]::ReadAllText($sourcePath)
$scopeStart = $source.IndexOf('$allowed = [Collections.Generic.List[string]]::new()', [StringComparison]::Ordinal)
$scopeEnd = $source.IndexOf('Require ($allowed.Count -eq 71', $scopeStart, [StringComparison]::Ordinal)
Pass ($scopeStart -ge 0 -and $scopeEnd -gt $scopeStart) 'Literal scope-generator source found'
$scopeCode = $source.Substring($scopeStart, $scopeEnd - $scopeStart) + "`nreturn ,`$allowed.ToArray()"
$allowed = & ([scriptblock]::Create($scopeCode))
Pass ($allowed.Count -eq 71 -and @($allowed | Select-Object -Unique).Count -eq 71) 'Exactly71 unique explicit generated cache paths'
Pass ($allowed[0] -ceq 'output/1ce-all-remote-batch-000.json' -and $allowed[28] -ceq 'output/1ce-all-remote-batch-560.json' -and $allowed[29] -ceq 'output/09fb-all-remote-batch-000.json' -and $allowed[70] -ceq 'output/09fb-all-remote-batch-820.json') '29plus42 exact endpoints and grouping'
Pass (@($allowed | Where-Object { $_ -match 'e8|progress-memo|private|model|review|tools' }).Count -eq 0) 'Auxiliary/newer/native/tool/review paths excluded from deletion scope'
$remove = @($tree.FindAll({ param($node) $node -is [Management.Automation.Language.CommandAst] -and $node.GetCommandName() -eq 'Remove-Item' }, $true))
Pass ($remove.Count -eq 1 -and $remove[0].Extent.Text -ceq 'Remove-Item -LiteralPath $identity.absolute_path -ErrorAction Stop') 'One literal-only PowerShell file deletion statement'
$recursive = @($tree.FindAll({ param($node) $node -is [Management.Automation.Language.CommandParameterAst] -and $node.ParameterName -eq 'Recurse' }, $true))
Pass ($recursive.Count -eq 0) 'No recursive deletion switch'
Pass ($source.IndexOf("if (-not `$Execute) { throw", [StringComparison]::Ordinal) -lt $source.IndexOf('function Require', [StringComparison]::Ordinal)) 'Entry disabled before helper definitions or filesystem actions'
$result = @{ format = 'has_cache_cleanup_extracted_pure_helper_cpu_1'; checks = $checks.Count; failures = 0;
    cases = $checks.ToArray(); cleanup_entry_invoked = $false; cache_files_read_by_this_test = $false;
    Git_native_process_or_delete_invoked = $false; parsed_remove_statements = $remove.Count;
    cleanup_source_sha256 = (Hash-Bytes ([IO.File]::ReadAllBytes($sourcePath))) }
$result | ConvertTo-Json -Depth 10
