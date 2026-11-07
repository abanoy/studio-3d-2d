# Retained storage for deleted-layer Undo

Deleting a layer retains its existing cel owners for Undo. It does not create a
full decoded snapshot of every drawing. Layer removal now charges retained pixel
storage once per raster identity instead of charging every cold drawing as a full
decoded canvas. Eager/hot Images still charge their full retained pixel size.

In the reproduced case, twelve unique compressed full-HD drawings retained 9,802
bytes. The old 99,532,800-byte charge caused the history limiter to discard the
preceding brush command. The fixed charge preserves that command: Undo restores
the layer, then Undo restores the original brush pixels; Redo preserves ordering.
Deleted owners remain registered in the shared budget while history keeps them.

This is a charge at removal time. It is not dynamic whole-process memory admission:
rehydration, borrowed Images, history tiles and derived/GPU resources still require
broader accounting. The soft hot/cache target and the 32-cel limit are unchanged.
No overall MEM-01 or MEM-02 acceptance closure follows from this scoped fix.

The focused fixture passes 13 checks, including exact twelve-cel restoration,
unchanged world/camera and ordinary packed Save/Open with equal final composition.
The existing layer UI/order/visibility/removal/recovery/media suite passes 40 checks,
with ffprobe confirming 48 H264 frames at 1920×1080 and 24fps. The 271 raster domain
checks also pass. The portable wrapper preserves Windows private-desktop receipt
checks and requires an explicit private Linux display:

```sh
python tests/verify_layer_retention.py --isolated-display :107 --output /absolute/new/result
```

See [before/fixed evidence](benchmarks/layer_retention_2026-11-06.json). The first
exploratory harness had an incorrect save argument after reproducing the history
failures; it was corrected and both baseline and fixed runs completed. Its logs
remain separate. Native Windows/hardware and global dense-project acceptance are
not certified by these fixtures.
