# Updated private review preparation

This is preparation only. No new review, project/runtime copy, Godot process or replay was created. The canonical run from `1236796865e677b150a2d7e2add20f2aac5325fe` still owns graphics.

The six protected packages currently match their recorded SHA256/size pins: 46,835,454 bytes total. The old review is the `e9cc7cfb20266b4863bde134bcb30457547a343d` copy. Its package/launcher metadata and 1,725 source-file identities are recorded without changing it. The approved SourceIO runtime has 574 non-cache files, 27,985,786 bytes, including LICENSE; its exact source index is retained.

After the full suite passes and root records its authoritative graphics-lease release, run the prepared coordinator in the approved host context with an exclusive graphics lease:

```powershell
& 'C:\Program Files\Python313\python.exe' -B 'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\helper-review-package-prep-20261113\execute_after_full.py' --revision 1236796865e677b150a2d7e2add20f2aac5325fe --canonical-run 'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\canonical-owned-20261113T200642700' --lease-release 'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\canonical-owned-20261113T200642700\graphics-lease-released.json' --final 'C:\a\Programming\cloudflare\HAS-Review-20261113-1236796' --execute-after-full --exclusive-graphics-lease --allow-checkout-eol
```

For a background launch, use Start-Process with `-WindowStyle Hidden` and redirected coordinator logs. Root should retain that process's actual PID/creation time. Do not launch while the canonical run or another graphics job remains active. If the full suite needs a fix, supply the new complete revision and its new passed canonical/release paths; choose the corresponding fresh final folder name.

The coordinator refuses a running/failed/mismatched canonical run, a missing or stale release record, an active/reused coordinator PID, a changed protected input/runtime, or an existing final target. Its default invocation without `--execute-after-full` only prints the plan.

Read-only Git preflight found checkout CRLF in the builder and two startup-scene files; their CRLF-to-LF bytes equal the requested Git blobs. The explicit `--allow-checkout-eol` flag admits only that difference and records both raw hashes. It changes no file and does not normalize the final snapshot, which remains exact Git blobs. Any other content difference refuses. The initial strict-raw preflight failure remains in `core-git-byte-preflight.json`.

The staged snapshot builder requires a new directory inside the checkout's output. It freezes exact Git blobs with `--revision`, performs its private ordinary Home/Simple startup, and generates the source proof. The coordinator then copies only those pinned source files and override.cfg into the final **new workspace sibling**, copies the six packed projects exactly, and freshly reads every declared archive payload through CRC and SHA checks without extracting anything into protected paths.

The existing builder's launchers are movable because project and Studio paths use `%~dp0`, but their SourceIO location points into the disposable checkout. The final launchers therefore use this PC's existing absolute Python/Godot/FFmpeg and a **relative** `%~dp0Dependencies\sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647` path. That folder is an exact local copy of the already approved runtime, with LICENSE and before/after file stamps; no download, installation, installed-app replacement or public redistribution occurs.

The final copy itself receives another normal Home/Simple startup and all **129 unchanged replay predicates across six private processes**. The existing main verifier's ROOT/output restriction is preserved. The output-only coordinator uses the unchanged committed `owner_review_replay.gd`, the existing pure metadata/compare functions and exact named final/evidence boundaries. Every project uses ordinary .has worker loading, fresh cache/recovery/display/recent/workspace paths, the unique builder profile, exact saved-state comparisons, native Setup/Focus captures and closed private-desktop receipts. The numeric contract remains finite 1e-12 absolute only, with no relative tolerance or new schema migration.

Validation/captures stay in a separate fresh checkout/output directory; final owner source/preferences do not receive copied development caches. The old review, original SourceIO and shared runtimes are checked again afterward. Failed attempts retain their owned source/logs and reports. A separate source-snapshot stage proof and actual final-path startup proof distinguish the relocation from the initial build.

`README.template.md` is written to the final review only after successful replays. It describes trying proposed loose parts before Apply and separate temporary wind checks, and keeps Mima head-only, synthetic Back hair, broad Source fidelity, human/device and clean-install limits explicit. No owner prompt is needed.

The final review remains private and outside the disposable checkout. This preparation does not authorize deleting the old review or its recovery; any unbacked-up owner work there remains protected during later checkout cleanup.
