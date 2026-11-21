param([switch]$Execute,[switch]$RootLaneConfirmed)
$ErrorActionPreference='Stop'
if (-not $RootLaneConfirmed) { throw 'Root must attest the exclusive cleanup lane' }
$cleanupRoot='C:\a\Programming\cloudflare\has-body-addition-20261120'
$cleanupOutput=Join-Path $cleanupRoot 'output'
$ownedPrep=Join-Path $cleanupOutput 'source-carrier-cleanup-prep-20261120'
if ([IO.Path]::GetFullPath($PSScriptRoot) -cne $ownedPrep) { throw 'Exact cleanup source location required' }
$planPath=Join-Path $ownedPrep 'plan.json'
$resultPath=Join-Path $ownedPrep 'result.json'
$receiptPath=Join-Path $cleanupOutput 'source-carrier-checkpoint-remote-receipt.json'
$receiptSha='986433bc02ad361d6991c0f6871fac0584a79931a6ca5cf2fe51312ad61bbff9'
$backedCommit='ffed3fc2fe4f078a4c6cd506c5c757b7f46db82b'
$sourceFamily='C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\sfm-bone-bindings-native-launch-20261114T033026205\run\Studio\output\compatibility\source-1794627119-888-34370685'
$originalPins=@(
 @('editable.blend',2423175,'ead1f1913812593abd69e353fed375944a15f280738784886fcef7fda3ee65c6'),
 @('scene.glb',2322644,'4e6ac7c2a7a84dea4b46b0bcb5724af68781243f57737e555b4cc82f2628b90d'),
 @('parameters.json',159684,'b807fc82ac1b1d1658b659b41250001e3bdecde99c3d32764122c2add6b51eed'),
 @('native/junko hair.mdl',37644,'8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716'),
 @('native/junko hair.vvd',618368,'2bfa2a363eea586d06d4fd0e28c7751c10276da5cc0c46c310ffa9dedbb159e0'),
 @('native/junko hair.dx90.vtx',173309,'924954f27574fc83945934a13e6b4e90049b5d46356053dc4b41ec43d3ce364a'))
