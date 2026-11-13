# Pending review-package checker

This standalone checker is preserved before its actual six-project run. It has
25 CPU checks and a headless syntax pass; it has not validated any review package
at runtime. Do not describe it as a successful native or owner review.

Copy the three overlay files into a new owned source checkout. Keep the supplied
private six-package review under that checkout/output, with its copy and package
preflight manifests. Run the exact-commit snapshot builder first, then follow
`docs/owner_review_validation.md`. All graphics use the built Studio's
`run.command` and fresh private Windows desktops. No installed app is replaced.

The source verifier and README in `reference` retain the CPU-probe context; review
their session paths before relocating. The actual application, package replay,
source-fidelity, owner/device and clean-install checks remain separate.
No model, HAS, PNG, audio or other private art payload is included here.
