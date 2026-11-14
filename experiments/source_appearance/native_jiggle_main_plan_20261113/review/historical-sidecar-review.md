# Historical sidecar-planner review

This review applies only to adapter SHA256 `b6153f4c75e8d8f374d7bced75bab1e12d1e1fbf2eb17f5ea0675f8d8f35e4b7` and the original25 authored tests. Root subsequently replaced that design with a smaller inline-or-omission adapter. This is historical evidence, not approval of the superseded sidecar API.

Two actionable defects were reproduced independently:

1. `plan_report` classified over-budget or nonfinite baseline reports before validating retained metadata's original-source context. With a valid retained attempt from original sourceA and base.source_sha256 changed to sourceB, it returned baseline_report_over_budget or baseline_unserializable rather than SourceIdentityError. Retained identity must be checked before optional serialization/budget fallbacks in the replacement implementation.
2. `confirm_artifacts` checked the outer receipts dictionary but assumed its named inner receipt had a .get method. `{METADATA_FILE:None}`, a boolean or a list raised AttributeError instead of the explicit sidecar_not_published fallback. The replacement design removes this API and the entire sidecar branch, so this issue is historical only.

All25 existing tests passed independently in memory; their source bodies were unchanged and only the top-level output-folder creation was suppressed. Additional checks showed compact metadata exactly131072 bytes was admitted and131073 bytes produced metadata_budget status without partial values. No actual Junko conversion, runtime, GPU, SourceIO import or report-fit claim was performed. Source files and prior reports were unchanged.

Reproduction details, original source hashes and test transcript are frozen in `adapter-review-initial.json` and `adapter-review-initial-tests.txt`.
