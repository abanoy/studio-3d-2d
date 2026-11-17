#requires -Version 7.0
[CmdletBinding()]
param([switch]$Delete)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$rootPath = 'C:\a\Programming\cloudflare\has-acceptance-session-20261111'
$outputPath = Join-Path $rootPath 'output'
$candidateFolder = Join-Path $rootPath 'experiments\public_remote_cache_candidates_20261117'
$candidateIndexSha = 'f9be18b1accd813d18f941c20978f3d0e9828394160d87fe561cc333796f340f'
$candidateInventorySha = '2814fd89078398168c718e1c22fb487085863e3592d1bfb8bab8c2d084ab7cf1'
$expectedFiles = 85
$expectedBytes = [long]33228774
$receiptStream = $null
$receiptWriter = $null
$receiptPath = $null
$deletedFiles = 0
$deletedBytes = [long]0

function Require([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}

function Assert-PlainPath([string]$Path) {
    Require ([IO.Path]::IsPathFullyQualified($Path)) 'Absolute filesystem path required.'
    $fullPath = [IO.Path]::GetFullPath($Path)
    Require ([string]::Equals($Path, $fullPath, [StringComparison]::OrdinalIgnoreCase)) 'Canonical absolute path required.'
    $pathPart = $fullPath
    while ($null -ne $pathPart) {
        $pathItem = Get-Item -LiteralPath $pathPart -Force
        Require (($pathItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) "Reparse or symbolic-link path refused: $pathPart"
        $pathPart = [IO.Path]::GetDirectoryName($pathPart)
    }
    $resolvedPath = Resolve-Path -LiteralPath $fullPath
    Require ($resolvedPath.Provider.Name -eq 'FileSystem' -and [string]::Equals($resolvedPath.ProviderPath, $fullPath, [StringComparison]::OrdinalIgnoreCase)) 'Resolved filesystem path differs.'
}

function Get-Identity([string]$Path) {
    Assert-PlainPath $Path
    $beforeItem = Get-Item -LiteralPath $Path -Force
    Require (-not $beforeItem.PSIsContainer -and $beforeItem -is [IO.FileInfo]) "Regular file required: $Path"
    $beforeSize = $beforeItem.Length
    $beforeTicks = $beforeItem.LastWriteTimeUtc.Ticks
    $fileSha = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-PlainPath $Path
    $afterItem = Get-Item -LiteralPath $Path -Force
    Require (-not $afterItem.PSIsContainer -and $afterItem -is [IO.FileInfo] -and $beforeSize -eq $afterItem.Length -and $beforeTicks -eq $afterItem.LastWriteTimeUtc.Ticks) "File changed while hashing: $Path"
    return [ordered]@{path=$Path; bytes=[long]$afterItem.Length; mtime_ns=[long](($afterItem.LastWriteTimeUtc.Ticks - [long]621355968000000000) * [long]100); sha256=$fileSha}
}

function Read-PinnedJson([string]$Path, [string]$Sha256) {
    $beforeIdentity = Get-Identity $Path
    Require ($beforeIdentity.sha256 -ceq $Sha256) "Pinned source identity differs: $Path"
    $jsonBytes = [IO.File]::ReadAllBytes($Path)
    $shaEngine = [Security.Cryptography.SHA256]::Create()
    try { $rawSha = ([BitConverter]::ToString($shaEngine.ComputeHash($jsonBytes))).Replace('-', '').ToLowerInvariant() }
    finally { $shaEngine.Dispose() }
    $afterIdentity = Get-Identity $Path
    Require ($rawSha -ceq $Sha256 -and $beforeIdentity.bytes -eq $afterIdentity.bytes -and $beforeIdentity.mtime_ns -eq $afterIdentity.mtime_ns -and $afterIdentity.sha256 -ceq $Sha256) "Pinned source changed while reading: $Path"
    return [Text.Encoding]::UTF8.GetString($jsonBytes) | ConvertFrom-Json
}

function Assert-Candidate($Candidate) {
    $cachePath = [string]$Candidate.path
    Require ([IO.Path]::IsPathFullyQualified($cachePath)) 'Absolute cache path required.'
    Require ([string]::Equals([IO.Path]::GetDirectoryName($cachePath), $outputPath, [StringComparison]::OrdinalIgnoreCase)) 'Only immediate ROOT/output children are admitted.'
    Require ([IO.Path]::GetFileName($cachePath) -cmatch '^(e8cf|4ec7|a41a|4fd0|855d)-all-remote-batch-[0-9]{3}\.json$') 'Only the five exact old public cache prefixes are admitted.'
    $observed = Get-Identity $cachePath
    Require ($observed.bytes -eq [long]$Candidate.bytes -and $observed.mtime_ns -eq [long]$Candidate.mtime_ns -and $observed.sha256 -ceq [string]$Candidate.sha256) "Candidate identity differs: $cachePath"
}

function Write-Receipt([string]$Action, [hashtable]$Fields) {
    $entry = [ordered]@{format='has_public_cache85_cleanup_journal_1'; action=$Action; utc=[DateTime]::UtcNow.ToString('o'); deleted_files=$script:deletedFiles; deleted_logical_bytes=$script:deletedBytes; logical_bytes_not_measured_free_space=$true}
    foreach ($entryKey in $Fields.Keys) { $entry[$entryKey] = $Fields[$entryKey] }
    $script:receiptWriter.WriteLine(($entry | ConvertTo-Json -Depth 12 -Compress))
    $script:receiptWriter.Flush()
    $script:receiptWriter.BaseStream.Flush($true)
}

try {
    Assert-PlainPath $outputPath
    Require ((Get-Item -LiteralPath $outputPath -Force).PSIsContainer) 'Existing ROOT/output directory required.'
    if ($Delete) {
        $receiptName = 'public-cache85-cleanup-' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffffffZ') + '-' + [Guid]::NewGuid().ToString('N') + '.jsonl'
        $receiptPath = Join-Path $outputPath $receiptName
        $receiptStream = [IO.FileStream]::new($receiptPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
        $receiptWriter = [IO.StreamWriter]::new($receiptStream, [Text.UTF8Encoding]::new($false))
        $receiptWriter.NewLine = "`n"
        Write-Receipt 'started' @{candidate_INDEX_sha256=$candidateIndexSha; candidate_inventory_sha256=$candidateInventorySha; expected_files=$expectedFiles; expected_logical_bytes=$expectedBytes}
    }
    $candidateIndex = Read-PinnedJson (Join-Path $candidateFolder 'INDEX.json') $candidateIndexSha
    $inventoryRows = @($candidateIndex.files | Where-Object { $_.path -ceq 'CANDIDATES.json' })
    Require ($inventoryRows.Count -eq 1 -and $inventoryRows[0].bytes -eq 87982 -and $inventoryRows[0].sha256 -ceq $candidateInventorySha) 'Pinned INDEX inventory binding differs.'
    $inventory = Read-PinnedJson (Join-Path $candidateFolder 'CANDIDATES.json') $candidateInventorySha
    Require ($inventory.root -ceq $rootPath -and $inventory.output_boundary -ceq $outputPath -and $inventory.candidate_cache_files -eq $expectedFiles -and $inventory.candidate_logical_bytes -eq $expectedBytes) 'Pinned inventory scope differs.'
    $candidates = @($inventory.candidates)
    Require ($candidates.Count -eq $expectedFiles) 'Exactly 85 candidates required.'
    $uniquePaths = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $verifiedBytes = [long]0
    foreach ($candidate in $candidates) {
        Require ($uniquePaths.Add([string]$candidate.path)) 'Duplicate candidate path refused.'
        Assert-Candidate $candidate
        $verifiedBytes += [long]$candidate.bytes
    }
    Require ($uniquePaths.Count -eq $expectedFiles -and $verifiedBytes -eq $expectedBytes) 'Exact 85-file logical total differs.'
    if (-not $Delete) {
        [ordered]@{mode='VERIFY_ONLY'; verified_files=$expectedFiles; verified_logical_bytes=$verifiedBytes; candidate_INDEX_sha256=$candidateIndexSha; candidate_inventory_sha256=$candidateInventorySha; deletion_performed=$false; receipt_created=$false; logical_bytes_not_measured_free_space=$true} | ConvertTo-Json -Compress
        return
    }
    Write-Receipt 'preflight_complete' @{verified_files=$expectedFiles; verified_logical_bytes=$verifiedBytes}
    for ($candidateNumber = 0; $candidateNumber -lt $candidates.Count; $candidateNumber++) {
        $candidate = $candidates[$candidateNumber]
        Write-Receipt 'before_delete' @{candidate_number=$candidateNumber; path=$candidate.path; bytes=$candidate.bytes; mtime_ns=$candidate.mtime_ns; sha256=$candidate.sha256}
        Assert-Candidate $candidate
        Remove-Item -LiteralPath $candidate.path -ErrorAction Stop
        Require (-not (Test-Path -LiteralPath $candidate.path)) "Deleted cache path is still present: $($candidate.path)"
        $deletedFiles++
        $deletedBytes += [long]$candidate.bytes
        Write-Receipt 'deleted_and_absent' @{candidate_number=$candidateNumber; path=$candidate.path; bytes=$candidate.bytes; sha256=$candidate.sha256}
    }
    Require ($deletedFiles -eq $expectedFiles -and $deletedBytes -eq $expectedBytes) 'Final deletion count or logical byte total differs.'
    Write-Receipt 'complete' @{expected_files=$expectedFiles; expected_logical_bytes=$expectedBytes}
    [ordered]@{mode='DELETE'; deleted_files=$deletedFiles; deleted_logical_bytes=$deletedBytes; receipt=$receiptPath; logical_bytes_not_measured_free_space=$true} | ConvertTo-Json -Compress
}
catch {
    $failureText = $_.Exception.Message
    if ($null -ne $receiptWriter) {
        try { Write-Receipt 'failed_partial_retained' @{error=$failureText; receipt=$receiptPath} }
        catch { [Console]::Error.WriteLine('Receipt update failed; retain the existing journal: ' + $receiptPath) }
    }
    throw ('Cache cleanup stopped. ' + $failureText + $(if ($null -ne $receiptPath) { ' Receipt: ' + $receiptPath } else { '' }))
}
finally {
    if ($null -ne $receiptWriter) { $receiptWriter.Dispose() }
    elseif ($null -ne $receiptStream) { $receiptStream.Dispose() }
}
