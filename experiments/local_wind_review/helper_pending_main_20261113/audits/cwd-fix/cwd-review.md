# Worker current-directory review

Static review found no new semantic or ownership regression in using the explicit validated profile work root as the worker current directory. Executable, worker script and all main/work/owned/job arguments remain absolute. Isolated Python omits CWD from import lookup, and worker operations use explicit job paths. The request-file check traverses and rejects reparse parents before launch. Job assignment, start gate, retained process identity and cleanup remain unchanged.

The work root must be an existing directory usable by CreateProcess; this is not an unlimited-long-work-root claim. The accepted minimal probe separately establishes that the 260-character job cwd fails with Win267 while the 194-character work root starts the approved child and reads the same 273-character request path. The extended-prefix refusal is retained.

This reviewer performed no new runtime launch. Actual long-job popup regression and fresh source-bound CPU/GPU passes remain root-owned. Exact reviewed source hash is in `cwd-review.json`.

The first minimal probe captured its request hash after the read only; its raw request_preserved flag is not treated as a before/after hash proof. The separate extended-prefix probe recorded the prior identity and its preservation result.
