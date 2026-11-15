[CmdletBinding()]
param(
    [switch]$Execute,
    [string]$ExpectedPublishedCheckpoint = '',
    [string]$PublishedPlanGitPrefix = '',
    [string]$PublishedExecutorGitPrefix = '',
    [string]$ExpectedExecutorSha256 = '',
    [string]$ExpectedHelperSha256 = '',
    [switch]$LibraryOnly
)
# Default: reads source/Git/process metadata; creates one receipt in this new output.
# Execute: separately hash- and remotely published-checkpoint-gated individual files.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$sfWorkspace = 'C:\a\Programming\cloudflare\has-acceptance-session-20261111'
$sfHome = Join-Path $sfWorkspace 'output\sfm-v2-code-cleanup-executor-20261113'
$sfPlanHome = Join-Path $sfWorkspace 'output\sfm-v2-code-cleanup-plan-20261113'
$sfScope = Join-Path $sfWorkspace 'output\sfm-static-appearance-probe-20261113-v2\runs'
$sfPython = 'C:\Program Files\Python313\python.exe'
$sfRevision = 'e9cc7cfb20266b4863bde134bcb30457547a343d'
$sfPacketSha = '847609fa241f70f89c711a93ed0035a8a1fe69cf34bd998b9d418630db1cb70a'
$sfPlanSha = 'e65b408acdf63eade874709b6dc37de43b6c244ff3f9fe5fc11cab222c43fa8a'
$sfGzipSha = 'c772ec391c36db95b8a016125e41bc1588cdbc14ae542d6a64e66d66136f55a4'
$sfRuns = @('1794555713647050600-5718442689ac488f931dce81ca1c3101','1794556016763092400-40301e3c9fe24f5a9c7441715f6268ba')
$sfRoots = @($sfRuns | ForEach-Object { Join-Path $sfScope ($_+'\writer-source'); Join-Path $sfScope ($_+'\reader-source') })
$sfDirectories = @{}
$sfFileIds = @{}
$sfPlan = $null
$sfJournal = $null

