param([Parameter(Mandatory=$true)][ValidateSet('BeforeProbe','BeforeRemoval')][string]$Phase)
$ErrorActionPreference='Stop'
$checkout='C:\a\Programming\cloudflare\has-acceptance-session-20261111'
$roots=@(
    'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\source-choices-native\1794615194930984000-ae0e0967',
    'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\source-choices-native\1794615438168999800-42f0686d'
)
$all=@(Get-CimInstance Win32_Process)
$runtime=@($all|Where-Object {$_.Name -match '^(Godot.*|blender|ffmpeg|ffprobe)\.exe$'})
$matchingArguments=@($all|Where-Object {$command=$_.CommandLine; $command -and @($roots|Where-Object {$command.IndexOf($_,[StringComparison]::OrdinalIgnoreCase) -ge 0}).Count -gt 0})
$old=@(@{pid=6924;birth='2026-11-14T00:13:14.8293269Z'},@{pid=27444;birth='2026-11-14T00:17:18.0852224Z'})
$identities=@()
foreach($pin in $old){
    $found=@($all|Where-Object {$_.ProcessId -eq $pin.pid})
    $same=$false
    $observedBirth=$null
    if($found.Count){
        $observedBirth=$found[0].CreationDate.ToUniversalTime().ToString('o')
        $same=([DateTimeOffset]::Parse($observedBirth) -eq [DateTimeOffset]::Parse($pin.birth))
    }
    $identities+=@{pid=$pin.pid;expected_creation_utc=$pin.birth;observed_creation_utc=$observedBirth;original_absent=(-not $same);pid_reused=($found.Count -gt 0 -and -not $same)}
}
$absent=@($identities|Where-Object {-not $_.original_absent}).Count -eq 0
$report=@{format='has_root_old_native_current_ownership_1';phase=$Phase;checked_utc=[DateTime]::UtcNow.ToString('o');literal_roots=$roots;owned_runtime_commands_absent=($runtime.Count -eq 0 -and $matchingArguments.Count -eq 0);exact_old_coordinators_absent=$absent;old_coordinators=$identities;engine_processes_any_path=$runtime.Count;old_root_argument_processes=$matchingArguments.Count;unreadable_command_lines=@($all|Where-Object {-not $_.CommandLine}).Count;all_global_nonuse_proven=$false;limitations='Process-name and readable-argument checks plus exact known coordinator identities. This is combined with source/dependency proof and fresh file-sharing evidence; inaccessible command lines and mapped views are not independently excluded.';no_process_killed=$true}
$target=Join-Path $checkout ('output\old-native-owner-'+$Phase+'-20261115.json')
if(Test-Path -LiteralPath $target){throw 'Preserve prior current ownership observation'}
$report|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $target
$report|ConvertTo-Json -Depth 8
if(-not $report.owned_runtime_commands_absent -or -not $absent){throw 'Old runtime ownership closure not established; retain roots'}
