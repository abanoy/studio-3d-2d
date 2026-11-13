# Source resource write CPU evidence

The first run passed the new resource-write suite (6 passed, 1 explicitly skipped) and all 8 existing archive regression tests. The skipped test is solely the real directory-symlink escape check: Windows refused symbolic-link creation with WinError 1314. No symlink escape result is claimed.

The mandatory real Windows long-path test wrote and read back 4,379 exact bytes at a 382-character logical path. It checked nested Unicode layout, a normal unprefixed returned Path, and exclusive repeat-write refusal preserving the existing SHA256 and nanosecond modification time. The long write/read used real filesystem I/O, with extended-length Windows syntax for readback; no filesystem mock was used.

Other checks cover empty/binary/bytearray payloads, accepted backslash normalization, 24 names rejected by the existing resource_path contract, invalid/oversize payload refusal before directory creation, and unchanged existing payloads. Oversize admission uses a bytes subclass reporting a length above 128 MiB to exercise the budget without allocating that payload.

verification.json retains exact commands, exit codes, long-path proof, counts and log hashes. source-before.json/source-after.json identify the helper, asset audit module, new test and existing archive test by SHA256, size and modification time; all remained unchanged. python.json/python-after.json retain the approved runtime identity and its unchanged gate. No graphics, Godot, Blender, native conversion, installed tool changes or Git actions were performed.
