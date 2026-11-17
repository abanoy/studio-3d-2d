# Docking source audit — 2026-11-16

Scope: read-only comparison of `src/workspace_layout.gd`, `src/dock_tree.gd` and the World rail additions in `src/world_selection.gd` in `C:/a/Programming/cloudflare/has-neon-review-20261116-c2d52ff` against `C:/a/Programming/cloudflare/has-acceptance-session-20261111`. Read relevant Step 3, grab-strip, full-height rail and final contract sections of `docs/REDESIGN-PORT.md`. No engine, CIM or Git commands were run. This is source evidence, not a Windows interaction result.

## Finding

### P2 — Narrow World docks outside the left edge enter a rail with no unfold button

Location: redesign `src/workspace_layout.gd:282`; related `:260–261`, `:294–301` and `src/world_selection.gd:231–234`.

`refresh_world_mode()` enables the rail whenever the World panel is less than 140 px wide, neon is active and World is not floating. It does not check the dock edge or whether World shares a tab group. `style_world_unfold()` shows the unfold button only when World's stored edge is `left`, and `unfold_world()` also refuses every other edge. Rail mode hides the hierarchy Tree and help label. Thus a narrow right/top/bottom World group can hide its full list without supplying the advertised direct unfold action.

Reproduction for a future private UI check: move World to a right-side dock (or split it beside another dock), narrow its group below 140 px, and select its tab if necessary. Source predicts an icon rail with no unfold button; widening the splitter manually is the only local recovery. The Step 3 contract says tab groups elsewhere use the full list, and the source comment at `workspace_layout.gd:32–33` repeats this intent.

Suggested correction: limit rail mode to the intended left-dock placement (and solitary placement if that is the contract), or provide an unfold action that resizes the actual dock leaf wherever World is placed. Re-evaluate rail mode after placement changes as well as width changes if location becomes part of the predicate.

## No additional actionable finding

- Recursive split/tab membership, pruning, v1/v2 migration, per-leaf selection, bounded state validation and floating geometry restoration retain the baseline algorithm; the `dock_tree.gd` changes are styling.
- The full-left physical nesting is reversible in source, reuses the four existing split instances, and is derived from saved membership rather than adding an unpersisted layout choice.
- The grab strip checks Home/export/modal state and gives primary splitter hit areas priority. Searching nested split controls under `vertical` does cover strip-bearing panels: full-left mode requires World alone on the left; once another panel joins that edge the layout returns to the original nesting.
- No source proof was found for another persistence, lost-control or nested-split regression. Native floating-window and drag-area geometry still need Windows runtime checks.

## Reviewed source identities

- `workspace_layout.gd`: `81e905a8c1bb7c25ae2ef7e9b84b3c8ab3043cfb226db4a50e772622922371bf`
- `dock_tree.gd`: `8b933a57aedcaf8e54e02b49eae7fef7fdf2cb6ade1c5aa6c6e2e3dcb00aa90a`
- `world_selection.gd`: `f37ef0081de1637025a129ab3e4d651bbb9915658555bc98837be3c6bea193d5`
