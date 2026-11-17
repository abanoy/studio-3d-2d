# Closed Scene106 compact archive recipe

Only the two explicitly named completed root folders, the child folder and
physical receipts named by their saved commands/reports, and selected public
source are allowed. INPUTS.json freezes every exact byte/hash/mtime binding.
`capture_inputs.py` performs that read-only capture once; `build_packet.py`
validates all inputs and joins before writing the new archive once. It never
overwrites an archive or changes originals. No engine, process observer, CIM,
Git or active full output is invoked or read.

The independent `verify_packet.py` reads only the archive and frozen recipe,
uses bounded decompression, and does not import the builder or join helper.
It rechecks original membership/hashes, the failed102/4 diagnostic, successful
106/0 plus unit12830/0, exact102 legacy message order, source preservation and
two private receipt jobs. `archive_checks.py` additionally binds captured original
receipt mtimes to recorded scope-observation intervals; that supplemental
metadata is labeled separately from original receipt-byte evidence.

Both packet and recipe must be sealed and externally pinned for publication.
Retain all failures and old source drafts. No PNG/media/model/native arrays or
executables are copied, published or deleted by this recipe. This scoped evidence
does not establish full-suite success, merge, native assets or portable behavior.

The first capture refused before any INPUTS/archive write because the diagnostic
global receipt and root copy differ in line endings and final newline. The failed
source drafts and PREPARATION_ATTEMPT1.json remain here. Final admission uses
exact typed JSON identity plus the independently verified exact serialization
relation, while retaining both original byte strings separately.
