$ErrorActionPreference = 'Stop'
$stageRoots = @(
 'C:\a\Programming\cloudflare\has-headless-components-1795240469769670600',
 'C:\a\Programming\cloudflare\has-headless-components-1795240567956647400',
 'C:\a\Programming\cloudflare\has-headless-components-1795240843368455500',
 'C:\a\Programming\cloudflare\has-headless-components-1795241062433191300'
)
$allProcesses = @(Get-CimInstance Win32_Process -ErrorAction Stop)
$matches = @()
$unreadableCandidates = @()
foreach ($proc in $allProcesses) {
 if ($proc.ProcessId -eq $PID) { continue }
 $line = [string]$proc.CommandLine
 if (-not $line -and $proc.Name -match '^(python|pythonw|Godot|blender|ffmpeg|ffprobe).*\.exe$') {
  $unreadableCandidates += [pscustomobject]@{ pid = $proc.ProcessId; name = $proc.Name }
 }
 foreach ($stageRoot in $stageRoots) {
  if ($line.IndexOf($stageRoot, [StringComparison]::OrdinalIgnoreCase) -ge 0 -or $line.Replace('/', '\').IndexOf($stageRoot, [StringComparison]::OrdinalIgnoreCase) -ge 0) {
   $matches += [pscustomobject]@{ pid = $proc.ProcessId; name = $proc.Name; stage = $stageRoot }
  }
 }
}
$result = [ordered]@{
 format = 'has_exact_four_headless_host_process_check_1'
 utc = [DateTime]::UtcNow.ToString('o')
 method = 'Get-CimInstance Win32_Process; own audit PID excluded; no unrelated command lines retained'
 host_process_count = $allProcesses.Count
 stage_roots = $stageRoots
 matches = $matches
 unreadable_runtime_candidates = $unreadableCandidates
 no_target_process_observed = ($matches.Count -eq 0 -and $unreadableCandidates.Count -eq 0)
 deletion_performed = $false
}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath 'C:\a\Programming\cloudflare\has-body-addition-20261120\output\HEADLESS_HOST_PROCESS_CHECK_20261121.json' -Encoding utf8
$result | ConvertTo-Json -Depth 8
