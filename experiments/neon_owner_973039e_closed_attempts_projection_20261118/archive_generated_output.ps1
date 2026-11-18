param([switch]$Archive)
$ErrorActionPreference = 'Stop'
$Root = 'C:\a\Programming\cloudflare\has-acceptance-session-20261111'
$Workspace = 'C:\a\Programming\cloudflare'
$Source = 'C:\a\Programming\cloudflare\HAS-Review-Neon-973039e-native\Studio\output'
$Target = Join-Path $Root 'output\PRIVATE-neon-owner973039e-attempt1-Studio-output-archive-20261117'
$PlanPath = Join-Path $Root 'output\PRIVATE-neon-owner973039e-attempt1-output-archive-plan-20261117.json'
$PlanSha = 'dd861256a348a2fd79b0c42d63ad1ad477771256650e1d2beb0377ca00469724'
$Receipt = Join-Path $Root 'output\PRIVATE-neon-owner973039e-attempt1-output-archive-20261117.jsonl'
$Godot = 'C:\a\Programming\cloudflare\HAS-Review-Neon-973039e-native\Studio\.godot'

function Need($Value, [string]$Message) { if (-not $Value) { throw $Message } }
function PlainPath([string]$Path) {
    $full = [IO.Path]::GetFullPath($Path)
    $cursor = $full
    while ($cursor) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            Need (-not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) 'Reparse path refused'
        }
        $cursor = [IO.Path]::GetDirectoryName($cursor)
    }
    return $full
}
function FileIdentity([string]$Path) {
    $full = PlainPath $Path
    $item = Get-Item -LiteralPath $full -Force
    Need ($item -is [IO.FileInfo]) 'Regular file required'
    $size = $item.Length
    $stamp = [long](($item.LastWriteTimeUtc.Ticks - [long]621355968000000000) * [long]100)
    $digest = (Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash.ToLowerInvariant()
    $again = Get-Item -LiteralPath $full -Force
    Need ($again.Length -eq $size -and $again.LastWriteTimeUtc.Ticks -eq $item.LastWriteTimeUtc.Ticks) 'File changed while read'
    return @{bytes=$size; mtime_ns=$stamp; sha256=$digest}
}
function DescriptorMatches($Descriptor) {
    $actual = FileIdentity $Descriptor.path
    Need ($actual.bytes -eq $Descriptor.bytes -and $actual.mtime_ns -eq $Descriptor.mtime_ns -and
          $actual.sha256 -ceq $Descriptor.sha256) 'Pinned provenance descriptor changed'
}
function Inventory([string]$Boundary) {
    $queue = [Collections.Generic.Stack[string]]::new()
    $queue.Push((PlainPath $Boundary))
    $files = [Collections.Generic.List[object]]::new()
    $dirs = [Collections.Generic.List[string]]::new()
    while ($queue.Count) {
        foreach ($item in (Get-ChildItem -LiteralPath $queue.Pop() -Force)) {
            Need (-not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) 'Generated reparse entry refused'
            $relative = [IO.Path]::GetRelativePath($Boundary, $item.FullName).Replace('\','/')
            if ($item.PSIsContainer) { $dirs.Add($relative); $queue.Push($item.FullName) }
            else { $row = FileIdentity $item.FullName; $row.path = $relative; $files.Add($row) }
            Need ($files.Count -le 10 -and $dirs.Count -le 5) 'Generated membership exceeds exact plan'
        }
    }
    return @{files=@($files | Sort-Object path); directories=@($dirs | Sort-Object)}
}
function MatchInventory($Actual, $Plan) {
    $expected = @($Plan.files | Sort-Object path)
    Need ($Actual.files.Count -eq 10 -and $expected.Count -eq 10) 'Exactly ten generated files required'
    for ($i=0; $i -lt 10; $i++) {
        $a=$Actual.files[$i]; $b=$expected[$i]
        Need ($a.path -ceq $b.path -and $a.bytes -eq $b.bytes -and $a.mtime_ns -eq $b.mtime_ns -and
              $a.sha256 -ceq $b.sha256) 'Generated file identity differs'
    }
    Need (($Actual.directories -join "`n") -ceq (@($Plan.directories | Sort-Object) -join "`n")) 'Generated directories differ'
}
function Preflight([bool]$RequireFreshReceipt) {
    $sourceFull = PlainPath $Source; $targetFull = PlainPath $Target
    $workspaceFull = (PlainPath $Workspace).TrimEnd('\') + '\'
    Need ($sourceFull.StartsWith($workspaceFull, [StringComparison]::OrdinalIgnoreCase) -and
          $targetFull.StartsWith($workspaceFull, [StringComparison]::OrdinalIgnoreCase)) 'Move paths leave workspace'
    Need ($sourceFull -ceq $Source -and [IO.Path]::GetDirectoryName($targetFull) -ceq (Join-Path $Root 'output')) 'Exact source/archive boundary required'
    Need ((Test-Path -LiteralPath $Source -PathType Container) -and -not (Test-Path -LiteralPath $Target)) 'Existing source and fresh archive required'
    Need (-not (Test-Path -LiteralPath $Godot)) '.godot must remain absent and untouched'
    if ($RequireFreshReceipt) { Need (-not (Test-Path -LiteralPath $Receipt)) 'Fresh private receipt required' }
    Need ((FileIdentity $PlanPath).sha256 -ceq $PlanSha) 'Exact reviewed plan hash required'
    $plan = Get-Content -LiteralPath $PlanPath -Raw | ConvertFrom-Json -AsHashtable
    Need ($plan.source -ceq $Source -and $plan.archive -ceq $Target -and $plan.private_receipt -ceq $Receipt) 'Pinned exact move paths differ'
    Need ($plan.file_count -eq 10 -and $plan.logical_bytes -eq 215197 -and $plan.directories.Count -eq 5) 'Pinned logical extent differs'
    foreach ($entry in $plan.provenance.Values) { DescriptorMatches $entry }
    DescriptorMatches $plan.attempt2.same_host
    DescriptorMatches $plan.attempt2.same_validator_INDEX
    Need ($plan.attempt2.same_host.sha256 -ceq '3c5b73f71fb2b482b8773b122ccb4889ad496e0a2067f52429d82d06b8b6b8fc' -and
          $plan.attempt2.same_validator_INDEX.sha256 -ceq '303b96a094d3ee61e8c1ec618db61adb0aa306811094347220b4b70436fafe38') 'Unchanged host/validator pins required'
    $before = Get-Content -LiteralPath $plan.provenance.generated_before.path -Raw | ConvertFrom-Json -AsHashtable
    $after = Get-Content -LiteralPath $plan.provenance.generated_after.path -Raw | ConvertFrom-Json -AsHashtable
    Need ($before.ContainsKey('output') -and $before.ContainsKey('.godot') -and $before.output.Count -eq 0 -and $before['.godot'].Count -eq 0) 'Original generated-before must be empty'
    Need ($after.output.Count -eq 10 -and $after['.godot'].Count -eq 0) 'Actual generated-after extent differs'
    foreach ($row in $plan.files) {
        Need (@($after.output.Keys) -ccontains $row.path) 'File absent from recorded generated-after'
        $recorded = $after.output[$row.path]
        Need ($recorded.bytes -eq $row.bytes -and $recorded.mtime_ns -eq $row.mtime_ns -and $recorded.sha256 -ceq $row.sha256) 'Actual generated-after provenance differs'
    }
    MatchInventory (Inventory $Source) $plan
    return $plan
}

$plan = Preflight $true
if (-not $Archive) {
    @{mode='VERIFY_ONLY'; files=10; logical_bytes=215197; plan_sha256=$PlanSha; moved=$false} | ConvertTo-Json -Compress
    return
}
$stream = [IO.File]::Open($Receipt, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
$writer = [IO.StreamWriter]::new($stream, [Text.UTF8Encoding]::new($false))
function Record($Value) { $writer.WriteLine(($Value | ConvertTo-Json -Depth 8 -Compress)); $writer.Flush() }
try {
    Record @{stage='started'; utc=[DateTime]::UtcNow.ToString('o'); plan_sha256=$PlanSha; source=$Source; archive=$Target}
    $plan = Preflight $false
    Record @{stage='preflight'; files=10; logical_bytes=215197; identities=$plan.files}
    Need (-not (Test-Path -LiteralPath $Target)) 'Archive appeared immediately before move'
    Move-Item -LiteralPath $Source -Destination $Target -ErrorAction Stop
    Record @{stage='moved'; source_absent=(-not (Test-Path -LiteralPath $Source)); archive=$Target}
    Need (-not (Test-Path -LiteralPath $Source)) 'Source remains after move'
    $null = PlainPath $Target
    MatchInventory (Inventory $Target) $plan
    Need (-not (Test-Path -LiteralPath $Godot)) '.godot changed during archive'
    Record @{stage='complete'; files=10; logical_bytes=215197; source_absent=$true; archived_identities_exact=$true; validator_launched=$false}
    @{mode='ARCHIVED'; files=10; logical_bytes=215197; source_absent=$true; receipt=$Receipt; validator_launched=$false} | ConvertTo-Json -Compress
}
catch {
    Record @{stage='failure'; error=$_.Exception.Message; partial_evidence_preserved=$true; no_rollback_or_cleanup=$true}
    throw
}
finally { $writer.Dispose() }
