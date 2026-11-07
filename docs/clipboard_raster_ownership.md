# Drawing clipboard ownership

Copy and Cut now prepare a separate registered raster owner before replacing the
transient drawing clipboard. The copied Image keeps copy-on-write independence
from its source. It joins the same document budget as live and history-owned
cels; an inactive compressible clipboard can cool without pinning a full-HD Image.
Only one clipboard is retained, and it is cleared on the existing scene/session/
layer invalidation rules. It remains absent from saved projects.

Paste reads through the integrity-checked drawing accessor before creating its
independent destination owner. Missing or corrupt cold pixels refuse without
changing drawing structure or history. The old clipboard is retained if preparing
a new copy fails. Split continues to preserve the clipboard.

This adds clipboard ownership to the existing conservative hot/cache counter.
It does not make the soft 64 MiB target a global RSS limit, and does not expand the
32-cel project cap. History tiles, derived/GPU resources and global admission remain
separate work. Incompressible copied artwork stays charged while it remains hot.

The ordinary menu workflow verifies registration, exact pixels after cooling,
refusal after deliberate owned clipboard corruption, frozen-source independence,
Paste/Cut/Split Undo/Redo, sequence invalidation, packed cold Open and actual
preview/movie agreement. The existing cold-write workflow reads the clipboard
through the same accessor and checks painting, fill, selection and transform
history across cooling, followed by packed Open and a real checkpoint save. This rerun does not certify
abrupt startup recovery.

Run `tests/verify_cel_clipboard.py` or `tests/verify_cel_raster_write.py` with an
explicit owned private display. The latter's Paste representation assertion now
expects the registered destination owner introduced by the earlier new-cel
migration; its exact pixel assertion is retained. See
[recorded evidence](benchmarks/clipboard_raster_ownership_2026-11-06.json).
Native Windows and physical hardware acceptance remain unrun.
