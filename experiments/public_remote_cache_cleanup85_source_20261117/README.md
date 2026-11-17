# Exact 85 public cache cleanup helper

`cleanup_public_caches.ps1` is a native PowerShell 7 helper for the pinned 85-file public-response inventory. **The default only verifies.** It checks candidate INDEX SHA `f9be18b1accd813d18f941c20978f3d0e9828394160d87fe561cc333796f340f` and inventory SHA `2814fd89078398168c718e1c22fb487085863e3592d1bfb8bab8c2d084ab7cf1`, every resolved immediate ROOT/output path, regular-file/reparse checks, exact size/mtime/SHA, uniqueness and the 33,228,774-byte logical total. Only e8cf/4ec7/a41a/4fd0/855d batch names are admitted.

Read-only verification:

```powershell
& 'C:\a\Programming\cloudflare\has-acceptance-session-20261111\experiments\public_remote_cache_cleanup85_source_20261117\cleanup_public_caches.ps1'
```

Root owns any later deletion after independent verification. Adding the explicit `-Delete` switch enables the sole `Remove-Item -LiteralPath` call, without recursion or shell composition. The helper verifies all 85 files before the first removal and rechecks each identity immediately before its removal. Current86df, private/native/full artifacts, tools, reviews and historical removed1ce/09fb paths cannot match the admitted list/names.

With `-Delete`, an exclusive fresh `public-cache85-cleanup-<time>-<guid>.jsonl` receipt is created under ROOT/output before preflight. Initial, preflight, before-delete and observed-deleted entries are flushed; completion or failure records include cumulative logical bytes. Any failure stops the operation and retains the journal/partial state. Existing receipts are never overwritten, and missing candidates are never skipped or reconstructed. No free-space change is measured or claimed.

The actual default run verified all 85 candidates and 33,228,774 logical bytes, with no receipt created and no deletion. `VALIDATION.json` records that result and source checks: no parse errors, one literal nonrecursive removal command, an unset Delete switch, immediate candidate recheck and no shell-composition commands. The Delete branch has not been executed in this preparation. Original candidate metadata, source/HEAD, native/full inputs and all cache files remain unchanged.