$targets=ConvertFrom-Json -InputObject '[{"name":"source-material-carrier-run-1795220688291646000","safe_reports":[{"source":"result/PLACEMENT_CARRIER_EXPORT.json","published":"experiments/source_material_carrier_20261120/actual/attempt1_failed/PLACEMENT_CARRIER_EXPORT.json","bytes":688,"sha256":"7a8941c90e1d82a74d4936f957b091ce87f8764d19ac20ba411cd84733035dcd"},{"source":"result/PUBLIC_CARRIER_EXPORT.json","published":"experiments/source_material_carrier_20261120/actual/attempt1_failed/PUBLIC_CARRIER_EXPORT.json","bytes":23674,"sha256":"7c8b85083ff22058e597929aa085f1aeaea76c56c5e4120ae997b470b2b13f60"},{"source":"PUBLIC_CARRIER_EXPORT_FAILED_PRESERVATION.json","published":"experiments/source_material_carrier_20261120/actual/attempt1_failed/PUBLIC_CARRIER_EXPORT_FAILED_PRESERVATION.json","bytes":2600,"sha256":"6ffdb9a91a08c593b3ef1165ec3d954bec115b6d1a192f010f4fdff9d1c0b0cb"},{"source":"graphics-release.json","published":"experiments/source_material_carrier_20261120/actual/attempt1_failed/graphics-release.json","bytes":683,"sha256":"e0813ba8c94e94e91693350c556563d712967adf1657adbb9bf918a7fb8073a5"},{"source":"physical-closure.json","published":"experiments/source_material_carrier_20261120/actual/attempt1_failed/physical-closure.json","bytes":649,"sha256":"966d3039a6931a818b2eba630614915cffdfbf5c559862750c2f747c0f3fa4c7"},{"source":"private-desktop.json","published":"experiments/source_material_carrier_20261120/actual/attempt1_failed/private-desktop.json","bytes":428,"sha256":"029b2b2a43bb18705ce326b2dbf438b1482c322de9e87d321668630adf16a763"}]},{"name":"source-material-carrier-run-1795221526821681200","safe_reports":[{"source":"result/PLACEMENT_CARRIER_EXPORT.json","published":"experiments/source_material_carrier_20261120/actual/attempt2_failed/PLACEMENT_CARRIER_EXPORT.json","bytes":688,"sha256":"7a8941c90e1d82a74d4936f957b091ce87f8764d19ac20ba411cd84733035dcd"},{"source":"result/PUBLIC_CARRIER_EXPORT.json","published":"experiments/source_material_carrier_20261120/actual/attempt2_failed/PUBLIC_CARRIER_EXPORT.json","bytes":24005,"sha256":"107bf4fba7b57470418653459f67a85500a4720b9b9b969eecb26c974be5f27e"},{"source":"PUBLIC_CARRIER_EXPORT_FAILED_PRESERVATION.json","published":"experiments/source_material_carrier_20261120/actual/attempt2_failed/PUBLIC_CARRIER_EXPORT_FAILED_PRESERVATION.json","bytes":2600,"sha256":"6cdf95fcf274a79cdec992fd07a2c2ea5f4a0130b39909619b397d7e26b0af59"},{"source":"graphics-release.json","published":"experiments/source_material_carrier_20261120/actual/attempt2_failed/graphics-release.json","bytes":683,"sha256":"db43b179cff300c6fe0abb7154b389f372c716ff15ba8bda3bf823da4a409153"},{"source":"physical-closure.json","published":"experiments/source_material_carrier_20261120/actual/attempt2_failed/physical-closure.json","bytes":649,"sha256":"7d1e141a6236da54a6ca5b95167c0fe2c50b46bdb8918d6c286bc82a86effb4e"},{"source":"private-desktop.json","published":"experiments/source_material_carrier_20261120/actual/attempt2_failed/private-desktop.json","bytes":428,"sha256":"c50b190bc1a6c819dafaecaed5b361bbbf5f2bb68c2823690fd2886cae59de8d"}]},{"name":"source-material-carrier-run-1795222877275620300","safe_reports":[{"source":"result/PLACEMENT_CARRIER_EXPORT.json","published":"experiments/source_material_carrier_20261120/actual/attempt3_failed/PLACEMENT_CARRIER_EXPORT.json","bytes":688,"sha256":"7a8941c90e1d82a74d4936f957b091ce87f8764d19ac20ba411cd84733035dcd"},{"source":"result/PUBLIC_CARRIER_EXPORT.json","published":"experiments/source_material_carrier_20261120/actual/attempt3_failed/PUBLIC_CARRIER_EXPORT.json","bytes":24058,"sha256":"5794852f4c8a62be9f94a72362b8bc0a925704f5c4293a79222096277af7caf9"},{"source":"PUBLIC_CARRIER_EXPORT_FAILED_PRESERVATION.json","published":"experiments/source_material_carrier_20261120/actual/attempt3_failed/PUBLIC_CARRIER_EXPORT_FAILED_PRESERVATION.json","bytes":2598,"sha256":"25ef1d1dea3c275497ab16b8f8c8f2fd8d37f5840eab924f112c0112a6feb0a0"},{"source":"graphics-release.json","published":"experiments/source_material_carrier_20261120/actual/attempt3_failed/graphics-release.json","bytes":683,"sha256":"b23cb115ce469cd81b7349a814cc678b2db24ee5199fe9ff54e2b1800ed2148a"},{"source":"physical-closure.json","published":"experiments/source_material_carrier_20261120/actual/attempt3_failed/physical-closure.json","bytes":648,"sha256":"9cc91a53b1144adbc55964c19b08f4321a2b0405ca32639646e118d78c979b84"},{"source":"private-desktop.json","published":"experiments/source_material_carrier_20261120/actual/attempt3_failed/private-desktop.json","bytes":428,"sha256":"3ef0e5ef124ed665bf9f09c7539cdda063b5cdd47bf18ae53c6e404c2532232c"}]}]'
Add-Type -TypeDefinition @'
using System;using System.Runtime.InteropServices;using Microsoft.Win32.SafeHandles;
public static class CarrierCleanupIdentity {
 [StructLayout(LayoutKind.Sequential)] public struct Info {
  public uint Attributes,CreationLow,CreationHigh,AccessLow,AccessHigh,WriteLow,WriteHigh;
  public uint Volume,SizeHigh,SizeLow,Links,IndexHigh,IndexLow;
 }
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetFileInformationByHandle(SafeFileHandle h,out Info i);
 public static Info Read(SafeFileHandle h){Info i;if(!GetFileInformationByHandle(h,out i))throw new System.ComponentModel.Win32Exception();return i;}
}
'@
function Ancestors([string]$path) {
 $p=[IO.Path]::GetFullPath($path)
 while($p) {
  $item=Get-Item -LiteralPath $p -Force
  if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse point refused' }
  $parent=[IO.Directory]::GetParent($p)
  if ($null -eq $parent) { break };$p=$parent.FullName
 }
}
function Signature($i) {
 # Mask only the already-qualified volatile RECALL_ON_OPEN enumeration hint.
 @($i.Volume,$i.IndexHigh,$i.IndexLow,$i.SizeHigh,$i.SizeLow,$i.WriteHigh,$i.WriteLow,$i.Links,($i.Attributes -band 0xfffbffff)) -join ':'
}
function FileIdentity([string]$path) {
 Ancestors $path
 $item=Get-Item -LiteralPath $path -Force
 if ($item.PSIsContainer) { throw 'Regular file required' }
 $stream=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
 try {
  $before=[CarrierCleanupIdentity]::Read($stream.SafeFileHandle)
  if ($before.Links -ne 1 -or ($before.Attributes -band 0x400)) { throw 'Hardlink or reparse file refused' }
  $digest=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($stream)).ToLowerInvariant()
  $after=[CarrierCleanupIdentity]::Read($stream.SafeFileHandle)
  if ((Signature $before) -cne (Signature $after)) { throw 'File changed while hashing' }
  $again=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
  try { if ((Signature ([CarrierCleanupIdentity]::Read($again.SafeFileHandle))) -cne (Signature $before)) { throw 'File path identity changed' } }
  finally { $again.Dispose() }
 } finally { $stream.Dispose() }
 Ancestors $path
 $final=Get-Item -LiteralPath $path -Force
 if ($final.PSIsContainer -or $final.Length -ne $item.Length -or $final.LastWriteTimeUtc.Ticks -ne $item.LastWriteTimeUtc.Ticks) { throw 'Final file metadata changed' }
 [ordered]@{bytes=[long]$final.Length;mtime_ticks=$final.LastWriteTimeUtc.Ticks;identity=(Signature $before);sha256=$digest}
}
function JsonHash($value) {
 $bytes=[Text.Encoding]::UTF8.GetBytes((ConvertTo-Json -InputObject $value -Depth 20 -Compress))
 [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant()
}
function FreshClosed {
 $needle=$cleanupRoot.Replace('/','\').ToLowerInvariant()
 $processRows=@(Get-CimInstance Win32_Process)
 $owned=@($processRows | Where-Object {
  $_.ProcessId -ne $PID -and $_.Name -match '^(pythonw?|blender|godot[^\\]*|pwsh|powershell|ffmpeg|ffprobe)(\.exe)?$' -and
  $_.CommandLine -and $_.CommandLine.Replace('/','\').ToLowerInvariant().Contains($needle)
 })
 $ownedIds=[Collections.Generic.HashSet[uint32]]::new()
 foreach($process in $owned){[void]$ownedIds.Add([uint32]$process.ProcessId)}
 do {
  $added=$false
  foreach($process in $processRows){
   if($process.ProcessId -ne $PID -and $ownedIds.Contains([uint32]$process.ParentProcessId) -and $ownedIds.Add([uint32]$process.ProcessId)){$added=$true}
  }
 } while($added)
 if ($ownedIds.Count -ne 0) { throw 'Session runtime/test process or descendant remains; never kill a foreign process' }
 [ordered]@{format='has_carrier_cleanup_fresh_owned_process_observation_1';observed_utc=[DateTime]::UtcNow.ToString('o');owned_processes=0;excluded_exact_pid=$PID;root_lane_attested=$true;global_runtime_lease_proven=$false;process_rows_published=$false;processes_killed=$false;descendant_scope_checked=$true;missing_commandline_global_absence_proven=$false}
}
function Inventory([string]$path) {
 Ancestors $path
 $base=Get-Item -LiteralPath $path -Force
 if (-not $base.PSIsContainer) { throw 'Target directory required' }
 $queue=[Collections.Generic.Stack[string]]::new();$queue.Push($path);$rows=@();$directories=@()
 while ($queue.Count) {
  $directory=$queue.Pop()
  foreach($item in @(Get-ChildItem -LiteralPath $directory -Force)) {
   if (-not $item.FullName.StartsWith($path+'\',[StringComparison]::OrdinalIgnoreCase) -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Entry escaped target or is reparse' }
   if ($item.PSIsContainer) { $directories+=$item.FullName.Substring($path.Length+1);$queue.Push($item.FullName) }
   else { $rows+= [ordered]@{relative=$item.FullName.Substring($path.Length+1);file=(FileIdentity $item.FullName)} }
  }
 }
 $rows=@($rows | Sort-Object { $_.relative });$directories=@($directories | Sort-Object)
 [ordered]@{files=$rows.Count;directories=$directories.Count;logical_bytes=[long](($rows | ForEach-Object {$_.file.bytes} | Measure-Object -Sum).Sum);inventory_sha256=(JsonHash ([ordered]@{files=$rows;directories=$directories}))}
}
function OriginalState {
 @($originalPins | ForEach-Object {
  $id=FileIdentity (Join-Path $sourceFamily $_[0])
  if ($id.bytes -ne $_[1] -or $id.sha256 -cne $_[2]) { throw 'Protected original pin differs' }
  [ordered]@{relative=$_[0];file=$id}
 })
}
function FreshWrite([string]$path,$value) {
 Ancestors $ownedPrep
 $bytes=[Text.Encoding]::UTF8.GetBytes((ConvertTo-Json -InputObject $value -Depth 20)+[Environment]::NewLine)
 $stream=[IO.File]::Open($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
 try{$stream.Write($bytes,0,$bytes.Length)}finally{$stream.Dispose()}
}
Ancestors $cleanupRoot;Ancestors $ownedPrep
$remote=FileIdentity $receiptPath
if ($remote.sha256 -cne $receiptSha -or $remote.bytes -ne 153941) { throw 'Exact remote receipt required' }
$backup=Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
if ($backup.format -cne 'has_source_carrier_checkpoint_independent_remote_readback_1' -or $backup.commit -cne $backedCommit -or $backup.files -ne 529 -or $backup.total_bytes -ne 13503036 -or @($backup.entries).Count -ne 529) { throw 'Remote backup scope differs' }
foreach($key in @('remote_raw_SHA256_GitSHA1_length_all_exact','remote_path_blob_bindings_all_exact','independent_V8_hashes_and_golden_empty_check','independent_Node_crypto_local_raw_readback_all_exact','working_file_identities_stable_during_Node_read','main_ref_exact')) { if ($backup.$key -isnot [bool] -or $backup.$key -ne $true) { throw 'Remote proof flag missing' } }
$head=(& git -C $cleanupRoot rev-parse HEAD).Trim();if($LASTEXITCODE -ne 0 -or $head -notmatch '^[0-9a-f]{40}$'){throw 'Current head unavailable'}
& git -C $cleanupRoot merge-base --is-ancestor $backedCommit $head
if($LASTEXITCODE -ne 0){throw 'Backed checkpoint is not an ancestor'}
$originals=OriginalState
$records=@()
foreach($target in $targets) {
 $expected=[IO.Path]::GetFullPath((Join-Path $cleanupOutput $target.name))
 $resolved=(Resolve-Path -LiteralPath $expected).Path
 if ($resolved -cne $expected -or -not $resolved.StartsWith($cleanupOutput+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Resolved target boundary failed' }
 foreach($safe in $target.safe_reports) {
  $rows=@($backup.entries | Where-Object {$_.path -ceq $safe.published})
  if($rows.Count -ne 1 -or $rows[0].bytes -ne $safe.bytes -or $rows[0].sha256 -cne $safe.sha256){throw 'Published report missing from exact backup'}
  $published=FileIdentity (Join-Path $cleanupRoot $safe.published)
  $original=FileIdentity (Join-Path $resolved $safe.source)
  if($published.bytes -ne $safe.bytes -or $original.bytes -ne $safe.bytes -or $published.sha256 -cne $safe.sha256 -or $original.sha256 -cne $safe.sha256){throw 'Published/source safe report differs'}
  $blob=(& git -C $cleanupRoot rev-parse ($backedCommit+':'+$safe.published)).Trim()
  if($LASTEXITCODE -ne 0 -or $blob -cne $rows[0].git_sha1){throw 'Published proof Git blob differs'}
 }
 $records+= [ordered]@{name=$target.name;resolved=$resolved;safe_reports=6;inventory=(Inventory $resolved)}
}
$closed=FreshClosed
$plan=[ordered]@{format='has_ffed_backed_three_carrier_stage_cleanup_plan_1';backed_commit=$backedCommit;observed_head=$head;remote_receipt_sha256=$receiptSha;target_count=3;targets=$records;protected_originals=$originals;physical=$closed;no_other_stage_authorized=$true;free_space_gain_measured=$false}
if(-not $Execute){FreshWrite $planPath $plan;Write-Output '{"status":"PLAN_ONLY_NO_REMOVAL","targets":3}';exit 0}
$old=Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
if($old.format -cne $plan.format -or $old.backed_commit -cne $backedCommit -or (JsonHash $old.targets) -cne (JsonHash $records) -or (JsonHash $old.protected_originals) -cne (JsonHash $originals)){throw 'Plan inventories or originals changed'}
if(Test-Path -LiteralPath $resultPath){throw 'Result already exists'}
# Second complete inventory of ALL roots before the first removal.
foreach($record in $records){if((JsonHash (Inventory $record.resolved)) -cne (JsonHash $record.inventory)){throw 'Target changed since double inventory'}}
if((JsonHash (OriginalState)) -cne (JsonHash $originals)){throw 'Originals changed before removal'}
$closed=FreshClosed
$journal=[ordered]@{format='has_ffed_backed_three_carrier_stage_cleanup_result_1';status='IN_PROGRESS';backed_commit=$backedCommit;head=$head;remote_receipt_sha256=$receiptSha;physical=$closed;removed=@();protected_originals_unchanged=$false;free_space_gain_measured=$false}
$journalStream=[IO.File]::Open($resultPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
$journalIdentity=[CarrierCleanupIdentity]::Read($journalStream.SafeFileHandle)
if($journalIdentity.Links -ne 1 -or ($journalIdentity.Attributes -band 0x400)){$journalStream.Dispose();throw 'Unsafe journal handle'}
$journalStamp=Signature $journalIdentity
try {
 function SaveJournal {
  $before=[CarrierCleanupIdentity]::Read($journalStream.SafeFileHandle)
  if((Signature $before) -cne $script:journalStamp -or $before.Links -ne 1 -or ($before.Attributes -band 0x400)){throw 'Owned journal handle changed'}
  $bytes=[Text.Encoding]::UTF8.GetBytes((ConvertTo-Json -InputObject $journal -Depth 20)+[Environment]::NewLine)
  $journalStream.Position=0;$journalStream.SetLength(0);$journalStream.Write($bytes,0,$bytes.Length);$journalStream.Flush($true)
  $after=[CarrierCleanupIdentity]::Read($journalStream.SafeFileHandle)
  if($after.Volume -ne $journalIdentity.Volume -or $after.IndexHigh -ne $journalIdentity.IndexHigh -or $after.IndexLow -ne $journalIdentity.IndexLow -or $after.Links -ne 1 -or ($after.Attributes -band 0x400)){throw 'Owned journal identity lost'}
  $script:journalStamp=Signature $after
 }
 SaveJournal
foreach($record in $records){
 Ancestors $record.resolved
 if((JsonHash (Inventory $record.resolved)) -cne (JsonHash $record.inventory)){throw 'Target changed immediately before removal'}
 if(([DateTime]::UtcNow-[DateTime]::Parse($closed.observed_utc)).TotalSeconds -gt 60){$closed=FreshClosed;$journal.physical=$closed}
 Remove-Item -LiteralPath $record.resolved -Recurse -Force
 if(Test-Path -LiteralPath $record.resolved){throw 'Removal absence unconfirmed'}
 $journal.removed+=[ordered]@{name=$record.name;files=$record.inventory.files;logical_bytes=$record.inventory.logical_bytes;absence_confirmed=$true}
 SaveJournal
}
if((JsonHash (OriginalState)) -cne (JsonHash $originals)){throw 'Protected originals changed after removal'}
$journal.protected_originals_unchanged=$true;$journal.status='REMOVED_ONLY_THREE_FFED_BACKED_CARRIER_STAGES'
SaveJournal
Write-Output (ConvertTo-Json -InputObject @{status=$journal.status;targets=$journal.removed.Count;files=($journal.removed.files|Measure-Object -Sum).Sum;logical_bytes=($journal.removed.logical_bytes|Measure-Object -Sum).Sum} -Compress)

} finally { $journalStream.Dispose() }
