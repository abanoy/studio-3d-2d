Source-only installed-Git link-policy successor of the sealed097e binding helper.
Root's3a full is running. Do not execute B preparation or launch B until Root's
actual full/native lane has closed. No admission or diagnostic was created here.

Root reported that the original helper refused before engine/admission at its
initial Git identity check because installed Git has two legitimate hard links.
Its approved identity was unchanged:46,480 bytes,mtime_ns1760720930000000000,
SHA256544548de8c9bed98eb90531729a2955f554e7009338788b68777258ea61867e4.
The actual refusal and original packet remain unchanged.

The new prepare_root.py changes only the two occurrences of
`reader.identity(S.safe(GIT), single_link=True)` to `single_link=False`.
Both the initial check and final preservation recheck retain exact bytes,
mtime and SHA256 equality against the same fixed Git descriptor. The pinned
identity reader's stable-read checks remain unchanged. The only Git command
remains the read-only `[str(GIT), 'rev-parse', 'HEAD']` invocation.

Every other source byte is identical to the original7b171aacc66c23a4d48f02f6801abf553b042349f2ffd105f791d9b2dd9b0d00.
In particular the generic/source/model descriptor still uses
`reader.identity(path, single_link=True)`. No installed tool, model, source,
cache, private/current output or Review file was changed or read during these
synthetic tests. The whole inverse restores the exact original helper bytes.
The original five test methods are copied exactly; three extra methods exercise
both actual Git guard expressions with synthetic two-link metadata, reject
changed byte/mtime/hash identities, retain source hard-link refusal and verify
the unchanged read-only command. All eight CPU methods passed.

The binding API is unchanged. After actual lane closure, Root invokes this
packet's absolute prepare_root.py path with `--preparer-index-sha256` set to
this new packet's INDEX hash, `--root-lane-closed`,
`--cold187-disposition NOT_STARTED_CURRENT_CONTEXT`, `--pose-source` and
`--transform-source`. All other defaults/optional arguments are unchanged.
The preparer emits private binding files and ROOT_COMMAND.json, then exits.
Root must wait for its terminal return before separately launching that JSON
command. The helper never launches B itself and claims no current/full/native
qualification. Root's ongoing full must not be interrupted for this helper.
