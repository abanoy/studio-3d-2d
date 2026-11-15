# Ready source-only proposal

The candidate is ready for root review. **No graphics, Blender, native worker,
normal adoption, HAS writer/reader or renderer test ran.** The only Godot use
was explicit `--headless --check-only` parsing of owned source copies.

- Final manifest: `runs/1794549675994255000-ba7b8ec3d91f4282a12af08e0e2645ce/manifest.json`,
  SHA256 `1b50ee89eeb3334e55115e885321752e5d1b1cc373aadf7d4ec89c8db813260e`.
- Final default preflight and check-only parse passed. Their commands, logs and
  `parse-verification.json` remain in that run. Protected originals and root
  functional files were unchanged over that preparation/parse interval.
- `cpu-check-1794549763594279900/verification.json` records **29/29 CPU controls**,
  zero failures, and unchanged candidate source. Partial timeout output has a
  mocked retention control; no actual runtime timeout is being claimed.
- The prepared source is the root-approved **working tree at base
  `2a54f252d128e4c800ae608ae798e0041a996b6b`**, including its uncommitted Wind
  phase 1 context. It is explicitly not exact Git 2a54 code. This driver's
  full functional policy counted 963 cached/untracked members under
  src/tests/tools and app entry points; the root matrix's 948-file policy is
  different. Both copies and this policy are spelled out in the manifest.

The main coordinator has since begun another Wind lifetime fix. Treat these
snapshots as historical preparation proof. After its final stable commit,
prepare a fresh exact-commit run, repeat preflight and obtain the coordinator's
exclusive graphics lease before using `--run-gpu --lease-confirmed`. A parsed
run's writer directory is consumed and must not be reused for actual graphics.

## Actual CPU reference observations

These are decoded derived GLB world positions, not native Source comparisons.

| Change | Moved used vertex records | Unchanged controls | Largest world delta |
| --- | ---: | ---: | ---: |
| Keiki Tools 0 to 1 | 1,180 | 1,616 | 0.0842537368 |
| Keiki box 20-degree pose | 38 | 2,758 | 0.0352969467 |
| Nitori hand 20-degree pose | 2,214 | 4,464 | 0.0348032478 |

Native Nitori bone 8 joins to actual GLB source node 25. Native Keiki bone 23
joins to source node 26. The explicit native-index / used-palette-index /
source-node table retains the native names and parents. Godot helper bones are
recorded separately rather than guessed from the native bone count.

Two early CPU preparations stopped before source-copy/runtime work completed:
the first bounded reader did not yet support Nitori's sparse `Ah` accessor, and
the next incorrectly assumed the Blender palette shared MDL table order.
Their partial owned input folders remain. The current reader supports validated
sparse overlays and requires exact unique-name plus nearest-joint-parent joins;
dense/sparse equivalence, corrupt sparse data and reordered-palette/parent
controls are included in the 29 checks. Neither stopped preparation is GPU
failure or native support evidence. The stale 0f8 HEAD refusal is retained too.

Independent source review covered the normal adoption/persistence contract and
the sparse/native-join/timeout corrections. Its note is in `review/`. After that
review, the app module gained one explicit identity placement/rotation/scale
assertion; the final check-only parse and source hashes include that assertion.

See `README.md` for the exact bounded future eight-capture/two-adoption exercise,
guards, local-only artifacts and remaining native/artist/device limitations.
`SOURCE-CHECKPOINT.json` binds the final five source files and compact receipts.
No production or Git writes were made by this task, and no GPU lease was taken.
