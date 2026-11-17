# Three-shell canonicalization delta proposal

Root review is pending. This is a source-metadata successor of a91/9cbb, not a Root-approved delta or an activation.

Exactly three added shell rows change only `new_content_sha256`, from their tested CRLF raw digest to their LF canonical-content digest. Every raw hash, the other 36 rows, all 39 reasons, counts, the separate107 EOL list, old52 entries/aggregate and the historical native-to52 bridge stay exact. The new core adds only those three exact names to TEXT_PATHS; its canonical function and qualification gates are unchanged.

Both maps bind the new canonicalizer source identity. Only the candidate map's three content entries and canonical aggregate change. Map-file identity metadata and the proposal's core/reproducer/provenance fields follow those bytes. Current proposal status is unreviewed; the old Root review is retained solely as `parent_root_review`. Other inherited parent preparation/status fields keep their original historical scope and are not new observations of current Main or the completed full.

`derive_proposal.py` checks the exact parent/map/core pins, reads only the three authorized current shell code files, verifies tested raw identities, and runs the unchanged `A.check_reviewed_delta` over the complete1019/1029 public metadata maps. `--check` reproduces the new public payloads without writes. It reads no actual full/native/private outputs and performs no Git or process query. Root must review/promote this proposal before downstream admission can accept it.
