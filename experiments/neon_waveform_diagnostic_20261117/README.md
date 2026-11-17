# Waveform transient palette diagnostic

Source-only diagnostic derivative of the sealed palette successor `9775d5a497b64025fc93d958aa1a900316288b5fb2fb7fb34f77f3340ec3aa66`. The root observed Classic 14/0 and Neon 14/1 with three matching bars in `output/neon-waveform-palette-profiles-20261117-attempt1`. This packet has not been parsed or run in Godot.

`waveform_levels_smoke.diagnostic.gd` retains every one of the predecessor's 14 check source lines, including its original RGB tolerance and four-transient condition. Only diagnostic print/data collection statements are added. Removing the six recorded insertion blocks recovers the predecessor bytes exactly. No scene size, expected color, product source, sample position or timing behavior was changed.

For each positive fine-waveform bucket it reports its index/value, raw and right draw X, renderer clip-cull condition, amplitude, clip rectangle, global/integer sample position, selected-border condition, expected RGB, actual match, bounds validity and all nine actual RGBA samples with offsets. A context line records theme, selected audio, source fill/wave RGBA, computed expectations, viewport and scroll positions, image size and the fact that text is drawn after the waveform. Invalid sample bounds still fail the existing check and skip pixel reads.

The root must stage this separately, retain the earlier failed result, run the same profile and inspect the four `WAVEFORM_TRANSIENT_DIAGNOSTIC` records. The purpose is to identify the failing bar before choosing a fix. This packet claims no diagnosis or runtime success. No engines, Win32, CIM, Git, native arrays or private logs were used by its preparer.

`prepare.py` constructs the derivative using only the pinned predecessor; `SOURCE_PROOF.json` records the insertion-only proof and exact identities. Once `INDEX.json` exists, preparation refuses regeneration.
