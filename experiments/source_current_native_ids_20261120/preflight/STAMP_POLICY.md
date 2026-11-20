# Reviewed directory-stamp hint boundary

This is a record of Root's reviewed successor policy, not an actual native/API
qualification. Exact observation and refusal are retained beside this note:
v2-FILE_CHANGED_BEFORE_READ.json and runtime-stamp-diagnostic.json.

Root observed only0x40000 changing between directory lstat and opened/final
runtime-file attributes. The file identity, bytes, size, nanosecond time and
link count remained exact. The official Win32 reference recorded by Root is
[Microsoft file attribute constants](https://learn.microsoft.com/en-us/windows/win32/fileio/file-attribute-constants).

The successor distinguishes the directory-enumeration recall-on-open hint from
a claim about internal extended-attribute state. Only that reviewed directory
hint is normalized in the comparison; raw attributes remain retained. Internal
EA semantics are unqualified. Reparse0x400 and every other attribute, device,
inode, size, nsmtime, link-count, literal digest and caller admission guard
remain strict. It is not a general permission to ignore attribute drift.

Root tested the actual f9bc/3ae CPU successor58 methods/1.039s with source
hash/size/nsmtime unchanged. The actual private SourceIO outcome remains PENDING.
The first f33 hardlink refusal and second b049 stamp refusal remain failed
preflights, not native imports or model-fidelity failures. Their actual Native/
Blender/input-copy counts are zero; only the second reached CIM-before.
