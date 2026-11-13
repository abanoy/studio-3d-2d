[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-fA-F0-9]{64}$')]
    [string]$ExpectedPlanSha256,
    [switch]$Execute
)

# Default is read-only preflight. The sole deletion command is inside the
# explicitly requested Execute branch, after every preflight check succeeds.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$rbRequiredPlanSha = '2030b3c4f6b838fa874a2cb93ad2a990f6b6d14d8e2088138f9c6065cf7c08ab'
$rbPublishedCheckpoint = 'c6782d2f0f7b6ebbe868214ceb975e42afd129dd'
$rbWorkspaceRoot = 'C:\a\Programming\cloudflare\has-acceptance-session-20261111'
$rbOutputRoot = Join-Path $rbWorkspaceRoot 'output'
$rbScopeRoot = Join-Path $rbOutputRoot 'native-readback-lifecycle'
$rbPlanPath = Join-Path $rbOutputRoot 'readback-reconstructible-cleanup-plan-20261112.json'
$rbGitHelper = Join-Path $rbOutputRoot 'verify-readback-cleanup-git-recipes-20261112.py'
$rbPython = 'C:\Program Files\Python313\python.exe'
$rbAllowedNonces = @(
    '1794518904450251700','1794518972504964900','1794519038987472200',
    '1794519164817658300','1794519222461088800','1794519379862095400',
    '1794519479391580800','1794519635389990600','1794519700574817300',
    '1794519720433512700','1794520506647727000','1794520570736123000',
    '1794520812223244900'
)
$rbProtectedNonces = @('1794522587152585700','1794523812750198700')
# Root independently reviewed these five protected desktop/input helper identities.
# These are exact PID + executable name + creation-time observations, not a name
# allowlist. They may be excluded only while command/executable paths are unreadable
# and native CWD inspection fails with access denied. No session runtime is exempt.
$rbProtectedOwnedCwdExceptions = @(
    @{ process_id=13228; name='DefenderSessionHelper.exe'; created_utc='2026-11-13T02:30:45.1630040Z' },
    @{ process_id=13532; name='logioptionsplus_appbroker.exe'; created_utc='2026-11-13T02:30:47.2577220Z' },
    @{ process_id=15132; name='aihost.exe'; created_utc='2026-11-13T02:30:48.6619190Z' },
    @{ process_id=4876; name='ctfmon.exe'; created_utc='2026-11-13T02:30:57.2708490Z' },
    @{ process_id=2592; name='TabTip.exe'; created_utc='2026-11-13T02:30:57.2793970Z' }
)
$rbAllowedSources = @{}
foreach ($rbNonceValue in $rbAllowedNonces) {
    $rbAllowedSources[$rbNonceValue] = Join-Path (Join-Path $rbScopeRoot $rbNonceValue) 'shipped-source'
}
$rbRunId = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffffffZ') + '-' + [Guid]::NewGuid().ToString('N')
$rbMode = if ($Execute.IsPresent) { 'execution' } else { 'preflight' }
$rbReportPath = Join-Path $rbOutputRoot ('readback-reconstructible-cleanup-' + $rbMode + '-' + $rbRunId + '.json')
$rbJournalPath = Join-Path $rbOutputRoot ('readback-reconstructible-cleanup-' + $rbMode + '-' + $rbRunId + '.jsonl')
$rbReceipt = [ordered]@{
    format = 'has_native_powershell_individual_cleanup_1'
    mode = $rbMode
    execute_requested = $Execute.IsPresent
    deletion_invoked = $false
    status = 'preflight_running'
    started_utc = (Get-Date).ToUniversalTime().ToString('o')
    plan_path = $rbPlanPath
    expected_plan_sha256 = $ExpectedPlanSha256.ToLowerInvariant()
    required_plan_sha256 = $rbRequiredPlanSha
    published_checkpoint = $rbPublishedCheckpoint
    report_path = $rbReportPath
    journal_path = $null
    planned_files = 16875
    planned_bytes = 224835913
    checked_candidate_files = 0
    checked_retained_source_files = 0
    checked_parent_evidence_files = 0
    checked_directories = 0
    deleted_files = 0
    deleted_bytes = 0L
    failed_files = 0
    current_candidate = $null
    retained_recheck_passed = $false
    no_directories_deleted = $true
    no_copy_move_archive_upload = $true
    all_unlisted_paths_excluded = $true
    process_checks = [System.Collections.Generic.List[object]]::new()
    errors = [System.Collections.Generic.List[string]]::new()
}
$rbPlan = $null
$rbDirectoryProofs = @{}
$rbKnownSources = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$rbKnownKeep = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)

