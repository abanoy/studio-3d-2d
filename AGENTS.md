# Hybrid studio continuation

Read the complete local `CODEX_CUSTOM_ANIMATION_STUDIO_SPEC.md`, parent `LLM.md`
and `docs/progress_memo.md` before editing. Preserve the essential workflow:
3D environment → animated camera → independent 2D cels → synchronized preview → MP4.
Read `docs/design/HAS_2026-10-29_Voice_Design_Addendum_for_Codex.md` in full and
`docs/voice_addendum_audit.md`. Owner clarified on 2026-10-29: the addendum overrides
earlier conflicting decisions. Keep its OPEN/SUGGESTED/PREFERENCE distinctions.
Read actual code; records are not tests you ran. Work in small runnable increments.
Do not overwrite the separate artist-animation-assistant prototype or Cloudflare app.

No cloud calls, downloaded art, compulsory AI, broad UI frameworks, stage 3–5 features
or publishing without the owner's authorization. Preserve original source assets.
Do not weaken path checks or silently flatten cels. Clearly distinguish implemented,
tested, planned, and unsupported. Ask for decisions only when actually needed.

Godot is pinned to 4.6 stable standard; GDScript, no .NET packages. Main application
is `src/app.gd`. Run `python tests/verify.py` for real GPU and encoder verification.
Use an absolute writable `--log-file` when invoking Godot in the restricted workspace.
Document changes/limitations and append accurate history to the current worktree's
root LLM.md. No subagents are required for this initial increment.

Owner requirement, 2026-10-30: automated app tests/screenshots must stay hidden and
must not take focus on the owner's desktop. Use run.command() and its private
Windows desktop launcher for graphical tests. If desktop creation is denied, use
the approved host execution context or continue nonvisual work; never silently
fall back to a visible Godot window. Normal owner-launched Studio stays interactive.