function Assert-Sfm([bool]$Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Get-SfmPath([string]$Value) {
    Assert-Sfm ([IO.Path]::IsPathFullyQualified($Value) -and $Value -notmatch '[*?]' -and -not $Value.StartsWith('\\')) 'Only a literal local absolute path is allowed.'
    $full = [IO.Path]::GetFullPath($Value)
    if ($full.Length -gt [IO.Path]::GetPathRoot($full).Length) { $full = $full.TrimEnd([char[]]'\/') }
    return $full
}
function Test-SfmSamePath([string]$First, [string]$Second) {
    return [string]::Equals((Get-SfmPath $First),(Get-SfmPath $Second),[StringComparison]::OrdinalIgnoreCase)
}
function Assert-SfmRelative([string]$Value) {
    Assert-Sfm (-not [string]::IsNullOrEmpty($Value) -and -not [IO.Path]::IsPathRooted($Value) -and $Value -notmatch '[\\:*?"<>|]') 'Unsafe relative path.'
    foreach ($part in $Value.Split('/')) {
        Assert-Sfm ($part -ne '' -and $part -notin @('.','..') -and $part -notmatch '[. ]$' -and $part -notmatch '^(?i:CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(\.|$)') 'Unsafe Windows path component.'
    }
}
function Assert-SfmDigest([string]$Actual, [string]$Expected) {
    Assert-Sfm ($Expected -cmatch '^[a-f0-9]{64}$' -and $Actual -ceq $Expected) 'Exact SHA256 gate failed.'
}
function Assert-SfmMembership($Actual, $Expected, [string]$Label) {
    Assert-Sfm ($Actual.SetEquals($Expected)) ('Unexpected or missing tree membership: '+$Label)
}
function Assert-SfmNonuseResult($Result) {
    Assert-Sfm (@($Result.matching_processes).Count -eq 0 -and @($Result.unknown_live_owned_or_runtime_processes).Count -eq 0) 'Process nonuse gate refused: observed use or an inaccessible live owned/runtime process.'
}
function Get-SfmSha([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }

if (-not ('SfmCleanupNativeV1' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Globalization;
using System.Numerics;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Text;
using Microsoft.Win32.SafeHandles;
public static class SfmCleanupNativeV1 {
    [StructLayout(LayoutKind.Sequential)] struct FileId128 { public ulong Low; public ulong High; }
    [StructLayout(LayoutKind.Sequential)] struct FileIdInfo { public ulong Volume; public FileId128 Id; }
    [StructLayout(LayoutKind.Sequential)] struct BasicInfo {
        public IntPtr Reserved1, Peb, Reserved2a, Reserved2b, ProcessId, ParentId;
    }
    public sealed class Identity { public string Device; public string Inode; }
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern SafeFileHandle CreateFileW(string path, uint access, uint share, IntPtr security, uint creation, uint flags, IntPtr template);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool GetFileInformationByHandleEx(SafeFileHandle file, int infoClass, out FileIdInfo info, uint size);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern SafeProcessHandle OpenProcess(uint access, bool inherit, int processId);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool ReadProcessMemory(SafeProcessHandle process, IntPtr address, byte[] bytes, UIntPtr size, out UIntPtr read);
    [DllImport("advapi32.dll", SetLastError=true)]
    static extern bool OpenProcessToken(SafeProcessHandle process, uint access, out SafeAccessTokenHandle token);
    [DllImport("advapi32.dll", SetLastError=true)]
    static extern bool GetTokenInformation(SafeAccessTokenHandle token, int infoClass, IntPtr buffer, uint length, out uint returned);
    [DllImport("ntdll.dll", EntryPoint="NtQueryInformationProcess")]
    static extern int QueryBasic(SafeProcessHandle process, int infoClass, out BasicInfo info, int size, out int returned);
    [DllImport("ntdll.dll", EntryPoint="NtQueryInformationProcess")]
    static extern int QueryPointer(SafeProcessHandle process, int infoClass, out IntPtr info, int size, out int returned);
    static byte[] Read(SafeProcessHandle process, long address, int size) {
        if (address<=0 || size<=0 || size>32768) throw new InvalidOperationException("Invalid read-only process address/size.");
        byte[] bytes=new byte[size]; UIntPtr count;
        if (!ReadProcessMemory(process,new IntPtr(address),bytes,(UIntPtr)(uint)size,out count) || count.ToUInt64()!=(ulong)size)
            throw new Win32Exception(Marshal.GetLastWin32Error());
        return bytes;
    }
    public static Identity DirectoryIdentity(string path) {
        using (SafeFileHandle file=CreateFileW(path,0x80,0x7,IntPtr.Zero,3,0x02200000,IntPtr.Zero)) {
            if (file.IsInvalid) throw new Win32Exception(Marshal.GetLastWin32Error());
            FileIdInfo info;
            if (!GetFileInformationByHandleEx(file,18,out info,(uint)Marshal.SizeOf<FileIdInfo>())) throw new Win32Exception(Marshal.GetLastWin32Error());
            BigInteger inode=((BigInteger)info.Id.High<<64)+(BigInteger)info.Id.Low;
            return new Identity { Device=info.Volume.ToString(CultureInfo.InvariantCulture), Inode=inode.ToString(CultureInfo.InvariantCulture) };
        }
    }
    [StructLayout(LayoutKind.Sequential)] struct NativeFileTime { public uint Low, High; }
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool GetProcessTimes(SafeProcessHandle process, out NativeFileTime creation, out NativeFileTime exit, out NativeFileTime kernel, out NativeFileTime user);
    static void AssertCreation(SafeProcessHandle process, long expectedTicks) {
        NativeFileTime creation,exit,kernel,user;
        if (!GetProcessTimes(process,out creation,out exit,out kernel,out user)) throw new Win32Exception(Marshal.GetLastWin32Error());
        long ticks=DateTime.FromFileTimeUtc(((long)creation.High<<32)|creation.Low).Ticks;
        if (expectedTicks<=0 || ticks!=expectedTicks) throw new InvalidOperationException("PID creation identity changed; retained-handle read refused.");
    }
    public static string CurrentDirectory(int processId, long expectedCreationTicks) {
        if (IntPtr.Size!=8) throw new PlatformNotSupportedException("The verified preflight host must be64bit.");
        using (SafeProcessHandle process=OpenProcess(0x0410,false,processId)) {
            if (process.IsInvalid) throw new Win32Exception(Marshal.GetLastWin32Error());
            AssertCreation(process,expectedCreationTicks);
            BasicInfo basic; int returned;
            if (QueryBasic(process,0,out basic,Marshal.SizeOf<BasicInfo>(),out returned)!=0) throw new InvalidOperationException("Cannot query process basic information.");
            IntPtr wow;
            if (QueryPointer(process,26,out wow,IntPtr.Size,out returned)!=0) throw new InvalidOperationException("Cannot query process architecture.");
            bool narrow=wow!=IntPtr.Zero; long peb=narrow?wow.ToInt64():basic.Peb.ToInt64();
            byte[] pointer=Read(process,peb+(narrow?0x10:0x20),narrow?4:8);
            long parameters=narrow?(long)BitConverter.ToUInt32(pointer,0):BitConverter.ToInt64(pointer,0);
            byte[] current=Read(process,parameters+(narrow?0x24:0x38),narrow?8:16);
            int length=BitConverter.ToUInt16(current,0);
            if (length==0 || (length&1)!=0) throw new InvalidOperationException("Invalid current directory string.");
            long buffer=narrow?(long)BitConverter.ToUInt32(current,4):BitConverter.ToInt64(current,8);
            return Encoding.Unicode.GetString(Read(process,buffer,length));
        }
    }
    public static string OwnerSid(int processId, long expectedCreationTicks) {
        using (SafeProcessHandle process=OpenProcess(0x1000,false,processId)) {
            if (process.IsInvalid) throw new Win32Exception(Marshal.GetLastWin32Error());
            AssertCreation(process,expectedCreationTicks);
            SafeAccessTokenHandle token;
            if (!OpenProcessToken(process,0x8,out token)) throw new Win32Exception(Marshal.GetLastWin32Error());
            using (token) {
                uint needed; GetTokenInformation(token,1,IntPtr.Zero,0,out needed);
                if (needed<(uint)IntPtr.Size || needed>65536) throw new InvalidOperationException("Invalid read-only token information size.");
                IntPtr buffer=Marshal.AllocHGlobal((int)needed);
                try {
                    if (!GetTokenInformation(token,1,buffer,needed,out needed)) throw new Win32Exception(Marshal.GetLastWin32Error());
                    return new SecurityIdentifier(Marshal.ReadIntPtr(buffer)).Value;
                } finally { Marshal.FreeHGlobal(buffer); }
            }
        }
    }
}
'@
}


function Assert-SfmAncestors([string]$Path, [switch]$Directory) {
    $full = Get-SfmPath $Path
    $current = if ($Directory) { $full } else { [IO.Path]::GetDirectoryName($full) }
    while ($null -ne $current -and $current -ne '') {
        $item = Get-Item -LiteralPath $current -Force
        Assert-Sfm ($item.PSIsContainer -and ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) ('Reparse/non-directory ancestor: '+$current)
        $identity = [SfmCleanupNativeV1]::DirectoryIdentity($current)
        $value = $identity.Device+':'+$identity.Inode
        if ($sfDirectories.ContainsKey($current)) { Assert-Sfm ($sfDirectories[$current] -ceq $value) ('Directory replaced during invocation: '+$current) }
        else { $sfDirectories[$current] = $value }
        $parent = [IO.Path]::GetDirectoryName($current)
        if ($parent -eq $current) { break }
        $current = $parent
    }
}
function Assert-SfmFile($Entry, [switch]$Source, [switch]$Candidate) {
    $full = Get-SfmPath ([string]$Entry.path)
    if ($Source) {
        $project = Get-SfmPath ([string]$Entry.project)
        Assert-Sfm (@($sfRoots | Where-Object { Test-SfmSamePath $_ $project }).Count -eq 1) 'File project is outside the four exact roots.'
        Assert-SfmRelative ([string]$Entry.relative_path)
        Assert-Sfm (Test-SfmSamePath (Join-Path $project ([string]$Entry.relative_path).Replace('/','\')) $full) 'Absolute/relative file path mismatch.'
        Assert-Sfm ($full.StartsWith($project+'\',[StringComparison]::OrdinalIgnoreCase)) 'File escaped exact source root.'
        if ($Candidate) {
            $relative = [string]$Entry.relative_path
            foreach ($part in $relative.Split('/')) {
                Assert-Sfm ($part.ToLowerInvariant() -notin @('output','.godot','.git','__pycache__','generated','cache','caches','recovery','private-desktop','has-cache','reference-cache','profiles','userdata','user-data')) 'Retained runtime/generated/private path cannot be deleted.'
            }
            Assert-Sfm ($Entry.git_commit -ceq $sfRevision -and $Entry.git_path -ceq $relative -and $Entry.original_manifest_sha256 -ceq $Entry.sha256) 'Candidate Git/manifest context mismatch.'
            Assert-Sfm ($Entry.git_mode -in @('100644','100755') -and $Entry.git_oid -cmatch '^[a-f0-9]{40}$') 'Only an ordinary exact Git blob is eligible.'
        }
    } else {
        Assert-Sfm ($full.StartsWith($sfScope+'\',[StringComparison]::OrdinalIgnoreCase)) 'Protected evidence escaped fixed run scope.'
    }
    Assert-SfmAncestors $full
    $item = Get-Item -LiteralPath $full -Force
    Assert-Sfm (-not $item.PSIsContainer -and ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) ('Not a regular nonreparse file: '+$full)
    $identity = [SfmCleanupNativeV1]::DirectoryIdentity($full)
    $fileId = $identity.Device+':'+$identity.Inode
    if ($sfFileIds.ContainsKey($full)) { Assert-Sfm ($sfFileIds[$full] -ceq $fileId) ('File identity replaced: '+$full) }
    else { $sfFileIds[$full] = $fileId }
    $ticks = $item.LastWriteTimeUtc.Ticks
    $ns = [long](($ticks-621355968000000000L)*100L)
    Assert-Sfm ([long]$item.Length -eq [long]$Entry.bytes -and $ns -eq [long]$Entry.mtime_ns) ('File size/nsmtime changed: '+$full)
    Assert-SfmDigest (Get-SfmSha $full) ([string]$Entry.sha256)
    $item.Refresh()
    $afterId = [SfmCleanupNativeV1]::DirectoryIdentity($full)
    Assert-Sfm ($item.Exists -and -not $item.PSIsContainer -and ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0 -and [long]$item.Length -eq [long]$Entry.bytes -and $item.LastWriteTimeUtc.Ticks -eq $ticks -and ($afterId.Device+':'+$afterId.Inode) -ceq $fileId) ('File changed during verification: '+$full)
    Assert-SfmAncestors $full
}
function Get-SfmTree([string]$Root) {
    $pending = [Collections.Generic.Stack[string]]::new()
    $files = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $directories = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $pending.Push($Root)
    while ($pending.Count -gt 0) {
        $directory = $pending.Pop()
        Assert-SfmAncestors $directory -Directory
        foreach ($item in Get-ChildItem -LiteralPath $directory -Force) {
            Assert-Sfm (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) ('Reparse child refused: '+$item.FullName)
            $full = Get-SfmPath $item.FullName
            Assert-Sfm ($full.StartsWith($Root+'\',[StringComparison]::OrdinalIgnoreCase)) 'Enumerated child escaped exact source root.'
            if ($item.PSIsContainer) { Assert-Sfm ($directories.Add($full)) 'Duplicate/case-alias directory.'; $pending.Push($full) }
            else { Assert-Sfm ($files.Add($full)) 'Duplicate/case-alias file.' }
        }
    }
    return @{files=$files; directories=$directories}
}
function New-SfmPathSet($Entries, [string]$Property = 'path') {
    $set = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($entry in $Entries) {
        $value = if ($entry -is [string]) { [string]$entry } else { [string]$entry[$Property] }
        Assert-Sfm ($set.Add((Get-SfmPath $value))) 'Duplicate/case-alias membership entry.'
    }
    return ,$set
}
function Test-SfmTrees([switch]$After) {
    foreach ($project in $sfPlan.projects) {
        $tree = Get-SfmTree ([string]$project.source_root)
        $entries = if ($After) { @($project.retained_files) } else { @($project.candidate_files)+@($project.retained_files) }
        Assert-SfmMembership $tree.files (New-SfmPathSet $entries) ([string]$project.source_root)
        Assert-SfmMembership $tree.directories (New-SfmPathSet $project.directories_never_candidates) 'all original directories preserved exactly'
    }
}
function Test-SfmRetained {
    foreach ($project in $sfPlan.projects) { foreach ($entry in $project.retained_files) { Assert-SfmFile $entry -Source } }
    foreach ($entry in $sfPlan.protected_evidence) { Assert-SfmFile $entry }
    $sfReceipt.retained_recheck_passed = $true
}
function Get-SfmProcessUsage {
    $matches = [Collections.Generic.List[object]]::new()
    $unknown = [Collections.Generic.List[object]]::new()
    $inaccessible = [Collections.Generic.List[object]]::new()
    $checked = [Collections.Generic.List[object]]::new()
    $ownSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $rows = @(Get-CimInstance Win32_Process)
    Assert-Sfm ($rows.Count -gt 0) 'Empty process inventory cannot establish nonuse.'
    foreach ($row in $rows) {
        $processIdValue = [int]$row.ProcessId
        $createdTicks = if ($null -ne $row.CreationDate) { $row.CreationDate.ToUniversalTime().Ticks } else { 0L }
        $record = [ordered]@{process_id=$processIdValue; name=[string]$row.Name; created_utc=$null; native_creation_ticks=$null; snapshot_created_utc=if($createdTicks -ne 0){$row.CreationDate.ToUniversalTime().ToString('o')}else{$null}; owner_checked=$false; owned=$false; cwd_checked=$false; cwd=$null; limitation=$null}
        $command = if ($null -ne $row.CommandLine) { ([string]$row.CommandLine).Replace('/','\') } else { '' }
        $executable = if ($null -ne $row.ExecutablePath) { ([string]$row.ExecutablePath).Replace('/','\') } else { '' }
        $runtime = [string]$row.Name -match '^(python(w|[0-9.]*)?|godot.*|pwsh|powershell|cmd|blender|ffmpeg|7z|node|node_repl|git)\.exe$'
        foreach ($root in $sfRoots) {
            if ($command.IndexOf($root,[StringComparison]::OrdinalIgnoreCase) -ge 0 -or $executable.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)) {
                $matches.Add(@{process_id=$processIdValue; created_utc=$record.created_utc; name=$record.name; source=$root; evidence='snapshot command line or executable'})
            }
        }
        try {
            Assert-Sfm ($createdTicks -gt 0) 'Creation time unavailable.'
            # WMI truncates to microseconds; retained native reads use all100ns.
            # Require the native creation to map to the exact snapshot microsecond,
            # then compare its complete ticks inside each newly retained handle.
            $nativeTicks = (Get-Process -Id $processIdValue -ErrorAction Stop).StartTime.ToUniversalTime().Ticks
            Assert-Sfm (($nativeTicks-($nativeTicks % 10L)) -eq $createdTicks) 'PID changed between WMI snapshot and native identity acquisition.'
            $createdTicks=$nativeTicks
            $record.native_creation_ticks=$createdTicks
            $record.created_utc=[DateTime]::new($createdTicks,[DateTimeKind]::Utc).ToString('o')
            $owned = [SfmCleanupNativeV1]::OwnerSid($processIdValue,$createdTicks) -ceq $ownSid
            $record.owner_checked=$true; $record.owned=$owned
            if ($owned -or $runtime) {
                $cwd = Get-SfmPath ([SfmCleanupNativeV1]::CurrentDirectory($processIdValue,$createdTicks))
                $record.cwd_checked=$true; $record.cwd=$cwd
                foreach ($root in $sfRoots) {
                    if ((Test-SfmSamePath $cwd $root) -or $cwd.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)) {
                        $matches.Add(@{process_id=$processIdValue; created_utc=$record.created_utc; name=$record.name; source=$root; evidence='retained native process handle exact creation + current directory'})
                    }
                }
            } else { $record.limitation='Other-account non-runtime CWD not read; no universal file-handle nonuse claim.' }
        } catch {
            $record.limitation=$_.Exception.Message
            # Never treat a PID that was reused as the original process. A changed
            # live identity fails this snapshot; a demonstrably exited PID is logged.
            $live = Get-Process -Id $processIdValue -ErrorAction SilentlyContinue
            if ($null -ne $live) {
                $inaccessible.Add(@{process_id=$processIdValue; created_utc=$record.created_utc; name=$record.name; reason=$record.limitation})
                if ($record.owned -or $runtime -or (-not $record.owner_checked -and [int]$row.SessionId -eq [Diagnostics.Process]::GetCurrentProcess().SessionId)) {
                    $unknown.Add(@{process_id=$processIdValue; created_utc=$record.created_utc; name=$record.name; reason=$record.limitation})
                }
            } else { $record.limitation='Exited during snapshot; original read failure: '+$record.limitation }
        }
        $checked.Add($record)
    }
    $result = @{utc=[DateTime]::UtcNow.ToString('o'); processes_in_snapshot=$rows.Count; matching_processes=$matches.ToArray(); unknown_live_owned_or_runtime_processes=$unknown.ToArray(); inaccessible_processes=$inaccessible.ToArray(); checked_identities=$checked.ToArray(); stale_pid_exceptions_used=$false; all_open_file_handles_enumerated=$false; limitation='Scoped evidence: known historical writer Job closure plus fresh command/executable and exact creation-bound native CWD audit. Reader absence is not closure. Protected/other-account non-runtime process access and arbitrary file handles cannot be universally certified; inaccessible owned/runtime identities refuse. No process is killed.'}
    $sfReceipt.process_audit_count++
    # Keep initial and failed snapshots plus the last snapshot in the receipt;
    # the execute journal binds every successful scan to exact PID/native ticks.
    if ($sfReceipt.process_checks.Count -lt 2 -or $matches.Count -gt 0 -or $unknown.Count -gt 0) { $sfReceipt.process_checks.Add($result) }
    $sfReceipt.last_process_check=$result
    return $result
}
function Test-SfmFrozenArtifacts {
    Assert-SfmAncestors $sfHome -Directory
    Assert-SfmAncestors $sfPlanHome -Directory
    foreach ($item in @(@('PACKET.json',$sfPacketSha),@('PLAN.json.gz',$sfGzipSha),@('PLAN.json',$sfPlanSha))) {
        $path = Join-Path $sfPlanHome $item[0]
        Assert-SfmAncestors $path
        $file = Get-Item -LiteralPath $path -Force
        Assert-Sfm (-not $file.PSIsContainer -and ($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'Frozen artifact must be a regular nonreparse file.'
        Assert-SfmDigest (Get-SfmSha $path) $item[1]
    }
    Assert-SfmDigest (Get-SfmSha $PSCommandPath) $sfReceipt.executor_sha256
    Assert-SfmDigest (Get-SfmSha (Join-Path $sfHome 'verify-git.py')) $sfReceipt.helper_sha256
}

if ($LibraryOnly) { Assert-Sfm (-not $Execute) 'Library-only mode cannot execute cleanup.'; return }
$sfReport = Join-Path $sfHome ('receipt-'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffffffZ')+'-'+[Guid]::NewGuid().ToString('N')+'.json')
$sfReceipt = [ordered]@{format='has_sfm_v2_individual_cleanup_1'; mode=if($Execute){'EXECUTE'}else{'DRY_RUN'}; started_utc=[DateTime]::UtcNow.ToString('o'); status='RUNNING'; deletion_invoked=$false; deleted_files=0; deleted_bytes=0L; candidate_files_checked=0; retained_files_checked=0; retained_recheck_passed=$false; post_membership_passed=$false; directories_deleted=0; report_path=$sfReport; journal_path=$null; publication_status='UNRUN'; executor_sha256=$null; helper_sha256=$null; process_audit_count=0; process_checks=[Collections.Generic.List[object]]::new(); last_process_check=$null; errors=[Collections.Generic.List[string]]::new(); unrun=[Collections.Generic.List[string]]::new(); current_candidate=$null}
try {
    Assert-Sfm ($PSVersionTable.PSVersion.Major -ge 7 -and [Environment]::Is64BitProcess -and [Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT) '64-bit PowerShell7 on Windows is required.'
    Assert-Sfm (Test-SfmSamePath $PSScriptRoot $sfHome) 'Executor must run from its exact new owned output folder.'
    Assert-Sfm (-not (Test-Path -LiteralPath $sfReport)) 'Fresh receipt path required.'
    $sfReceipt.executor_sha256 = Get-SfmSha $PSCommandPath
    $sfReceipt.helper_sha256 = Get-SfmSha (Join-Path $sfHome 'verify-git.py')
    if ($Execute) {
        Assert-Sfm ($ExpectedPublishedCheckpoint -cmatch '^[a-f0-9]{40}$' -and $PublishedPlanGitPrefix -ne '' -and $PublishedExecutorGitPrefix -ne '') 'Execute needs exact reviewed published checkpoint and Git paths.'
        Assert-SfmDigest $sfReceipt.executor_sha256 $ExpectedExecutorSha256
        Assert-SfmDigest $sfReceipt.helper_sha256 $ExpectedHelperSha256
    }
    Test-SfmFrozenArtifacts
    Assert-Sfm (Test-SfmSamePath ([SfmCleanupNativeV1]::CurrentDirectory([Environment]::ProcessId,[Diagnostics.Process]::GetCurrentProcess().StartTime.ToUniversalTime().Ticks)) ([Environment]::CurrentDirectory)) 'Native CWD reader failed own-process self-test.'
    $sfPlan = Get-Content -LiteralPath (Join-Path $sfPlanHome 'PLAN.json') -Raw -Encoding utf8 | ConvertFrom-Json -AsHashtable -Depth 100
    Assert-Sfm ($sfPlan.format -ceq 'has_four_v2_git_code_cleanup_plan_1' -and $sfPlan.historical_source_commit -ceq $sfRevision -and $sfPlan.projects.Count -eq 4) 'Plan schema/revision/root count mismatch.'
    Assert-Sfm ($sfPlan.candidate_files -eq 4308 -and $sfPlan.candidate_bytes -eq 33607832L -and $sfPlan.retained_files -eq 2613 -and $sfPlan.retained_bytes -eq 68376831L) 'Frozen plan totals differ.'
    Assert-SfmMembership (New-SfmPathSet $sfPlan.projects 'source_root') (New-SfmPathSet $sfRoots) 'four exact source roots'
    foreach ($project in $sfPlan.projects) {
        Assert-Sfm ($project.run_id -cin $sfRuns -and $project.mode -cin @('writer','reader')) 'Unexpected historical run/mode.'
        Assert-Sfm (Test-SfmSamePath $project.source_root (Join-Path (Join-Path $sfScope $project.run_id) ($project.mode+'-source'))) 'Run/mode/root mismatch.'
        Assert-SfmFile $project.original_manifest
        if ($project.mode -ceq 'writer') {
            $closure = $project.historical_closure
            Assert-Sfm ($closure.status -ceq 'HISTORICAL_PRIVATE_JOB_AND_DESKTOP_CLOSED' -and $closure.receipt.job_closed -eq $true -and $closure.receipt.desktop_closed -eq $true -and $closure.receipt.foreground_child_observed -eq $false) 'Historical writer closure missing.'
            Assert-SfmFile $closure.receipt_identity
            Assert-SfmFile $closure.command_identity
            $actualReceipt = Get-Content -LiteralPath $closure.receipt_identity.path -Raw | ConvertFrom-Json -AsHashtable
            Assert-Sfm ($actualReceipt.job_closed -eq $true -and $actualReceipt.desktop_closed -eq $true -and $actualReceipt.foreground_child_observed -eq $false) 'Actual historical receipt does not attest closure.'
        } else {
            Assert-Sfm ($project.historical_closure.status -ceq 'NO_RETAINED_PHASE_COMMAND_OR_JOB_RECEIPT') 'Unexpected reader historical status.'
            Assert-Sfm (-not (Test-Path -LiteralPath (Join-Path (Join-Path $sfScope $project.run_id) 'reader\command.json'))) 'Previously absent reader phase command now exists; new review required.'
        }
    }
    $gitArguments = @('-B',(Join-Path $sfHome 'verify-git.py'))
    if ($Execute -or $ExpectedPublishedCheckpoint -ne '') {
        $gitArguments += @('--checkpoint',$ExpectedPublishedCheckpoint,'--plan-prefix',$PublishedPlanGitPrefix,'--executor-prefix',$PublishedExecutorGitPrefix,'--executor-sha',$ExpectedExecutorSha256,'--helper-sha',$ExpectedHelperSha256)
    }
    $gitOutput = & $sfPython @gitArguments
    Assert-Sfm ($LASTEXITCODE -eq 0) 'Exact raw Git/publication verification failed.'
    $sfReceipt.git_proof = ($gitOutput -join "`n") | ConvertFrom-Json -AsHashtable
    Assert-Sfm ($sfReceipt.git_proof.passed -eq $true -and $sfReceipt.git_proof.raw_plan_sha256 -ceq $sfPlanSha) 'Git proof does not match frozen plan.'
    $sfReceipt.publication_status=$sfReceipt.git_proof.publication_status
    if ($Execute) { Assert-Sfm ($sfReceipt.publication_status -ceq 'REMOTE_MAIN_REACHABLE_EXACT_ARTIFACTS_VERIFIED') 'Execute requires actual remote publication proof.' }
    [long]$candidateBytes=0; [long]$retainedBytes=0
    foreach ($project in $sfPlan.projects) {
        foreach ($entry in $project.candidate_files) { Assert-SfmFile $entry -Source -Candidate; $sfReceipt.candidate_files_checked++; $candidateBytes += [long]$entry.bytes }
        foreach ($entry in $project.retained_files) { Assert-SfmFile $entry -Source; $sfReceipt.retained_files_checked++; $retainedBytes += [long]$entry.bytes }
    }
    Assert-Sfm ($sfReceipt.candidate_files_checked -eq 4308 -and $candidateBytes -eq 33607832L -and $sfReceipt.retained_files_checked -eq 2613 -and $retainedBytes -eq 68376831L) 'Actual checked totals differ.'
    Test-SfmTrees
    Test-SfmRetained
    Assert-SfmNonuseResult (Get-SfmProcessUsage)
    Test-SfmFrozenArtifacts
    if (-not $Execute) {
        $sfReceipt.status='DRY_RUN_PASSED_NO_DELETION'
        if ($ExpectedPublishedCheckpoint -eq '') { $sfReceipt.unrun.Add('Publication checkpoint verification; no checkpoint supplied for read-only preparation.') }
        $sfReceipt.unrun.Add('All individual deletion and post-deletion checks; Execute not requested.')
    } else {
        # MUTATION BOUNDARY. Root alone invokes this after review/publication.
        # No directory, wildcard, recursive, move, kill, alternate-shell or retry branch.
        Assert-SfmNonuseResult (Get-SfmProcessUsage)
        Test-SfmTrees
        Test-SfmFrozenArtifacts
        $sfReceipt.journal_path=[IO.Path]::ChangeExtension($sfReport,'.jsonl')
        Assert-SfmAncestors $sfReceipt.journal_path
        $sfJournal=[IO.StreamWriter]::new([IO.FileStream]::new($sfReceipt.journal_path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read),[Text.UTF8Encoding]::new($false))
        foreach ($project in $sfPlan.projects) {
            foreach ($entry in $project.candidate_files) {
                $sfReceipt.current_candidate=$entry.path
                # Fresh native identity/CWD inventory before every individual deletion.
                $currentNonuse = Get-SfmProcessUsage
                Assert-SfmNonuseResult $currentNonuse
                Assert-SfmFile $entry -Source -Candidate
                Test-SfmFrozenArtifacts
                $exactAuditedIdentities = @($currentNonuse.checked_identities | Where-Object { $_.cwd_checked } | ForEach-Object { @($_.process_id,$_.native_creation_ticks) })
                $sfJournal.WriteLine((@{event='remove_intent'; path=$entry.path; sha256=$entry.sha256; bytes=$entry.bytes; mtime_ns=$entry.mtime_ns; nonuse_scan_utc=$currentNonuse.utc; exact_pid_creation_ticks=$exactAuditedIdentities; utc=[DateTime]::UtcNow.ToString('o')}|ConvertTo-Json -Depth 8 -Compress)); $sfJournal.Flush()
                $sfReceipt.deletion_invoked=$true
                Remove-Item -LiteralPath ([string]$entry.path) -ErrorAction Stop
                $sfReceipt.deleted_files++; $sfReceipt.deleted_bytes += [long]$entry.bytes
                Assert-Sfm (-not (Test-Path -LiteralPath ([string]$entry.path))) 'Deleted candidate immediately reappeared.'
                $sfJournal.WriteLine((@{event='remove_complete'; path=$entry.path; sha256=$entry.sha256; bytes=$entry.bytes; utc=[DateTime]::UtcNow.ToString('o')}|ConvertTo-Json -Compress)); $sfJournal.Flush()
            }
        }
        $sfReceipt.current_candidate=$null
        Test-SfmRetained
        Test-SfmTrees -After
        $sfReceipt.post_membership_passed=$true
        Assert-Sfm ($sfReceipt.deleted_files -eq 4308 -and $sfReceipt.deleted_bytes -eq 33607832L) 'Final exact removal totals differ.'
        $sfReceipt.status='COMPLETED_EXACT_INDIVIDUAL_FILES_RETAINED_AND_MEMBERSHIP_VERIFIED'
    }
} catch {
    $sfReceipt.status=if($sfReceipt.deletion_invoked){'STOPPED_AFTER_FAILURE_PARTIAL_CLEANUP'}else{'PREFLIGHT_FAILED_NO_DELETION'}
    $sfReceipt.errors.Add($_.Exception.Message)
    if ($sfReceipt.deletion_invoked -and $null -ne $sfPlan) {
        try { Test-SfmRetained } catch { $sfReceipt.errors.Add('Retained recheck failed: '+$_.Exception.Message) }
    }
    if (-not $sfReceipt.deletion_invoked) { $sfReceipt.unrun.Add('Individual deletion and all post-deletion proof remain unrun.') }
    throw
} finally {
    if ($null -ne $sfJournal) { $sfJournal.Dispose() }
    Assert-SfmAncestors $sfHome -Directory
    $sfReceipt.finished_utc=[DateTime]::UtcNow.ToString('o')
    $sfStream=[IO.FileStream]::new($sfReport,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
    $sfWriter=[IO.StreamWriter]::new($sfStream,[Text.UTF8Encoding]::new($false))
    try { $sfWriter.Write(($sfReceipt|ConvertTo-Json -Depth 30)); $sfWriter.WriteLine() } finally { $sfWriter.Dispose() }
    Write-Output $sfReport
}