function Assert-Readback([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}
function Get-ReadbackFullPath([string]$PathValue) {
    Assert-Readback ([IO.Path]::IsPathFullyQualified($PathValue)) ('Absolute path required: ' + $PathValue)
    $full = [IO.Path]::GetFullPath($PathValue)
    $drive = [IO.Path]::GetPathRoot($full)
    if ($full.Length -gt $drive.Length) { $full = $full.TrimEnd([char[]]'\/') }
    return $full
}
function Test-ReadbackSamePath([string]$First, [string]$Second) {
    return [string]::Equals((Get-ReadbackFullPath $First), (Get-ReadbackFullPath $Second), [StringComparison]::OrdinalIgnoreCase)
}
function Assert-ReadbackReportPath([string]$PathValue) {
    $full = Get-ReadbackFullPath $PathValue
    Assert-Readback (Test-ReadbackSamePath ([IO.Path]::GetDirectoryName($full)) $rbOutputRoot) 'Reports must stay directly inside this owned output folder.'
    Assert-Readback ([IO.Path]::GetFileName($full).StartsWith('readback-reconstructible-cleanup-', [StringComparison]::Ordinal)) 'Unexpected report filename.'
}
function Write-ReadbackReceipt {
    Assert-ReadbackReportPath $rbReportPath
    $rbReceipt.finished_or_updated_utc = (Get-Date).ToUniversalTime().ToString('o')
    $rbReceipt | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $rbReportPath -Encoding utf8NoBOM
}

# Read-only native identity/CWD inspection. No mutation APIs or DELETE access.
if (-not ('ReadbackCleanupNativeV1' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Globalization;
using System.Numerics;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Text;
using Microsoft.Win32.SafeHandles;
public static class ReadbackCleanupNativeV1 {
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
    public static string CurrentDirectory(int processId) {
        if (IntPtr.Size!=8) throw new PlatformNotSupportedException("The verified preflight host must be64bit.");
        using (SafeProcessHandle process=OpenProcess(0x0410,false,processId)) {
            if (process.IsInvalid) throw new Win32Exception(Marshal.GetLastWin32Error());
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
    public static string OwnerSid(int processId) {
        using (SafeProcessHandle process=OpenProcess(0x1000,false,processId)) {
            if (process.IsInvalid) throw new Win32Exception(Marshal.GetLastWin32Error());
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

function Assert-ReadbackDirectory([string]$PathValue) {
    $full = Get-ReadbackFullPath $PathValue
    Assert-Readback ($rbDirectoryProofs.ContainsKey($full)) ('Directory absent from the exact plan: ' + $full)
    $item = Get-Item -LiteralPath $full -Force
    Assert-Readback ($item.PSIsContainer -and (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0)) ('Non-directory or reparse path: ' + $full)
    $expected = $rbDirectoryProofs[$full]
    $identity = [ReadbackCleanupNativeV1]::DirectoryIdentity($full)
    $device = ([System.Numerics.BigInteger]$expected.device).ToString([Globalization.CultureInfo]::InvariantCulture)
    $inode = ([System.Numerics.BigInteger]$expected.inode).ToString([Globalization.CultureInfo]::InvariantCulture)
    Assert-Readback ($identity.Device -eq $device -and $identity.Inode -eq $inode) ('Directory identity changed: ' + $full)
}
function Assert-ReadbackAncestors([string]$FilePath) {
    $directory = [IO.Path]::GetDirectoryName((Get-ReadbackFullPath $FilePath))
    while ($true) {
        Assert-ReadbackDirectory $directory
        if (Test-ReadbackSamePath $directory $rbWorkspaceRoot) { break }
        Assert-Readback ($directory.StartsWith($rbWorkspaceRoot + '\', [StringComparison]::OrdinalIgnoreCase)) 'An ancestor escaped the owned workspace.'
        $directory = [IO.Path]::GetDirectoryName($directory)
    }
}
function Assert-ReadbackFile($Entry, [switch]$Candidate, [switch]$ParentEvidence) {
    $full = Get-ReadbackFullPath ([string]$Entry.path)
    Assert-Readback ($rbAllowedSources.ContainsKey([string]$Entry.nonce)) ('Unlisted/protected nonce: ' + [string]$Entry.nonce)
    $source = Get-ReadbackFullPath $rbAllowedSources[[string]$Entry.nonce]
    if ($ParentEvidence.IsPresent) {
        Assert-Readback (Test-ReadbackSamePath ([IO.Path]::GetDirectoryName($full)) ([IO.Path]::GetDirectoryName($source))) 'Parent evidence escaped its explicit nonce folder.'
    } else {
        Assert-Readback ($full.StartsWith($source + '\', [StringComparison]::OrdinalIgnoreCase)) ('File escaped its exact source folder: ' + $full)
        Assert-Readback (-not (Test-ReadbackSamePath $full $source)) 'A source directory cannot be a file target.'
    }
    if ($Candidate.IsPresent) {
        Assert-Readback (Test-ReadbackSamePath ([string]$Entry.source_root) $source) 'Candidate source_root mismatch.'
        $relative = [string]$Entry.relative_path
        Assert-Readback (-not [IO.Path]::IsPathRooted($relative) -and $relative -notmatch '(^|/)\.\.?(/|$)|:|\\') 'Unsafe candidate relative path.'
        $joined = Join-Path $source ($relative.Replace('/', '\'))
        Assert-Readback (Test-ReadbackSamePath $joined $full) 'Candidate path/relative-path mismatch.'
        Assert-Readback ($Entry.category -in @('reconstructible_source','regenerable_python_bytecode')) 'Unknown deletion category.'
        if ($Entry.category -eq 'regenerable_python_bytecode') {
            Assert-Readback ($relative -ceq '__pycache__/run.cpython-313.pyc' -and $null -eq $Entry.git_object) 'Unexpected cache deletion target.'
        }
    }
    Assert-ReadbackAncestors $full
    $item = Get-Item -LiteralPath $full -Force
    Assert-Readback (-not $item.PSIsContainer -and (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0)) ('Non-regular or reparse file: ' + $full)
    Assert-Readback ([long]$item.Length -eq [long]$Entry.bytes) ('File size changed: ' + $full)
    $beforeTicks = $item.LastWriteTimeUtc.Ticks
    $hash = (Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash.ToLowerInvariant()
    $item.Refresh()
    Assert-Readback ([long]$item.Length -eq [long]$Entry.bytes -and $item.LastWriteTimeUtc.Ticks -eq $beforeTicks) ('File changed during verification: ' + $full)
    Assert-Readback ($hash -ceq [string]$Entry.sha256) ('File SHA256 changed: ' + $full)
    $writeNs = [long](($beforeTicks - 621355968000000000L) * 100L)
    Assert-Readback ($writeNs -eq [long]$Entry.mtime_ns) ('File modification time changed: ' + $full)
}
function Get-ReadbackTreePaths([string]$Source) {
    $pending = [System.Collections.Generic.Stack[string]]::new()
    $result = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $pending.Push($Source)
    while ($pending.Count -gt 0) {
        $directory = $pending.Pop(); Assert-ReadbackDirectory $directory
        foreach ($item in Get-ChildItem -LiteralPath $directory -Force) {
            Assert-Readback (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) ('Reparse child refused: ' + $item.FullName)
            if ($item.PSIsContainer) { $pending.Push($item.FullName) }
            else { Assert-Readback ($result.Add((Get-ReadbackFullPath $item.FullName))) 'Case-colliding source paths.' }
        }
    }
    return ,$result
}
function Get-ReadbackProcessUsage([switch]$RecordOnly) {
    $usageMatches = [System.Collections.Generic.List[object]]::new()
    $usageUnknown = [System.Collections.Generic.List[object]]::new()
    $ownershipUnreadable = [System.Collections.Generic.List[object]]::new()
    $reviewedCwdExclusions = [System.Collections.Generic.List[object]]::new()
    $ownSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $inspected = 0
    $otherOwners = 0
    $processCount = 0
    foreach ($processRow in Get-CimInstance Win32_Process) {
        $processCount++
        $processIdValue = [int]$processRow.ProcessId
        $commandValue = if ($null -eq $processRow.CommandLine) { '' } else { ([string]$processRow.CommandLine).Replace('/', '\') }
        $executableValue = if ($null -eq $processRow.ExecutablePath) { '' } else { ([string]$processRow.ExecutablePath).Replace('/', '\') }
        foreach ($source in $rbAllowedSources.Values) {
            if ($commandValue.IndexOf($source, [StringComparison]::OrdinalIgnoreCase) -ge 0 -or $executableValue.StartsWith($source + '\', [StringComparison]::OrdinalIgnoreCase)) {
                $usageMatches.Add(@{ process_id = $processIdValue; name = $processRow.Name; source = $source; evidence = 'command_line_or_executable_path' })
            }
        }
        $owned = $false
        try { $owned = [ReadbackCleanupNativeV1]::OwnerSid($processIdValue) -ceq $ownSid }
        catch {
            if ($null -ne (Get-Process -Id $processIdValue -ErrorAction SilentlyContinue)) {
                $ownershipUnreadable.Add(@{ process_id = $processIdValue; name = $processRow.Name; session_id = $processRow.SessionId; reason = $_.Exception.Message })
                if ([string]$processRow.Name -match '^(python(w|[0-9.]*)?|godot.*|pwsh|powershell|cmd|blender|ffmpeg|7z|node|node_repl|git)\.exe$') {
                    $usageUnknown.Add(@{ process_id = $processIdValue; name = $processRow.Name; reason = 'Runtime/shell ownership could not be established.' })
                }
            }
        }
        if ($owned) {
            $inspected++
            try {
                $cwd = Get-ReadbackFullPath ([ReadbackCleanupNativeV1]::CurrentDirectory($processIdValue))
                foreach ($source in $rbAllowedSources.Values) {
                    if (Test-ReadbackSamePath $cwd $source) { $usageMatches.Add(@{ process_id = $processIdValue; name = $processRow.Name; source = $source; evidence = 'current_directory' }) }
                    elseif ($cwd.StartsWith($source + '\', [StringComparison]::OrdinalIgnoreCase)) { $usageMatches.Add(@{ process_id = $processIdValue; name = $processRow.Name; source = $source; evidence = 'current_directory_descendant' }) }
                }
            } catch {
                $cwdReadFailure = $_.Exception
                if ($null -ne (Get-Process -Id $processIdValue -ErrorAction SilentlyContinue)) {
                    $reviewedException = $false
                    $accessDenied = $cwdReadFailure.InnerException -is [ComponentModel.Win32Exception] -and $cwdReadFailure.InnerException.NativeErrorCode -eq 5
                    foreach ($exceptionIdentity in $rbProtectedOwnedCwdExceptions) {
                        $expectedCreated = [DateTimeOffset]::Parse($exceptionIdentity.created_utc, [Globalization.CultureInfo]::InvariantCulture).UtcDateTime
                        if ($accessDenied -and $processIdValue -eq $exceptionIdentity.process_id -and [string]$processRow.Name -ceq $exceptionIdentity.name -and $processRow.CreationDate.ToUniversalTime().Ticks -eq $expectedCreated.Ticks -and $commandValue -eq '' -and $executableValue -eq '') {
                            $reviewedException = $true
                            $reviewedCwdExclusions.Add(@{ process_id=$processIdValue; name=$processRow.Name; created_utc=$expectedCreated.ToString('o'); reason='Exact protected helper identity independently reviewed by root; unreadable CWD/command/executable. No arbitrary file-handle freedom asserted.' })
                        }
                    }
                    if (-not $reviewedException) { $usageUnknown.Add(@{ process_id = $processIdValue; name = $processRow.Name; reason = $cwdReadFailure.Message }) }
                }
            }
        } else { $otherOwners++ }
    }
    $check = @{ utc = (Get-Date).ToUniversalTime().ToString('o'); processes_in_snapshot = $processCount; owned_current_directories_attempted = $inspected; other_or_unreadable_owners_excluded_from_cwd = $otherOwners; ownership_unreadable = $ownershipUnreadable.ToArray(); exact_root_reviewed_protected_helper_exclusions=$reviewedCwdExclusions.ToArray(); matching_processes = $usageMatches.ToArray(); unknown_live_owned_or_runtime_processes = $usageUnknown.ToArray(); command_lines_examined_for_all_processes = $true; all_open_file_handles_enumerated = $false; scope='Absence of observed session/test use of the thirteen old source copies.'; limitation = 'CWD inspection covers positively identified current-account processes except the exact independently reviewed protected helper identities. Inaccessible system/service ownership is reported. Universal ownership, CWD or arbitrary open-file-handle freedom is not proven.' }
    $rbReceipt.process_checks.Add($check)
    if (-not $RecordOnly.IsPresent) {
        Assert-Readback ($usageMatches.Count -eq 0 -and $usageUnknown.Count -eq 0) 'A target source copy is in use, or a live owned/runtime process could not be checked; no deletion is permitted.'
    }
}
function Test-ReadbackRetained {
    foreach ($entry in $rbPlan.retain_source_files_in_place) { Assert-ReadbackFile $entry }
    foreach ($entry in $rbPlan.retain_parent_evidence_in_place) { Assert-ReadbackFile $entry -ParentEvidence }
    $rbReceipt.retained_recheck_passed = $true
}

try {
    Assert-Readback ([Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT) 'This runner is Windows-only.'
    Assert-Readback ($PSVersionTable.PSVersion.Major -ge 7) 'PowerShell7or newer is required.'
    Assert-Readback (Test-ReadbackSamePath $PSScriptRoot $rbOutputRoot) 'Runner must remain in this exact owned output folder.'
    Assert-Readback ($ExpectedPlanSha256.ToLowerInvariant() -ceq $rbRequiredPlanSha) 'The caller did not supply the exact reviewed plan SHA256.'
    Assert-Readback (-not (Test-Path -LiteralPath $rbReportPath) -and -not (Test-Path -LiteralPath $rbJournalPath)) 'Fresh receipt paths are required.'
    $rbRawPlanBytes = [IO.File]::ReadAllBytes($rbPlanPath)
    $rbActualPlanSha = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($rbRawPlanBytes)).ToLowerInvariant()
    Assert-Readback ($rbActualPlanSha -ceq $rbRequiredPlanSha) 'Raw plan SHA256 mismatch.'
    $rbPlan = [Text.UTF8Encoding]::new($false, $true).GetString($rbRawPlanBytes) | ConvertFrom-Json -AsHashtable -Depth 100
    Assert-Readback ($rbPlan.format -ceq 'has_individual_reconstructible_readback_cleanup_plan_1') 'Unexpected plan format.'
    Assert-Readback (Test-ReadbackSamePath ([string]$rbPlan.scope_root) $rbScopeRoot) 'Unexpected scope root.'
    Assert-Readback (($rbPlan.explicit_allowed_nonces -join ',') -ceq ($rbAllowedNonces -join ',')) 'The explicit nonce set differs from the reviewed13copies.'
    Assert-Readback (($rbPlan.protected_canonical_nonces -join ',') -ceq ($rbProtectedNonces -join ',')) 'Protected canonical set differs.'
    Assert-Readback ($rbPlan.no_directory_deletion -and $rbPlan.all_unlisted_or_future_copies_excluded -and $rbPlan.no_archival_upload_or_relocation) 'Required scope protections are absent.'
    Assert-Readback (@($rbPlan.delete_individual_files).Count -eq 16875 -and @($rbPlan.retain_source_files_in_place).Count -eq 104 -and @($rbPlan.retain_parent_evidence_in_place).Count -eq 142) 'Unexpected file/retention counts.'
    foreach ($directory in $rbPlan.verified_parent_directories) {
        $full = Get-ReadbackFullPath ([string]$directory.path)
        Assert-Readback (-not $rbDirectoryProofs.ContainsKey($full)) 'Duplicate directory identity proof.'
        $rbDirectoryProofs[$full] = $directory
    }
    foreach ($directory in $rbDirectoryProofs.Keys) { Assert-ReadbackDirectory $directory; $rbReceipt.checked_directories++ }
    Assert-Readback (Test-ReadbackSamePath ([ReadbackCleanupNativeV1]::CurrentDirectory([Environment]::ProcessId)) ([Environment]::CurrentDirectory)) 'Native current-directory reader failed its own-process validation.'
    $rbReceipt.native_directory_and_cwd_reader_self_test = $true
    $rbReceipt.script_sha256 = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $rbReceipt.git_helper_sha256 = (Get-FileHash -LiteralPath $rbGitHelper -Algorithm SHA256).Hash.ToLowerInvariant()
    $gitOutput = & $rbPython $rbGitHelper --workspace $rbWorkspaceRoot --plan $rbPlanPath
    Assert-Readback ($LASTEXITCODE -eq 0) 'Read-only Git/blob/EOL verification failed.'
    $gitProof = ($gitOutput -join "`n") | ConvertFrom-Json -AsHashtable
    Assert-Readback ($gitProof.passed -and $gitProof.published_checkpoint -ceq $rbPublishedCheckpoint -and $gitProof.raw_plan_sha256 -ceq $rbRequiredPlanSha) 'Git proof does not match the reviewed checkpoint/plan.'
    $rbReceipt.git_recovery_proof = $gitProof
    foreach ($audit in @($rbPlan.original_audit, $rbPlan.supplementary_audit)) {
        Assert-Readback (Test-ReadbackSamePath ([IO.Path]::GetDirectoryName([string]$audit.path)) $rbOutputRoot) 'Audit proof escaped this output folder.'
        Assert-Readback ((Get-FileHash -LiteralPath ([string]$audit.path) -Algorithm SHA256).Hash.ToLowerInvariant() -ceq [string]$audit.sha256) 'Retained audit proof changed.'
    }
    Get-ReadbackProcessUsage -RecordOnly
    [long]$candidateBytes = 0
    foreach ($entry in $rbPlan.delete_individual_files) {
        Assert-Readback ($rbKnownSources.Add((Get-ReadbackFullPath ([string]$entry.path)))) 'Duplicate/case-colliding deletion path.'
        Assert-ReadbackFile $entry -Candidate
        $candidateBytes += [long]$entry.bytes; $rbReceipt.checked_candidate_files++
        if (($rbReceipt.checked_candidate_files % 1024) -eq 0) { Write-ReadbackReceipt }
    }
    Assert-Readback ($candidateBytes -eq 224835913L) 'Unexpected exact deletion byte count.'
    foreach ($entry in $rbPlan.retain_source_files_in_place) {
        $full = Get-ReadbackFullPath ([string]$entry.path)
        Assert-Readback (-not $rbKnownSources.Contains($full) -and $rbKnownKeep.Add($full)) 'Retention/deletion overlap or duplicate.'
        Assert-ReadbackFile $entry; $rbReceipt.checked_retained_source_files++
    }
    foreach ($entry in $rbPlan.retain_parent_evidence_in_place) { Assert-ReadbackFile $entry -ParentEvidence; $rbReceipt.checked_parent_evidence_files++ }
    foreach ($nonce in $rbAllowedNonces) {
        $source = $rbAllowedSources[$nonce]; $actual = Get-ReadbackTreePaths $source
        $expected = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
        foreach ($entry in @($rbPlan.delete_individual_files) + @($rbPlan.retain_source_files_in_place)) {
            if ([string]$entry.nonce -ceq $nonce) { Assert-Readback ($expected.Add((Get-ReadbackFullPath ([string]$entry.path)))) 'Duplicate source-tree partition entry.' }
        }
        Assert-Readback ($actual.SetEquals($expected)) ('Unexpected/missing file in source tree: ' + $source)
    }
    Get-ReadbackProcessUsage
    Assert-Readback ((Get-FileHash -LiteralPath $rbPlanPath -Algorithm SHA256).Hash.ToLowerInvariant() -ceq $rbRequiredPlanSha) 'Plan changed during preflight.'
    $rbReceipt.all_preflight_checks_passed = $true
    if (-not $Execute.IsPresent) {
        $rbReceipt.status = 'preflight_passed_no_deletion'
        $rbReceipt.retained_recheck_passed = $true
        Write-ReadbackReceipt
        Write-Output $rbReportPath
        return
    }

    # MUTATION BOUNDARY: only root's later -Execute invocation can reach here.
    $rbReceipt.deletion_invoked = $true; $rbReceipt.status = 'deleting_individual_files'
    $rbReceipt.journal_path = $rbJournalPath
    Assert-ReadbackReportPath $rbJournalPath
    '' | Set-Content -LiteralPath $rbJournalPath -Encoding utf8NoBOM -NoNewline
    Write-ReadbackReceipt
    [int]$entryIndex = 0
    foreach ($entry in $rbPlan.delete_individual_files) {
        $rbReceipt.current_candidate = [string]$entry.path
        Assert-ReadbackFile $entry -Candidate
        if (($entryIndex % 512) -eq 0) { Get-ReadbackProcessUsage }
        # No wildcard, recursive operation, directory target or secondary shell.
        Remove-Item -LiteralPath ([string]$entry.path) -ErrorAction Stop
        $rbReceipt.deleted_files++; $rbReceipt.deleted_bytes += [long]$entry.bytes
        Assert-Readback (-not (Test-Path -LiteralPath ([string]$entry.path))) 'A deleted file path immediately reappeared.'
        @{ index = $entryIndex; path = [string]$entry.path; sha256 = [string]$entry.sha256; bytes = [long]$entry.bytes; deleted_utc = (Get-Date).ToUniversalTime().ToString('o') } | ConvertTo-Json -Compress | Add-Content -LiteralPath $rbJournalPath -Encoding utf8NoBOM
        $entryIndex++
        if (($entryIndex % 512) -eq 0) { Write-ReadbackReceipt }
    }
    $rbReceipt.current_candidate = $null
    Test-ReadbackRetained
    foreach ($nonce in $rbAllowedNonces) {
        $actual = Get-ReadbackTreePaths $rbAllowedSources[$nonce]
        $expected = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
        foreach ($entry in $rbPlan.retain_source_files_in_place) { if ([string]$entry.nonce -ceq $nonce) { [void]$expected.Add((Get-ReadbackFullPath ([string]$entry.path))) } }
        Assert-Readback ($actual.SetEquals($expected)) 'Post-cleanup retained sparse tree differs from the exact keep set.'
    }
    Assert-Readback ($rbReceipt.deleted_files -eq 16875 -and $rbReceipt.deleted_bytes -eq 224835913L) 'Actual deletion accounting mismatch.'
    $rbReceipt.status = 'completed_individual_deletions_retained_evidence_verified'
    $rbReceipt.historical_source_trees_intentionally_sparse = $true
    $rbReceipt.sparse_tree_recovery = $rbPlan.recovery_note
} catch {
    $rbReceipt.status = if ($rbReceipt.deletion_invoked) { 'stopped_after_failure_during_individual_cleanup' } else { 'preflight_failed_no_deletion' }
    $rbReceipt.errors.Add($_.Exception.Message)
    if ($null -ne $rbReceipt.current_candidate) { $rbReceipt.failed_files++ }
    if ($rbReceipt.deletion_invoked -and $null -ne $rbPlan) {
        try { Test-ReadbackRetained } catch { $rbReceipt.errors.Add('Retained recheck: ' + $_.Exception.Message) }
    }
    throw
} finally {
    Write-ReadbackReceipt
}
Write-Output $rbReportPath
