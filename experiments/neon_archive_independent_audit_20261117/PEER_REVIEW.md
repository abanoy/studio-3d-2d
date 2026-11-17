# Independent archive receipt and interpretation review

Reviewed immutable sequence packet INDEX
`e8a7f25ed780eaac2b6d0611fcbc7c7d388945fd82e7f23df6979cf0147060c9`
and standalone32 packet INDEX
`db32fd9398c358a74b455d26e074482c717c456b812b17fd43a3d5233e41618e`.
Archive object payloads were decoded through their exact bindings and checked
against stored/original byte lengths and SHA256 while consulted. No builder was
imported or run. No active full-run state/report/log, original native asset,
engine, process query, CIM, Git or review/runtime write was used.

## Physical receipts

The sequence contains 25 physical receipt files for 23 distinct desktop/child
identities: 21 exit 0 and two exit 1. The duplicate pairs are the typed29
lifecycle receipt and the rail diagnostic receipt, each preserved both at its
global receipt path and as a stage-local copy. Each pair has identical decoded
typed content. No conflicting ownership copy was found.

All selected receipts affirm private window, child desktop, job closure and
desktop closure; foreground observation and desktop switching are false.
Monitor/enumeration/error/cancellation fields do not indicate an unexpected
wrapper failure. The two exit-1 jobs are the failed rail45/1 run and its separate
rail diagnostic. Their failures remain recorded rather than counted as passes.

Twenty-one sequence jobs have direct absolute command/report receipt-path
references. Twelve inline receipt occurrences exactly match the physical
payloads. The standalone32 packet has two identical physical copies for one
exit-0 job and a direct command receipt reference. These are actual archived
GUI jobs; no historical or headless-job count is inferred.

**Attribution boundary:** the failed baseline and two-file-fix controls receipts
ending `dfe4f265026a40d88ad8a813a24aad0a` and
`77671800f00448538ba348b51cea2950` are closed physical receipts, but their failed
wrappers did not emit a report receipt path. The archive selects them with the
recipe label `exact_controls_physical_receipt` and does not retain original file
mtime. Their assignment to those two phases cannot be independently derived
from archive bytes alone. This is not evidence they are the wrong receipts, and
does not prevent preservation of the failures. A later source-filesystem mtime
observation must be labelled supplemental, rather than presented as an existing
archive-byte proof or a new process observation.

## Outcomes retained

All eleven archived phase-verification summaries match their bound raw JSON.
The baseline, two-file-fix and font-cache controls each retain raw 48/0 results;
the first two strict wrappers fail on diagnostics, while the cache controls pass.
The original typed lifecycle parse attempt retains all six Variant-inference
parse errors. Its corrected standalone run retains 29/0 separately.

The first cache-era standard attempt retains inset 12,384/0 but fails strict
file/marker equality: only the projection-error and ray-error numeric precision
fields differ. The later first 12,504 suite completes inset, behavior and compact,
then records rail45/1; lifecycle GUI execution is not invented. The transaction
successor retains all five exact result counts totaling 12,504 with zero failures,
plus separate controls/resize/docking/nested successes. Standalone32 retains
32/0 and all four case names, including `withheld-control-transaction`; it does
not change formal 12,504 integration. Neither packet claims canonical full
Windows PASS, merge, native-normal qualification or owner acceptance.

## Corrected interpretations

The bound ordered engine log
`experiments/neon_workspace_font_diagnosis_20261117/first-lifecycle-fix-ordered-engine.log`
places the splitter PASS at line 27, the first fd-null error at line 28, and the
docking-swap PASS at line 43. This supports live resize/docking chronology.
Concatenated stdout/stderr cannot establish that ordering; the old after-free
attribution is correctly retracted without altering the old failed archive.
This does not establish a particular internal TextServer mechanism.

The old native-name matcher in source `9f604060…` independently AST-decodes to
one backslash before `.exe` and matches all four native ASCII names. No historical
bad hash has been demonstrated. The strong driver's preserved `1ffd784a…` and
current `234a3f6a…` have identical ASTs; the correction changes comments only.
The archive correctly retracts the overescaping suspicion while keeping the
strong driver's broader helper/coordinator scope and host-tested positive/negative
cases separate. No prior physical closure result is invalidated by that suspicion.

Source/receipt/outcome review found no additional blocker within these stated
limits. The parent performs the separate full membership/original-root/privacy
audit; this note does not replace it or qualify the active canonical run.
