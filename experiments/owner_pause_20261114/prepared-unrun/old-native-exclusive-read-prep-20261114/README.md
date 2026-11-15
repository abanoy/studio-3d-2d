# Old native-output exclusive-read probe — prepared, UNRUN

This optional source-only preparation complements the independent two-root audit. Its current verdict remains **RETAIN_FOR_NOW**. The earlier Restart Manager registration failed with error29, 202 process command lines were unavailable, and the shared DELETE-access probe did not establish nonuse. No new resource check, Windows API call, source-tree inventory, application or cleanup was executed by this preparation.

Only these literal historical roots are admitted:

| Phase | Root below this workspace's `output/source-choices-native` | Files | Directories below root | Bytes |
|---|---|---:|---:|---:|
| core14 | `1794615194930984000-ae0e0967` | 4,707 | 791 | 387,640,663 |
| wider11 | `1794615438168999800-42f0686d` | 4,600 | 746 | 1,054,546,425 |
| Total | Two roots only | 9,307 | 1,537 | 1,442,187,088 |

The script pins the independent audit's two complete inventories by size and SHA256. A future run first requires exact current membership, file SHA256/size/mtime, no reparse points and single-link regular files. For each file it requests `GENERIC_READ`, sharing mode0, `OPEN_EXISTING`, `FILE_FLAG_OPEN_REPARSE_POINT` and no inheritable security attributes. It checks handle-observed volume/file ID, size, mtime and hardlink count against the frozen record, then closes that handle immediately. No file read or wait occurs while that exclusive handle is held. A close failure stops further opens and fails the run.

A second full membership/hash/mtime/kind inventory must equal the first. Results, errors and both inventories are written only to a new direct child of this workspace's `output`, never either candidate root. Existing outputs are never overwritten. The script has no deletion, disposition, rename, write-access, process launch, process query, process stop or installation API. It does not attempt directory exclusive opens or DELETE access.

The root-release template deliberately contains false flags. Only root may create a separate fresh release record after independently establishing: the full suite passed and closed; final-review runtimes closed; required evidence was published and remotely verified; source and protected data remain preserved; and the old exact coordinator/worker, dependency and preservation evidence still applies. These booleans record root's attestation; this probe does not independently infer those prerequisites. Never set them merely because this preparation exists.

A pass means all9,307 sequential read-sharing opens succeeded and closed with the expected identities during their observed intervals. It does **not** exclude metadata-only handles, existing mapped views, directory handles or later reopening, and it does not hold all files simultaneously or reserve later deletion access. It does not identify the202 unobserved command lines. Root must combine this evidence with exact owned-process closure, no dependency and preserved originals/source/Git evidence, then decide any later literal removal separately under Windows' current sharing rules. `cleanup_authorized` is always false.

All newer four-case runs, original families/stages, previous reviews, installed Studio/shared tools and recovery remain outside scope. The existing removal text is not executed or changed. Even a successful future probe does not change the old audit's verdict automatically; uncertain or changed evidence means retain.

Future invocation, **only after root's release and review**, using a separately created valid release JSON:

```powershell
& 'C:\Program Files\Python313\python.exe' -B 'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\old-native-exclusive-read-prep-20261114\probe_after_release.py' --after-full-and-final-review-closed --root-release-evidence 'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\old-native-exclusive-read-root-release.json' --output 'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\old-native-exclusive-read-20261114T_AFTER_RELEASE'
```

The Windows sharing semantics and handle-identity APIs were checked against [CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew), [Creating and Opening Files](https://learn.microsoft.com/en-us/windows/win32/fileio/creating-and-opening-files) and [GetFileInformationByHandle](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfileinformationbyhandle). This is an authored Windows-specific implementation awaiting actual qualification, not a claim that the probe has succeeded on this PC.
