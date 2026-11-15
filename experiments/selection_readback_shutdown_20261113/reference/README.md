# Godot 4.6 Windows shutdown crash: exact-binary research

Research date: 2026-11-13. Read-only analysis, no application run, no downloads, no engine replacement, no private dump upload.

## Result

The fault stack can be narrowed without guessing from the nearest exported symbol. The exact executable reports a leaked **Variant::Pools::BucketMedium** allocator during CRT static teardown. The crash then occurs entering the global error-reporting mutex. This does not identify the original retained Variant owner, and it does not prove why the critical section is invalid. The test's nonzero exit remains a failure.

## Exact input and tool evidence

- Executable: `C:\a\tools\Godot\Godot_v4.6-stable_win64.exe`, 171924488 bytes.
- SHA256: `63913D01BE2C2D1F929B4A626F5347117126B34E9C64CBF350EA9F35A9657EBF`.
- Reported engine commit: `89cea1439` (parent diagnostic input).
- Existing CDB log: `..\drawing-selection-crash-20261113\cdb-offline.log`.
- Existing LLVM tools: `C:\a\tools\llvm-mingw-20260324-msvcrt-x86_64\bin`.
- PE preferred image base: `0x140000000`; dump image base: `0x00007ff6b2320000`.
- PE characteristics include symbols stripped and line numbers stripped. The COFF symbol table is empty. PE Debug Directory RVA/size are both zero. There are no `.debug_*`, `.gnu_debuglink`, or CodeView/PDB sections/record.
- `llvm-symbolizer --relative-address` returns only `NoHotPatch` and `??:0:0` for all three Godot stack RVAs. This is an export-nearest fallback, not function identification.
- Targeted symbol inventory checked `C:\a\tools`, `C:\a\Programming\HAS`, `C:\a\Programming\cloudflare`, Downloads, and Documents. No Godot PDB/debug/symbol/map file was found; Documents has an unrelated ILSpy PDB. This is a scoped inventory, not a claim to scan every disk.

## Manual identification from exact instructions and literals

All RVAs below are relative to the Godot image, not the `NoHotPatch` export.

| RVA | Observed exact instructions/literals | Identification |
| --- | --- | --- |
| `0x4b60408` | Loads literal at VA `0x147c4c4e0`: `N7Variant5Pools12BucketMediumE` | Existing `llvm-cxxfilt -t` gives `Variant::Pools::BucketMedium`. |
| `0x4b60433` | Loads literal at VA `0x1472094f8`: `Pages in use exist at exit in PagedAllocator: ` | Allocator leaked-element reporting path. |
| `0x4b6047b` | Loads line `0xa9` (=169). | Source line argument. |
| `0x4b60489` | Loads `./core/templates/paged_allocator.h`. | Source file argument. |
| `0x4b60490` | Loads `~PagedAllocator`. | Source function argument. |
| `0x4b60497` | Calls RVA `0x3d95dd0`; return PC is stack RVA `0x4b6049c`. | `_err_print_error` overload for a String argument, correlated with exact source. |
| `0x3d95e3f` | Calls RVA `0x3d95a70`; return PC is stack RVA `0x3d95e44`. | Main error printer, correlated with exact source's overload delegation. |
| `0x3d95b67` | Calls RVA `0x37f8890`; return PC is stack RVA `0x3d95b6c`. Afterward code walks a global error-handler linked list. | Main error printer's `_global_lock()` before walking error handlers. |
| `0x37f8890` | Loads RCX from address `0x14a3caf80`, jumps via imported critical-section routine. | Global error mutex at RVA `0xa3caf80`, matching dump RCX `0x7ff6bc6eaf80`. |

The mutex RVA lies in PE `.bss` (starts at RVA `0xa325000`), not initialized `.data`. The source declares `static Mutex _global_mutex` in mutex.cpp. Error-macros source explicitly locks it before traversing `error_handler_list`. These independent instruction/literal/source correspondences identify the route much more strongly than export-nearest labels.

## Primary source correlations

Exact engine source at commit 89cea1439:

