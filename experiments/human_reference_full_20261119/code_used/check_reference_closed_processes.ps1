$ErrorActionPreference='Stop'
$items=@(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(Godot.*|blender|ffmpeg|ffprobe|pythonw?)\.exe$' -and $_.CommandLine -like '*has-height-addition-20261119*' })
if ($items.Count -ne 0) { throw 'Owned verification process scope is not closed' }
$result=[ordered]@{format='has_reference_closed_process_scope_1';observed_utc=[DateTime]::UtcNow.ToString('o');scope='C:\a\Programming\cloudflare\has-height-addition-20261119';names='Godot, Blender, FFmpeg/FFprobe, Python/Pythonw';owned_count=$items.Count;termination_issued=$false;full_child_pid=22560;full_coordinator_pid=16684;query='Read-only Win32_Process, executable names and owned-worktree command-line scope'}
[System.IO.File]::WriteAllText('C:\a\Programming\cloudflare\has-height-addition-20261119\output\reference-closed-processes.json',($result|ConvertTo-Json -Depth 5),[System.Text.UTF8Encoding]::new($false))
$result|ConvertTo-Json -Compress
