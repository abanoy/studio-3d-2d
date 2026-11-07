# Recovery payload retention

Successful checkpoints now retire drawing/asset blobs that were referenced by a
previously retained manifest and are no longer referenced by any retained state.
The worker captures that known inventory before rotation, commits and checks the
new project and journal, then compares against both catalogs plus current and
backup manifests. It removes only exact content-addressed filenames in
cels/content, assets and references, inside this process-owned session.

This is not a cache-directory sweep. Unknown files, unreferenced hash-shaped files,
legacy non-content-addressed payloads, temporary files, other sessions and original
sources stay untouched. Corrupt/missing retained metadata, changed owner identity,
unsafe paths or symbolic links prevent reclamation. Failed reclamation leaves the
new checkpoint valid. The ordinary application serializes its writer and preview;
this does not establish a new cross-process quota reservation or global cleanup
protocol. The512MiB recovery root limit remains and may still require manual review
when retained states or other sessions consume the budget.

In25changing real checkpoint generations, at most13drawing PNGs and13geometry GLBs
remain, including rollback-catalog coverage. Every retained current, backup and
immutable history manifest opens with its checked pixels/assets. All25original
geometry files remain byte-identical. Foreign ownership, corrupt rollback JSON,
path escapes, unrelated hash-shaped files and an actual Linux symbolic link are
covered. Nested drawings, audio, effect JSON/textures and reference images remain
roots. The37retention checks and existing33journal checks pass.

The96-check background writer/app/preview/scheduling regression and70-check nested
reference/audio/crash/startup/lesson regression also pass. The latter includes a
real abrupt exit, cold readers with sources/cache offline, and a48frame1080p24
H264/AAC movie with exact preview inputs. These are scoped Linux software checks;
Windows/device power-loss and concurrent whole-root quotas remain separate.

Run `python tests/verify_recovery_blob_retention.py --output /absolute/new-case`.
See [recorded evidence](benchmarks/recovery_blob_retention_2026-11-07.json).
