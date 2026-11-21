# Empty room after an earlier successful VoxelGI bake

Isolated review branch `worker/lighting-rebake-review-20261121`, checkout
`has-lighting-rebake-review-20261121`, based on primary integration `38b39ec7`.
The qualified `96e5d50b` branch/checkout remains unchanged.

The primary worker's native bake boundary and early-return controls were copied
explicitly into this owned checkout and snapshot separately in `2ec0fd64`:
runtime SHA256 `a99f28128f963a84133e1e862f67b1d48b012bde6fb9865c17cb90598dcb1816`,
authoritative test SHA256 `4e4f6a47e38d2dfdc25263405b103402937ebceb41ce2e05ab2fecf83217fffb`.
This review does not replace or duplicate those controls.

A separate real-bake regression imports the original room fixture, bakes it, moves
the bounds away from every environment mesh, then runs later ordinary syncs.
Before the fix, 18 checks produced four failures across Neon and Classic: earlier
data stayed attached, and sync re-showed the failed probe. Error reporting,
capture admission refusal and real Undo recovery already worked.

The runtime delta against the primary snapshot is exactly two lines:

- `sync()` visibility additionally requires `error.is_empty()`.
- The zero-contributor branch clears `probe.data` before recording its error.

`python -B tests/verify_voxel_empty_rebake.py` now passes **18/18 headless checks**.
The primary's unchanged native-boundary tests also pass **42/42** on this runtime.
Final runtime is 3227 bytes, SHA256
`fa9d4e43b375a61ccbc3e5a653cc423a22c4c8a1f8d357ab3d5b7a90b1826a3a`.
See `benchmarks/voxel_empty_rebake_review_2026-11-21.json` for before/after evidence.

The optional `--graphics` runner uses only the existing private Windows desktop
launcher. It adds actual failed-movie refusal and successful-movie recovery with
two-frame H.264 probing in both themes. **Those four graphical checks have not run**;
the primary reserves the GPU for the frozen Full5d run. Headless admission checks
do not establish those end-to-end movie outcomes or new preview pixel evidence.
Original runtime previews/movies at `96e5d50b` remain a separate qualification.

Integrate only the two-line runtime delta and the new focused test/runner. Keep
the primary native boundary/test authoritative, and refresh the changed runtime
port leaf as the primary directs. No app, renderer, world, material, encoder,
original asset, installed Studio/tool or primary-checkout edits were made here.
