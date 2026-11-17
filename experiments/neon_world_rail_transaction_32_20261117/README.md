# Standalone 32-check World transaction lifecycle source

This derives from the exact typed 29-check fixture `f033f975735efe5089dbadb478661f620dceeca4a1328ce090638747c03df202`.
All nine original non-run functions and their predicates remain unchanged; the
original three cases still execute in order. An exact inverse removes the new
case and its report/transport changes to reproduce that source. The formal
five-case 12,504-check integration and its 29-check lifecycle alias are untouched.

The fourth case first establishes a narrow left World rail, keeps the actual
help Label and its parent/index, and detaches that Label without freeing it.
Three additional checks verify:

1. A different-mode setter call explicitly refuses while that held control is
   off-tree, with the initial layout and selection both in rail mode.
2. Moving World to the right and refreshing while the control is withheld leaves
   both accepted mode caches unchanged, despite the requested list arrangement.
3. Reattaching that same Label at its original parent/index, then making one
   explicit refresh, restores the full World list and agrees in both caches.

Two scalar diagnostic lines disclose the withheld/restored states. The separate
result uses format `has_neon_world_rail_transaction_lifecycle_1` and marker
`NEON_WORLD_RAIL_TRANSACTION_LIFECYCLE `. File and stdout share one full-precision
JSON string. A passing actual run must report exactly 32 checks, zero failures,
the original three cases followed by `withheld-control-transaction`, and native
model scope false. Root must retain strict error/log and private job/desktop
closure gates. The script still requires one fresh output directory beneath the
review's output folder.

`prepare.py` ran only source/static checks and wrote this packet. It verified
the original source SHA, exact inverse, unchanged original function bodies/check
lines and exactly three new check call sites. No Godot, native model, CIM, Git,
review file or product-runtime change occurred. The 32-check runtime is unrun;
root will run this standalone source after its current work closes.
