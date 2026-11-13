# Review command after the save-order full run

Do not run this command while `canonical-owned-20261113T211216019` owns graphics. Its observed state was **running**, PID **6548**, creation **2026-11-13T21:12:16.0315845Z**. No terminal pass or release is implied by this preparation.

After that exact run passes and root records its authoritative release, use the approved host context and an exclusive graphics lease:

```powershell
& 'C:\Program Files\Python313\python.exe' -B 'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\helper-review-package-prep-20261113\execute_after_full.py' --revision 12071fe182a17d17e2a1547c7dbb97f6aa4dd160 --canonical-run 'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\canonical-owned-20261113T211216019' --lease-release 'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\canonical-owned-20261113T211216019\graphics-lease-released.json' --final 'C:\a\Programming\cloudflare\HAS-Review-20261113-12071fe' --execute-after-full --exclusive-graphics-lease --allow-checkout-eol
```

For a background launch, pass the argument array in `command.json` to Start-Process with `-WindowStyle Hidden` and redirect stdout/stderr into a **new** owned launch directory. Retain the actual coordinator PID/creation time. Do not execute the prepared coordinator now.

The existing script still defaults to the **failed** `1236796` run; all revision/run/final arguments above are intentional overrides. Its five builder/startup/replay/compare files have no Git diff between `1236796` and `12071fe`. `--allow-checkout-eol` remains required for the already recorded three CRLF-versus-Git-LF core files. Both raw hashes are retained; final Studio files are still exact requested Git blobs.

The old preparation's planned1236796 labels do not constrain an explicit new revision; its protected package, old Studio and SourceIO indices remain applicable. All those identities and approved executable pins must be rechecked by the coordinator **after** the full lease is released. Their current preservation was not recertified by this command-only inspection.

Final target must be absent, be the exact new named workspace sibling, and contain no links/reparse path. If it already exists, choose a fresh permitted suffix such as `HAS-Review-20261113-12071fe-b`; do not overwrite it. If this full run fails, this command must remain unexecuted until a new revision/run obtains its own pass and release.

The unchanged coordinator SHA256 is `d5c17e97d67bf91250229d9f62bfe9aaefe922057c148a362e4fdc706ba4fadd`. It checks the terminal state and release first, then performs a native synchronize-only check of the old canonical PID. A live/reused PID, access-denied inspection or stale/missing release refuses before new review staging.

The original preparation packet and its INDEX are preserved. This folder is a separately indexed command/release-schema addendum, not a replacement for the original 21-file preparation manifest. No coordinator, review copy, Godot, Python worker or software test was launched here.
