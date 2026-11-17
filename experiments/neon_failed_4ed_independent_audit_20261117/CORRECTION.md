# Scope of the closed4ed helper launch wording

The immutable original
`experiments/neon_failed_4ed_actual_packet_20261117/README.md`
(SHA256 `72215f53ba8f442efe17b5f0328f3713b3e8f050e36ca31752f6bcd8c9a81f58`)
contains: “before running checks or launching a process.”

The supported boundary is **before snapshot creation or helper engine, worker
or graphical launch**. The unchanged pinned driver
`tests/verify_helper_preview.py` (SHA256
`d92e3e5f7286866cde895bbdef400c59028b5f59650c2d021bc55446b969b878`)
calls Git subprocesses in `source_state` before `validate_port`, and its final
head-preservation check calls Git again. An assertion that no subprocess of any
kind was launched would be broader than this source supports.

The actual helper report records checks0, an empty results list, null snapshot
root, no native request/input/fidelity, no graphical attempt and the strict stale
app-source-pin refusal. Those facts remain unchanged. The original archive is
preserved byte-exact, and this addendum makes no helper-success or full-PASS claim.

This independent audit first checked all71 original bindings before root's
authorized source-manifest successor. A later strict recheck refused when the
live source manifest became the reviewed2c9e4836 successor. The refused source
draft and observed delta remain here. The final audit checks70 current original
paths and separately joins the archived ce456c5e manifest to its preserved exact
candidate-original copy. The closed run's before/after source manifests retain
the old source identity. Active focused-run outputs were not read.
