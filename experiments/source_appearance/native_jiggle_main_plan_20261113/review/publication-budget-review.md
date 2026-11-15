# Independent publication-budget review

No inherent blocker to an output-only publication adapter was found. The following details are required to keep its result faithful to current static imports.

## Existing behavior, directly inspected

`tools/blender_source_bridge.py:439` constructs the complete report and line454 writes `json.dumps(report, ensure_ascii=True, indent=2)` using `Path.write_text(..., encoding="utf-8")`. The default Windows text newline translation makes physical CRLF bytes; there is no UTF-8 BOM and no appended final newline. The bridge does not enforce a report-size cap itself here.

`src/pose_editor.gd:200` reads adjacent `parameters.json`. It rejects unreadable files or a physical byte length **greater than262144**, then requires parsed JSON to be a dictionary. An exactly262144-byte valid report is admitted. The complete parsed report becomes `data.metadata.native_parameters`; the path to the preparation bundle is retained. Its existing note explicitly says only the GLB and supplied report are managed. An added external native-jiggle JSON or status file is neither automatically loaded nor packed by this path.

`tools/has_project.py:30,78` separately caps entire `project.json` at1048576 bytes. The container header also has its own1048576-byte limit at line433. Several imported reports share the project limit with poses, keys, layers, audio and other data. A report below256KiB is not a promise that a project containing it can be saved. `src/contact_editor.gd:208` estimates aggregate scene metadata using compact UTF-8 JSON plus8192 bytes, while `has_project.py` authoritatively checks the actual snapshot bytes. Do not infer save roundtrip from adapter-only tests.

## Concrete identity distinction

`prepare_source.py:181` sets request source to a staged native asset but sha256 to the original selected input digest. `blender_source_bridge.py:443` labels that digest source_sha256. For container imports this differs from the selected native MDL digest. `source_appearance.py` already keeps original-source and native-model hash namespaces separate. Compare native_mdl_sha256 with the MDL bytes, and original/source_sha256 with the original input identity. Do not compare report source_sha256 directly with the MDL digest. A mismatch is a distinct integrity error and must never publish numeric values or be relabelled unsupported layout.

## Exact serialization contract

Finalize one byte string for every prospective file before checking its budget. For the current Windows report contract: serialize with the same ensure_ascii=True, indent=2 and insertion order, convert serializer-produced LF to CRLF exactly once, then encode UTF-8 without a BOM or final newline. Publish those exact finalized bytes with a binary writer in a future integration. Alternatively, retain the existing text writer and only simulate its newline translation when measuring, without feeding pretranslated CRLF back into it. Preconverting to CRLF and then using default Windows write_text would create CRCRLF and defeat the measurement.

Measure the standalone inert metadata serialization against131072 bytes and the **fully nested complete report serialization** separately against262144 bytes. Added nesting increases indentation overhead. For the actual Junko proposal, standalone pretty metadata is108386 LF bytes or112575 CRLF bytes; nesting under native_parameters.native_jiggle alone is129389 CRLF bytes before existing report fields. The original compact JSON file is67525 bytes including its final LF. These distinct sizes must not be interchanged.

No-JIGGLE and BSP paths must preserve baseline report bytes, ordering, formatting, warnings, counts, view and metadata exactly, with no new status keys or optional sidecars. A verified zero-rule MDL49 may take this no-op path; an unsupported layout is not evidence that it has no declarations. Avoid parsing/reformatting an already supplied base byte string merely to return a no-op result.

## Proposed deterministic branch semantics

1. Capture the exact legacy baseline report bytes. If already over262144 bytes, preserve that baseline and label the existing admission failure; optional metadata must not compact, truncate or otherwise make the base report appear fixed.
2. Skip BSP unchanged. For a supported, integrity-bound MDL with zero JIGGLE declarations, return unchanged report bytes and no sidecars.
3. Keep an integrity mismatch as its own error branch with no numeric publication. Do not catch it with unsupported-layout/count/optional-budget cases.
4. For supported inert metadata of at most131072 standalone serialized bytes, try a complete report containing the full metadata in a reserved additive namespace. Only choose this branch if the finalized full report is at most262144 bytes.
5. If full metadata fits its budget but the complete embedded report does not, publish the complete bounded metadata externally as fixed-name `native-jiggle.json`. Try a compact status in the report containing a fixed reason code, filename, byte count, SHA256, applied=false and binding_status=unattempted. Require the finalized status-bearing full report to fit262144 bytes.
6. If even that compact status would exceed the report cap, preserve the baseline report bytes exactly and emit fixed-name `native-jiggle-status.json`. The status may point to the bounded external metadata and explicitly say it is external-only/unapplied/unbound. This status sidecar is not automatically read by current UI or preserved in HAS.
7. If the metadata itself exceeds131072 bytes, or layout/count is unsupported, do not publish an oversized numeric sidecar or a truncated subset of rules/fields. Publish only bounded explicit optional-unavailable status with a fixed reason code, in-report if it fits and otherwise in the fixed status sidecar. Valid static report admission remains unchanged.

A status-sidecar cap such as4096 bytes should be fixed and tested, with a closed field set and bounded messages. Never copy arbitrary exception strings, source paths or large arrays into the fallback status. Keep source/procedure/rule flags separate. Treat a collision with an existing reserved metadata key as an explicit optional conflict, preserving existing data rather than overwriting it.

The pure adapter should return a publication plan and finalized byte strings. Future file publication must successfully finalize sidecars before a report references them; a sidecar-write failure must not leave a report claiming an absent or stale sidecar. This is an integration concern, unproven by a pure planner. No values should be auto-bound to joints, Hair & clothes, physics or a runtime solver.

## Meaningful tests to require

- Exact256KiB report admission, plus one byte; exact128KiB standalone metadata admission, plus one byte; full nested report measured independently.
- Windows CRLF versus LF, non-ASCII names escaped by ensure_ascii, no BOM, no trailing newline, and no CRCRLF.
- Base just below the cap where full metadata fails but compact status fits; base at the cap where any status fails and baseline bytes remain identical.
- Base already oversized retains identical bytes and existing failure classification.
- Unsupported layout/count/unknown bits and metadata budget remain optional-unavailable; integrity mismatch remains distinct with no values.
- No-JIGGLE MDL and BSP return identical report bytes, including warnings/materials/counts/suggested_view, with no new optional outputs.
- External sidecar complete values/hash and explicit inert status; absence of native binding/physics/generated-helper fields; no reserved-key overwrite.
- Aggregate HAS project-save limits remain an explicit unresolved integration boundary; no adapter-only roundtrip claim.

No production source, runtime or original asset was edited. This report proposes semantics for an output-only draft and grants no integration/deployment approval.
