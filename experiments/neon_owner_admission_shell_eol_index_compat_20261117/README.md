# Exact three shell-script EOL admission

This source-only successor adds exactly `tools/linux/liveness_shim.sh`, `tools/linux/run_test.sh` and `tools/linux/shoot.sh` to the existing `TEXT_PATHS` set. The tested working files retain CRLF while their committed Git blobs use LF. The predecessor treated these paths as binary, so its merged-source admission refused that exact text-only bridge.

The suffix allowlist and every function body remain unchanged. Only the single TEXT_PATHS assignment changes, with a complete raw-byte inverse to core5479/cdad. The original 27 authored CPU methods, c39e reference, legacy gates, registry, reference tests and predecessor source pins are byte-exact. Seven new methods exercise the exact path set, old refusal, tested-byte preservation, explicit EOL permission, content mutation, undeclared shell/case alias/binary negatives and exact-byte modes. No functional source, Git blob, assertion threshold, full/native/receipt gate or activation is changed.

The new core remains inactive. It does not supply a copier, activation token, full result or Root approval. Downstream source dependencies and the three canonical-content hashes in the reviewed delta need separately pinned successors. The changed delta remains a proposal until Root reviews/promotes it; all tested raw hashes and the historical native-to52 bridge remain unchanged.

Run approved Python `-B -X utf8 -m unittest -v test_admission_core test_shell_eol` from this folder to repeat the CPU checks without changing evidence. Preparation and evidence writers use exclusive creation and must not be rerun into the sealed folder.
