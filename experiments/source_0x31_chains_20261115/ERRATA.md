# Native25 rule correction

The frozen README's statement that native25 has a separate retained Source rule is **incorrect**. The exact retained parameters report (`b807fc82ac1b1d1658b659b41250001e3bdecde99c3d32764122c2add6b51eed`) contains49 jiggle rules and **none belongs to native25**.

Native25 is the authored intermediate `1Steps-1_L`, parent7. Native26 is its child and native27 is native26's child. The implemented four-rule experiment correctly solves17/18/26/27 and transports native26 through authored25; it creates no native25 rule. The code and numeric profile need no change for this correction.

Any future all49-rule orchestration must also retain no-rule intermediate bones such as25 in actual parent traversal. It must not infer a missing rule from a child's rule or invent coefficients for that intermediate.

This erratum is intentionally outside the original frozen INDEX. The earlier README and failed metadata-preparation history remain recoverable. No original indexed file, driver, production source, assertion or tolerance was changed. Actual engine results remain separately scoped evidence.
