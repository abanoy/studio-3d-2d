#requires -Version 7.0
<# Preparation only: do not invoke until root independently reviews and pins it.
   File deletion uses one native PowerShell Remove-Item -LiteralPath, never recursion.
#>
param(
    [switch]$Execute,
    [string]$ExpectedPlanSha256 = '',
    [string]$ExpectedScriptSha256 = '',
    [string]$ReportDirectory = ''
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (-not $Execute) { throw 'Execution is disabled by default; root must review the exact plan and script first.' }

function Require([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}
function Hash-Bytes([byte[]]$Data, [string]$Algorithm = 'SHA256') {
    $hasher = [Security.Cryptography.HashAlgorithm]::Create($Algorithm)
    try { return [BitConverter]::ToString($hasher.ComputeHash($Data)).Replace('-', '').ToLowerInvariant() }
    finally { $hasher.Dispose() }
}
function Git-ObjectId([string]$Kind, [byte[]]$Data) {
    $header = $script:StrictUtf8.GetBytes($Kind + ' ' + $Data.Length + [char]0)
    $buffer = [byte[]]::new($header.Length + $Data.Length)
    [Array]::Copy($header, 0, $buffer, 0, $header.Length)
    [Array]::Copy($Data, 0, $buffer, $header.Length, $Data.Length)
    return Hash-Bytes $buffer 'SHA1'
}
function Is-Integer($Value) { return ($Value -is [int] -or $Value -is [long]) }
function Same-Text([string]$Left, [string]$Right) {
    return [string]::Equals($Left, $Right, [StringComparison]::Ordinal)
}
function Assert-NoReparse([string]$Path) {
    $current = [IO.Path]::GetFullPath($Path)
    while ($current) {
        $attributes = [IO.File]::GetAttributes($current)
        Require (($attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'Reparse path refused.'
        $current = [IO.Path]::GetDirectoryName($current)
    }
}
function Owned-File([string]$Relative) {
    Require (-not [IO.Path]::IsPathRooted($Relative) -and $Relative -notmatch '(^|[\\/])\.\.([\\/]|$)') 'Relative traversal refused.'
    $path = [IO.Path]::GetFullPath([IO.Path]::Combine($script:WorkspaceRoot, $Relative))
    Require ($path.StartsWith($script:WorkspaceRoot + '\', [StringComparison]::OrdinalIgnoreCase)) 'File escapes the fixed workspace.'
    Assert-NoReparse $path
    $item = Get-Item -LiteralPath $path -Force
    Require (-not $item.PSIsContainer) 'Only regular files may be read.'
    return $path
}
function Read-Exact([string]$Relative, $Expected) {
    $path = Owned-File $Relative
    $before = Get-Item -LiteralPath $path -Force
    Require ($before.Length -le 8MB) 'Read budget exceeded.'
    [byte[]]$bytes = [IO.File]::ReadAllBytes($path)
    $after = Get-Item -LiteralPath $path -Force
    $mtime = [long](([long]$before.LastWriteTimeUtc.Ticks - [long]621355968000000000) * [long]100)
    Require ($before.Length -eq $after.Length -and $before.LastWriteTimeUtc.Ticks -eq $after.LastWriteTimeUtc.Ticks) 'File changed during read.'
    $digest = Hash-Bytes $bytes
    Require ((Is-Integer $Expected.bytes) -and $bytes.Length -eq $Expected.bytes -and (Same-Text $digest $Expected.sha256)) 'Pinned file size/hash differs.'
    if ($Expected.Contains('mtime_ns')) { Require ((Is-Integer $Expected.mtime_ns) -and $mtime -eq $Expected.mtime_ns) 'Pinned file modification time differs.' }
    return @{ absolute_path = $path; relative_path = $Relative; bytes = $bytes; byte_count = $bytes.Length; sha256 = $digest; mtime_ns = $mtime }
}
function Parse-Json([byte[]]$Data) {
    return ConvertFrom-Json -AsHashtable -Depth 100 -InputObject ($script:StrictUtf8.GetString($Data))
}
function Get-GitRaw([string[]]$Arguments) {
    $start = [Diagnostics.ProcessStartInfo]::new()
    $start.FileName = $script:GitExecutable
    $start.WorkingDirectory = $script:WorkspaceRoot
    $start.UseShellExecute = $false; $start.CreateNoWindow = $true
    $start.RedirectStandardOutput = $true; $start.RedirectStandardError = $true
    $start.Environment['GIT_OPTIONAL_LOCKS'] = '0'
    $start.ArgumentList.Add('--no-optional-locks')
    foreach ($argument in $Arguments) { $start.ArgumentList.Add($argument) }
    $process = [Diagnostics.Process]::new(); $process.StartInfo = $start
    $memory = [IO.MemoryStream]::new()
    try {
        Require ($process.Start()) 'Could not start an owned read-only Git command.'
        $copy = $process.StandardOutput.BaseStream.CopyToAsync($memory)
        $errorText = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit(30000)) {
            # Only this exact retained process object is ever terminated.
            $event = @{ pid = $process.Id; arguments = $Arguments; timed_out = $true;
                kill_requested = $false; reaped_within_5000ms = $false; error = $null }
            $script:GitTimeouts.Add($event)
            try { $event.kill_requested = $true; $process.Kill() }
            catch { $event.error = $_.Exception.Message; throw 'Owned read-only Git timed out and its kill request failed; retain the exact PID record.' }
            $event.reaped_within_5000ms = $process.WaitForExit(5000)
            if (-not $event.reaped_within_5000ms) { throw 'Owned read-only Git was not reaped within5000ms; retain the exact PID record.' }
            throw 'Owned read-only Git command timed out; its retained process was reaped.'
        }
        $copy.GetAwaiter().GetResult(); $stderr = $errorText.GetAwaiter().GetResult()
        Require ($process.ExitCode -eq 0 -and $stderr.Length -eq 0) 'Read-only Git command failed or emitted stderr.'
        return ,$memory.ToArray()
    } finally { $memory.Dispose(); $process.Dispose() }
}
function Assert-Head {
    $actual = $script:StrictUtf8.GetString((Get-GitRaw @('rev-parse', '--verify', 'HEAD'))).Trim()
    Require (Same-Text $actual $script:ExpectedHead) 'Main HEAD differs from the verified published checkpoint.'
}
function Assert-Untracked([string[]]$RelativePaths) {
    $arguments = @('--literal-pathspecs', 'ls-files', '-z', '--') + $RelativePaths
    [byte[]]$tracked = Get-GitRaw $arguments
    Require ($tracked.Length -eq 0) 'A cleanup target is tracked; no source may be deleted.'
}
function Decode-Response($Row, $Published, $Auxiliary) {
    Require (Same-Text $Row.path $Published.path) 'Cached/proof ordered path differs.'
    $response = $Row.response
    Require (Same-Text $response.encoding 'base64') 'Unexpected cached response encoding.'
    [byte[]]$decoded = [Convert]::FromBase64String($response.content)
    $method = 'contents_base64'
    if ($decoded.Length -eq 0 -and $Row.Contains('fallback_utf8')) {
        Require ($Row.fallback_utf8 -is [string]) 'Inline fallback must be text.'
        $decoded = $script:StrictUtf8.GetBytes($Row.fallback_utf8)
        $method = 'blob_sha_utf8_contents_api_oversize_fallback'
    } elseif ($decoded.Length -eq 0 -and (Same-Text $Row.path 'docs/progress_memo.md')) {
        Require ((Same-Text $Auxiliary.path $Row.path) -and (Same-Text $Auxiliary.encoding 'utf-8') -and (Same-Text $Auxiliary.blob_sha $response.sha)) 'Retained original fallback identity differs.'
        $decoded = $script:StrictUtf8.GetBytes($Auxiliary.content)
        $method = 'blob_sha_utf8_contents_api_oversize_fallback'
    }
    Require ((Is-Integer $Published.bytes) -and $decoded.Length -eq $Published.bytes -and (Same-Text (Hash-Bytes $decoded) $Published.sha256)) 'Decoded contents bytes/hash differ from published proof.'
    Require ((Same-Text (Git-ObjectId 'blob' $decoded) $response.sha) -and (Same-Text $response.sha $Published.git_blob)) 'Decoded Git blob differs.'
    Require ($Published.independent_remote_bytes_exact -is [bool] -and $Published.independent_remote_bytes_exact -eq $true -and (Same-Text $Published.remote_method $method)) 'Published response method/exact flag differs.'
    return @{ path = $Row.path; bytes = $decoded.Length; sha256 = (Hash-Bytes $decoded); git_blob = $response.sha; remote_method = $method }
}
function Write-NewJson([string]$Path, $Value) {
    $parent = [IO.Path]::GetDirectoryName($Path)
    Require ([string]::Equals($parent, $script:ReportRoot, [StringComparison]::OrdinalIgnoreCase)) 'Journal must stay in the fresh owned report directory.'
    Assert-NoReparse $parent
    [byte[]]$data = $script:StrictUtf8.GetBytes((ConvertTo-Json -Depth 100 -InputObject $Value) + "`n")
    $stream = [IO.FileStream]::new($Path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try { $stream.Write($data, 0, $data.Length); $stream.Flush($true) } finally { $stream.Dispose() }
}

$script:StrictUtf8 = [Text.UTF8Encoding]::new($false, $true)
$script:WorkspaceRoot = 'C:\a\Programming\cloudflare\has-acceptance-session-20261111'
$script:ExpectedHead = 'e8cf93ce25811cbc967b1024a6d2c87ffd9cfb9a'
Require ($ExpectedPlanSha256 -cmatch '^[a-f0-9]{64}$' -and $ExpectedScriptSha256 -cmatch '^[a-f0-9]{64}$') 'Root must supply both exact source/plan SHA256 pins.'
Require ([string]::Equals([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..')), $script:WorkspaceRoot, [StringComparison]::OrdinalIgnoreCase)) 'Preparation is outside the fixed workspace.'
Assert-NoReparse $script:WorkspaceRoot
Require (Same-Text (Hash-Bytes ([IO.File]::ReadAllBytes($PSCommandPath))) $ExpectedScriptSha256) 'Reviewed script bytes differ.'
$planPath = Owned-File 'experiments/remote_download_cache_cleanup_preparation_20261117/PLAN.json'
[byte[]]$planRaw = [IO.File]::ReadAllBytes($planPath)
Require (Same-Text (Hash-Bytes $planRaw) $ExpectedPlanSha256) 'Reviewed cleanup plan bytes differ.'
$plan = Parse-Json $planRaw
Require ((Same-Text $plan.format 'has_exact_public_download_cache_cleanup_plan_1') -and (Same-Text $plan.workspace_root $script:WorkspaceRoot) -and (Same-Text $plan.expected_main_head $script:ExpectedHead)) 'Wrong cleanup plan scope.'

$allowed = [Collections.Generic.List[string]]::new()
foreach ($group in @(@('1ce', 560), @('09fb', 820))) {
    for ($start = 0; $start -le $group[1]; $start += 20) { $allowed.Add(('output/{0}-all-remote-batch-{1:000}.json' -f $group[0], $start)) }
}
Require ($allowed.Count -eq 71 -and $plan.targets.Count -eq 71 -and $plan.target_files -eq 71 -and $plan.target_bytes -eq 14151060) 'Only the exact71 public caches are admitted.'
for ($index = 0; $index -lt 71; $index++) { Require (Same-Text $plan.targets[$index].path $allowed[$index]) 'Cleanup target membership/order differs.' }
$script:GitExecutable = (Get-Command git -CommandType Application | Select-Object -First 1).Source
Require ([IO.File]::Exists($script:GitExecutable)) 'Read-only Git executable is unavailable.'
$outputRoot = [IO.Path]::Combine($script:WorkspaceRoot, 'output'); Assert-NoReparse $outputRoot
if (-not $ReportDirectory) { $ReportDirectory = [IO.Path]::Combine($outputRoot, 'remote-cache-cleanup-1ce-09fb-20261117-attempt1') }
$script:ReportRoot = [IO.Path]::GetFullPath($ReportDirectory)
Require ([string]::Equals([IO.Path]::GetDirectoryName($script:ReportRoot), $outputRoot, [StringComparison]::OrdinalIgnoreCase)) 'Report must be one fresh child of the owned output directory.'
Require ([IO.Path]::GetFileName($script:ReportRoot) -cmatch '^remote-cache-cleanup-1ce-09fb-20261117-attempt[1-9][0-9]{0,2}$') 'Report directory name is outside the exact cleanup domain.'
Require (-not (Test-Path -LiteralPath $script:ReportRoot)) 'Never overwrite an earlier cleanup result.'
[void][IO.Directory]::CreateDirectory($script:ReportRoot); Assert-NoReparse $script:ReportRoot

$started = [DateTime]::UtcNow.ToString('o'); $phase = 'preflight'; $deleted = [Collections.Generic.List[object]]::new()
$attempted = $null; $failure = $null; $success = $false
$removeStarted = $false; $removeReturned = $false; $absenceObserved = $false; $removeReturns = 0
$script:GitTimeouts = [Collections.Generic.List[object]]::new()
try {
    Write-NewJson (Join-Path $script:ReportRoot 'EXECUTION_REQUESTED.json') @{
        format = 'has_exact_public_cache_cleanup_execution_1'; started_utc = $started; plan_sha256 = $ExpectedPlanSha256;
        script_sha256 = $ExpectedScriptSha256; target_files = 71; target_bytes = 14151060; recursive_delete = $false
    }
    Assert-Head; Assert-Untracked $allowed.ToArray()
    $proofs = [Collections.Generic.List[object]]::new(); $proofBytes = [Collections.Generic.List[object]]::new()
    Require ($plan.proofs.Count -eq 3) 'Three exact published readback proofs required.'
    foreach ($proof in $plan.proofs) {
        $identity = Read-Exact $proof.path $proof; $value = Parse-Json $identity.bytes
        Require ((Same-Text $value.format 'has_complete_independent_remote_readback_1') -and (Same-Text $value.commit $proof.commit)) 'Proof format/commit differs.'
        Require ((Is-Integer $value.file_count) -and $value.file_count -eq $value.files.Count -and $value.file_count -eq $proof.file_count) 'Exact proof file count differs.'
        $seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal); [long]$sum = 0
        foreach ($row in $value.files) { Require ($seen.Add($row.path) -and $row.independent_remote_bytes_exact -is [bool] -and $row.independent_remote_bytes_exact -eq $true -and (Is-Integer $row.bytes)) 'Duplicate or nonexact proof row.'; $sum += $row.bytes }
        Require ($sum -eq $value.bytes -and $sum -eq $proof.remote_bytes) 'Exact published proof byte total differs.'
        $proofs.Add($value); $proofBytes.Add($identity.bytes)
    }
    Require ((Same-Text $proofs[2].commit $script:ExpectedHead) -and $proofs[0].file_count -eq 565 -and $proofs[1].file_count -eq 837 -and $proofs[2].file_count -eq 534) 'Wrong published proof sequence.'
    for ($child = 1; $child -le 2; $child++) {
        $parent = $child - 1; $parentPath = $plan.proofs[$parent].path
        $matches = @($proofs[$child].files | Where-Object { Same-Text $_.path $parentPath })
        Require ($matches.Count -eq 1) 'Published parent proof must occur exactly once.'
        $row = $matches[0]; [byte[]]$parentBody = $proofBytes[$parent]
        Require ($row.bytes -eq $parentBody.Length -and (Same-Text $row.sha256 (Hash-Bytes $parentBody)) -and (Same-Text $row.git_blob (Git-ObjectId 'blob' $parentBody))) 'Published proof body chain differs.'
        [byte[]]$committed = Get-GitRaw @('cat-file', 'blob', ($proofs[$child].commit + ':' + $parentPath))
        Require ((Same-Text (Hash-Bytes $committed) $row.sha256) -and (Same-Text (Git-ObjectId 'blob' $committed) $row.git_blob)) 'Proof is not the exact committed published blob.'
        [byte[]]$commitRaw = Get-GitRaw @('cat-file', 'commit', $proofs[$child].commit)
        Require (Same-Text (Git-ObjectId 'commit' $commitRaw) $proofs[$child].commit) 'Commit object hash differs.'
        $commitText = $script:StrictUtf8.GetString($commitRaw)
        $separator = $commitText.IndexOf("`n`n", [StringComparison]::Ordinal)
        Require ($separator -ge 0) 'Commit header/message separator is absent.'
        $header = $commitText.Substring(0, $separator)
        $parents = @($header.Split("`n") | Where-Object { $_.StartsWith('parent ') })
        Require ($parents.Count -eq 1 -and (Same-Text $parents[0] ('parent ' + $proofs[$parent].commit))) 'Exact published commit ancestry differs.'
    }
    $auxiliaryIdentity = Read-Exact $plan.retained_auxiliary_fallback.path $plan.retained_auxiliary_fallback
    $auxiliary = Parse-Json $auxiliaryIdentity.bytes
    $verified = [Collections.Generic.List[object]]::new(); $coverage = @{}
    foreach ($cache in $plan.targets) {
        $identity = Read-Exact $cache.path $cache; $batch = Parse-Json $identity.bytes
        $group = if (Same-Text $cache.prefix '1ce') { 0 } else { 1 }; $proof = $proofs[$group]
        Require ((Same-Text $batch.format 'has_independent_remote_fetch_batch_1') -and (Same-Text $batch.commit $proof.commit) -and (Is-Integer $batch.start) -and $batch.start -eq $cache.start) 'Cached batch format/commit/start differs.'
        $count = [Math]::Min(20, $proof.files.Count - $cache.start)
        Require ($batch.files.Count -eq $count -and $cache.records.Count -eq $count) 'Exact cached response count differs.'
        for ($member = 0; $member -lt $count; $member++) {
            $published = $proof.files[$cache.start + $member]
            $decoded = Decode-Response $batch.files[$member] $published $auxiliary
            $retained = $cache.records[$member]
            foreach ($key in @('path', 'sha256', 'git_blob', 'remote_method')) { Require (Same-Text $decoded[$key] $retained[$key]) 'Prepared decoded record identity differs.' }
            Require ($decoded.bytes -eq $retained.bytes) 'Prepared decoded byte count differs.'
        }
        $verified.Add(@{ path = $cache.path; bytes = $identity.byte_count; sha256 = $identity.sha256; mtime_ns = $identity.mtime_ns; response_files = $count })
        if (-not $coverage.Contains($cache.prefix)) { $coverage[$cache.prefix] = 0 }; $coverage[$cache.prefix] += $count
    }
    Require ($coverage['1ce'] -eq 565 -and $coverage['09fb'] -eq 837) 'Incomplete decoded proof coverage.'
    Write-NewJson (Join-Path $script:ReportRoot 'PREFLIGHT_VERIFIED.json') @{
        format = 'has_cache_cleanup_preflight_1'; verified_utc = [DateTime]::UtcNow.ToString('o'); expected_head = $script:ExpectedHead;
        plan_sha256 = $ExpectedPlanSha256; script_sha256 = $ExpectedScriptSha256; targets = $verified.ToArray();
        decoded_records = 1402; proofs = $plan.proofs; auxiliary_fallback_retained = $plan.retained_auxiliary_fallback.path
    }
    $phase = 'deleting_exact_public_cache_files'
    for ($index = 0; $index -lt 71; $index++) {
        $cache = $plan.targets[$index]; $attempted = $cache.path
        $removeStarted = $false; $removeReturned = $false; $absenceObserved = $false
        Assert-Head; Assert-Untracked @($cache.path)
        $identity = Read-Exact $cache.path $cache
        Require ([string]::Equals([IO.Path]::GetDirectoryName($identity.absolute_path), $outputRoot, [StringComparison]::OrdinalIgnoreCase)) 'Deletion target must be an immediate output file.'
        Require (Same-Text $cache.path $allowed[$index]) 'Deletion target is not the exact admitted filename.'
        $entry = @{ sequence = $index; path = $cache.path; absolute_path = $identity.absolute_path; bytes = $identity.byte_count;
            sha256 = $identity.sha256; mtime_ns = $identity.mtime_ns; plan_sha256 = $ExpectedPlanSha256;
            checked_utc = [DateTime]::UtcNow.ToString('o'); status = 'VERIFIED_BEFORE_DELETE_NOT_YET_DELETED'; tracked = $false; reparse = $false }
        Write-NewJson (Join-Path $script:ReportRoot ('predelete-{0:000}.json' -f $index)) $entry
        # The only deletion operation in this script. No wildcard, recursion,
        # shell delegation, directory deletion, move or installed-tool action.
        $removeStarted = $true
        Remove-Item -LiteralPath $identity.absolute_path -ErrorAction Stop
        $removeReturned = $true; $removeReturns++
        Require (-not (Test-Path -LiteralPath $identity.absolute_path)) 'Deleted filename reappeared; stop instead of deleting again.'
        $absenceObserved = $true
        $done = @{ sequence = $index; path = $cache.path; bytes = $identity.byte_count; sha256 = $identity.sha256;
            observed_absent_utc = [DateTime]::UtcNow.ToString('o'); status = 'DELETED_AND_ABSENCE_OBSERVED' }
        $deleted.Add($done)
        Write-NewJson (Join-Path $script:ReportRoot ('deleted-{0:000}.json' -f $index)) $done
    }
    $phase = 'final_identity_and_scope_check'; Assert-Head
    foreach ($proof in $plan.proofs) { $null = Read-Exact $proof.path $proof }
    $null = Read-Exact $plan.retained_auxiliary_fallback.path $plan.retained_auxiliary_fallback
    foreach ($relative in $allowed) { Require (-not (Test-Path -LiteralPath (Join-Path $script:WorkspaceRoot $relative))) 'An admitted filename is present after cleanup.' }
    Require ($deleted.Count -eq 71) 'Incomplete deletion count.'
    $success = $true
} catch {
    $failure = $_.Exception.Message
} finally {
    [long]$logicalBytes = 0; foreach ($entry in $deleted) { $logicalBytes += $entry.bytes }
    $result = @{ format = 'has_exact_public_cache_cleanup_result_1'; status = $(if ($success) { 'COMPLETE_EXACT71' } else { 'FAILED_OR_PARTIAL_STOPPED' });
        started_utc = $started; finished_utc = [DateTime]::UtcNow.ToString('o'); expected_main_head = $script:ExpectedHead;
        phase = $phase; attempted_path = $attempted; error = $failure; plan_sha256 = $ExpectedPlanSha256; script_sha256 = $ExpectedScriptSha256;
        confirmed_deleted_and_absent_files = $deleted.Count; confirmed_deleted_logical_bytes = $logicalBytes; confirmed_deleted = $deleted.ToArray();
        remove_calls_returned_successfully = $removeReturns; last_remove_call_started = $removeStarted;
        last_remove_call_returned_successfully = $removeReturned; last_path_absence_observed = $absenceObserved;
        uncertain_last_attempt_effect = ($removeStarted -and -not $absenceObserved); owned_Git_timeout_records = $script:GitTimeouts.ToArray();
        expected_files = 71; expected_bytes = 14151060; recursive_delete = $false; auxiliary_fallback_deleted = $false;
        other_e8_private_native_model_review_tool_or_source_paths_authorized = $false; journal_directory = $script:ReportRoot }
    Write-NewJson (Join-Path $script:ReportRoot 'RESULT.json') $result
}
if (-not $success) { throw ('Cleanup stopped; retain RESULT.json and per-file journal: ' + $script:ReportRoot + '; ' + $failure) }
Write-Output ('Completed exact71 public cache cleanup. Result: ' + (Join-Path $script:ReportRoot 'RESULT.json'))
