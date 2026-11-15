# Read-only publication audit

The authoritative top-level indexes of both requested packets matched every actual indexed SHA256 and byte count, their declared totals, and the complete on-disk file set excluding the index itself. All indexed targets remained contained and no reparse files, unlisted files, unexpected file types, invalid UTF-8 or NUL-containing text payloads were found.

| Packet | Authoritative index SHA256 | Indexed files | Indexed bytes | Physical files including index |
| --- | --- | ---: | ---: | ---: |
| experiments/source_appearance/static_choice_draft_20261113 | 9ee70b5f50ea95f0f0b8487d59c04b82b90d80afe5b32c37c6e354cc21d46332 | 53 | 344989 | 54 |
| experiments/owner_review/relocatable_prep_20261113 | ea345867bbccc96f21e50237c1e5fa2c7d572513b4f45aaf2112f304669493bf | 21 | 513942 | 22 |

The static packet uses `FILE_INDEX.json`; the relocatable packet uses `INDEX.json`. No gzip files occur in either requested packet, so bounded decompression was unnecessary. The inspected contents are source, text logs, metadata and documentation. No native model/archive, packed project, raw decoded geometry, image, audio or installed runtime payload is present. Authored table-catalogue result files contain names, indices, hashes, vertex counts and explicit false native-fidelity/resource/correspondence flags; they contain no vertex arrays.

Additional nested checks matched:

- Static `SOURCE_INDEX.json`, anchored at `overlay/`:15 files,175923 bytes.
- Relocatable `audit/INDEX.json`:2 files,3803 bytes.
- Relocatable `audit-eol/INDEX.json`:2 files,2422 bytes.

One documentation finding remains: static `catalogue_source/FILE_INDEX.json` is the copied historical local nine-file index. Eight rows are present in that nested copied folder,46822 bytes; its `source_mdl_choices.py` row is absent there. The exact missing13104-byte source with SHA `a0f5e551ba9e2e38e3a92ca1d824a09311bf4ec4979a0d9947c128d15666e555` is present and correctly indexed at `overlay/tools/source_mdl_choices.py`. This does **not** invalidate the authoritative root index. Label the nested index and its README's standalone test command as historical/local-only so a future reader follows the root README's working `overlay/tests/` commands. Do not rewrite historical proof as though it originally used the compact layout.

Scope labels are accurate: the static packet is explicitly a draft/unshipped source proposal,82 authored Python methods, with Godot/UI/native/conversion/graphics still unrun for these bytes. Its historical14 conversions/388 derived app checks are distinguished from the new chooser. The relocatable packet is preparation, with `new_review_built:false`, `new_replay_run:false`, dry plans and explicit future canonical/release/lease requirements. Its included default-runtime probe records a separate narrow historical headless exit0; it does not certify a relocated review or129 replays. The final README is expressly a template written only after future success.

This audit performed no tests, Godot/Blender/conversion/GPU/tool launches, model reads, packet edits, main edits or Git operations. Live main was not used as a fixed reference. Findings apply to the exact top-level index hashes above; later publication edits require a fresh index check.