- [PagedAllocator](https://raw.githubusercontent.com/godotengine/godot/89cea1439/core/templates/paged_allocator.h): the destructor detects allocations still in use, then attempts an error report naming the template type when leak reporting is enabled.
- [Variant declarations](https://raw.githubusercontent.com/godotengine/godot/89cea1439/core/variant/variant.h): BucketMedium contains Basis and Transform3D storage. This narrows the retained data type; it does not identify the retaining object.
- [Variant implementation](https://raw.githubusercontent.com/godotengine/godot/89cea1439/core/variant/variant.cpp): defines the static medium allocator and uses it for BASIS/TRANSFORM3D construction and destruction.
- [Error printer](https://raw.githubusercontent.com/godotengine/godot/89cea1439/core/error/error_macros.cpp): the String overload delegates to the main printer, which then calls `_global_lock` before traversing handlers. A reentrancy guard is already present.
- [Global mutex](https://raw.githubusercontent.com/godotengine/godot/89cea1439/core/os/mutex.cpp): `_global_lock` and `_global_unlock` use one static global mutex.

## Available symbols and next route

The [official 4.6 release asset inventory](https://github.com/godotengine/godot-builds/releases/expanded_assets/4.6-stable) lists Android native symbols only. It does not list Windows editor symbols or a Windows link map. Android symbols cannot symbolize this x86-64 Windows editor. No artifact was downloaded.

The [Godot 4.6 build-system documentation](https://docs.godotengine.org/en/4.6/engine_details/development/compiling/introduction_to_the_buildsystem.html#debugging-symbols) says official binaries omit debugging symbols. A future source build can use `debug_symbols=yes`; `separate_debug_symbols=yes` creates a separate debug file, while MSVC writes PDBs. Production optimization can be retained with `production=yes debug_symbols=yes`.

Actionable options:

1. Continue offline investigation of this exact dump using its preserved stack, unwind records, disassembly, RTTI, and embedded file/function literals. In CDB, `.ecxr; .frame /r 5; r` should expose the callee-saved RBX allocator pointer in the PagedAllocator frame. If the minidump includes that memory, its members are page_pool at +0, available_pool at +8, pages_allocated at +0x10, allocs_available at +0x14, page_shift at +0x18, page_mask at +0x1c, page_size at +0x20, spin lock at +0x24. The outstanding allocation count is pages_allocated*page_size - allocs_available. Do not assume heap pages are present in this limited minidump.
2. Locate an exact unstripped binary/map/debug file from the original official build producer if such private artifacts were retained. There is no PDB GUID/debug-file locator in this shipped image, and no public Windows release artifact was found.
3. If separately authorized later, build the same engine commit in an isolated directory with symbols and reproduce the failure using that paired executable/symbol file. An arbitrary rebuilt same-version binary or PDB must not be applied to the existing dump by raw offsets: compiler, linker, flags, LTO, and layout can differ. A new debug reproduction can identify the leak owner; rebuilding does not automatically symbolize this old binary.

No source map is applicable to this native PE executable. A Microsoft system-symbol download could improve ntdll/CRT names, but it would not provide missing Godot internals. None was requested or performed here.

## Related official issues: context, not diagnosis

- [Godot #106235](https://github.com/godotengine/godot/issues/106235) tracks unsafe cross-translation-unit static initialization/destruction dependencies, including global containers, Variants, StringNames and allocators. It is compatible with the observed teardown phase, but does not prove this instance's root cause or fix.
- [Godot #108838](https://github.com/godotengine/godot/issues/108838) contains an older macOS shutdown stack with the same BucketMedium allocator destructor followed by recursive StringName error printing. [PR #108860](https://github.com/godotengine/godot/pull/108860) added printing reentrancy protection in July 2025. That guard is present in the exact source above. The observed Windows critical-section AV is not the same demonstrated recursion failure.
- [godot-cpp #2024](https://github.com/godotengine/godot-cpp/issues/2024) is a separate extension/AHashMap shutdown regression and is not evidence that this GDScript-only case has that cause.

No installed engine, prototype, test source, GPU state, or user's original dump was modified. The root must continue to require a clean child exit in addition to the 35 passing application checks.

## Follow-up: read-only original-dump allocator inspection

The parent authorized the proposed CDB follow-up. It was performed against the original dump with `_NT_SYMBOL_PATH` and `-y` pointing to the empty owned `local-symbols-only` directory; `_NT_ALT_SYMBOL_PATH` was absent. Exact commands, CDB output, and before/after dump hashes are saved in `cdb-allocator-explicit-commands.txt`, `cdb-allocator-explicit.log`, and `cdb-allocator-explicit-provenance.json`.

`.frame /r 5` recovered callee-saved RBX = `0x00007ff6bc6ec7a0`, the medium allocator at RVA `0xa3cc7a0`. Explicit-address reads gave:

| Member | Address offset | Value |
| --- | --- | --- |
| page_pool | +0 | `0x000001b7ad6be9e0` |
| available_pool | +8 | `0x000001b7ad6be6a0` |
| pages_allocated | +0x10 | 1 |
| allocs_available | +0x14 | 4095 (`0xfff`) |
| page_shift | +0x18 | 12 |
| page_mask | +0x1c | 4095 (`0xfff`) |
| page_size | +0x20 | 4096 (`0x1000`) |
| spin lock byte | +0x24 | 1 (held by this destructor) |

CDB directly evaluated `pages_allocated * page_size - allocs_available` as **1**. Thus exactly one medium-pool allocation is outstanding at this crash. This is not a count of leaked application objects and does not distinguish Basis from Transform3D. Both pointer-table heap reads returned `????????`, so the limited minidump does not expose the corresponding pool pages/value/owner via those tables.

The original exception context's critical-section address `0x00007ff6bc6eaf80` contains qwords `0`, `0x00000000fffffffa`, `0`, `0xffffffffffffffff`, `0`. Using the local Windows SDK header `C:\Program Files (x86)\Windows Kits\10\Include\10.0.28000.0\um\winnt.h:25085` for the x64 RTL_CRITICAL_SECTION layout, this is DebugInfo=null, LockCount=-6, RecursionCount=0, OwningThread=null, LockSemaphore=-1, SpinCount=0. These are observations at failure, not proof of the earlier destruction sequence.

The original dump SHA256 matched before and after every CDB invocation. No target process was launched or attached.

Two debugger-command details are preserved for reproducibility: an initial `.sympath; ...` command was parsed by CDB as a symbol-path assignment instead of subsequent commands, so it supplied no allocator evidence (`cdb-path-query-attempt*`). In the next run, `.frame /r 5` printed the correct recovered frame registers, but a later bare `r` and `@rbx` reverted to the exception register context; those `@rbx` memory lines in `cdb-allocator.log` are not allocator evidence. The final `cdb-allocator-explicit.log` avoids this by using the recovered explicit allocator address throughout.
