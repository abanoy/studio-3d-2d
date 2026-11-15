# Fresh native picking diagnostic

The production picker correctly rejects a request whose displayed view changes.
The historical native test clicked in the same callback that changed workspace
mode, before deferred layout completed. The output-only diagnostic logs its
request/current view, matching serial, native ID pixel and interaction guards,
then stops after the original failed predicate instead of crashing on its later
foreign pose-tree lookup. That diagnostic is not a full passing selection test.

The normal test now waits for the next presented layout using its existing
settled() helper; all41original assertions remain. The actual fresh native replay
passes. The saved diagnostics derive ROOT from their output placement and must
be copied to a fresh owned checkout/output location before use, not run directly
from this archive. They never modify the production picker.

The actual eb7full run, old PowerShell startup error, diagnostic/fixed receipts,
source hashes and native fixture metadata snapshot are in the benchmark. Raw
project/model data and diagnostic actor snapshots remain private, not included.
