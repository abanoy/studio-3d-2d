# Explicit preview controller transport

Launch the indexed `candidate/tools/wind_preview_controller.py` with the approved absolute CPython 3.13 executable, `-I -B -u`, and these arguments: `--main-root`, a fresh descendant `--owned-root` below that root's `output`, `--parent-pid`, `--parent-created-100ns`, a 32-character lowercase hexadecimal `--session`, `--controller-sha256`, and `--python-sha256`. `--idle-timeout` defaults to 30 seconds and may be within (0,120]. An existing owned directory is refused. The host creation identity must be captured from the known live host, not inferred from a later unrelated process with the same PID.

Each input is one ASCII JSON object followed by LF. Unicode text and paths travel through JSON escapes. Maximum command size including LF is 1 MiB. Duplicate keys, nonfinite constants and non-ASCII bytes are refused. There are four queued inputs, four queued output events and at most 128 serviced command records. Output events are at most 16 KiB each; worker stdout/stderr have the preceding adapter's separate caps. Queue overflow ends the session and closes ownership.

Every command contains `format: "has_wind_preview_controller_command_1"`, the exact `session`, a strict integer `seq` equal to the preceding accepted envelope sequence plus one, `op`, strict integer `generation`, and the exact current `nonce` (null before a draft). Refused command envelopes with a valid next sequence consume that sequence; duplicate/out-of-order sequences do not. Wrong tickets and replay are checked before side effects. The session identifies a dedicated trusted host pipe; it is not network authentication.

| Operation | Additional fields | Behavior |
| --- | --- | --- |
| `start` | `source`, reviewed `items`, complete `context`, optional `mode` (`focused-single` or `included-batch`) | Validates first, then starts one owned child. An active draft must be cancelled before replacement. An already prepared draft may be replaced using its current ticket. |
| `poll` | Current complete `context` | Reports running, or a checksum-bound prepared-hidden result after exit/cleanup. Context or receipt drift invalidates the ticket. No pending draft is refused. |
| `cancel` | None | Invalidates the current building/prepared ticket and closes child ownership. No pending draft is refused. |
| `close` | None | Invalidates the current ticket, closes ownership, emits a bounded close event, then exits. Initial idle close is valid. |

Each event contains `format: "has_wind_preview_controller_event_1"`, `session`, last accepted `seq`, `event`, current `{generation,nonce}` in `ticket`, and `phase`. Event names are `ready`, `started`, `running`, `prepared`, `refused`, `invalidated`, `cancelled`, and `closed`. `ready` binds the controller and host native identities, source hashes and Python fingerprint. `started` binds the child owner and job. `prepared` carries only the exact job path and the trusted completion object (including full receipt digest); the potentially large receipt remains a separate checksum-bound artifact. A host must verify session, sequence, ticket, current context and its own pending request before consuming it, then still perform actual hidden-import/binding validation.

EOF discards any remaining queued input and cancels the session. It is not a substitute for reading a close acknowledgement. Host exit, transport error and idle timeout independently trigger invalidation/cleanup. Closing output or ceasing to drain it cannot keep the child alive through a blocked writer. The controller writes a bounded `controller-outcome.json` only as audit evidence, never as the expected trusted preparation token. Abrupt controller termination cannot publish a final outcome; the retained observer receipts provide that experiment's evidence.

No operation can author or install the original model, apply an edit, write Undo, or enable app physics. `prepared_hidden` is the end of this CPU layer.
