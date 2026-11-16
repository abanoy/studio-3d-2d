param(
    [Parameter(Mandatory=$true)][string]$Decision,
    [Parameter(Mandatory=$true)][switch]$Execute
)
$ErrorActionPreference='Stop'
$checkout='C:\a\Programming\cloudflare\has-acceptance-session-20261111'
$parent=Join-Path $checkout 'output\source-choices-native'
$literalRoots=@(
    'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\source-choices-native\1794615194930984000-ae0e0967',
    'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\source-choices-native\1794615438168999800-42f0686d'
)
if(-not $Execute){throw 'Explicit root execution required'}
$decisionPath=(Resolve-Path -LiteralPath $Decision).Path
if(-not $decisionPath.StartsWith(($checkout+'\output\'),[StringComparison]::OrdinalIgnoreCase)){throw 'Owned decision output required'}
$value=Get-Content -LiteralPath $decisionPath -Raw|ConvertFrom-Json -AsHashtable -DateKind String
if($value.format -ne 'has_root_old_native_cleanup_decision_1' -or $value.decision -ne 'REMOVE_EXACT_TWO_DISPOSABLE_ROOTS' -or $value.verified_backup_commit -notmatch '^[a-f0-9]{40}$'){throw 'Separate concrete root decision required'}
if(($value.literal_roots -join '|') -ne ($literalRoots -join '|')){throw 'Literal cleanup roots differ'}
if((Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $value.cleanup_script_sha256){throw 'Cleanup source differs from separate root decision'}
if($value.expected_files -ne 9307 -or $value.expected_directories -ne 1537 -or $value.expected_bytes -ne 1442187088){throw 'Exact old task scope required'}
foreach($name in @('remote_increment','remote_recovery','exclusive_probe','inventory_after','current_ownership','preserved_originals','source_catalogue','protected_review_tools')){
    $pin=$value.evidence[$name]
    if(-not $pin -or $pin.sha256 -notmatch '^[a-f0-9]{64}$' -or -not [IO.Path]::IsPathFullyQualified($pin.path)){throw 'Incomplete decision evidence'}
    if((Get-FileHash -LiteralPath $pin.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pin.sha256){throw 'Changed decision evidence'}
}
$remote=Get-Content -LiteralPath $value.evidence.remote_increment.path -Raw|ConvertFrom-Json -AsHashtable -DateKind String
$recovery=Get-Content -LiteralPath $value.evidence.remote_recovery.path -Raw|ConvertFrom-Json -AsHashtable -DateKind String
$probe=Get-Content -LiteralPath $value.evidence.exclusive_probe.path -Raw|ConvertFrom-Json -AsHashtable -DateKind String
$ownership=Get-Content -LiteralPath $value.evidence.current_ownership.path -Raw|ConvertFrom-Json -AsHashtable -DateKind String
$originals=Get-Content -LiteralPath $value.evidence.preserved_originals.path -Raw|ConvertFrom-Json -AsHashtable -DateKind String
if($remote.passed -ne $true -or $remote.remote_main_commit -ne $value.verified_backup_commit -or $recovery.passed -ne $true -or $recovery.publication_commit -ne $value.verified_backup_commit){throw 'Actual exact remote backup required'}
if($probe.passed -ne $true -or $probe.files_exclusively_opened_closed_verified -ne 9307 -or $probe.inventories_before_after_identical -ne $true -or $probe.cleanup_authorized -ne $false){throw 'Read-only access proof required; it is not cleanup authorization'}
if(($probe.literal_roots -join '|') -ne ($literalRoots -join '|')){throw 'Probe scope differs'}
if($ownership.format -ne 'has_root_old_native_current_ownership_1' -or $ownership.phase -ne 'BeforeRemoval' -or ($ownership.literal_roots -join '|') -ne ($literalRoots -join '|')){throw 'Fresh removal-phase ownership for these literal roots required'}
if($ownership.owned_runtime_commands_absent -ne $true -or $ownership.exact_old_coordinators_absent -ne $true -or $ownership.no_process_killed -ne $true){throw 'Actual current root process closure required'}
$ownershipAge=([DateTimeOffset]::UtcNow-[DateTimeOffset]::Parse($ownership.checked_utc)).TotalMinutes
if($ownershipAge -lt 0 -or $ownershipAge -gt 10){throw 'Current ownership observation expired or future-dated'}
if($originals.passed -ne $true){throw 'Protected original preservation required'}
$protected=Get-Content -LiteralPath $value.evidence.protected_review_tools.path -Raw|ConvertFrom-Json -AsHashtable -DateKind String
if($protected.format -ne 'has_protected_inputs_fresh_readonly_proof_1' -or $protected.passed -ne $true -or $protected.originals.files -ne 561 -or $protected.shared_runtime_executables -ne 6 -or $protected.original_SourceIO_files -ne 574 -or $protected.installed_exporter_noncache_sources -ne 120 -or $protected.current_review.shipped_files -ne 5844 -or $protected.functional_source_files -ne 1008){throw 'Fresh complete protected review/tool/original preservation required'}
if($value.evidence.preserved_originals.sha256 -ne $value.evidence.protected_review_tools.sha256 -or -not $value.evidence.preserved_originals.path.Equals($value.evidence.protected_review_tools.path,[StringComparison]::OrdinalIgnoreCase)){throw 'Both preservation aliases must bind the same fresh combined proof'}
$protectionStart=[DateTimeOffset]::Parse($protected.started_utc)
$protectionFinish=[DateTimeOffset]::Parse($protected.finished_utc)
if($protectionStart -lt [DateTimeOffset]::Parse($remote.observed_utc) -or $protectionStart -lt [DateTimeOffset]::Parse($recovery.finished_utc) -or $protectionFinish -lt $protectionStart -or $protectionFinish -gt [DateTimeOffset]::UtcNow){throw 'Protection must be freshly measured after both remote readbacks'}
$catalogue=Get-Content -LiteralPath $value.evidence.source_catalogue.path -Raw|ConvertFrom-Json -AsHashtable -DateKind String
if($value.evidence.source_catalogue.sha256 -ne '8d9e7d94c745081e0ca084bc64e7498bc7ccb218c44209e1354bcd53f3c50a2a'){throw 'Unqualified source catalogue'}
if($catalogue.source_sha256.Count -ne 1008){throw 'Exact functional source catalogue required'}
foreach($relative in $catalogue.source_sha256.Keys){
    $source=Join-Path $checkout $relative
    if((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $catalogue.source_sha256[$relative]){throw 'Current functional source differs'}
}
$inventoryPath=Join-Path (Split-Path -Parent $value.evidence.exclusive_probe.path) 'inventory-after.json'
if(-not $inventoryPath.Equals($value.evidence.inventory_after.path,[StringComparison]::OrdinalIgnoreCase)){throw 'Exact pinned probe sibling inventory required'}
$inventory=Get-Content -LiteralPath $inventoryPath -Raw|ConvertFrom-Json -AsHashtable -DateKind String
Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
public static class HasOldNativeCleanupIdentity {
    [StructLayout(LayoutKind.Sequential)] public struct Stamp { public uint lo, hi; }
    [StructLayout(LayoutKind.Sequential)] public struct Info {
        public uint attrs; public Stamp created, accessed, written;
        public uint volume, sizeHi, sizeLo, links, indexHi, indexLo;
    }
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern IntPtr CreateFileW(string path, uint access, uint share, IntPtr security,
        uint disposition, uint flags, IntPtr template);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool GetFileInformationByHandle(IntPtr handle, out Info info);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool CloseHandle(IntPtr handle);
    public static Info Read(string path) {
        // FILE_READ_ATTRIBUTES only, shared access; this never requests write,
        // delete or disposition permission. Fresh exclusive-read proof is separate.
        IntPtr handle=CreateFileW(@"\\?\"+path,0x80,7,IntPtr.Zero,3,0x00200000,IntPtr.Zero);
        if(handle==new IntPtr(-1)) throw new Win32Exception(Marshal.GetLastWin32Error());
        try {
            Info info;
            if(!GetFileInformationByHandle(handle,out info)) throw new Win32Exception(Marshal.GetLastWin32Error());
            return info;
        } finally {
            if(!CloseHandle(handle)) throw new Win32Exception(Marshal.GetLastWin32Error());
        }
    }
    public static ulong Index(Info info) { return ((ulong)info.indexHi<<32)|info.indexLo; }
}
'@
$scopes=@(@{phase='core14';files=4707;directories=791;bytes=387640663},@{phase='wider11';files=4600;directories=746;bytes=1054546425})
$validated=@()
for($i=0;$i -lt $literalRoots.Count;$i++){
    $literal=$literalRoots[$i]
    $resolved=(Resolve-Path -LiteralPath $literal).Path
    if(-not $resolved.Equals($literal,[StringComparison]::OrdinalIgnoreCase) -or -not (Split-Path -Parent $resolved).Equals($parent,[StringComparison]::OrdinalIgnoreCase)){throw 'Resolved absolute removal boundary differs'}
    $ancestor=Get-Item -LiteralPath $resolved -Force
    while($null -ne $ancestor){
        if($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Reparse ancestor refused'}
        $ancestor=$ancestor.Parent
    }
    $members=@(Get-ChildItem -LiteralPath $resolved -Recurse -Force)
    if(@($members|Where-Object {$_.Attributes -band [IO.FileAttributes]::ReparsePoint}).Count){throw 'Reparse member refused'}
    $files=@($members|Where-Object {-not $_.PSIsContainer})
    $directories=@($members|Where-Object {$_.PSIsContainer})
    $scope=$scopes[$i]
    $expected=$inventory[$scope.phase]
    if($files.Count -ne $scope.files -or $directories.Count -ne $scope.directories -or $expected.files.Count -ne $scope.files){throw 'Current membership differs'}
    $total=[long]0
    foreach($file in $files){
        $name=$file.FullName.Substring($resolved.Length+1).Replace('\','/')
        $pin=$expected.files[$name]
        if(-not $pin -or $file.Length -ne $pin.bytes){throw 'Unexpected current file/size'}
        $beforeTime=$file.LastWriteTimeUtc
        if((Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pin.sha256){throw 'Current disposable file hash differs'}
        $file.Refresh()
        $mtimeNs=([long]$file.LastWriteTimeUtc.ToFileTimeUtc()-[long]116444736000000000)*[long]100
        if($file.Length -ne $pin.bytes -or $file.LastWriteTimeUtc -ne $beforeTime -or $mtimeNs -ne $pin.mtime_ns){throw 'Current disposable file stamp differs'}
        $native=[HasOldNativeCleanupIdentity]::Read($file.FullName)
        if($pin.hardlinks -ne 1 -or $native.links -ne 1 -or ($native.attrs -band 0x410) -ne 0 -or [HasOldNativeCleanupIdentity]::Index($native) -ne [ulong]$pin.stat_inode){throw 'Current single-link regular native identity differs'}
        $total+=$file.Length
    }
    foreach($directory in $directories){
        $name=$directory.FullName.Substring($resolved.Length+1).Replace('\','/')
        if(-not $expected.directories_including_root.ContainsKey($name)){throw 'Unexpected directory'}
    }
    if($total -ne $scope.bytes){throw 'Current disposable bytes differ'}
    $validated+=@{path=$resolved;phase=$scope.phase;files=$files.Count;directories=$directories.Count;bytes=$total}
}
$resultPath=Join-Path $checkout 'output\old-native-cleanup-actual-20261115.json'
if(Test-Path -LiteralPath $resultPath){throw 'Preserve previous cleanup receipt'}
$ownershipAge=([DateTimeOffset]::UtcNow-[DateTimeOffset]::Parse($ownership.checked_utc)).TotalMinutes
if($ownershipAge -lt 0 -or $ownershipAge -gt 10){throw 'Ownership observation expired during validation; retain roots'}
$removed=@()
$failure=$null
foreach($entry in $validated){
    try{
        $ownershipAge=([DateTimeOffset]::UtcNow-[DateTimeOffset]::Parse($ownership.checked_utc)).TotalMinutes
        if($ownershipAge -lt 0 -or $ownershipAge -gt 10){throw 'Ownership observation expired before this literal removal'}
        # Native PowerShell end-to-end; both resolved literal targets were fully
        # validated before either recursive removal. No cross-shell path list.
        Remove-Item -LiteralPath $entry.path -Recurse -Force -ErrorAction Stop
        if(Test-Path -LiteralPath $entry.path){throw 'Removal did not finish'}
        $removed+=$entry
    }catch{
        $failure=$_.Exception.Message
        break
    }
}
$reclaimed=[long]0
foreach($entry in $removed){$reclaimed+=$entry.bytes}
$receipt=@{format='has_root_old_native_cleanup_actual_1';passed=($removed.Count -eq 2 -and $null -eq $failure);checked_utc=[DateTime]::UtcNow.ToString('o');verified_backup_commit=$value.verified_backup_commit;decision_path=$decisionPath;decision_sha256=(Get-FileHash -LiteralPath $decisionPath -Algorithm SHA256).Hash.ToLowerInvariant();validated=$validated;removed=$removed;removed_roots=$removed.Count;fully_removed_files=(@($removed|Measure-Object -Property files -Sum)[0].Sum);reclaimed_bytes=$reclaimed;reclaimed_bytes_scope='Logical bytes in fully removed roots only; physical allocated disk blocks are not measured';partial_removal_unmeasured=($null -ne $failure);failure=$failure;originals_installed_tools_newer_runs_reviews_recovery_removed=$false;no_process_killed=$true}
$receipt|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $resultPath
$receipt|ConvertTo-Json -Depth 12
if(-not $receipt.passed){throw 'Cleanup incomplete; inspect exact retained evidence before further action'}
