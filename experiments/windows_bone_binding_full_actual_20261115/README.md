# Actual complete Windows bone-binding verification — November 15, 2026

`full/` is a byte-exact copy of the independently reviewed 468-file consolidated packet plus its original INDEX. That INDEX is unchanged. `execution/` separately preserves the actual recipe-copy provenance and reviewed source index. OUTER_INDEX covers the complete new wrapper.

Retrieve this directory from the saved Git checkpoint, verify every OUTER_INDEX length/hash, then verify full/INDEX.json. Use full/provenance/LOSSLESS_ALIAS_MAP.json and its retained original summary/audit indices to restore raw metadata: gzip_decode means lossless gzip decompression followed by the declared raw size/SHA check. Original absolute paths remain historical provenance; they are not instructions to execute old launchers. App source is recoverable at f0dd57a2e568089d396fecba819ab987da658bf0. Follow the current pickup for fresh tests.

This is evidence and reproduction metadata, not an app, artwork or media bundle. Original models, projects, native coordinates, outputs and tools remain protected locally. Earlier failures and the interrupted run are not relabelled. Formal acceptance counts do not change from this packet alone.
